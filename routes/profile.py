"""
User profile routes - view and edit user profile information
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import os
import uuid
from models import User
from utils import allowed_file

def init_profile_routes(app):
    """Initialize profile routes"""
    
    @app.route('/profile')
    def profile():
        """View user profile"""
        if 'user_id' not in session:
            flash('Please login to view your profile!', 'error')
            return redirect(url_for('login'))
        
        user = User.get_by_id(session['user_id'])
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('login'))
        
        # Get user statistics
        from models import Issue, Comment
        user_issues_count = Issue.get_count_by_user(session['user_id'])
        user_comments_count = Comment.get_count_by_user(session['user_id'])
        
        return render_template('profile.html', user=user, 
                             user_issues_count=user_issues_count,
                             user_comments_count=user_comments_count)
    
    @app.route('/profile/edit', methods=['GET', 'POST'])
    def edit_profile():
        """Edit user profile"""
        if 'user_id' not in session:
            flash('Please login to edit your profile!', 'error')
            return redirect(url_for('login'))
        
        user = User.get_by_id(session['user_id'])
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name', '').strip()
                phone = request.form.get('phone', '').strip()
                bio = request.form.get('bio', '').strip()
                location = request.form.get('location', '').strip()
                
                # Validate required fields
                if not name:
                    flash('Name is required!', 'error')
                    return render_template('profile.html', user=user, edit_mode=True)
                
                # Handle profile picture upload
                profile_picture = user.get('profile_picture')  # Keep existing if no new upload
                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
                        # Generate unique filename
                        filename = f"profile_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        
                        # Delete old profile picture if exists
                        if profile_picture and profile_picture != 'default-avatar.png':
                            old_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_picture)
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        
                        profile_picture = filename
                
                # Update profile
                User.update_profile(
                    user_id=session['user_id'],
                    name=name,
                    phone=phone if phone else None,
                    bio=bio if bio else None,
                    location=location if location else None,
                    profile_picture=profile_picture
                )
                
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
                
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'error')
                return render_template('profile.html', user=user, edit_mode=True)
        
        # GET request - show edit form
        return render_template('profile.html', user=user, edit_mode=True)
    
    @app.route('/profile/change-password', methods=['POST'])
    def change_password():
        """Change user password"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first!'}), 401
        
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate inputs
            if not all([current_password, new_password, confirm_password]):
                return jsonify({'success': False, 'message': 'All fields are required!'}), 400
            
            if new_password != confirm_password:
                return jsonify({'success': False, 'message': 'New passwords do not match!'}), 400
            
            if len(new_password) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters long!'}), 400
            
            # Get user and verify current password
            user = User.get_by_id(session['user_id'])
            if not user or not check_password_hash(user['password'], current_password):
                return jsonify({'success': False, 'message': 'Current password is incorrect!'}), 400
            
            # Update password
            User.update_password(session['user_id'], new_password)
            
            return jsonify({'success': True, 'message': 'Password changed successfully!'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'}), 500