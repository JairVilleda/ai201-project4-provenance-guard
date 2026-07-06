"""
Transparency Label Generator

Converts a final confidence score into a human-readable transparency label.

Per planning.md, the confidence score (an AI-likelihood in [0.0, 1.0]) maps to
exactly one of three labels. The thresholds come from the "Uncertainty
Representation" section and the label wording comes verbatim from the
"Transparency Label Design" section:

    - Likely Human: 0.00 - 0.29  -> High-confidence Human label
    - Uncertain:    0.30 - 0.69  -> Uncertain label
    - Likely AI:    0.70 - 1.00  -> High-confidence AI label

The cut points (0.30 and 0.70) are reused from the Confidence Scorer so the
label boundaries and the attribution boundaries can never drift apart.
"""

from confidence_scorer import UNCERTAIN_LOWER, UNCERTAIN_UPPER

# Label text copied verbatim from the Transparency Label Design section of
# planning.md. Do not paraphrase -- these strings are the specification.
HIGH_CONFIDENCE_HUMAN_LABEL = (
    "This content is likely human-written. Our analysis found strong evidence "
    "that this text was written by a person."
)
UNCERTAIN_LABEL = (
    "We could not confidently determine whether this content is AI-generated "
    "or human-written. The available evidence is inconclusive."
)
HIGH_CONFIDENCE_AI_LABEL = (
    "This content is likely AI-generated. Our analysis found strong evidence "
    "that AI tools were used to create or significantly assist this text."
)


def generate_transparency_label(confidence: float) -> str:
    """Return the transparency label text for a final confidence score.

    Args:
        confidence: The final confidence score in [0.0, 1.0], where 0.0 means
            the text appears human-written and 1.0 means it appears
            AI-generated.

    Returns:
        Exactly one of ``HIGH_CONFIDENCE_HUMAN_LABEL``, ``UNCERTAIN_LABEL``, or
        ``HIGH_CONFIDENCE_AI_LABEL``, with wording matching planning.md.

    Raises:
        ValueError: if ``confidence`` is non-numeric, NaN, or outside
            [0.0, 1.0].
    """
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        raise ValueError(f"confidence must be a number, got {confidence!r}")
    # NaN is the only float that is not equal to itself.
    if value != value:
        raise ValueError("confidence must not be NaN")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"confidence must be within [0.0, 1.0], got {value}")

    # Map the confidence score to a label using the same thresholds the
    # Confidence Scorer uses for attribution.
    if value < UNCERTAIN_LOWER:
        return HIGH_CONFIDENCE_HUMAN_LABEL
    if value < UNCERTAIN_UPPER:
        return UNCERTAIN_LABEL
    return HIGH_CONFIDENCE_AI_LABEL
