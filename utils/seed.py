from models.user import User, StudentProfile, Document, Payment, Notification
from extensions import db
from datetime import datetime, timedelta
import random

def seed_data():
    if User.query.filter_by(email='admin@studyflow.com').first():
        return

    # Créer admin
    admin = User(email='admin@studyflow.com', role='admin')
    admin.set_password('admin2024')
    db.session.add(admin)

    # Créer étudiant de test
    student = User(email='etudiant@studyflow.com', role='student')
    student.set_password('etudiant2024')
    db.session.add(student)
    db.session.flush()

    profile = StudentProfile(
        user_id=student.id,
        first_name='Ibrahima',
        last_name='Bah',
        phone='+224 621 000 001',
        nationality='Guinéenne',
        destination_country='France',
        program='Licence Informatique',
        university='Université Paris 8',
        status='en_cours'
    )
    db.session.add(profile)
    db.session.flush()

    # Documents
    docs = [
        ('Passeport', 'passeport', 'validé'),
        ('Relevés de notes', 'releves_notes', 'en_attente'),
        ('Lettre de motivation', 'lettre_motivation', 'en_attente'),
        ('Acte de naissance', 'acte_naissance', 'rejeté'),
    ]
    for nom, code, statut in docs:
        doc = Document(
            student_id=profile.id,
            name=nom,
            doc_type=code,
            status=statut
        )
        db.session.add(doc)

    # Paiements
    payments = [
        ('Frais de dossier', 500000, 'payé'),
        ('Visa étudiant', 1500000, 'en_attente'),
        ('Assurance voyage', 800000, 'payé'),
    ]
    for service, montant, statut in payments:
        p = Payment(
            student_id=profile.id,
            amount=montant,
            currency='GNF',
            service=service,
            status=statut
        )
        db.session.add(p)

    # Notification
    notif = Notification(
        user_id=student.id,
        title="Bienvenue sur StudyFlow !",
        content="Bonjour Ibrahima, votre dossier est en cours de traitement.",
        type="success"
    )
    db.session.add(notif)

    db.session.commit()
    print("Données de test créées avec succès !")
