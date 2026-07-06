"""
Provenance Guard — Flask application.

Provides the content submission API. This foundation implements the
`POST /submit` endpoint with request validation and a placeholder response.
Detection, scoring, labeling, logging, and appeals arrive in later milestones.
"""

import uuid

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from confidence_scorer import calculate_confidence
from llm_detector import get_llm_ai_score
from stylometric_detector import get_stylometric_ai_score
from services.audit import log_submission, read_entries, record_appeal
from transparency_label import generate_transparency_label

app = Flask(__name__)

# Rate limiter. No default_limits are set, so limits apply only to the routes
# that explicitly opt in via @limiter.limit(...). This keeps /appeal, /log, and
# / unlimited while still protecting the expensive /submit endpoint.
# In-memory storage is sufficient for this single-process project.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
)


@app.route("/")
def home():
    return "Provenance Guard is running."


@app.route("/submit", methods=["POST"])
# Limits chosen for a realistic single creator submitting drafts: 10 per minute
# comfortably covers iterating on a few drafts back-to-back, and 100 per day is
# generous for one person's editing sessions while still capping automated
# flooding — which also protects the paid LLM API call behind this endpoint.
@limiter.limit("10 per minute;100 per day")
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

    # Two independent detection signals, each an AI-likelihood score in
    # [0.0, 1.0] (0.0 = appears human-written, 1.0 = appears AI-generated).
    # Signal 1: LLM classifier.
    llm_score = get_llm_ai_score(text)
    # Signal 2: stylometric heuristics.
    stylometric_score = get_stylometric_ai_score(text)

    # Confidence scorer: averages the two signals (they contribute equally)
    # and derives the attribution result from the combined confidence score.
    confidence, attribution = calculate_confidence(llm_score, stylometric_score)

    # Generate the human-readable transparency label from the confidence score.
    label = generate_transparency_label(confidence)

    # Record one structured decision entry in the audit log.
    log_submission(
        content_id=content_id,
        creator_id=creator_id,
        attribution=attribution,
        confidence=confidence,
        llm_score=llm_score,
        stylometric_score=stylometric_score,
    )

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
    })


@app.route("/log", methods=["GET"])
def get_log():
    """Return all audit log entries."""
    return jsonify({"entries": read_entries()})


@app.route("/appeal", methods=["POST"])
def appeal():
    """Accept a creator's appeal of a prior classification.

    Expects a JSON body with `content_id` and `creator_reasoning`. Updates the
    matching submission's status to "under_review" and records the reasoning in
    the same audit entry. Per the Appeals Workflow, the content is NOT
    reclassified — no detection signal or confidence score is rerun.
    """
    data = request.get_json(silent=True) or {}

    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id or not creator_reasoning:
        return jsonify({
            "error": "Both 'content_id' and 'creator_reasoning' are required."
        }), 400

    updated = record_appeal(content_id, creator_reasoning)
    if updated is None:
        return jsonify({"error": "No submission found for the given content_id."}), 404

    return jsonify({
        "content_id": content_id,
        "status": updated["status"],
        "message": "Your appeal was received and the submission is now under review.",
    })


if __name__ == "__main__":
    app.run(port=5001, debug=True)
