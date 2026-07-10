from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.user import User, StudentProfile, Document, Payment, Notification, ServiceRequest
from extensions import db
from functools import wraps
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Accès refusé. Vous n\'êtes pas administrateur.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    """Autorise admin ET agent"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'agent'):
            flash('Accès refusé.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = StudentProfile.query.count()
    validated = StudentProfile.query.filter_by(status='validé').count()
    pending_docs = Document.query.filter_by(status='en_attente').count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status='payé').scalar() or 0

    stale_threshold = datetime.utcnow() - timedelta(days=7)
    stale_students = StudentProfile.query.filter(
        StudentProfile.status.in_(['nouveau', 'en_cours']),
        StudentProfile.status_updated_at < stale_threshold
    ).all()
    
    recent_students = StudentProfile.query.order_by(StudentProfile.created_at.desc()).limit(8).all()
    
    dest_france = StudentProfile.query.filter_by(destination_country='France').count()
    dest_canada = StudentProfile.query.filter_by(destination_country='Canada').count()
    dest_belgique = StudentProfile.query.filter_by(destination_country='Belgique').count()
    
    status_counts = {
        'nouveau': StudentProfile.query.filter_by(status='nouveau').count(),
        'en_cours': StudentProfile.query.filter_by(status='en_cours').count(),
        'validé': StudentProfile.query.filter_by(status='validé').count(),
        'refusé': StudentProfile.query.filter_by(status='refusé').count(),
    }
    
    import json as json_lib

    chart_status_labels = list(status_counts.keys())
    chart_status_values = list(status_counts.values())

    chart_dest_labels = ['France', 'Canada', 'Belgique']
    chart_dest_values = [dest_france, dest_canada, dest_belgique]

    return render_template('admin/dashboard.html',
        total_students=total_students,
        validated=validated,
        pending_docs=pending_docs,
        total_revenue=total_revenue,
        recent_students=recent_students,
        dest_france=dest_france,
        dest_canada=dest_canada,
        dest_belgique=dest_belgique,
        status_counts=status_counts,
        chart_status_labels=json_lib.dumps(chart_status_labels),
        chart_status_values=json_lib.dumps(chart_status_values),
        chart_dest_labels=json_lib.dumps(chart_dest_labels),
        chart_dest_values=json_lib.dumps(chart_dest_values),
        stale_students=stale_students
    )

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    destination = request.args.get('destination', '')
    
    query = StudentProfile.query
    if q:
        query = query.filter(db.or_(
            StudentProfile.first_name.ilike(f'%{q}%'),
            StudentProfile.last_name.ilike(f'%{q}%'),
            StudentProfile.user.has(User.email.ilike(f'%{q}%'))
        ))
    if status:
        query = query.filter_by(status=status)
    if destination:
        query = query.filter_by(destination_country=destination)
    
    students_list = query.order_by(StudentProfile.created_at.desc()).all()
    return render_template('admin/students.html',
        students=students_list, q=q, status=status, destination=destination
    )

@admin_bp.route('/student/<int:sid>')
@login_required
@admin_required
def student_detail(sid):
    profile = StudentProfile.query.get_or_404(sid)
    docs = Document.query.filter_by(student_id=sid).all()
    payments = Payment.query.filter_by(student_id=sid).all()
    all_agents = User.query.filter_by(role='agent').all()
    from models.user import ActivityLog, InternalNote
    logs = ActivityLog.query.filter_by(student_id=sid).order_by(ActivityLog.created_at.desc()).limit(20).all()
    notes = InternalNote.query.filter_by(student_id=sid).order_by(InternalNote.created_at.desc()).all()
    return render_template('admin/student_detail.html',
        profile=profile, docs=docs, payments=payments, all_agents=all_agents, logs=logs, notes=notes
    )

@admin_bp.route('/student/<int:sid>/status', methods=['POST'])
@login_required
@admin_required
def update_student_status(sid):
    profile = StudentProfile.query.get_or_404(sid)
    new_status = request.form.get('status', profile.status)
    profile.status = new_status
    profile.status_updated_at = datetime.utcnow()
    db.session.commit()
    from utils.activity_log import log_activity
    log_activity(current_user.id, profile.id, f"Statut changé en '{new_status}'")

    
    notif = Notification(
        user_id=profile.user_id,
        title="Statut de votre dossier mis à jour",
        content=f"Votre dossier est maintenant : {new_status}",
        type="info"
    )
    db.session.add(notif)
    db.session.commit()
    
    flash('Statut mis à jour.', 'success')
    return redirect(url_for('admin.student_detail', sid=sid))

