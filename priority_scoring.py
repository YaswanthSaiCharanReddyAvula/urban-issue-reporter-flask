"""
Multi-Factor Priority Scoring System for Urban Issue Reporter

This module implements a comprehensive priority scoring system based on multiple factors:
1. Severity/Urgency (image analysis + citizen votes)
2. Location Importance (road type + proximity to important facilities)
3. Number of Reports (duplicate detection)
4. Time Reported (age-based priority increase)
5. Impact on Public Safety & Economy

Priority Score = Σ(factor_score × weight)
"""
import math
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import requests
from models import get_db_connection

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

class PriorityScoring:
    """Enhanced priority scoring system with multi-factor analysis"""
    
    # Priority weights for different factors (total = 1.0)
    WEIGHTS = {
        'severity': 0.35,      # Severity/urgency of the issue
        'location': 0.25,      # Location importance
        'reports_count': 0.15, # Number of duplicate reports
        'age': 0.15,          # Time since reported
        'safety_impact': 0.10  # Public safety and economic impact
    }
    
    # Location importance mapping
    LOCATION_TYPES = {
        'highway': 10,
        'main_road': 8,
        'arterial': 7,
        'collector': 6,
        'residential': 4,
        'local': 3,
        'private': 1
    }
    
    # Important facility proximity bonuses
    FACILITY_BONUSES = {
        'hospital': 3.0,
        'school': 2.5,
        'emergency_services': 3.0,
        'public_transport': 2.0,
        'shopping_center': 1.5,
        'government_building': 1.8
    }
    
    @staticmethod
    def calculate_severity_score(issue_data: Dict) -> float:
        """
        Calculate severity score based on multiple factors
        Range: 0-10
        """
        base_score = 5.0  # Default medium severity
        
        # Factor 1: Category-based severity
        category_scores = {
            'road': 7.0,      # High impact on traffic
            'water': 8.0,     # Health and safety risk
            'electricity': 9.0, # Safety critical
            'dustbin': 4.0,   # Lower immediate impact
            'transport': 6.0,
            'others': 5.0
        }
        base_score = category_scores.get(issue_data.get('category', 'others'), 5.0)
        
        # Factor 2: Keyword-based severity analysis
        title = issue_data.get('title', '').lower()
        description = issue_data.get('description', '').lower()
        text = f"{title} {description}"
        
        # High severity keywords
        high_severity_keywords = [
            'emergency', 'urgent', 'danger', 'accident', 'broke', 'burst',
            'flood', 'fire', 'electrical', 'gas', 'leak', 'blocked',
            'collapsed', 'severe', 'major', 'critical'
        ]
        
        # Medium severity keywords  
        medium_severity_keywords = [
            'damage', 'problem', 'issue', 'concern', 'repair', 'fix',
            'maintenance', 'replace', 'broken'
        ]
        
        # Low severity keywords
        low_severity_keywords = [
            'minor', 'small', 'slight', 'cosmetic', 'aesthetic',
            'request', 'suggestion', 'improvement'
        ]
        
        severity_modifier = 0
        for keyword in high_severity_keywords:
            if keyword in text:
                severity_modifier += 2.0
        for keyword in medium_severity_keywords:
            if keyword in text:
                severity_modifier += 0.5
        for keyword in low_severity_keywords:
            if keyword in text:
                severity_modifier -= 1.0
        
        base_score = min(10.0, max(1.0, base_score + severity_modifier))
        
        # Factor 3: Citizen votes (if available)
        citizen_votes = issue_data.get('citizen_severity_votes', [])
        if citizen_votes:
            avg_citizen_vote = sum(citizen_votes) / len(citizen_votes)
            # Weight citizen votes as 30% of severity score
            base_score = (base_score * 0.7) + (avg_citizen_vote * 0.3)
        
        # Factor 4: Image analysis severity (if available)
        image_severity = issue_data.get('ai_severity_score')
        if image_severity:
            # Weight AI analysis as 20% of severity score
            base_score = (base_score * 0.8) + (image_severity * 0.2)
        
        return round(min(10.0, max(1.0, base_score)), 2)
    
    @staticmethod
    def calculate_location_score(latitude: float, longitude: float, address: str) -> float:
        """
        Calculate location importance score based on road type and proximity to facilities
        Range: 0-10
        """
        base_score = 5.0
        
        # Factor 1: Road type detection from address
        address_lower = address.lower()
        road_type_score = 5.0
        
        if any(keyword in address_lower for keyword in ['highway', 'expressway', 'freeway']):
            road_type_score = 10.0
        elif any(keyword in address_lower for keyword in ['main', 'avenue', 'boulevard']):
            road_type_score = 8.0
        elif any(keyword in address_lower for keyword in ['street', 'road', 'drive']):
            road_type_score = 6.0
        elif any(keyword in address_lower for keyword in ['lane', 'circle', 'court']):
            road_type_score = 4.0
        elif any(keyword in address_lower for keyword in ['private', 'alley']):
            road_type_score = 2.0
        
        base_score = road_type_score
        
        # Factor 2: Proximity to important facilities
        facility_bonus = PriorityScoring._calculate_facility_proximity_bonus(
            latitude, longitude, address_lower
        )
        
        base_score = min(10.0, base_score + facility_bonus)
        
        return round(base_score, 2)
    
    @staticmethod
    def _calculate_facility_proximity_bonus(lat: float, lng: float, address: str) -> float:
        """Calculate bonus score based on proximity to important facilities"""
        bonus = 0.0
        
        # Check address keywords for facility proximity
        if any(keyword in address for keyword in ['hospital', 'medical', 'clinic']):
            bonus += PriorityScoring.FACILITY_BONUSES['hospital']
        if any(keyword in address for keyword in ['school', 'college', 'university', 'education']):
            bonus += PriorityScoring.FACILITY_BONUSES['school']
        if any(keyword in address for keyword in ['police', 'fire station', 'emergency']):
            bonus += PriorityScoring.FACILITY_BONUSES['emergency_services']
        if any(keyword in address for keyword in ['bus stop', 'metro', 'station', 'transport']):
            bonus += PriorityScoring.FACILITY_BONUSES['public_transport']
        if any(keyword in address for keyword in ['mall', 'market', 'shopping', 'commercial']):
            bonus += PriorityScoring.FACILITY_BONUSES['shopping_center']
        if any(keyword in address for keyword in ['government', 'municipal', 'office', 'admin']):
            bonus += PriorityScoring.FACILITY_BONUSES['government_building']
        
        return min(3.0, bonus)  # Cap facility bonus at 3.0
    
    @staticmethod
    def calculate_reports_count_score(issue_id: int, latitude: float, longitude: float) -> Tuple[float, int]:
        """
        Calculate score based on number of similar/duplicate reports
        Returns: (score, duplicate_count)
        Range: 0-10
        """
        # Find similar issues within 100 meters radius
        conn = get_db_connection()
        similar_issues = conn.execute('''
            SELECT id, latitude, longitude, title, description, created_at
            FROM issues 
            WHERE id != ? AND status != 'resolved'
        ''', (issue_id,)).fetchall()
        
        duplicate_count = 0
        base_score = 1.0  # Base score for single report
        
        current_location = (latitude, longitude)
        
        for similar in similar_issues:
            distance = calculate_distance(
                latitude, longitude,
                similar['latitude'], similar['longitude']
            )
            
            # Consider as duplicate if within 100 meters
            if distance <= 100:
                duplicate_count += 1
        
        # Score increases with number of duplicates
        if duplicate_count == 0:
            score = 1.0
        elif duplicate_count <= 2:
            score = 3.0
        elif duplicate_count <= 5:
            score = 6.0
        elif duplicate_count <= 10:
            score = 8.0
        else:
            score = 10.0
        
        conn.close()
        return round(score, 2), duplicate_count
    
    @staticmethod
    def calculate_age_score(created_at: str) -> float:
        """
        Calculate priority score based on issue age
        Older issues gradually increase in priority
        Range: 1-10
        """
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            created_date = datetime.now()
        
        age_days = (datetime.now().replace(tzinfo=None) - created_date.replace(tzinfo=None)).days
        
        if age_days <= 1:
            return 2.0  # New issues start with low age priority
        elif age_days <= 7:
            return 3.0
        elif age_days <= 30:
            return 5.0
        elif age_days <= 90:
            return 7.0
        elif age_days <= 180:
            return 8.5
        else:
            return 10.0  # Very old issues get highest age priority
    
    @staticmethod
    def calculate_safety_impact_score(issue_data: Dict) -> float:
        """
        Calculate public safety and economic impact score
        Range: 0-10
        """
        base_score = 5.0
        
        title = issue_data.get('title', '').lower()
        description = issue_data.get('description', '').lower()
        category = issue_data.get('category', '').lower()
        text = f"{title} {description}"
        
        # High safety impact keywords
        high_impact_keywords = [
            'accident', 'traffic', 'block', 'congestion', 'jam',
            'dangerous', 'hazard', 'unsafe', 'risk', 'injury',
            'emergency', 'ambulance', 'fire truck', 'police'
        ]
        
        # Economic impact keywords
        economic_keywords = [
            'business', 'commerce', 'shop', 'delivery', 'truck',
            'transport', 'goods', 'supply', 'economic', 'revenue'
        ]
        
        safety_modifier = 0
        for keyword in high_impact_keywords:
            if keyword in text:
                safety_modifier += 1.5
        
        for keyword in economic_keywords:
            if keyword in text:
                safety_modifier += 1.0
        
        # Category-based safety impact
        category_impact = {
            'road': 3.0,      # High traffic impact
            'electricity': 4.0, # Safety critical
            'water': 3.5,     # Health risk
            'transport': 3.0,
            'dustbin': 1.0,   # Lower safety impact
            'others': 2.0
        }
        
        base_score += safety_modifier + category_impact.get(category, 2.0)
        
        return round(min(10.0, max(1.0, base_score)), 2)
    
    @staticmethod
    def calculate_overall_priority_score(issue_data: Dict) -> Dict:
        """
        Calculate overall priority score combining all factors
        Returns detailed breakdown and final score
        """
        # Calculate individual factor scores
        severity_score = PriorityScoring.calculate_severity_score(issue_data)
        location_score = PriorityScoring.calculate_location_score(
            issue_data['latitude'], issue_data['longitude'], issue_data['address']
        )
        reports_score, duplicate_count = PriorityScoring.calculate_reports_count_score(
            issue_data['id'], issue_data['latitude'], issue_data['longitude']
        )
        age_score = PriorityScoring.calculate_age_score(issue_data['created_at'])
        safety_score = PriorityScoring.calculate_safety_impact_score(issue_data)
        
        # Calculate weighted final score
        final_score = (
            severity_score * PriorityScoring.WEIGHTS['severity'] +
            location_score * PriorityScoring.WEIGHTS['location'] +
            reports_score * PriorityScoring.WEIGHTS['reports_count'] +
            age_score * PriorityScoring.WEIGHTS['age'] +
            safety_score * PriorityScoring.WEIGHTS['safety_impact']
        )
        
        # Determine priority level
        if final_score >= 8.0:
            priority_level = 'critical'
        elif final_score >= 6.5:
            priority_level = 'high'
        elif final_score >= 4.5:
            priority_level = 'medium'
        elif final_score >= 2.5:
            priority_level = 'low'
        else:
            priority_level = 'very_low'
        
        return {
            'final_score': round(final_score, 2),
            'priority_level': priority_level,
            'factor_scores': {
                'severity': severity_score,
                'location': location_score,
                'reports_count': reports_score,
                'age': age_score,
                'safety_impact': safety_score
            },
            'weights': PriorityScoring.WEIGHTS,
            'duplicate_count': duplicate_count,
            'calculation_timestamp': datetime.now().isoformat()
        }

