from main import engine
from sqlalchemy import text

def fix_database():
    print("🛠️ Upgrading Database for Pro Forum...")
    
    with engine.connect() as conn:
        # 1. Add Columns to forum_posts
        try:
            conn.execute(text("ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS category VARCHAR DEFAULT 'General';"))
            conn.execute(text("ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS author_role VARCHAR DEFAULT 'Farmer';"))
            conn.execute(text("ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0;"))
            conn.execute(text("ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;"))
            conn.execute(text("ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0;"))
            print("✅ 'forum_posts' table updated.")
        except Exception as e:
            print(f"⚠️ Error updating forum_posts: {e}")

        # 2. Create post_votes table
        vote_sql = """
        CREATE TABLE IF NOT EXISTS post_votes (
            vote_id SERIAL PRIMARY KEY,
            user_id INTEGER,
            post_id INTEGER,
            vote_type INTEGER
        );
        """
        try:
            conn.execute(text(vote_sql))
            print("✅ 'post_votes' table created.")
        except Exception as e:
             # In SQLite/Postgres conflicts, sometimes raw SQL varies. 
             # If this fails, the main.py auto-create might catch it on restart.
            print(f"⚠️ Error creating post_votes: {e}")
            
        conn.commit()
    
    print("🎉 Database Upgrade Complete!")

if __name__ == "__main__":
    fix_database()