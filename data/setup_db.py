import psycopg
from config import DB_CONNECTION_STR

def create_courses_table():
    """
    Creates the courses table in the database.
    Based on the schema used in util/course.py
    """
    try:
        with psycopg.connect(DB_CONNECTION_STR) as conn:
            print("Connection established")
            
            with conn.cursor() as cur:
                # Drop the table if it already exists (optional, for clean setup)
                # cur.execute("DROP TABLE IF EXISTS courses;")
                # print("Dropped existing table (if it existed).")
                
                # Create the courses table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS courses (
                        course_code VARCHAR(50) PRIMARY KEY,
                        title VARCHAR(500),
                        description TEXT,
                        credits INTEGER,
                        level VARCHAR(100),
                        prerequisites TEXT,
                        video_link VARCHAR(500),
                        instructors JSONB,
                        learning_outcomes JSONB,
                        syllabus JSONB,
                        resources_and_books JSONB,
                        assessment_structure TEXT,
                        extra JSONB,
                        source_url VARCHAR(500),
                        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'wip')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("Created courses table.")
                
                # Add status column to existing table if it doesn't exist
                cur.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='courses' AND column_name='status'
                        ) THEN
                            ALTER TABLE courses ADD COLUMN status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'wip'));
                        END IF;
                    END $$;
                """)
                print("Ensured status column exists.")
                
                # Create an index on level for faster queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level);
                """)
                print("Created index on level column.")
                
                # Commit the changes
                conn.commit()
                print("Database setup completed successfully!")
                
    except Exception as e:
        print("Database setup failed.")
        print(e)

if __name__ == "__main__":
    create_courses_table()

