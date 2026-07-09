from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User, StudentProfile, Document, Payment, Notification, ServiceRequest
from extensions import db, limiter
from utils.document_requirements import get_required_documents, DOC_LABELS
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_profile():
    return StudentProfile.query.filter_by(user_id=current_user.id).first()

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('auth.dashboard'))
        flash('Email ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        destination = request.form.get('destination', '')
        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
            return render_template('auth/register.html')
        if not any(c.isupper() for c in password):
            flash('Le mot de passe doit contenir au moins une majuscule.', 'danger')
            return render_template('auth/register.html')
        if not any(c.isdigit() for c in password):
            flash('Le mot de passe doit contenir au moins un chiffre.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Un compte avec cet email existe déjà.', 'danger')
            return render_template('auth/register.html')
        user = User(email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        profile = StudentProfile(
            user_id=user.id, first_name=first_name,
            last_name=last_name, phone=phone,
            destination_country=destination, status='nouveau'
        )
        db.session.add(profile)
        notif = Notification(
            user_id=user.id,
            title="Bienvenue sur StudyFlow !",
            content=f"Bonjour {first_name}, votre dossier a été créé avec succès.",
            type="success"
        )
        db.session.add(notif)
        db.session.commit()

        from utils.email_service import send_welcome_email
        send_welcome_email(email, first_name)

        login_user(user, remember=True)
        return redirect(url_for('auth.dashboard'))
    return render_template('auth/register.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    profile = get_profile()
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    return render_template('auth/dashboard.html', profile=profile, notifs=notifs)

@auth_bp.route('/documents', methods=['GET', 'POST'])
@login_required
def documents():
    profile = get_profile()
    if request.method == 'POST':
        doc_name = request.form.get('doc_name', '').strip()
        doc_type = request.form.get('doc_type', '').strip()
        file = request.files.get('file')

        if not doc_name or not doc_type:
            flash('Veuillez remplir tous les champs.', 'danger')
        elif not file or file.filename == '':
            flash('Veuillez sélectionner un fichier.', 'danger')
        elif not allowed_file(file.filename):
            flash('Format non accepté. Utilisez PDF, JPG, PNG, DOC ou DOCX.', 'danger')
        else:
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
            file.save(save_path)
            file_size = os.path.getsize(save_path)

            doc = Document(
                student_id=profile.id,
                name=doc_name,
                doc_type=doc_type,
                file_url=unique_name,
                file_name=secure_filename(file.filename),
                file_size=file_size,
                status='en_attente'
            )
            db.session.add(doc)
            notif = Notification(
                user_id=current_user.id,
                title="Document déposé",
                content=f"'{doc_name}' est en attente de validation.",
                type="info"
            )
            db.session.add(notif)
            db.session.commit()
            flash('Document uploadé avec succès !', 'success')

    docs = Document.query.filter_by(
        student_id=profile.id
    ).order_by(Document.uploaded_at.desc()).all()

    required_docs = get_required_documents(
        profile.nationality,
        profile.destination_country,
        profile.program_level
    )
    submitted_types = [d.doc_type for d in docs]
    missing_docs = [d for d in required_docs if d not in submitted_types]

    return render_template('auth/documents.html', profile=profile, docs=docs,
                          required_docs=required_docs, missing_docs=missing_docs,
                          doc_labels=DOC_LABELS)

@auth_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@auth_bp.route('/payments')
@login_required
def payments():
    profile = get_profile()
    pays = Payment.query.filter_by(
        student_id=profile.id
    ).order_by(Payment.created_at.desc()).all()
    total_paye = sum(p.amount for p in pays if p.status == 'payé')
    total_attente = sum(p.amount for p in pays if p.status == 'en_attente')
    return render_template('auth/payments.html', profile=profile,
        payments=pays, total_paye=total_paye, total_attente=total_attente)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    p = get_profile()
    if request.method == 'POST':
        p.first_name = request.form.get('first_name', p.first_name)
        p.last_name = request.form.get('last_name', p.last_name)
        p.phone = request.form.get('phone', p.phone)
        p.nationality = request.form.get('nationality', p.nationality)
        p.passport_number = request.form.get('passport_number', p.passport_number)
        p.destination_country = request.form.get('destination', p.destination_country)
        p.program = request.form.get('program', p.program)
        p.university = request.form.get('university', p.university)
        db.session.commit()
        flash('Profil mis à jour avec succès !', 'success')
    return render_template('auth/profile.html', profile=p)

@auth_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('auth/notifications.html', notifs=notifs)

@auth_bp.route('/suivi')
@login_required
def suivi():
    profile = get_profile()
    return render_template('auth/suivi.html', profile=profile)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/services')
@login_required
def services():
    profile = get_profile()
    requests = ServiceRequest.query.filter_by(student_id=profile.id).order_by(ServiceRequest.created_at.desc()).all()
    return render_template('student/services.html', requests=requests)

@auth_bp.route('/services/new/<service_type>', methods=['GET', 'POST'])
@login_required
def new_service_request(service_type):
    profile = get_profile()

    if request.method == 'POST':
        details = request.form.get('details', '')
        new_request = ServiceRequest(
            student_id=profile.id,
            service_type=service_type,
            details=details
        )
        db.session.add(new_request)
        db.session.commit()
        flash(f'Votre demande de {service_type} a été soumise avec succès!', 'success')
        return redirect(url_for('auth.services'))

    return render_template('student/new_service_request.html', service_type=service_type)

@auth_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    from utils.ai_service import chat_with_ai
    profile = get_profile()

    if request.method == 'POST':
        from flask import jsonify
        message = request.json.get('message', '').strip()
        if not message:
            return jsonify({'response': 'Veuillez écrire un message.'})

        response = chat_with_ai(profile, message)
        return jsonify({'response': response})

    return render_template('student/chat.html')
