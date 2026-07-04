"""
Standalone manual test for Detection Signal 2 (stylometric detector).

Calls get_stylometric_ai_score() with the same sample texts used to test the
LLM classifier and prints the returned AI-likelihood scores. Run directly:

    .venv/bin/python test_stylometric_detector.py
"""

from stylometric_detector import get_stylometric_ai_score

# Same samples used in test_llm_detector.py so the two signals can be
# compared on identical inputs.
SAMPLES = [
    (
        "Human, casual",
        "ngl i totally forgot we had that thing today lol. my bad, i was up "
        "way too late watching dumb videos and slept through my alarm again.",
    ),
    (
        "AI-style, polished",
        "In today's rapidly evolving digital landscape, it is important to "
        "recognize that effective communication plays a pivotal role in "
        "fostering collaboration and driving sustainable, long-term success.",
    ),
    (
        "Human, personal narrative",
        "The kitchen still smelled like burnt toast when my grandmother laughed "
        "and told me the story about the goat that ate her wedding invitations.",
    ),
]


def main():
    for label, text in SAMPLES:
        score = get_stylometric_ai_score(text)
        print(f"[{label}] score={score:.2f}")
        print(f"    text: {text[:70]}...")


if __name__ == "__main__":
    main()
