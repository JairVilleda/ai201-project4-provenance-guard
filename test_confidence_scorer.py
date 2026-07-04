"""
Standalone manual test for the Confidence Scorer.

Exercises calculate_confidence() with representative pairs of detector scores
and prints the LLM score, stylometric score, combined confidence, and the
resulting attribution. Run directly:

    .venv/bin/python test_confidence_scorer.py
"""

from confidence_scorer import calculate_confidence

# Each case is (label, llm_score, stylometric_score). The scores stand in for
# what the two detectors would plausibly return for each kind of text.
CASES = [
    # Both signals strongly agree the text is AI-generated.
    ("Clearly AI-generated", 0.95, 0.85),
    # Both signals strongly agree the text is human-written.
    ("Clearly human-written", 0.05, 0.15),
    # Formal human writing: the LLM may over-flag polished prose, and the
    # stylometric signal reacts to its uniform structure -> should land in the
    # protective uncertain band rather than a false "likely_ai".
    ("Formal human writing", 0.45, 0.55),
    # Lightly edited AI writing: human edits soften both signals, so neither
    # is confident -> uncertain.
    ("Lightly edited AI writing", 0.60, 0.50),
]


def main():
    for label, llm_score, stylometric_score in CASES:
        confidence, attribution = calculate_confidence(
            llm_score, stylometric_score
        )
        print(f"[{label}]")
        print(f"    llm_score        = {llm_score:.2f}")
        print(f"    stylometric_score= {stylometric_score:.2f}")
        print(f"    confidence       = {confidence:.2f}")
        print(f"    attribution      = {attribution}")


if __name__ == "__main__":
    main()
