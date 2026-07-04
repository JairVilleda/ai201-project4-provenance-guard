"""
Standalone manual test for the integrated POST /submit endpoint.

Drives the endpoint end-to-end for four sample inputs (the Milestone 4
categories) using Flask's test client, so the request flows through both
detection signals and the confidence scorer exactly as a real request would.

For transparency it also prints each detector's individual AI-likelihood score
alongside the endpoint's JSON response. Run directly:

    .venv/bin/python test_submit_endpoint.py

Note: this calls the live Groq API (Signal 1) and appends entries to the
audit log, just as a real submission does.
"""

import json

from app import app
from llm_detector import get_llm_ai_score
from stylometric_detector import get_stylometric_ai_score

# Four representative text samples, one per Milestone 4 category.
SAMPLES = [
    (
        "Clearly AI-generated",
        "In today's rapidly evolving digital landscape, it is important to "
        "recognize that effective communication plays a pivotal role in "
        "fostering collaboration and driving sustainable, long-term success "
        "across organizations of every size and industry.",
    ),
    (
        "Clearly human-written",
        "ngl i totally forgot we had that thing today lol. my bad, i was up "
        "way too late watching dumb videos and slept through my alarm again. "
        "gonna grab coffee then head over, save me a seat ok?",
    ),
    (
        "Formal human writing",
        "The committee reviewed the quarterly figures and concluded that the "
        "shortfall stemmed from a single vendor delay. We recommend renewing "
        "the contract with revised delivery terms and a modest penalty clause.",
    ),
    (
        "Lightly edited AI writing",
        "Remote work changed how teams operate. Sure, it offers flexibility, "
        "but it also brings real challenges around communication and trust. "
        "Honestly, the teams that do well are the ones that set clear "
        "expectations early and actually stick to them.",
    ),
]


def main():
    client = app.test_client()

    for label, text in SAMPLES:
        # Individual detector scores, shown for transparency (the endpoint
        # itself only returns the combined confidence + attribution).
        llm_score = get_llm_ai_score(text)
        stylometric_score = get_stylometric_ai_score(text)

        # Drive the integrated endpoint.
        response = client.post(
            "/submit",
            json={"text": text, "creator_id": "test-creator"},
        )
        body = response.get_json()

        print(f"[{label}]")
        print(f"    llm_score         = {llm_score:.2f}")
        print(f"    stylometric_score = {stylometric_score:.2f}")
        print(f"    confidence        = {body['confidence']:.2f}")
        print(f"    attribution       = {body['attribution']}")
        print(f"    JSON response     = {json.dumps(body)}")


if __name__ == "__main__":
    main()
