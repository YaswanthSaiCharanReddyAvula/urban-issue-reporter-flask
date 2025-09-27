"""
Role-based access control decorators and utilities
"""
from functools import wraps
from flask import session, flash, redirect, url_for

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges (any admin level)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        user_role = session.get('user_role', 'user')
        if user_role not in ['super_admin', 'org_admin', 'org_staff']:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'super_admin':
            flash('Super Admin access required.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def org_admin_required(f):
    """Decorator to require organization admin or higher privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        user_role = session.get('user_role', 'user')
        if user_role not in ['super_admin', 'org_admin']:
            flash('Organization Admin access required.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_info():
    """Get current user information from session"""
    if 'user_id' not in session:
        return None
    
    return {
        'id': session.get('user_id'),
        'name': session.get('user_name'),
        'email': session.get('user_email'),
        'role': session.get('user_role', 'user'),
        'organization_id': session.get('organization_id'),
        'organization_category': session.get('organization_category'),
        'organization_name': session.get('organization_name'),
        'is_admin': session.get('is_admin', False)
    }

def can_access_category(user_role, user_org_category, issue_category):
    """Check if user can access issues of a specific category"""
    # Super admin can access all categories
    if user_role == 'super_admin':
        return True
    
    # Organization admin/staff can only access their organization's category
    if user_role in ['org_admin', 'org_staff']:
        return user_org_category == issue_category
    
    # Regular users can view all (for reporting purposes)
    return True

def can_manage_issue(user_role, user_org_category, issue_category):
    """Check if user can manage (update status) issues of a specific category"""
    # Super admin can manage all issues
    if user_role == 'super_admin':
        return True
    
    # Organization admin/staff can only manage their organization's category issues
    if user_role in ['org_admin', 'org_staff']:
        return user_org_category == issue_category
    
    # Regular users cannot manage issues
    return False

def get_accessible_categories(user_role, user_org_category):
    """Get list of categories accessible to the user"""
    if user_role == 'super_admin':
        return ['electric', 'water', 'road', 'transport', 'dustbin', 'others']
    elif user_role in ['org_admin', 'org_staff'] and user_org_category:
        return [user_org_category]
    else:
        return ['electric', 'water', 'road', 'transport', 'dustbin', 'others']