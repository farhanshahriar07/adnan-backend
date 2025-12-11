from app import app, db

# This script forces the creation of any missing tables (like 'achievement')
with app.app_context():
    print("⏳ Connecting to database...")
    db.create_all()
    print("✅ Database successfully updated! 'Achievement' table created.")