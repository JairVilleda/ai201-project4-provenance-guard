"""
Standalone manual test for the POST /appeal endpoint (Appeals Workflow).

Drives the full appeal flow with Flask's test client:
  1. Submit content and save the returned content_id.
  2. Capture the original classification from GET /log.
  3. Call POST /appeal with the content_id and creator_reasoning.
  4. Verify the confirmation response.
  5. Confirm through GET /log that the entry's status is now "under_review",
     the appeal_reasoning is populated, and the original attribution,
     confidence, and detector scores are unchanged.

Run directly:

    .venv/bin/python test_appeal_endpoint.py

Note: submission calls the live Groq API (Signal 1) and appends to the audit
log, just as a real submission does. The appeal itself reruns nothing.
"""

from app import app

SAMPLE_TEXT = (
    "The committee reviewed the quarterly figures and concluded that the "
    "shortfall stemmed from a single vendor delay."
)
APPEAL_REASONING = "This is my own writing; I never used any AI tools on it."


def _find_entry(client, content_id):
    entries = client.get("/log").get_json()["entries"]
    return next(e for e in entries if e["content_id"] == content_id)


def main():
    client = app.test_client()

    # 1. Submit content and save the returned content_id.
    submit_resp = client.post(
        "/submit",
        json={"text": SAMPLE_TEXT, "creator_id": "test-creator"},
    )
    content_id = submit_resp.get_json()["content_id"]
    print(f"Submitted content_id = {content_id}")

    # 2. Capture the original classification before appealing.
    original = _find_entry(client, content_id)
    print(f"    original status      = {original['status']}")
    print(f"    original attribution = {original['attribution']}")
    print(f"    original confidence  = {original['confidence']}")

    # 3. Call POST /appeal.
    appeal_resp = client.post(
        "/appeal",
        json={"content_id": content_id, "creator_reasoning": APPEAL_REASONING},
    )
    body = appeal_resp.get_json()
    print(f"Appeal response = {body}")

    # 4. Verify the confirmation response.
    assert appeal_resp.status_code == 200, "appeal should succeed"
    assert body["content_id"] == content_id
    assert body["status"] == "under_review"
    assert body["message"], "confirmation message should be present"

    # 5. Confirm through GET /log that the entry was updated correctly and the
    #    original classification was preserved.
    updated = _find_entry(client, content_id)
    assert updated["status"] == "under_review", "status should be under_review"
    assert updated["appeal_reasoning"] == APPEAL_REASONING, "reasoning stored"
    assert updated["attribution"] == original["attribution"], "attribution unchanged"
    assert updated["confidence"] == original["confidence"], "confidence unchanged"
    assert updated["llm_score"] == original["llm_score"], "llm_score unchanged"
    assert (
        updated["stylometric_score"] == original["stylometric_score"]
    ), "stylometric_score unchanged"

    print(f"    updated status       = {updated['status']}")
    print(f"    appeal_reasoning     = {updated['appeal_reasoning']}")
    print("\nPASS: appeal recorded, status is under_review, original "
          "classification preserved.")


if __name__ == "__main__":
    main()
