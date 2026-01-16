from main import engine
from sqlalchemy import text

def fix_database():
    print("🛠️ Creating Expert Recommendations Table...")
    sql_command = """
    CREATE TABLE IF NOT EXISTS expert_recommendations (
        recommendation_id SERIAL PRIMARY KEY,
        report_id INTEGER REFERENCES disease_reports(report_id),
        expert_id INTEGER REFERENCES users(user_id),
        expert_name VARCHAR,
        suggested_disease VARCHAR,
        notes VARCHAR,
        timestamp VARCHAR
    );
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(sql_command))
            conn.commit()
            print("✅ Table 'expert_recommendations' created.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_database()