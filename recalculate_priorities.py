#!/usr/bin/env python3
"""
Recalculate priority scores for all existing issues
"""
import sqlite3
import sys
import os

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from priority_scoring import PriorityScoring
from models import get_db_connection
import json

def recalculate_all_priorities():
    """Recalculate priority scores for all issues"""
    conn = get_db_connection()
    
    # Get all issues
    issues = conn.execute('''
        SELECT id, title, description, category, priority, latitude, longitude, 
               address, created_at, ai_severity_score, location_importance_score
        FROM issues
    ''').fetchall()
    
    print(f'🔄 Recalculating priority scores for {len(issues)} issues...\n')
    
    for issue in issues:
        try:
            # Convert to dict for priority calculation
            issue_data = {
                'id': issue['id'],
                'title': issue['title'],
                'description': issue['description'],
                'category': issue['category'],
                'priority': issue['priority'],
                'latitude': issue['latitude'],
                'longitude': issue['longitude'],
                'address': issue['address'],
                'created_at': issue['created_at'],
                'ai_severity_score': issue['ai_severity_score']
            }
            
            # Calculate priority score
            priority_data = PriorityScoring.calculate_overall_priority_score(issue_data)
            
            # Update database
            conn.execute('''
                UPDATE issues 
                SET priority_score = ?, priority_level = ?, priority_breakdown = ?, 
                    last_priority_update = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                priority_data['final_score'],
                priority_data['priority_level'],
                json.dumps(priority_data),
                issue['id']
            ))
            
            print(f'✅ Issue #{issue["id"]}: "{issue["title"][:30]}..." - Score: {priority_data["final_score"]} ({priority_data["priority_level"]})')
            print(f'   Category: {issue["category"]}, Factors: Severity={priority_data["factor_scores"]["severity"]:.1f}, Location={priority_data["factor_scores"]["location"]:.1f}, Age={priority_data["factor_scores"]["age"]:.1f}')
            
        except Exception as e:
            print(f'❌ Error calculating priority for issue #{issue["id"]}: {e}')
    
    conn.commit()
    conn.close()
    print(f'\n✅ Priority scores recalculated successfully!')

if __name__ == '__main__':
    recalculate_all_priorities()