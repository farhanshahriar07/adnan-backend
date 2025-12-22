from app import app, db

# This script creates the new Blog table in the database
with app.app_context():
    print("⏳ Connecting to database...")
    db.create_all()
    print("✅ Database successfully updated! 'Blog' table created.")