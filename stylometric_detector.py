"""
Detection Signal 2: Stylometric Heuristics

Measures statistical writing features and produces an AI-likelihood score
between 0.0 (appears human-written) and 1.0 (appears AI-generated). Per the
planning document, the signal uses exactly four metrics:

    1. sentence length variation
    2. vocabulary diversity (type-token ratio)
    3. punctuation density
    4. average sentence length

This detector is fully deterministic and self-contained: it performs no API
calls and shares no state with the LLM classifier (Signal 1), so the two
signals are genuinely independent.
"""

import re
import statistics

# Text shorter than this many words is too small for the statistics to be
# meaningful, so we return a neutral score instead of an unreliable one.
MIN_WORDS = 15

# Neutral score returned when the text is empty or too short to analyze.
NEUTRAL_SCORE = 0.5

# --- Metric calibration ranges -------------------------------------------
# Each metric is mapped to a per-metric AI-likelihood sub-score in [0.0, 1.0]
# via a simple linear ramp between a "human-like" bound and an "AI-like"
# bound. The numbers below are deliberately simple, hand-picked thresholds
# meant to be easy to read and adjust later, not statistically trained. The
# ranges are intentionally wide so a single sample near one extreme produces
# a moderate sub-score rather than saturating at 0.0 or 1.0 -- this keeps any
# one metric from dominating the averaged result.

# Sentence length variation, measured as the coefficient of variation
# (stdev / mean of sentence word counts). Humans write with "bursty",
# uneven sentence lengths (high variation); AI tends toward uniform lengths
# (low variation). Low variation -> more AI-like.
CV_AI_MAX = 0.15    # variation at/below this looks very AI-like  -> 1.0
CV_HUMAN_MIN = 0.55  # variation at/above this looks very human     -> 0.0

# Vocabulary diversity (type-token ratio = unique words / total words).
# Repetitive, lower-diversity text reads as more AI-like; rich, varied
# vocabulary reads as more human. Low TTR -> more AI-like. Short texts almost
# always have very high TTR, so the human bound is set high (0.80) to avoid
# this metric flat-lining at 0.0 on every short sample.
TTR_AI_MAX = 0.45    # diversity at/below this looks very AI-like    -> 1.0
TTR_HUMAN_MIN = 0.80  # diversity at/above this looks very human      -> 0.0

# Punctuation density (punctuation marks / total words). Long, polished
# AI-style prose tends to chain clauses together with commas, raising
# punctuation density, while terse casual/personal writing uses fewer marks.
# High density -> more AI-like. (This is the weakest, most ambiguous signal,
# so it carries a lower weight below.)
PUNCT_HUMAN_MAX = 0.05  # density at/below this looks very human       -> 0.0
PUNCT_AI_MIN = 0.20    # density at/above this looks very AI-like     -> 1.0

# Average sentence length (words per sentence). AI tends toward longer,
# steady sentences; very short average sentences read as more human. The
# upper bound is set to 30 (not 25) so that a single long human sentence
# does not saturate this metric to 1.0. Long average -> more AI-like.
AVGLEN_HUMAN_MAX = 12.0  # short sentences look very human            -> 0.0
AVGLEN_AI_MIN = 30.0    # long sentences look very AI-like           -> 1.0

# Per-metric weights used to combine the four sub-scores. The two robust,
# structural metrics (sentence length variation and average sentence length)
# carry slightly more weight than the two noisier metrics (vocabulary
# diversity and punctuation density). No single weight exceeds 0.30, so no
# individual metric can dominate the final score. Weights sum to 1.0.
WEIGHT_VARIATION = 0.30
WEIGHT_DIVERSITY = 0.20
WEIGHT_PUNCTUATION = 0.20
WEIGHT_AVG_LENGTH = 0.30


def _linear_score(value: float, low: float, high: float) -> float:
    """Map ``value`` to [0.0, 1.0] as it moves from ``low`` to ``high``.

    Returns 0.0 at ``low`` and 1.0 at ``high``, ramping linearly in between
    and clamping outside the range. Works whether ``low`` < ``high`` (score
    increases with value) or ``low`` > ``high`` (score decreases with value).
    """
    if low == high:
        return 0.0
    fraction = (value - low) / (high - low)
    return max(0.0, min(1.0, fraction))


def _split_sentences(text: str) -> list[str]:
    """Split text into non-empty sentences on ., !, or ? boundaries."""
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


def _words(text: str) -> list[str]:
    """Extract lowercased word tokens (letters/digits/apostrophes)."""
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def get_stylometric_ai_score(text: str) -> float:
    """Return an AI-likelihood score in [0.0, 1.0] for the given text.

    0.0 means the text appears human-written; 1.0 means it appears
    AI-generated, based purely on structural writing statistics. Empty or
    very short text returns a neutral 0.5 rather than raising.

    Args:
        text: The submitted text to analyze.

    Returns:
        A float in the range [0.0, 1.0].
    """
    # Error handling: guard against non-string, empty, or too-short input so
    # the detector always returns a valid score instead of failing.
    if not isinstance(text, str) or not text.strip():
        return NEUTRAL_SCORE

    words = _words(text)
    if len(words) < MIN_WORDS:
        return NEUTRAL_SCORE

    sentences = _split_sentences(text)
    if not sentences:
        return NEUTRAL_SCORE

    # Word count per sentence, used by both the variation and average metrics.
    sentence_lengths = [len(_words(s)) for s in sentences]
    mean_length = statistics.mean(sentence_lengths)

    # --- Metric 1: sentence length variation (coefficient of variation) ---
    # A single sentence has UNMEASURABLE variation (not zero variation), so
    # return a neutral 0.5 rather than 1.0. Scoring it as fully AI-like was
    # wrong: it made every one-sentence text -- human or AI -- look AI.
    if len(sentence_lengths) < 2 or mean_length == 0:
        variation_score = 0.5
    else:
        cv = statistics.stdev(sentence_lengths) / mean_length
        # Low variation -> high AI score, so ramp DOWN from CV_AI_MAX to
        # CV_HUMAN_MIN (low=CV_HUMAN_MIN gives 0.0, high=CV_AI_MAX gives 1.0).
        variation_score = _linear_score(cv, CV_HUMAN_MIN, CV_AI_MAX)

    # --- Metric 2: vocabulary diversity (type-token ratio) ----------------
    ttr = len(set(words)) / len(words)
    # Low diversity -> high AI score.
    diversity_score = _linear_score(ttr, TTR_HUMAN_MIN, TTR_AI_MAX)

    # --- Metric 3: punctuation density ------------------------------------
    punctuation_count = len(re.findall(r"[.,;:!?\"'()\-—…]", text))
    punct_density = punctuation_count / len(words)
    # High density -> high AI score.
    punctuation_score = _linear_score(
        punct_density, PUNCT_HUMAN_MAX, PUNCT_AI_MIN
    )

    # --- Metric 4: average sentence length --------------------------------
    # Long average -> high AI score.
    length_score = _linear_score(mean_length, AVGLEN_HUMAN_MAX, AVGLEN_AI_MIN)

    # Combine the four sub-scores using the per-metric weights. Because the
    # weights sum to 1.0 and each sub-score is in [0.0, 1.0], the result is
    # guaranteed to stay in [0.0, 1.0], and no single metric can dominate.
    final_score = (
        variation_score * WEIGHT_VARIATION
        + diversity_score * WEIGHT_DIVERSITY
        + punctuation_score * WEIGHT_PUNCTUATION
        + length_score * WEIGHT_AVG_LENGTH
    )

    return max(0.0, min(1.0, final_score))
