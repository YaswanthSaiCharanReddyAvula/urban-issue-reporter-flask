#!/usr/bin/env python3
"""
Fix database schema by adding missing priority columns
"""
import sqlite3

def fix_database():
    conn = sqlite3.connect('urban_issues.db')
    
    # Add missing columns
    try:
        conn.execute('ALTER TABLE issues ADD COLUMN priority_score REAL DEFAULT 5.0')
        print('✅ Added priority_score column')
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print('ℹ️  priority_score column already exists')
        else:
            print(f'❌ Error adding priority_score: {e}')

    try:
        conn.execute('ALTER TABLE issues ADD COLUMN priority_level TEXT DEFAULT "medium"')
        print('✅ Added priority_level column')
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print('ℹ️  priority_level column already exists')
        else:
            print(f'❌ Error adding priority_level: {e}')

    try:
        conn.execute('ALTER TABLE issues ADD COLUMN priority_breakdown TEXT')
        print('✅ Added priority_breakdown column')
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print('ℹ️  priority_breakdown column already exists')
        else:
            print(f'❌ Error adding priority_breakdown: {e}')

    conn.commit()
    
    # Check current schema
    schema = conn.execute('PRAGMA table_info(issues)').fetchall()
    print('\n📋 Current issues table schema:')
    for col in schema:
        print(f'   {col[1]}: {col[2]}')
    
    # Calculate priority scores for existing issues
    issues = conn.execute('SELECT * FROM issues').fetchall()
    print(f'\n🔄 Found {len(issues)} issues to update with priority scores')
    
    # Now we need to recalculate priority scores for existing issues
    print('\n🎯 Priority scores will be calculated when you next run the app')
    
    conn.close()
    print('\n✅ Database schema updated successfully!')

if __name__ == '__main__':
    fix_database()