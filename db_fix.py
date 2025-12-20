from app import app, db
from sqlalchemy import text

# This script adds the 'mini_profile_image' column to the 'about' table
with app.app_context():
    print("⏳ Attempting to add column 'mini_profile_image' to 'about' table...")
    try:
        # Using raw SQL to alter table
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE about ADD COLUMN mini_profile_image VARCHAR(255)"))
            conn.commit()
        print("✅ Success: Column 'mini_profile_image' added!")
    except Exception as e:
        print(f"ℹ️  Note: {e}")
        print("   (This usually means the column already exists.)")