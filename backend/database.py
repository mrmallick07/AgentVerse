"""
Firestore Database Layer — stores tasks and sessions for AgentVerse.
"""

from google.cloud import firestore
from datetime import datetime

db = firestore.Client(project="prodogenie")

# ─── TASKS ───────────────────────────────────────────────

def create_task(session_id: str, title: str, description: str = "") -> dict:
    """Save a new task to Firestore."""
    task_ref = db.collection("tasks").document()
    task = {
        "id": task_ref.id,
        "session_id": session_id,
        "title": title,
        "description": description,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    task_ref.set(task)
    return task


def get_tasks(session_id: str) -> list:
    """Get all tasks for a session."""
    tasks = db.collection("tasks")\
              .where("session_id", "==", session_id)\
              .stream()
    return [t.to_dict() for t in tasks]


def update_task_status(task_id: str, status: str) -> dict:
    """Update task status — pending, in_progress, done."""
    task_ref = db.collection("tasks").document(task_id)
    task_ref.update({"status": status, "updated_at": datetime.utcnow().isoformat()})
    return {"task_id": task_id, "status": status}


# ─── SESSIONS ────────────────────────────────────────────

def save_session_message(session_id: str, role: str, content: str):
    """Save a chat message to Firestore."""
    db.collection("sessions").document(session_id)\
      .collection("messages").add({
          "role": role,
          "content": content,
          "timestamp": datetime.utcnow().isoformat(),
      })


def get_session_history(session_id: str) -> list:
    """Get full chat history for a session."""
    msgs = db.collection("sessions").document(session_id)\
             .collection("messages")\
             .order_by("timestamp")\
             .stream()
    return [m.to_dict() for m in msgs]
