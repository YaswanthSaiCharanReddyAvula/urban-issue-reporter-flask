"""
Database models and initialization for Urban Issue Reporter
"""
import sqlite3
import json
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This enables dict-like access to rows
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(Config.DATABASE_NAME)
    c = conn.cursor()
    
    # Organizations table
    c.execute('''CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Users table with role hierarchy
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        organization_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
    )''')
    
    # Add profile fields to users table (if they don't exist)
    try:
        c.execute('ALTER TABLE users ADD COLUMN phone TEXT')
    except:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE users ADD COLUMN bio TEXT')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE users ADD COLUMN profile_picture TEXT')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE users ADD COLUMN location TEXT')
    except:
        pass  # Column already exists
    
    # Issues table
    c.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        image TEXT,
        reported_by INTEGER,
        assigned_to INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reported_by) REFERENCES users (id),
        FOREIGN KEY (assigned_to) REFERENCES users (id)
    )''')
    
    # Add new priority scoring columns to issues table
    try:
        c.execute('ALTER TABLE issues ADD COLUMN priority_score REAL DEFAULT 5.0')
    except:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE issues ADD COLUMN priority_level TEXT DEFAULT "medium"')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE issues ADD COLUMN priority_breakdown TEXT')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE issues ADD COLUMN ai_severity_score REAL')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE issues ADD COLUMN location_importance_score REAL')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE issues ADD COLUMN duplicate_reports_count INTEGER DEFAULT 0')
    except:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE issues ADD COLUMN last_priority_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except:
        pass  # Column already exists
    
    # Citizen voting table
    c.execute('''CREATE TABLE IF NOT EXISTS citizen_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        vote_type TEXT NOT NULL, -- 'severity', 'duplicate', 'importance'
        rating INTEGER, -- 1-10 for severity votes
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(issue_id, user_id, vote_type)
    )''')
    
    # Duplicate reports tracking
    c.execute('''CREATE TABLE IF NOT EXISTS duplicate_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        duplicate_issue_id INTEGER NOT NULL,
        reported_by INTEGER NOT NULL,
        confidence_score REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (id),
        FOREIGN KEY (duplicate_issue_id) REFERENCES issues (id),
        FOREIGN KEY (reported_by) REFERENCES users (id),
        UNIQUE(issue_id, duplicate_issue_id)
    )''')
    
    # Priority calculation logs
    c.execute('''CREATE TABLE IF NOT EXISTS priority_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        old_priority_score REAL,
        new_priority_score REAL,
        old_priority_level TEXT,
        new_priority_level TEXT,
        trigger_reason TEXT, -- 'new_vote', 'age_update', 'duplicate_found', 'manual'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (id)
    )''')
    
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER,
        user_id INTEGER,
        content TEXT NOT NULL,
        is_official INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # User upvotes table
    c.execute('''CREATE TABLE IF NOT EXISTS user_upvotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        issue_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (issue_id) REFERENCES issues (id),
        UNIQUE(user_id, issue_id)
    )''')
    
    # Create default organizations if not exist
    organizations_data = [
        ('Government Main Body', 'general', 'Main government administrative body'),
        ('Electric Department', 'electric', 'Electricity and power related issues'),
        ('Water Department', 'water', 'Water supply and drainage issues'),
        ('Road Department', 'road', 'Road and transportation infrastructure'),
        ('Transport Department', 'transport', 'Public transportation services'),
        ('Sanitation Department', 'dustbin', 'Waste management and cleanliness'),
        ('Others Department', 'others', 'Other civic issues')
    ]
    
    for org_name, category, description in organizations_data:
        c.execute("SELECT * FROM organizations WHERE name = ?", (org_name,))
        if not c.fetchone():
            c.execute("INSERT INTO organizations (name, category, description) VALUES (?, ?, ?)",
                     (org_name, category, description))
    
    # Create super admin user if not exists
    c.execute("SELECT * FROM users WHERE email = ?", (Config.DEFAULT_ADMIN_EMAIL,))
    if not c.fetchone():
        admin_password = generate_password_hash(Config.DEFAULT_ADMIN_PASSWORD)
        c.execute("INSERT INTO users (name, email, password, role, organization_id) VALUES (?, ?, ?, ?, ?)",
                 (Config.DEFAULT_ADMIN_NAME, Config.DEFAULT_ADMIN_EMAIL, admin_password, 'super_admin', None))
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized successfully")

class User:
    """User model class"""
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def get_all():
        """Get all users"""
        conn = get_db_connection()
        users = conn.execute('''SELECT u.*, o.name as organization_name, o.category as organization_category
                               FROM users u 
                               LEFT JOIN organizations o ON u.organization_id = o.id
                               ORDER BY u.created_at DESC''').fetchall()
        conn.close()
        return [dict(user) for user in users]
    
    @staticmethod
    def get_by_role(role):
        """Get users by role"""
        conn = get_db_connection()
        users = conn.execute('''SELECT u.*, o.name as organization_name, o.category as organization_category
                               FROM users u 
                               LEFT JOIN organizations o ON u.organization_id = o.id
                               WHERE u.role = ?
                               ORDER BY u.created_at DESC''', (role,)).fetchall()
        conn.close()
        return [dict(user) for user in users]
    
    @staticmethod
    def get_by_organization(org_id):
        """Get users by organization"""
        conn = get_db_connection()
        users = conn.execute('''SELECT u.*, o.name as organization_name, o.category as organization_category
                               FROM users u 
                               LEFT JOIN organizations o ON u.organization_id = o.id
                               WHERE u.organization_id = ?
                               ORDER BY u.created_at DESC''', (org_id,)).fetchall()
        conn.close()
        return [dict(user) for user in users]
    
    @staticmethod
    def update_role(user_id, role, organization_id=None):
        """Update user role and organization"""
        conn = get_db_connection()
        conn.execute("UPDATE users SET role = ?, organization_id = ? WHERE id = ?",
                    (role, organization_id, user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def is_admin(user):
        """Check if user has admin privileges"""
        return user and user.get('role') in ['super_admin', 'org_admin', 'org_staff']
    
    @staticmethod
    def is_super_admin(user):
        """Check if user is super admin"""
        return user and user.get('role') == 'super_admin'
    
    @staticmethod
    def is_org_admin(user):
        """Check if user is organization admin"""
        return user and user.get('role') == 'org_admin'
    
    @staticmethod
    def is_org_staff(user):
        """Check if user is organization staff"""
        return user and user.get('role') == 'org_staff'
    
    @staticmethod
    def create(name, email, password, role='user', organization_id=None):
        """Create new user"""
        conn = get_db_connection()
        hashed_password = generate_password_hash(password)
        cursor = conn.execute("INSERT INTO users (name, email, password, role, organization_id) VALUES (?, ?, ?, ?, ?)",
                             (name, email, hashed_password, role, organization_id))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    @staticmethod
    def get_count():
        """Get total user count (all users including admins)"""
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def get_citizen_count():
        """Get count of regular users only (excludes admin roles)"""
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def update_profile(user_id, name=None, phone=None, bio=None, location=None, profile_picture=None):
        """Update user profile information"""
        conn = get_db_connection()
        
        # Build the update query dynamically based on provided fields
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if profile_picture is not None:
            updates.append("profile_picture = ?")
            params.append(profile_picture)
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            conn.execute(query, params)
            conn.commit()
        
        conn.close()
        return True
    
    @staticmethod
    def update_password(user_id, new_password):
        """Update user password"""
        conn = get_db_connection()
        hashed_password = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        conn.close()
        return True

class Issue:
    """Issue model class"""
    
    @staticmethod
    def get_all(category=None, status=None, search=None):
        """Get all issues with optional filters"""
        conn = get_db_connection()
        
        query = '''SELECT i.*, u.name as reporter_name 
                   FROM issues i 
                   LEFT JOIN users u ON i.reported_by = u.id 
                   WHERE 1=1'''
        params = []
        
        if category and category != 'all':
            query += ' AND i.category = ?'
            params.append(category)
        
        if status and status != 'all':
            query += ' AND i.status = ?'
            params.append(status)
        
        if search:
            query += ' AND (i.title LIKE ? OR i.description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY i.created_at DESC'
        
        issues = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(issue) for issue in issues]
    
    @staticmethod
    def get_by_id(issue_id):
        """Get issue by ID"""
        conn = get_db_connection()
        issue = conn.execute('''SELECT i.*, u.name as reporter_name, u.email as reporter_email 
                               FROM issues i 
                               LEFT JOIN users u ON i.reported_by = u.id 
                               WHERE i.id = ?''', (issue_id,)).fetchone()
        conn.close()
        return dict(issue) if issue else None
    
    @staticmethod
    def create(title, description, category, priority, latitude, longitude, address, image_filename, reported_by):
        """Create new issue with ML predictions"""
        # Try to import ML models (graceful fallback if not available)
        try:
            from ml_models import get_ml_predictions
            ml_available = True
        except ImportError:
            print("⚠️  ML models not available, using provided values")
            ml_available = False
        
        # Use ML predictions if available and no category/priority provided
        if ml_available:
            # Get ML predictions
            predictions = get_ml_predictions(title, description, category)
            
            # Use ML prediction if no category provided or confidence is high
            if not category or category == 'auto':
                category = predictions['category']['category']
                print(f"🤖 ML predicted category: {category} (confidence: {predictions['category']['confidence']:.2f})")
            
            # Use ML prediction if no priority provided or confidence is high
            if not priority or priority == 'auto':
                priority = predictions['priority']['priority']
                print(f"🎯 ML predicted priority: {priority} (confidence: {predictions['priority']['confidence']:.2f})")
            
            # Store prediction metadata for tracking
            prediction_metadata = {
                'category_confidence': predictions['category']['confidence'],
                'priority_confidence': predictions['priority']['confidence'],
                'category_method': predictions['category']['method'],
                'priority_method': predictions['priority']['method'],
                'explanation': predictions['explanation']
            }
            
            print(f"🧠 ML Predictions - Category: {category}, Priority: {priority}")
        
        conn = get_db_connection()
        cursor = conn.execute("""INSERT INTO issues 
                    (title, description, category, priority, latitude, longitude, address, image_filename, reported_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (title, description, category, priority, latitude, longitude, address, image_filename, reported_by))
        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return issue_id
    
    @staticmethod
    def update_status(issue_id, status):
        """Update issue status"""
        conn = get_db_connection()
        conn.execute("UPDATE issues SET status = ? WHERE id = ?", (status, issue_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def upvote(issue_id, user_id):
        """Add upvote to issue (only once per user)"""
        conn = get_db_connection()
        
        # Check if user has already upvoted this issue
        existing_upvote = conn.execute(
            "SELECT id FROM user_upvotes WHERE user_id = ? AND issue_id = ?", 
            (user_id, issue_id)
        ).fetchone()
        
        if existing_upvote:
            conn.close()
            return {'error': 'You have already upvoted this issue', 'already_upvoted': True}
        
        # Add upvote record
        conn.execute(
            "INSERT INTO user_upvotes (user_id, issue_id) VALUES (?, ?)", 
            (user_id, issue_id)
        )
        
        # Increment upvote count
        conn.execute("UPDATE issues SET upvotes = upvotes + 1 WHERE id = ?", (issue_id,))
        upvotes = conn.execute("SELECT upvotes FROM issues WHERE id = ?", (issue_id,)).fetchone()[0]
        
        conn.commit()
        conn.close()
        return {'upvotes': upvotes, 'success': True}
    
    @staticmethod
    def has_user_upvoted(issue_id, user_id):
        """Check if user has already upvoted this issue"""
        if not user_id:
            return False
        
        conn = get_db_connection()
        result = conn.execute(
            "SELECT id FROM user_upvotes WHERE user_id = ? AND issue_id = ?", 
            (user_id, issue_id)
        ).fetchone()
        conn.close()
        return result is not None
    
    @staticmethod
    def get_count():
        """Get total issue count"""
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def get_count_by_user(user_id):
        """Get issue count for a specific user"""
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM issues WHERE reported_by = ?", (user_id,)).fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def get_by_category(category):
        """Get issues by category (for organization filtering)"""
        conn = get_db_connection()
        query = '''SELECT i.*, u.name as reporter_name 
                   FROM issues i 
                   LEFT JOIN users u ON i.reported_by = u.id 
                   WHERE i.category = ?
                   ORDER BY i.created_at DESC'''
        issues = conn.execute(query, (category,)).fetchall()
        conn.close()
        return [dict(issue) for issue in issues]
    
    @staticmethod
    def get_for_organization(user_role, org_category=None, status=None):
        """Get issues based on user role and organization"""
        conn = get_db_connection()
        
        # Super admin can see all issues
        if user_role == 'super_admin':
            query = '''SELECT i.*, u.name as reporter_name 
                       FROM issues i 
                       LEFT JOIN users u ON i.reported_by = u.id 
                       WHERE 1=1'''
            params = []
        else:
            # Organization admin/staff can only see their category issues
            query = '''SELECT i.*, u.name as reporter_name 
                       FROM issues i 
                       LEFT JOIN users u ON i.reported_by = u.id 
                       WHERE i.category = ?'''
            params = [org_category]
        
        if status and status != 'all':
            query += ' AND i.status = ?'
            params.append(status)
        
        query += ' ORDER BY i.created_at DESC'
        
        issues = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(issue) for issue in issues]
    
    @staticmethod
    def get_stats():
        """Get issue statistics"""
        conn = get_db_connection()
        total_issues = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        pending_issues = conn.execute("SELECT COUNT(*) FROM issues WHERE status = 'pending'").fetchone()[0]
        resolved_issues = conn.execute("SELECT COUNT(*) FROM issues WHERE status = 'resolved'").fetchone()[0]
        recent_issues = conn.execute('''SELECT i.*, u.name as reporter_name 
                                       FROM issues i 
                                       LEFT JOIN users u ON i.reported_by = u.id 
                                       ORDER BY i.created_at DESC 
                                       LIMIT 10''').fetchall()
        conn.close()
        
        return {
            'total_issues': total_issues,
            'pending_issues': pending_issues,
            'resolved_issues': resolved_issues,
            'recent_issues': [dict(issue) for issue in recent_issues]
        }
    
    @staticmethod
    def get_ml_predictions(title, description, category=None):
        """Get ML predictions for issue category and priority"""
        try:
            from ml_models import get_ml_predictions
            return get_ml_predictions(title, description, category)
        except ImportError:
            return {
                'category': {'category': category or 'general', 'confidence': 0.5, 'method': 'fallback'},
                'priority': {'priority': 'medium', 'confidence': 0.5, 'method': 'fallback'},
                'explanation': {'category_reasoning': [], 'priority_reasoning': []},
                'error': 'ML models not available'
            }
    
    @staticmethod
    def update_with_ml_predictions(issue_id):
        """Update existing issue with ML predictions"""
        # Get issue details
        issue = Issue.get_by_id(issue_id)
        if not issue:
            return False
        
        # Get ML predictions
        predictions = Issue.get_ml_predictions(issue['title'], issue['description'])
        
        # Update if ML confidence is high
        conn = get_db_connection()
        updates = []
        params = []
        
        if predictions['category']['confidence'] > 0.8:
            updates.append("category = ?")
            params.append(predictions['category']['category'])
        
        if predictions['priority']['confidence'] > 0.8:
            updates.append("priority = ?")
            params.append(predictions['priority']['priority'])
        
        if updates:
            params.append(issue_id)
            query = f"UPDATE issues SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, params)
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    @staticmethod
    def update_priority_score(issue_id, priority_data):
        """Update issue priority score and related data"""
        conn = get_db_connection()
        
        # Get current priority data for logging
        current = conn.execute(
            "SELECT priority_score, priority_level FROM issues WHERE id = ?", 
            (issue_id,)
        ).fetchone()
        
        # Update priority data
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
        
        # Log priority change
        if current:
            conn.execute('''
                INSERT INTO priority_logs (
                    issue_id, old_priority_score, new_priority_score,
                    old_priority_level, new_priority_level, trigger_reason
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                issue_id,
                current['priority_score'],
                priority_data['final_score'],
                current['priority_level'],
                priority_data['priority_level'],
                'automatic_recalculation'
            ))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_priority_sorted(limit=None, category=None, status=None):
        """Get issues sorted by priority score (highest first)"""
        conn = get_db_connection()
        
        query = '''SELECT i.*, u.name as reporter_name 
                   FROM issues i 
                   LEFT JOIN users u ON i.reported_by = u.id 
                   WHERE 1=1'''
        params = []
        
        if category and category != 'all':
            query += ' AND i.category = ?'
            params.append(category)
        
        if status and status != 'all':
            query += ' AND i.status = ?'
            params.append(status)
        
        query += ' ORDER BY i.priority_score DESC, i.created_at DESC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        issues = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(issue) for issue in issues]
    
    @staticmethod
    def get_critical_issues(limit=10):
        """Get critical priority issues (score >= 8.0)"""
        conn = get_db_connection()
        issues = conn.execute('''
            SELECT i.*, u.name as reporter_name 
            FROM issues i 
            LEFT JOIN users u ON i.reported_by = u.id 
            WHERE i.priority_score >= 8.0 AND i.status != 'resolved'
            ORDER BY i.priority_score DESC, i.created_at ASC
            LIMIT ?
        ''', (limit,)).fetchall()
        conn.close()
        
        return [dict(issue) for issue in issues]
    
    @staticmethod
    def recalculate_all_priorities():
        """Recalculate priority scores for all unresolved issues"""
        from priority_scoring import PriorityScoring
        import json
        
        conn = get_db_connection()
        issues = conn.execute('''
            SELECT * FROM issues WHERE status != 'resolved'
        ''').fetchall()
        
        updated_count = 0
        for issue in issues:
            issue_data = dict(issue)
            priority_data = PriorityScoring.calculate_overall_priority_score(issue_data)
            
            # Update the issue with new priority data
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
                issue['id']
            ))
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        return updated_count

