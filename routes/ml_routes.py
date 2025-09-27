"""
ML Management Routes - Admin interface for ML models
"""
from flask import render_template, request, jsonify, flash, redirect, url_for, session
from models import Issue, User
from auth_utils import admin_required
import json

def init_ml_routes(app):
    """Initialize ML management routes"""
    
    @app.route('/admin/ml')
    @admin_required
    def ml_dashboard():
        """ML model management dashboard"""
        try:
            from ml_models import ml_pipeline
            
            # Check if models are loaded
            models_loaded = {
                'category_model': ml_pipeline.category_model is not None,
                'priority_model': ml_pipeline.priority_model is not None
            }
            
            # Get some statistics
            stats = Issue.get_stats()
            
            return render_template('admin/ml_dashboard.html', 
                                 models_loaded=models_loaded, 
                                 stats=stats)
        except ImportError:
            flash('ML models are not available. Please install required packages.', 'error')
            return redirect(url_for('admin.dashboard'))
    
    @app.route('/admin/ml/train', methods=['POST'])
    @admin_required
    def train_models():
        """Train ML models with current data"""
        try:
            from train_models import train_models as run_training
            
            # Run training in background (in production, use Celery or similar)
            success = run_training()
            
            if success:
                flash('ML models trained successfully!', 'success')
            else:
                flash('Model training completed with warnings. Check logs for details.', 'warning')
            
        except Exception as e:
            flash(f'Error training models: {str(e)}', 'error')
        
        return redirect(url_for('ml_dashboard'))
    
    @app.route('/admin/ml/predict', methods=['POST'])
    @admin_required
    def test_prediction():
        """Test ML prediction with sample text"""
        try:
            title = request.form.get('title', '')
            description = request.form.get('description', '')
            
            if not title or not description:
                return jsonify({'error': 'Title and description are required'}), 400
            
            # Get ML predictions
            predictions = Issue.get_ml_predictions(title, description)
            
            return jsonify(predictions)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/ml/batch-update', methods=['POST'])
    @admin_required
    def batch_update_with_ml():
        """Update existing issues with ML predictions"""
        try:
            updated_count = 0
            issues = Issue.get_all()
            
            for issue in issues:
                if Issue.update_with_ml_predictions(issue['id']):
                    updated_count += 1
            
            flash(f'Updated {updated_count} issues with ML predictions', 'success')
            
        except Exception as e:
            flash(f'Error updating issues: {str(e)}', 'error')
        
        return redirect(url_for('ml_dashboard'))
    
    @app.route('/api/ml/predict')
    def api_predict():
        """API endpoint for ML predictions (for AJAX calls)"""
        title = request.args.get('title', '')
        description = request.args.get('description', '')
        
        if not title and not description:
            return jsonify({'error': 'No input provided'}), 400
        
        try:
            predictions = Issue.get_ml_predictions(title, description)
            return jsonify({
                'success': True,
                'predictions': predictions
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500