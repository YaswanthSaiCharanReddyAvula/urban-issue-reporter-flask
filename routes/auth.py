"""
Authentication routes - login, register, logout
"""
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models import User, Organization
from utils import send_email_notification, generate_welcome_email

def init_routes(app):
    """Initialize authentication routes"""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login"""
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            user = User.get_by_email(email)
            
            if user and check_password_hash(user['password'], password):
                # Get organization info if user has one
                org_info = None
                if user['organization_id']:
                    org_info = Organization.get_by_id(user['organization_id'])
                
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                session['user_role'] = user['role']
                session['organization_id'] = user['organization_id']
                session['organization_category'] = org_info['category'] if org_info else None
                session['organization_name'] = org_info['name'] if org_info else None
                
                # Backwards compatibility
                session['is_admin'] = User.is_admin(user)
                
                flash('Login successful!', 'success')
                
                # Redirect based on role
                if User.is_admin(user):
                    return redirect(url_for('admin_panel'))
                else:
                    return redirect(url_for('index'))
            else:
                flash('Invalid email or password!', 'error')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration"""
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            
            if len(password) < 6:
                flash('Password must be at least 6 characters!', 'error')
                return render_template('register.html')
            
            # Check if user exists
            if User.get_by_email(email):
                flash('Email already exists!', 'error')
                return render_template('register.html')
            
            # Create user
            user_id = User.create(name, email, password)
            
            # Auto-login after registration
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['user_role'] = 'user'
            session['organization_id'] = None
            session['organization_category'] = None
            session['organization_name'] = None
            session['is_admin'] = False
            
            # Send welcome email
            welcome_body = generate_welcome_email(name)
            send_email_notification(email, "🏙 Welcome to Urban Issue Reporter!", welcome_body, app.config)
            
            flash('Registration successful! Welcome email sent!', 'success')
            return redirect(url_for('index'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    def logout():
        """User logout"""
        session.clear()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('index'))