class Organization:
    """Organization model class"""
    
    @staticmethod
    def get_all():
        """Get all organizations"""
        conn = get_db_connection()
        organizations = conn.execute("SELECT * FROM organizations ORDER BY name").fetchall()
        conn.close()
        return [dict(org) for org in organizations]
    
    @staticmethod
    def get_by_id(org_id):
        """Get organization by ID"""
        conn = get_db_connection()
        org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
        conn.close()
        return dict(org) if org else None
    
    @staticmethod
    def get_by_category(category):
        """Get organization by category"""
        conn = get_db_connection()
        org = conn.execute("SELECT * FROM organizations WHERE category = ?", (category,)).fetchone()
        conn.close()
        return dict(org) if org else None
    
    @staticmethod
    def create(name, category, description=""):
        """Create new organization"""
        conn = get_db_connection()
        cursor = conn.execute("INSERT INTO organizations (name, category, description) VALUES (?, ?, ?)",
                             (name, category, description))
        org_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return org_id

class Comment:
    """Comment model class"""
    
    @staticmethod
    def get_by_issue_id(issue_id):
        """Get all comments for an issue"""
        conn = get_db_connection()
        comments = conn.execute('''SELECT c.*, u.name as user_name 
                                  FROM comments c 
                                  LEFT JOIN users u ON c.user_id = u.id 
                                  WHERE c.issue_id = ? 
                                  ORDER BY c.created_at ASC''', (issue_id,)).fetchall()
        conn.close()
        return [dict(comment) for comment in comments]
    
    @staticmethod
    def create(issue_id, user_id, content, is_official=0):
        """Create new comment"""
        conn = get_db_connection()
        cursor = conn.execute("INSERT INTO comments (issue_id, user_id, content, is_official) VALUES (?, ?, ?, ?)",
                             (issue_id, user_id, content, is_official))
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return comment_id
    
    @staticmethod
    def get_count_by_user(user_id):
        """Get comment count for a specific user"""
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM comments WHERE user_id = ?", (user_id,)).fetchone()[0]
        conn.close()
        return count
