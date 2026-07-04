"""
Standalone manual test for Detection Signal 1 (LLM classifier).

Calls get_llm_ai_score() with a few sample texts and prints the returned
AI-likelihood scores. Run directly:

    .venv/bin/python test_llm_detector.py
"""

from llm_detector import get_llm_ai_score

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
        score = get_llm_ai_score(text)
        print(f"[{label}] score={score:.2f}")
        print(f"    text: {text[:70]}...")


if __name__ == "__main__":
    main()
