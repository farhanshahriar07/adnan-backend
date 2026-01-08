import sqlalchemy
from app import app, db
from sqlalchemy import text

def fix_database():
    """
    1. Creates new tables (like DailyUpdate).
    2. Manually adds missing columns to existing tables (like 'about').
    """
    print("🔧 Starting Database Fix...")
    
    with app.app_context():
        # 1. Create any new tables (e.g. DailyUpdate) that don't exist yet
        print("   - Checking for new tables...")
        db.create_all()
        print("   ✅ New tables created (if any were missing).")

        # 2. Add missing columns to 'about' table
        # Since db.create_all() DOES NOT update existing tables, we do this manually.
        print("   - Checking 'about' table for missing columns...")
        
        inspector = sqlalchemy.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('about')]
        
        # List of new columns we added to models.py: (column_name, sql_type)
        new_columns = [
            ('daily_update', 'TEXT'),
            ('mini_profile_image', 'VARCHAR(255)'),
            ('resume_link', 'VARCHAR(255)')
        ]

        with db.engine.connect() as conn:
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    print(f"     -> Adding missing column: {col_name} ({col_type})")
                    try:
                        # ALTER TABLE command works for both SQLite and PostgreSQL
                        conn.execute(text(f'ALTER TABLE about ADD COLUMN {col_name} {col_type}'))
                        conn.commit()
                        print(f"     ✅ Added {col_name}")
                    except Exception as e:
                        print(f"     ❌ Error adding {col_name}: {e}")
                else:
                    print(f"     - {col_name} already exists.")

    print("\n🎉 Database migration finished!")

if __name__ == "__main__":
    fix_database()