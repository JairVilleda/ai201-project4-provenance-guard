"""
Provenance Guard — Flask application.

Provides the content submission API. This foundation implements the
`POST /submit` endpoint with request validation and a placeholder response.
Detection, scoring, labeling, logging, and appeals arrive in later milestones.
"""

import uuid

from flask import Flask, jsonify, request

from llm_detector import get_llm_ai_score
from services.audit import log_submission, read_entries

# TODO(Milestone 4): import the stylometric detector (Signal 2).
# TODO(Milestone 4): import the confidence scorer that averages the two signals.
# TODO(Milestone 5): import the transparency label generator.

app = Flask(__name__)


@app.route("/")
def home():
    return "Provenance Guard is running."


@app.route("/submit", methods=["POST"])
def submit():
    """Accept a content submission and return a classification result.

    Expects a JSON body with `text` and `creator_id`.
    """
    data = request.get_json(silent=True) or {}

    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify({"error": "Both 'text' and 'creator_id' are required."}), 400

    content_id = str(uuid.uuid4())

    # Signal 1: LLM classifier AI-likelihood score in [0.0, 1.0].
    llm_score = get_llm_ai_score(text)

    # TODO(Milestone 4): Run Signal 2 (stylometric detector) on the text.
    # TODO(Milestone 4): Combine the two AI-likelihood scores into a confidence score.
    # TODO(Milestone 5): Generate the transparency label from the confidence score.

    # Temporary attribution based solely on Signal 1 until confidence scoring
    # (Milestone 4) combines both signals.
    attribution = "likely_ai" if llm_score >= 0.5 else "likely_human"

    # Placeholder until confidence scoring is implemented (Milestone 4).
    confidence = 0.0

    # Record one structured decision entry in the audit log.
    log_submission(
        content_id=content_id,
        creator_id=creator_id,
        attribution=attribution,
        confidence=confidence,
        llm_score=llm_score,
    )

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        # Placeholder until transparency label generation (Milestone 5).
        "label": "Placeholder label",
    })


@app.route("/log", methods=["GET"])
def get_log():
    """Return all audit log entries."""
    return jsonify({"entries": read_entries()})


# TODO(Milestone 5): Add the POST /appeal endpoint and appeals workflow
# (update submission status to "Under Review" and record the appeal in the
# audit log).


if __name__ == "__main__":
    app.run(port=5000, debug=True)
