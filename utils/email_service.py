from flask_mail import Message
from extensions import mail
from flask import current_app

def send_email(to, subject, body_html):
    """Envoie un email simple"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=body_html
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Erreur envoi email: {e}")
        print(f"ERREUR EMAIL: {e}")
        return False

def send_welcome_email(user_email, first_name):
    """Email de bienvenue après inscription"""
    subject = "Bienvenue sur StudyFlow ! 🎓"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#0D1B3E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">StudyFlow</h1>
        </div>
        <div style="padding:30px;background:#F8FAFC;">
            <h2 style="color:#0D1B3E;">Bonjour {first_name} 👋</h2>
            <p>Bienvenue sur StudyFlow ! Votre compte a été créé avec succès.</p>
            <p>Vous pouvez maintenant :</p>
            <ul>
                <li>Déposer vos documents</li>
                <li>Faire des demandes de services (Visa, Logement, Assurance...)</li>
                <li>Suivre l'avancement de votre dossier</li>
                <li>Discuter avec notre assistant IA</li>
            </ul>
            <p>Nous sommes ravis de vous accompagner dans votre projet d'études à l'étranger !</p>
            <p style="color:#64748B;font-size:13px;margin-top:30px;">L'équipe StudyFlow</p>
        </div>
    </div>
    """
    return send_email(user_email, subject, body)

def send_document_status_email(user_email, first_name, doc_name, status):
    """Email quand un document est validé ou rejeté"""
    status_text = "validé ✅" if status == "validé" else "rejeté ❌"
    color = "#10B981" if status == "validé" else "#F43F5E"

    subject = f"Document {status_text} - StudyFlow"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#0D1B3E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">StudyFlow</h1>
        </div>
        <div style="padding:30px;background:#F8FAFC;">
            <h2 style="color:#0D1B3E;">Bonjour {first_name},</h2>
            <p>Votre document <strong>{doc_name}</strong> a été
            <span style="color:{color};font-weight:bold;">{status_text}</span>.</p>
            <p>Connectez-vous à votre espace StudyFlow pour plus de détails.</p>
            <p style="color:#64748B;font-size:13px;margin-top:30px;">L'équipe StudyFlow</p>
        </div>
    </div>
    """
    return send_email(user_email, subject, body)

def send_password_reset_email(user_email, reset_link):
    """Email pour réinitialiser le mot de passe"""
    subject = "Réinitialisation de votre mot de passe - StudyFlow"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#0D1B3E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">StudyFlow</h1>
        </div>
        <div style="padding:30px;background:#F8FAFC;">
            <h2 style="color:#0D1B3E;">Réinitialisation de mot de passe</h2>
            <p>Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le bouton ci-dessous :</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{reset_link}" style="background:#1A56E8;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:600;">
                    Réinitialiser mon mot de passe
                </a>
            </div>
            <p style="color:#64748B;font-size:13px;">Ce lien expire dans 1 heure. Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
            <p style="color:#64748B;font-size:13px;margin-top:30px;">L'équipe StudyFlow</p>
        </div>
    </div>
    """
    return send_email(user_email, subject, body)
