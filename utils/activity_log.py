from extensions import db
from models.user import ActivityLog

def log_activity(actor_id, student_id, action):
    """Enregistre une action dans le journal d'activité"""
    try:
        log = ActivityLog(actor_id=actor_id, student_id=student_id, action=action)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
