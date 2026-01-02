from app import app, db
from sqlalchemy import text

def add_daily_update_column():
    with app.app_context():
        print("Checking database schema...")
        
        # SQL command to add the column
        # "IF NOT EXISTS" prevents errors if you run it twice
        sql = text("ALTER TABLE about ADD COLUMN IF NOT EXISTS daily_update TEXT;")
        
        try:
            with db.engine.connect() as conn:
                conn.execute(sql)
                conn.commit()
            print("✅ Successfully added 'daily_update' column to 'about' table.")
        except Exception as e:
            print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_daily_update_column()