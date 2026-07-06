"""
Standalone manual test for rate limiting on POST /submit.

Sends a burst of requests to /submit and shows that the first 10 (the
per-minute limit) return 200 while the rest return 429 (Too Many Requests).
Also confirms that /log and /appeal are NOT rate limited.

To isolate the rate-limiting behavior — and to avoid making real Groq API
calls — this test stubs the two detectors with fixed scores. It does not modify
any production detection, scoring, labeling, or audit logic; the stubs live
only inside this test process.

Run directly:

    .venv/bin/python test_rate_limit.py
"""

import app as app_module

# Test-only stubs: replace the live detectors with fixed scores so the burst
# does not call the Groq API. Production code is untouched.
app_module.get_llm_ai_score = lambda text: 0.5
app_module.get_stylometric_ai_score = lambda text: 0.5

from app import app

PER_MINUTE_LIMIT = 10
BURST = 13


def main():
    client = app.test_client()

    print(f"Sending {BURST} rapid POST /submit requests "
          f"(per-minute limit = {PER_MINUTE_LIMIT})...")
    statuses = []
    for i in range(1, BURST + 1):
        resp = client.post(
            "/submit",
            json={"text": "sample draft text", "creator_id": "test-creator"},
        )
        statuses.append(resp.status_code)
        print(f"    request {i:2d} -> {resp.status_code}")

    allowed = statuses[:PER_MINUTE_LIMIT]
    blocked = statuses[PER_MINUTE_LIMIT:]

    assert all(s == 200 for s in allowed), "first 10 requests should return 200"
    assert all(s == 429 for s in blocked), "requests past the limit should return 429"

    # /log and /appeal must remain unlimited even after /submit is exhausted.
    assert client.get("/log").status_code == 200, "/log must not be rate limited"
    appeal_resp = client.post(
        "/appeal",
        json={"content_id": "does-not-exist", "creator_reasoning": "x"},
    )
    assert appeal_resp.status_code != 429, "/appeal must not be rate limited"

    print(f"\nPASS: first {PER_MINUTE_LIMIT} returned 200, "
          f"remaining {len(blocked)} returned 429; /log and /appeal unaffected.")


if __name__ == "__main__":
    main()
