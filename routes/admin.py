"""
Admin routes - admin panel and administrative functions
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from models import Issue, User, Comment, Organization
from utils import send_email_notification, generate_status_update_email
from auth_utils import admin_required, super_admin_required, org_admin_required, get_current_user_info, can_manage_issue

def init_routes(app):
    """Initialize admin routes"""
    
    @app.route('/admin')
    @admin_required
    def admin_panel():
        """Admin dashboard with role-based access"""
        current_user = get_current_user_info()
        user_role = current_user['role']
        org_category = current_user['organization_category']
        
        # Get filtered statistics based on role
        if user_role == 'super_admin':
            # Super admin sees all issues
            stats = Issue.get_stats()
            all_issues = Issue.get_all()  # Get all issues instead of just recent ones
        else:
            # Organization admin/staff see only their category issues
            org_issues = Issue.get_by_category(org_category)
            stats = {
                'total_issues': len(org_issues),
                'pending_issues': len([i for i in org_issues if i['status'] == 'pending']),
                'resolved_issues': len([i for i in org_issues if i['status'] == 'resolved']),
                'recent_issues': org_issues  # Return all org issues for management
            }
            all_issues = org_issues
        
        # Add user count (Super admin sees all, org admin sees org users)
        if user_role == 'super_admin':
            stats['total_users'] = User.get_count()
            users_list = User.get_all()
        else:
            org_users = User.get_by_organization(current_user['organization_id']) if current_user['organization_id'] else []
            stats['total_users'] = len(org_users)
            users_list = org_users
        
        return render_template('admin.html', 
                             stats=stats, 
                             recent_issues=all_issues,
                             current_user=current_user,
                             users_list=users_list)
    
    @app.route('/update_status/<int:issue_id>', methods=['POST'])
    @admin_required
    def update_status(issue_id):
        """Update issue status (admin only with role-based access)"""
        current_user = get_current_user_info()
        
        # Get issue details first
        issue = Issue.get_by_id(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user can manage this category of issue
        if not can_manage_issue(current_user['role'], current_user['organization_category'], issue['category']):
            return jsonify({'error': 'You do not have permission to manage this issue category'}), 403
        
        new_status = request.form['status']
        comment = request.form.get('comment', '')
        
        # Update status
        Issue.update_status(issue_id, new_status)
        
        # Add admin comment if provided
        if comment:
            Comment.create(issue_id, session['user_id'], comment, is_official=1)
        
        # Send status update email
        if issue and issue['reporter_email']:
            email_body = generate_status_update_email(
                issue['reporter_name'], issue['title'], new_status, comment, issue_id
            )
            status_emojis = {
                'pending': '⏳',
                'in-progress': '🔄', 
                'resolved': '✅',
                'rejected': '❌'
            }
            send_email_notification(issue['reporter_email'], 
                                  f"{status_emojis.get(new_status, '📋')} Status Update: {issue['title']}", 
                                  email_body, app.config)
        
        flash('Status updated successfully! Email notification sent!', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/issues-map')
    @admin_required
    def issues_map():
        """Admin Issues Map - View issues based on role and organization"""
        current_user = get_current_user_info()
        user_role = current_user['role']
        org_category = current_user['organization_category']
        
        # Get issues based on user role and organization
        map_issues = []
        if user_role == 'super_admin':
            # Super admin sees all issues
            all_issues = Issue.get_all()
        else:
            # Organization admin/staff see only their category issues
            all_issues = Issue.get_by_category(org_category)
        
        # Filter out issues without valid coordinates and prepare for map
        for issue in all_issues:
            if issue['latitude'] and issue['longitude']:
                map_issues.append({
                    'id': issue['id'],
                    'title': issue['title'],
                    'description': issue['description'],
                    'category': issue['category'],
                    'status': issue['status'],
                    'priority': issue['priority'],
                    'latitude': float(issue['latitude']),
                    'longitude': float(issue['longitude']),
                    'address': issue['address'],
                    'reporter_name': issue['reporter_name'],
                    'upvotes': issue['upvotes'],
                    'created_at': issue['created_at'],
                    'image_filename': issue['image_filename']
                })
        
        return render_template('issues_map.html', 
                             issues=map_issues, 
                             current_user=current_user)
    
    @app.route('/admin/manage-organizations')
    @super_admin_required
    def manage_organizations():
        """Super Admin: Manage organizations and assign admins"""
        organizations = Organization.get_all()
        users = User.get_all()
        
        return render_template('manage_organizations.html', 
                             organizations=organizations,
                             users=users)
    
    @app.route('/admin/assign-admin', methods=['POST'])
    @super_admin_required
    def assign_admin():
        """Super Admin: Assign user to organization as admin/staff"""
        user_id = request.form['user_id']
        organization_id = request.form['organization_id']
        role = request.form['role']  # org_admin or org_staff
        
        if role not in ['org_admin', 'org_staff']:
            flash('Invalid role selected!', 'error')
            return redirect(url_for('manage_organizations'))
        
        # Update user role and organization
        User.update_role(user_id, role, organization_id)
        
        user = User.get_by_id(user_id)
        org = Organization.get_by_id(organization_id)
        
        flash(f'Successfully assigned {user["name"]} as {role.replace("_", " ").title()} for {org["name"]}!', 'success')
        return redirect(url_for('manage_organizations'))
