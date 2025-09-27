"""
Priority management routes for Urban Issue Reporter
Handles priority scoring, citizen voting, and duplicate detection
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, session
import json
from models import Issue, User, get_db_connection
from priority_scoring import PriorityScoring, CitizenVoting, ImageAnalysis

def init_priority_routes(app):
    """Initialize priority management routes"""
    
    @app.route('/priority/dashboard')
    def priority_dashboard():
        """Priority dashboard showing high-priority issues"""
        if 'user_id' not in session:
            flash('Please login to view priority dashboard!', 'error')
            return redirect(url_for('login'))
        
        # Get critical issues
        critical_issues = Issue.get_critical_issues(limit=20)
        
        # Get priority-sorted issues
        high_priority_issues = Issue.get_priority_sorted(limit=50)
        
        return render_template('priority_dashboard.html', 
                             critical_issues=critical_issues,
                             high_priority_issues=high_priority_issues)
    
    @app.route('/api/priority/calculate/<int:issue_id>', methods=['POST'])
    def calculate_issue_priority(issue_id):
        """Calculate/recalculate priority for a specific issue"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        try:
            issue = Issue.get_by_id(issue_id)
            if not issue:
                return jsonify({'success': False, 'message': 'Issue not found'}), 404
            
            # Calculate priority score
            priority_data = PriorityScoring.calculate_overall_priority_score(issue)
            
            # Update issue with new priority
            Issue.update_priority_score(issue_id, priority_data)
            
            return jsonify({
                'success': True,
                'priority_data': priority_data,
                'message': 'Priority calculated successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'Error calculating priority: {str(e)}'
            }), 500
    
    @app.route('/api/priority/recalculate-all', methods=['POST'])
    def recalculate_all_priorities():
        """Recalculate priorities for all issues (admin only)"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        user = User.get_by_id(session['user_id'])
        if not User.is_admin(user):
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        try:
            updated_count = Issue.recalculate_all_priorities()
            
            return jsonify({
                'success': True,
                'updated_count': updated_count,
                'message': f'Recalculated priorities for {updated_count} issues'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error recalculating priorities: {str(e)}'
            }), 500
    
    @app.route('/api/vote/severity', methods=['POST'])
    def vote_severity():
        """Submit citizen vote for issue severity"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        try:
            data = request.get_json()
            issue_id = data.get('issue_id')
            severity_rating = data.get('severity_rating')
            
            if not all([issue_id, severity_rating]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            if not (1 <= severity_rating <= 10):
                return jsonify({'success': False, 'message': 'Severity rating must be between 1-10'}), 400
            
            # Submit vote
            success = CitizenVoting.submit_severity_vote(
                issue_id, session['user_id'], severity_rating
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Severity vote submitted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to submit vote'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error submitting vote: {str(e)}'
            }), 500
    
    @app.route('/api/vote/duplicate', methods=['POST'])
    def mark_duplicate():
        """Mark two issues as duplicates"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        try:
            data = request.get_json()
            issue_id = data.get('issue_id')
            duplicate_issue_id = data.get('duplicate_issue_id')
            
            if not all([issue_id, duplicate_issue_id]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            if issue_id == duplicate_issue_id:
                return jsonify({'success': False, 'message': 'Cannot mark issue as duplicate of itself'}), 400
            
            # Mark as duplicate
            success = CitizenVoting.mark_duplicate(
                issue_id, duplicate_issue_id, session['user_id']
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Issues marked as duplicates successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to mark as duplicate'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error marking duplicate: {str(e)}'
            }), 500
    
    @app.route('/api/priority/get-votes/<int:issue_id>')
    def get_issue_votes(issue_id):
        """Get voting data for an issue"""
        try:
            conn = get_db_connection()
            
            # Get severity votes
            severity_votes = conn.execute('''
                SELECT rating, COUNT(*) as count
                FROM citizen_votes 
                WHERE issue_id = ? AND vote_type = 'severity'
                GROUP BY rating
                ORDER BY rating
            ''', (issue_id,)).fetchall()
            
            # Get duplicate reports
            duplicate_reports = conn.execute('''
                SELECT COUNT(*) as count
                FROM duplicate_reports 
                WHERE issue_id = ? OR duplicate_issue_id = ?
            ''', (issue_id, issue_id)).fetchone()
            
            # Get user's vote if logged in
            user_vote = None
            if 'user_id' in session:
                vote = conn.execute('''
                    SELECT rating FROM citizen_votes 
                    WHERE issue_id = ? AND user_id = ? AND vote_type = 'severity'
                ''', (issue_id, session['user_id'])).fetchone()
                user_vote = vote['rating'] if vote else None
            
            conn.close()
            
            # Calculate average severity
            total_votes = sum(vote['count'] for vote in severity_votes)
            avg_severity = 0
            if total_votes > 0:
                weighted_sum = sum(vote['rating'] * vote['count'] for vote in severity_votes)
                avg_severity = weighted_sum / total_votes
            
            return jsonify({
                'success': True,
                'severity_votes': [dict(vote) for vote in severity_votes],
                'duplicate_count': duplicate_reports['count'] if duplicate_reports else 0,
                'average_severity': round(avg_severity, 1),
                'total_votes': total_votes,
                'user_vote': user_vote
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error getting votes: {str(e)}'
            }), 500
    
    @app.route('/api/priority/analyze-image', methods=['POST'])
    def analyze_uploaded_image():
        """Analyze uploaded image for severity detection"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        try:
            data = request.get_json()
            issue_id = data.get('issue_id')
            image_path = data.get('image_path')
            category = data.get('category')
            
            if not all([issue_id, image_path, category]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            # Analyze image
            severity_score = ImageAnalysis.analyze_issue_image(image_path, category)
            
            if severity_score:
                # Update issue with AI severity score
                conn = get_db_connection()
                conn.execute(
                    "UPDATE issues SET ai_severity_score = ? WHERE id = ?",
                    (severity_score, issue_id)
                )
                conn.commit()
                conn.close()
                
                # Recalculate priority
                issue = Issue.get_by_id(issue_id)
                priority_data = PriorityScoring.calculate_overall_priority_score(issue)
                Issue.update_priority_score(issue_id, priority_data)
                
                return jsonify({
                    'success': True,
                    'ai_severity_score': severity_score,
                    'priority_data': priority_data,
                    'message': 'Image analyzed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to analyze image'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error analyzing image: {str(e)}'
            }), 500
    
    @app.route('/api/priority/find-similar/<int:issue_id>')
    def find_similar_issues(issue_id):
        """Find similar issues for duplicate detection"""
        try:
            issue = Issue.get_by_id(issue_id)
            if not issue:
                return jsonify({'success': False, 'message': 'Issue not found'}), 404
            
            conn = get_db_connection()
            
            # Find issues with similar location (within 200 meters) and same category
            similar_issues = conn.execute('''
                SELECT id, title, description, address, latitude, longitude, 
                       created_at, priority_score, status
                FROM issues 
                WHERE id != ? AND category = ? AND status != 'resolved'
                ORDER BY created_at DESC
                LIMIT 10
            ''', (issue_id, issue['category'])).fetchall()
            
            conn.close()
            
            # Filter by geographic proximity (simple distance check)
            import math
            
            def calculate_distance(lat1, lon1, lat2, lon2):
                """Calculate distance between two points in meters"""
                R = 6371000  # Earth's radius in meters
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                delta_phi = math.radians(lat2 - lat1)
                delta_lambda = math.radians(lon2 - lon1)
                
                a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                
                return R * c
            
            current_location = (issue['latitude'], issue['longitude'])
            nearby_issues = []
            
            for similar in similar_issues:
                distance = calculate_distance(
                    issue['latitude'], issue['longitude'],
                    similar['latitude'], similar['longitude']
                )
                
                if distance <= 200:  # Within 200 meters
                    similar_dict = dict(similar)
                    similar_dict['distance_meters'] = round(distance, 1)
                    nearby_issues.append(similar_dict)
            
            # Sort by distance
            nearby_issues.sort(key=lambda x: x['distance_meters'])
            
            return jsonify({
                'success': True,
                'similar_issues': nearby_issues[:5],  # Return top 5 most similar
                'total_found': len(nearby_issues)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error finding similar issues: {str(e)}'
            }), 500