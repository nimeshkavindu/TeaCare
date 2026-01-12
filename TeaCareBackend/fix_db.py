from main import engine
from sqlalchemy import text

def fix_database():
    print("🛠️ Patching database for Forum Moderation...")
    
    sql_command = """
    CREATE TABLE IF NOT EXISTS post_reports (
        report_id SERIAL PRIMARY KEY,
        post_id INTEGER,
        user_id INTEGER,
        reason VARCHAR,
        timestamp VARCHAR
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql_command))
            conn.commit()
            print("✅ Successfully created 'post_reports' table.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    fix_database()