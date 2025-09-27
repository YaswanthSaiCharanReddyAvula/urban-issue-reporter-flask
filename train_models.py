"""
ML Model Training Script
Trains category classification and priority detection models
"""
from ml_models import IssueMLPipeline
import sqlite3
import os

def create_sample_training_data():
    """Create sample training data to demonstrate ML capabilities"""
    sample_issues = [
        # Road issues
        ("Dangerous pothole on Main Street", "Large pothole blocking traffic on Main Street near the mall. Cars are swerving to avoid it, creating dangerous conditions.", "road", "high"),
        ("Street sign fallen down", "Stop sign at Oak Avenue intersection has fallen down after yesterday's storm", "road", "medium"),
        ("Minor crack in sidewalk", "Small crack in sidewalk near park entrance, not dangerous but should be fixed eventually", "road", "low"),
        ("Road completely blocked", "Emergency! Large tree fell across Highway 101 blocking all traffic. Need immediate attention!", "road", "critical"),
        
        # Electricity issues  
        ("Streetlight out on Park Avenue", "Streetlight has been out for 3 days making it dark and unsafe for pedestrians at night", "electricity", "high"),
        ("Power lines sparking", "URGENT: Power lines are sparking near residential area on Elm Street. Dangerous situation!", "electricity", "critical"),
        ("Dim streetlight needs bulb", "One streetlight is very dim, probably needs new bulb when convenient", "electricity", "low"),
        ("Multiple lights out downtown", "Several streetlights are out in downtown area affecting visibility", "electricity", "medium"),
        
        # Water issues
        ("Water main burst flooding street", "EMERGENCY: Major water main burst on 5th Street causing severe flooding", "water", "critical"),
        ("Small leak under fire hydrant", "Minor water leak noticed under fire hydrant on Maple Street", "water", "low"),
        ("Drain clogged causing puddles", "Storm drain on First Avenue is clogged causing large puddles after rain", "water", "medium"),
        ("No water pressure in area", "Entire residential block has very low water pressure since this morning", "water", "high"),
        
        # Sanitation issues
        ("Overflowing dumpster", "Dumpster behind shopping center is overflowing with garbage attracting rats", "sanitation", "high"),
        ("Missed garbage collection", "Our street's garbage hasn't been collected for 2 weeks, bins are overflowing", "sanitation", "medium"),
        ("Litter in park needs cleaning", "Some litter scattered in Central Park, would be nice to clean when possible", "sanitation", "low"),
        ("Sewage overflow emergency", "URGENT: Sewage is overflowing on residential street creating health hazard!", "sanitation", "critical")
    ]
    
    return sample_issues

def train_models():
    """Train both category and priority models"""
    print("🤖 Starting ML Model Training...")
    
    # Create ML pipeline
    pipeline = IssueMLPipeline()
    
    # Check if we have real data in database
    db_path = 'urban_issues.db'
    if os.path.exists(db_path):
        print("📊 Found existing database, checking for training data...")
        
        # Load existing data
        training_data = pipeline._load_training_data(db_path)
        
        if len(training_data) < 5:
            print("⚠️  Insufficient real data found. Adding sample training data...")
            add_sample_data_to_db(db_path)
        else:
            print(f"✅ Found {len(training_data)} existing issues for training")
    else:
        print("⚠️  No database found. Creating sample data...")
        add_sample_data_to_db(db_path)
    
    # Train models
    print("\n🎯 Training Category Classification Model...")
    category_success = pipeline.train_category_model(db_path)
    
    print("\n🔥 Training Priority Detection Model...")
    priority_success = pipeline.train_priority_model(db_path)
    
    # Test predictions
    print("\n🧪 Testing Trained Models...")
    test_predictions(pipeline)
    
    print("\n✅ Model training completed!")
    if category_success or priority_success:
        print("💾 Models saved to 'models/' directory")
        print("🚀 Models ready for use in the application")
    else:
        print("⚠️  Models will use rule-based fallback")

def add_sample_data_to_db(db_path):
    """Add sample training data to database"""
    sample_data = create_sample_training_data()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create issues table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            latitude REAL DEFAULT 0.0,
            longitude REAL DEFAULT 0.0,
            address TEXT DEFAULT 'Sample Address',
            image TEXT,
            upvotes INTEGER DEFAULT 0,
            reporter_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Insert sample data
        for title, description, category, priority in sample_data:
            cursor.execute('''
                INSERT INTO issues (title, description, category, priority, latitude, longitude, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, category, priority, 40.7128, -74.0060, "Sample Address"))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added {len(sample_data)} sample issues to database")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")

def test_predictions(pipeline):
    """Test model predictions with sample inputs"""
    test_cases = [
        ("Broken streetlight", "The streetlight on Oak Street is completely broken and it's very dark at night"),
        ("Emergency water leak", "URGENT: Water is flooding the entire intersection, need immediate help!"),
        ("Small pothole", "There's a minor pothole on Side Street, not too bad but should be fixed eventually"),
        ("Garbage overflow", "Trash bins are overflowing and attracting animals, creating unsanitary conditions")
    ]
    
    print("\n🧪 Testing Model Predictions:")
    print("-" * 60)
    
    for title, description in test_cases:
        # Test category prediction
        category_pred = pipeline.predict_category(title, description)
        priority_pred = pipeline.predict_priority(title, description, category_pred['category'])
        
        print(f"\n📝 Issue: '{title}'")
        print(f"   Category: {category_pred['category']} (confidence: {category_pred['confidence']:.2f})")
        print(f"   Priority: {priority_pred['priority']} (confidence: {priority_pred['confidence']:.2f})")
        print(f"   Methods: {category_pred['method']} / {priority_pred['method']}")

if __name__ == "__main__":
    train_models()