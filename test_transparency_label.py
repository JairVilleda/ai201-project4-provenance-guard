"""
Standalone manual test for the Transparency Label Generator.

Exercises generate_transparency_label() with a representative confidence score
from each of the three threshold ranges defined in planning.md, and confirms
each returns the exact label wording from the Transparency Label Design section.
Run directly:

    .venv/bin/python test_transparency_label.py
"""

from transparency_label import (
    generate_transparency_label,
    HIGH_CONFIDENCE_HUMAN_LABEL,
    UNCERTAIN_LABEL,
    HIGH_CONFIDENCE_AI_LABEL,
)

# Each case is (label, confidence, expected_text). The confidence values are
# representative of each threshold range from the Uncertainty Representation
# section: Likely Human (0.00-0.29), Uncertain (0.30-0.69), Likely AI (0.70-1.00).
CASES = [
    ("High-confidence Human", 0.10, HIGH_CONFIDENCE_HUMAN_LABEL),
    ("Uncertain", 0.50, UNCERTAIN_LABEL),
    ("High-confidence AI", 0.90, HIGH_CONFIDENCE_AI_LABEL),
]


def main():
    for name, confidence, expected in CASES:
        actual = generate_transparency_label(confidence)
        status = "PASS" if actual == expected else "FAIL"
        print(f"[{status}] {name} (confidence = {confidence:.2f})")
        print(f"    label = {actual}")
        assert actual == expected, f"{name}: label did not match planning.md"

    print("\nAll three transparency label variants matched planning.md exactly.")


if __name__ == "__main__":
    main()
