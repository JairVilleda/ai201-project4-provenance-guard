"""
Confidence Scorer

Combines the two independent AI-likelihood scores -- Signal 1 (LLM classifier)
and Signal 2 (stylometric heuristics) -- into a single confidence score and an
attribution result.

Per planning.md ("Confidence Scoring" and "Uncertainty Representation"), the
two scores are combined by simple averaging, and the resulting confidence
score is mapped to one of three attribution results using fixed thresholds.
"""

# Attribution result labels.
LIKELY_HUMAN = "likely_human"
UNCERTAIN = "uncertain"
LIKELY_AI = "likely_ai"

# Attribution thresholds, taken directly from the Uncertainty Representation
# section of planning.md:
#   - Likely Human: 0.00 - 0.29
#   - Uncertain:    0.30 - 0.69
#   - Likely AI:    0.70 - 1.00
# The cut points are therefore 0.30 and 0.70: a confidence score below 0.30 is
# likely_human, a score of 0.70 or above is likely_ai, and everything in
# between is uncertain.
UNCERTAIN_LOWER = 0.30
UNCERTAIN_UPPER = 0.70


def _validate_score(score: float, name: str) -> float:
    """Return ``score`` as a float in [0.0, 1.0], or raise ValueError.

    Both detectors are specified to return a value in [0.0, 1.0], so anything
    outside that range (or non-numeric / NaN) is a programming error rather
    than expected runtime data. Raising a clear, specific error here surfaces
    the problem instead of silently producing a meaningless confidence score.
    """
    try:
        value = float(score)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number, got {score!r}")
    # NaN is the only float that is not equal to itself.
    if value != value:
        raise ValueError(f"{name} must not be NaN")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be within [0.0, 1.0], got {value}")
    return value


def calculate_confidence(llm_score: float, stylometric_score: float):
    """Combine two AI-likelihood scores into a confidence score + attribution.

    Both inputs are AI-likelihood scores in [0.0, 1.0], where 0.0 means the
    text appears human-written and 1.0 means it appears AI-generated.

    Args:
        llm_score: AI-likelihood from Signal 1 (LLM classifier).
        stylometric_score: AI-likelihood from Signal 2 (stylometric heuristics).

    Returns:
        A tuple ``(confidence, attribution)`` where ``confidence`` is a float
        in [0.0, 1.0] and ``attribution`` is one of ``LIKELY_HUMAN``,
        ``UNCERTAIN``, or ``LIKELY_AI``.

    Raises:
        ValueError: if either input is non-numeric, NaN, or outside [0.0, 1.0].
    """
    llm = _validate_score(llm_score, "llm_score")
    stylometric = _validate_score(stylometric_score, "stylometric_score")

    # Combine the two independent signals by averaging, exactly as specified
    # in planning.md. Both signals contribute equally to the final score.
    confidence = (llm + stylometric) / 2.0

    # Map the confidence score to an attribution result using the thresholds
    # from the Uncertainty Representation section.
    if confidence < UNCERTAIN_LOWER:
        attribution = LIKELY_HUMAN
    elif confidence < UNCERTAIN_UPPER:
        attribution = UNCERTAIN
    else:
        attribution = LIKELY_AI

    return confidence, attribution
