from flask import Blueprint, render_template, request, redirect, url_for, flash

auth_bp = Blueprint('auth', __name__)

users = {}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == 'test@test.com' and password == 'test123':
            flash('Connexion réussie!', 'success')
            return redirect(url_for('auth.dashboard'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('Inscription réussie!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/dashboard')
def dashboard():
    return render_template('student/dashboard.html')
