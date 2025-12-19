from app import app, db
from sqlalchemy import text

# This script manually adds the 'image_url' column to the 'skill' table
with app.app_context():
    print("⏳ Attempting to add column 'image_url' to 'skill' table...")
    try:
        # For SQLite
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE skill ADD COLUMN image_url VARCHAR(255)"))
            conn.commit()
        print("✅ Success: Column added!")
    except Exception as e:
        print(f"ℹ️  Note: {e}")
        print("   (This usually means the column already exists, which is fine.)")