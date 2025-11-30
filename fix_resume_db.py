from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Migrating Database for Resume Link...")
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE about ADD COLUMN resume_link VARCHAR(255)"))
            conn.commit()
            print("✅ Added column: resume_link")
        except Exception as e:
            print(f"⚠️  Error (column might already exist): {e}")
    print("Migration Complete!")