"""
ML Models and Pipeline for Urban Issue Automation
Handles category classification and priority detection
"""
import re
import sqlite3
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline
import joblib
import os

class IssueMLPipeline:
    """ML Pipeline for issue classification and priority detection"""
    
    def __init__(self):
        self.category_model = None
        self.priority_model = None
        self.category_vectorizer = None
        self.priority_vectorizer = None
        
        # Urgency keywords for priority classification
        self.urgency_keywords = {
            'critical': ['emergency', 'dangerous', 'urgent', 'immediate', 'critical', 
                        'life-threatening', 'accident', 'fire', 'explosion', 'collapse'],
            'high': ['broken', 'severe', 'major', 'blocked', 'flooded', 'outage', 
                    'leak', 'damage', 'hazard', 'safety'],
            'medium': ['issue', 'problem', 'concern', 'needs', 'repair', 'fix', 
                      'maintenance', 'improvement'],
            'low': ['minor', 'small', 'cosmetic', 'suggestion', 'enhancement', 
                   'when possible', 'eventually']
        }
        
        # Category keywords for classification
        self.category_keywords = {
            'road': ['pothole', 'road', 'street', 'pavement', 'traffic', 'sign', 
                    'marking', 'intersection', 'sidewalk', 'curb'],
            'electricity': ['light', 'power', 'electric', 'lamp', 'pole', 'wire', 
                          'outage', 'streetlight', 'electrical'],
            'water': ['water', 'leak', 'pipe', 'drain', 'sewer', 'flooding', 
                     'overflow', 'burst', 'supply'],
            'sanitation': ['trash', 'garbage', 'waste', 'cleaning', 'dirty', 
                          'bins', 'collection', 'hygiene', 'litter']
        }
    
    def preprocess_text(self, text):
        """Clean and preprocess text for ML models"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers, keep only letters and spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_urgency_features(self, text, category):
        """Extract features for priority classification"""
        text = text.lower()
        features = {}
        
        # Count urgency keywords
        for priority_level, keywords in self.urgency_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text)
            features[f'{priority_level}_keywords'] = count
        
        # Text length (longer descriptions might indicate more serious issues)
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        
        # Category-specific urgency indicators
        if category == 'road':
            features['road_urgency'] = any(word in text for word in 
                ['blocked', 'traffic', 'accident', 'dangerous'])
        elif category == 'electricity':
            features['power_urgency'] = any(word in text for word in 
                ['outage', 'dark', 'dangerous', 'sparking'])
        elif category == 'water':
            features['water_urgency'] = any(word in text for word in 
                ['flooding', 'burst', 'leak', 'overflow'])
        elif category == 'sanitation':
            features['sanitation_urgency'] = any(word in text for word in 
                ['overflowing', 'smell', 'health', 'rats'])
        
        # Time indicators
        features['time_mentioned'] = any(word in text for word in 
            ['days', 'weeks', 'months', 'yesterday', 'today', 'since'])
        
        return features
    
    def predict_category(self, title, description):
        """Predict issue category from title and description"""
        if not self.category_model:
            return self._fallback_category_prediction(title, description)
        
        # Combine title and description
        text = f"{title} {description}"
        processed_text = self.preprocess_text(text)
        
        try:
            # Get prediction and confidence
            prediction = self.category_model.predict([processed_text])[0]
            probabilities = self.category_model.predict_proba([processed_text])[0]
            confidence = max(probabilities)
            
            return {
                'category': prediction,
                'confidence': confidence,
                'method': 'ml_model'
            }
        except Exception as e:
            print(f"ML prediction failed: {e}")
            return self._fallback_category_prediction(title, description)
    
    def predict_priority(self, title, description, category):
        """Predict issue priority based on urgency"""
        if not self.priority_model:
            return self._fallback_priority_prediction(title, description, category)
        
        try:
            # Extract features
            text = f"{title} {description}"
            features = self.extract_urgency_features(text, category)
            
            # Convert to format expected by model
            feature_vector = [list(features.values())]
            
            prediction = self.priority_model.predict(feature_vector)[0]
            probabilities = self.priority_model.predict_proba(feature_vector)[0]
            confidence = max(probabilities)
            
            return {
                'priority': prediction,
                'confidence': confidence,
                'method': 'ml_model'
            }
        except Exception as e:
            print(f"Priority prediction failed: {e}")
            return self._fallback_priority_prediction(title, description, category)
    
    def _fallback_category_prediction(self, title, description):
        """Rule-based fallback for category prediction"""
        text = f"{title} {description}".lower()
        
        # Score each category based on keyword matches
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[category] = score
        
        # Get category with highest score
        predicted_category = max(scores, key=scores.get)
        confidence = scores[predicted_category] / sum(scores.values()) if sum(scores.values()) > 0 else 0.25
        
        return {
            'category': predicted_category,
            'confidence': confidence,
            'method': 'rule_based'
        }
    
    def _fallback_priority_prediction(self, title, description, category):
        """Rule-based fallback for priority prediction"""
        text = f"{title} {description}".lower()
        
        # Check for critical keywords first
        if any(keyword in text for keyword in self.urgency_keywords['critical']):
            return {'priority': 'critical', 'confidence': 0.9, 'method': 'rule_based'}
        
        # Check for high priority keywords
        if any(keyword in text for keyword in self.urgency_keywords['high']):
            return {'priority': 'high', 'confidence': 0.8, 'method': 'rule_based'}
        
        # Check for low priority keywords
        if any(keyword in text for keyword in self.urgency_keywords['low']):
            return {'priority': 'low', 'confidence': 0.7, 'method': 'rule_based'}
        
        # Default to medium priority
        return {'priority': 'medium', 'confidence': 0.6, 'method': 'rule_based'}
    
    def train_category_model(self, db_path=None):
        """Train category classification model"""
        # Load training data from database
        data = self._load_training_data(db_path)
        
        if len(data) < 10:
            print("Insufficient training data. Using rule-based classification only.")
            return False
        
        # Prepare data
        X = [self.preprocess_text(f"{row['title']} {row['description']}") for row in data]
        y = [row['category'] for row in data]
        
        # Create pipeline
        self.category_model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
            ('classifier', MultinomialNB())
        ])
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.category_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.category_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Category Model Accuracy: {accuracy:.3f}")
        print(classification_report(y_test, y_pred))
        
        # Save model
        joblib.dump(self.category_model, 'models/category_model.pkl')
        return True
    
    def train_priority_model(self, db_path=None):
        """Train priority classification model"""
        # Load training data
        data = self._load_training_data(db_path)
        
        if len(data) < 10:
            print("Insufficient training data. Using rule-based priority only.")
            return False
        
        # Prepare features
        X = []
        y = []
        
        for row in data:
            features = self.extract_urgency_features(
                f"{row['title']} {row['description']}", 
                row['category']
            )
            X.append(list(features.values()))
            y.append(row['priority'])
        
        # Train model
        self.priority_model = RandomForestClassifier(n_estimators=100, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.priority_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.priority_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Priority Model Accuracy: {accuracy:.3f}")
        print(classification_report(y_test, y_pred))
        
        # Save model
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.priority_model, 'models/priority_model.pkl')
        return True
    
    def _load_training_data(self, db_path=None):
        """Load training data from database"""
        if not db_path:
            db_path = 'urban_issues.db'
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, description, category, priority 
                FROM issues 
                WHERE title IS NOT NULL AND description IS NOT NULL
            """)
            
            data = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return data
        except Exception as e:
            print(f"Error loading training data: {e}")
            return []
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            if os.path.exists('models/category_model.pkl'):
                self.category_model = joblib.load('models/category_model.pkl')
                print("Category model loaded successfully")
            
            if os.path.exists('models/priority_model.pkl'):
                self.priority_model = joblib.load('models/priority_model.pkl')
                print("Priority model loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def get_prediction_explanation(self, title, description, predictions):
        """Generate human-readable explanation for predictions"""
        explanation = {
            'category_reasoning': [],
            'priority_reasoning': []
        }
        
        text = f"{title} {description}".lower()
        
        # Category explanation
        for category, keywords in self.category_keywords.items():
            found_keywords = [kw for kw in keywords if kw in text]
            if found_keywords:
                explanation['category_reasoning'].append(
                    f"Found {category} keywords: {', '.join(found_keywords[:3])}"
                )
        
        # Priority explanation
        for priority, keywords in self.urgency_keywords.items():
            found_keywords = [kw for kw in keywords if kw in text]
            if found_keywords:
                explanation['priority_reasoning'].append(
                    f"Found {priority} urgency indicators: {', '.join(found_keywords[:3])}"
                )
        
        return explanation


# Global ML pipeline instance
ml_pipeline = IssueMLPipeline()

def get_ml_predictions(title, description, category=None):
    """
    Get ML predictions for issue category and priority
    Returns dict with category and priority predictions
    """
    # Predict category if not provided
    if not category:
        category_pred = ml_pipeline.predict_category(title, description)
        category = category_pred['category']
    else:
        category_pred = {'category': category, 'confidence': 1.0, 'method': 'provided'}
    
    # Predict priority
    priority_pred = ml_pipeline.predict_priority(title, description, category)
    
    # Get explanation
    explanation = ml_pipeline.get_prediction_explanation(
        title, description, {'category': category_pred, 'priority': priority_pred}
    )
    
    return {
        'category': category_pred,
        'priority': priority_pred,
        'explanation': explanation,
        'timestamp': datetime.now().isoformat()
    }

def initialize_ml_models():
    """Initialize ML models - call this on app startup"""
    ml_pipeline.load_models()
    return ml_pipeline