class CitizenVoting:
    """Handle citizen voting for issue severity and duplicate marking"""
    
    @staticmethod
    def submit_severity_vote(issue_id: int, user_id: int, severity_rating: int) -> bool:
        """Submit citizen vote for issue severity (1-10 scale)"""
        if not (1 <= severity_rating <= 10):
            return False
        
        conn = get_db_connection()
        try:
            # Check if user already voted
            existing_vote = conn.execute(
                "SELECT id FROM citizen_votes WHERE issue_id = ? AND user_id = ? AND vote_type = 'severity'",
                (issue_id, user_id)
            ).fetchone()
            
            if existing_vote:
                # Update existing vote
                conn.execute(
                    "UPDATE citizen_votes SET rating = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (severity_rating, existing_vote['id'])
                )
            else:
                # Insert new vote
                conn.execute(
                    "INSERT INTO citizen_votes (issue_id, user_id, vote_type, rating) VALUES (?, ?, 'severity', ?)",
                    (issue_id, user_id, severity_rating)
                )
            
            conn.commit()
            
            # Recalculate priority for this issue
            CitizenVoting._recalculate_issue_priority(issue_id)
            
            return True
        except Exception as e:
            print(f"Error submitting severity vote: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def mark_duplicate(issue_id: int, duplicate_issue_id: int, user_id: int) -> bool:
        """Mark two issues as duplicates"""
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO duplicate_reports (issue_id, duplicate_issue_id, reported_by, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (issue_id, duplicate_issue_id, user_id)
            )
            conn.commit()
            
            # Recalculate priority for both issues
            CitizenVoting._recalculate_issue_priority(issue_id)
            CitizenVoting._recalculate_issue_priority(duplicate_issue_id)
            
            return True
        except Exception as e:
            print(f"Error marking duplicate: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def _recalculate_issue_priority(issue_id: int):
        """Recalculate priority score for an issue"""
        conn = get_db_connection()
        try:
            issue = conn.execute(
                "SELECT * FROM issues WHERE id = ?", (issue_id,)
            ).fetchone()
            
            if issue:
                issue_data = dict(issue)
                priority_data = PriorityScoring.calculate_overall_priority_score(issue_data)
                
                # Update issue with new priority data
                conn.execute('''
                    UPDATE issues SET 
                        priority_score = ?,
                        priority_level = ?,
                        priority_breakdown = ?,
                        last_priority_update = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    priority_data['final_score'],
                    priority_data['priority_level'], 
                    json.dumps(priority_data),
                    issue_id
                ))
                conn.commit()
        except Exception as e:
            print(f"Error recalculating priority: {e}")
        finally:
            conn.close()

class ImageAnalysis:
    """AI-based image analysis for automatic severity detection"""
    
    @staticmethod
    def analyze_issue_image(image_path: str, issue_category: str) -> Optional[float]:
        """
        Analyze uploaded image to determine severity score
        Returns severity score 1-10 or None if analysis fails
        """
        try:
            # This is a placeholder for actual AI image analysis
            # In a real implementation, you would integrate with:
            # - Computer Vision APIs (Google Vision, Azure Cognitive Services)
            # - Custom trained models for pothole/infrastructure damage detection
            # - OpenCV for image processing
            
            # For now, return a mock severity score based on category
            category_base_scores = {
                'road': 7.0,
                'water': 6.0,
                'electricity': 8.0,
                'dustbin': 4.0,
                'transport': 5.0,
                'others': 5.0
            }
            
            base_score = category_base_scores.get(issue_category, 5.0)
            
            # Add some random variation to simulate AI analysis
            import random
            variation = random.uniform(-1.5, 1.5)
            final_score = max(1.0, min(10.0, base_score + variation))
            
            return round(final_score, 2)
            
        except Exception as e:
            print(f"Error in image analysis: {e}")
            return None
    
    @staticmethod
    def schedule_batch_analysis():
        """Schedule batch analysis of all unanalyzed images"""
        conn = get_db_connection()
        try:
            unanalyzed_issues = conn.execute('''
                SELECT id, image, category FROM issues 
                WHERE image IS NOT NULL AND ai_severity_score IS NULL
            ''').fetchall()
            
            for issue in unanalyzed_issues:
                if issue['image']:
                    severity_score = ImageAnalysis.analyze_issue_image(
                        issue['image'], issue['category']
                    )
                    
                    if severity_score:
                        conn.execute(
                            "UPDATE issues SET ai_severity_score = ? WHERE id = ?",
                            (severity_score, issue['id'])
                        )
            
            conn.commit()
            print(f"Analyzed {len(unanalyzed_issues)} images for severity")
            
        except Exception as e:
            print(f"Error in batch image analysis: {e}")
        finally:
            conn.close()