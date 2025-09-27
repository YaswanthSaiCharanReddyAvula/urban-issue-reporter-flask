"""
Main application routes - home, issues, and general functionality
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
from models import Issue, Comment, User, get_db_connection
from utils import send_email_notification, generate_issue_report_email, generate_comment_email, allowed_file

def init_routes(app):
    """Initialize main routes"""
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve uploaded images"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/')
    def index():
        """Home page with issue listing and statistics"""
        # Get statistics for the homepage - count only regular citizens, not admins
        total_users = User.get_citizen_count()
        total_issues = Issue.get_count()
        
        # Get filters from query params
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        # Organization category to issue category mapping
        org_to_issue_category_map = {
            'electricity': 'electricity',
            'water': 'water',
            'road': 'road',
            'transport': 'transport',
            'sanitation': 'sanitation',
            'dustbin': 'sanitation',  # Map dustbin to sanitation
            'others': 'others',
            'general': None  # General can see all categories
        }
        
        # Check if user is logged in and get their organization category
        user_org_category = None
        if 'user_id' in session:
            user = User.get_by_id(session['user_id'])
            if user and (User.is_org_admin(user) or User.is_org_staff(user)):
                # Get user's organization category to filter issues
                if user.get('organization_id'):
                    conn = get_db_connection()
                    org = conn.execute("SELECT category FROM organizations WHERE id = ?", 
                                     (user['organization_id'],)).fetchone()
                    if org:
                        org_category = org['category']
                        # Map organization category to issue category
                        user_org_category = org_to_issue_category_map.get(org_category)
                    conn.close()
        
        # If user is org admin/staff and no category filter is specified, 
        # filter by their organization category (unless they're general admin)
        if user_org_category and not category:
            category = user_org_category
        
        # Get filtered issues
        issues = Issue.get_all(category, status, search)
        
        return render_template('index.html', issues=issues, 
                             current_category=category, current_status=status, search_term=search,
                             total_users=total_users, total_issues=total_issues,
                             user_org_category=user_org_category)
    
    @app.route('/report', methods=['GET', 'POST'])
    def report_issue():
        """Report new issue"""
        if 'user_id' not in session:
            flash('Please login to report issues!', 'error')
            return redirect(url_for('login'))

        # Check if user profile is complete (profile_picture optional)
        user = User.get_by_id(session['user_id'])
        required_fields = ['name', 'email', 'phone', 'bio', 'location']  # profile_picture optional
        missing = [field for field in required_fields if not user.get(field)]
        if missing:
            # Create readable field names
            label_map = {
                'name': 'Name',
                'email': 'Email',
                'phone': 'Phone',
                'bio': 'Bio',
                'location': 'Location'
            }
            readable = ', '.join(label_map[f] for f in missing)
            flash(f'Please complete your profile before reporting an issue. Missing: {readable}', 'error')
            return redirect(url_for('profile'))

        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            category = request.form['category']
            priority = request.form['priority']
            latitude = float(request.form['latitude'])
            longitude = float(request.form['longitude'])
            address = request.form['address']
            
            # Handle file upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_filename = filename
            
            # Save to database
            issue_id = Issue.create(title, description, category, priority, latitude, longitude, 
                                  address, image_filename, session['user_id'])
            
            # Calculate initial priority score
            try:
                from priority_scoring import PriorityScoring, ImageAnalysis
                
                # Get the created issue
                issue = Issue.get_by_id(issue_id)
                
                # Analyze image if present
                if image_filename:
                    ai_severity = ImageAnalysis.analyze_issue_image(
                        os.path.join(app.config['UPLOAD_FOLDER'], image_filename), 
                        category
                    )
                    if ai_severity:
                        # Update issue with AI severity score
                        from models import get_db_connection
                        conn = get_db_connection()
                        conn.execute(
                            "UPDATE issues SET ai_severity_score = ? WHERE id = ?",
                            (ai_severity, issue_id)
                        )
                        conn.commit()
                        conn.close()
                        
                        # Refresh issue data
                        issue = Issue.get_by_id(issue_id)
                
                # Calculate comprehensive priority score
                priority_data = PriorityScoring.calculate_overall_priority_score(issue)
                Issue.update_priority_score(issue_id, priority_data)
                
            except Exception as e:
                print(f"Warning: Could not calculate priority score: {e}")
            
            # Send notification email to user
            email_body = generate_issue_report_email(
                session['user_name'], title, category, priority, address, issue_id
            )
            send_email_notification(session['user_email'], f"📋 Issue Reported: {title}", email_body, app.config)
            
            flash('Issue reported successfully! Confirmation email sent!', 'success')
            return redirect(url_for('issue_detail', issue_id=issue_id))
        
        return render_template('report.html')
    
    @app.route('/issue/<int:issue_id>')
    def issue_detail(issue_id):
        """Issue detail page"""
        # Get issue details
        issue = Issue.get_by_id(issue_id)
        
        if not issue:
            flash('Issue not found!', 'error')
            return redirect(url_for('index'))
        
        # Get comments
        comments = Comment.get_by_issue_id(issue_id)
        
        # Check if current user has upvoted this issue
        user_has_upvoted = False
        if 'user_id' in session:
            user_has_upvoted = Issue.has_user_upvoted(issue_id, session['user_id'])
        
        return render_template('issue_detail.html', issue=issue, comments=comments, user_has_upvoted=user_has_upvoted)
    
    @app.route('/add_comment/<int:issue_id>', methods=['POST'])
    def add_comment(issue_id):
        """Add comment to issue"""
        if 'user_id' not in session:
            flash('Please login to comment!', 'error')
            return redirect(url_for('login'))
        
        content = request.form['content']
        is_official = 1 if session.get('is_admin') else 0
        
        # Add comment
        Comment.create(issue_id, session['user_id'], content, is_official)
        
        # Get issue details for email notification
        issue = Issue.get_by_id(issue_id)
        
        # Send email notification to issue reporter
        if issue and issue['reporter_email'] and issue['reporter_email'] != session.get('user_email'):
            email_body = generate_comment_email(
                issue['reporter_name'], issue['title'], session['user_name'], 
                content, issue_id, is_official
            )
            comment_type = "Official Response" if is_official else "New Comment"
            send_email_notification(issue['reporter_email'], 
                                  f"💬 {comment_type}: {issue['title']}", email_body, app.config)
        
        flash('Comment added successfully!', 'success')
        return redirect(url_for('issue_detail', issue_id=issue_id))
    
    @app.route('/upvote/<int:issue_id>', methods=['POST'])
    def upvote_issue(issue_id):
        """Upvote an issue"""
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        
        result = Issue.upvote(issue_id, session['user_id'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    @app.route('/demo')
    def demo():
        """Interactive demo showing how to report an issue"""
        return render_template('demo.html')