@admin_bp.route('/document/<int:did>/validate', methods=['POST'])
@login_required
@admin_required
def validate_document(did):
    doc = Document.query.get_or_404(did)
    action = request.form.get('action')
    doc.status = 'validé' if action == 'validate' else 'rejeté'
    doc.rejection_reason = request.form.get('reason', '')
    db.session.commit()
    from utils.activity_log import log_activity
    log_activity(current_user.id, doc.student_id, f"Document '{doc.name}' {doc.status}")

    
    student = doc.student
    msg_type = 'success' if action == 'validate' else 'danger'
    notif = Notification(
        user_id=student.user_id,
        title=f"Document {doc.name}",
        content=f"Votre document a été {'validé ✓' if action == 'validate' else 'rejeté ✗'}",
        type=msg_type
    )
    db.session.add(notif)
    db.session.commit()
    

    from utils.email_service import send_document_status_email
    send_document_status_email(student.user.email, student.first_name, doc.name, doc.status)
    flash(f'Document {doc.status}.', 'success')
    return redirect(url_for('admin.student_detail', sid=doc.student_id))

@admin_bp.route('/documents')
@login_required
@admin_required
def documents():
    all_docs = Document.query.order_by(Document.uploaded_at.desc()).all()
    pending = [d for d in all_docs if d.status == 'en_attente']
    validated = [d for d in all_docs if d.status == 'validé']
    rejected = [d for d in all_docs if d.status == 'rejeté']
    
    return render_template('admin/documents.html',
        all_docs=all_docs,
        pending=pending,
        validated=validated,
        rejected=rejected
    )

@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    all_payments = Payment.query.order_by(Payment.created_at.desc()).all()
    total = sum(p.amount for p in all_payments if p.status == 'payé')
    pending = sum(p.amount for p in all_payments if p.status == 'en_attente')
    
    return render_template('admin/payments.html',
        payments=all_payments, total=total, pending=pending
    )

@admin_bp.route('/services')
@login_required
@admin_required
def services():
    requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    return render_template('admin/services.html', requests=requests)

@admin_bp.route('/service/<int:req_id>/update', methods=['POST'])
@login_required
@admin_required
def update_service_status(req_id):
    service_request = ServiceRequest.query.get_or_404(req_id)
    new_status = request.form.get('status')
    service_request.status = new_status
    db.session.commit()

    notif = Notification(
        user_id=service_request.student.user_id,
        title=f'Mise à jour: {service_request.service_type}',
        content=f'Votre demande de {service_request.service_type} est maintenant: {new_status}',
        type='info'
    )
    db.session.add(notif)
    db.session.commit()

    flash('Statut mis à jour!', 'success')
    return redirect(url_for('admin.services'))

@admin_bp.route('/agents', methods=['GET', 'POST'])
@login_required
@admin_required
def agents():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()

        if User.query.filter_by(email=email).first():
            flash('Un compte avec cet email existe déjà.', 'danger')
            return redirect(url_for('admin.agents'))

        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
            return redirect(url_for('admin.agents'))

        agent = User(email=email, role='agent')
        agent.set_password(password)
        db.session.add(agent)
        db.session.commit()

        flash(f'Agent {first_name} créé avec succès.', 'success')
        return redirect(url_for('admin.agents'))

    all_agents = User.query.filter_by(role='agent').all()
    agent_counts = {}
    for agent in all_agents:
        agent_counts[agent.id] = StudentProfile.query.filter_by(assigned_agent_id=agent.id).count()

    return render_template('admin/agents.html', agents=all_agents, agent_counts=agent_counts)

@admin_bp.route('/student/<int:sid>/assign', methods=['POST'])
@login_required
@admin_required
def assign_agent(sid):
    student = StudentProfile.query.get_or_404(sid)
    agent_id = request.form.get('agent_id')

    student.assigned_agent_id = int(agent_id) if agent_id else None
    db.session.commit()
    agent_email = User.query.get(int(agent_id)).email if agent_id else 'aucun agent'
    from utils.activity_log import log_activity
    log_activity(current_user.id, student.id, f"Dossier assigné à {agent_email}")


    flash('Dossier assigné avec succès.', 'success')
    return redirect(url_for('admin.student_detail', sid=sid))

@admin_bp.route('/my-students')
@login_required
def my_students():
    if current_user.role not in ('admin', 'agent'):
        flash('Accès refusé.', 'danger')
        return redirect(url_for('auth.login'))

    if current_user.role == 'admin':
        my_list = StudentProfile.query.all()
    else:
        my_list = StudentProfile.query.filter_by(assigned_agent_id=current_user.id).all()

    return render_template('admin/my_students.html', students=my_list)

@admin_bp.route('/student/<int:sid>/note', methods=['POST'])
@login_required
def add_note(sid):
    if current_user.role not in ('admin', 'agent'):
        flash('Accès refusé.', 'danger')
        return redirect(url_for('auth.login'))

    content = request.form.get('content', '').strip()
    if content:
        from models.user import InternalNote
        note = InternalNote(student_id=sid, author_id=current_user.id, content=content)
        db.session.add(note)
        db.session.commit()

        from utils.activity_log import log_activity
        log_activity(current_user.id, sid, "Note interne ajoutée")

        flash('Note ajoutée.', 'success')

    return redirect(url_for('admin.student_detail', sid=sid))
