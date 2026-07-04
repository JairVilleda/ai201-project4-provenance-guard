"""
Audit logging for Provenance Guard.

Keeps the audit-log persistence separate from the Flask routes. The log is a
simple JSON file holding a list of decision records — one entry per successful
submission, matching the Architecture's Audit Log node.
"""

import json
import os
from datetime import datetime, timezone

# Log file lives under data/ at the project root.
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_PATH = os.path.join(_DATA_DIR, "audit_log.json")


def _ensure_log_file():
    """Create the data directory and an empty log file if they don't exist."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w") as f:
            json.dump([], f)


def read_entries():
    """Return all audit entries as a list (empty if the log is missing)."""
    _ensure_log_file()
    with open(LOG_PATH) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def log_submission(content_id, creator_id, attribution, confidence, llm_score):
    """Append one structured audit entry for a successful submission.

    Returns the entry that was written.
    """
    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "status": "classified",
    }

    entries = read_entries()
    entries.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    return entry
