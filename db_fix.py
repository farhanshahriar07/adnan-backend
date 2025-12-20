from app import app, db

# This script forces the creation of the new 'Research' table
with app.app_context():
    print("⏳ Connecting to database...")
    db.create_all()
    print("✅ Database successfully updated! 'Research' table created.")