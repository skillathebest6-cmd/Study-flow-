from extensions import db
from models.user import User, Notification

def notify_admins(title, content):
    """Envoie une notification interne à tous les comptes admin"""
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            title=title,
            content=content,
            type='info'
        )
        db.session.add(notif)
    db.session.commit()
