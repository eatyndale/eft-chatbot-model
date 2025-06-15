"""
Database module for EFT Chatbot with persistent storage
Handles SQLite database operations for user accounts, sessions, and messages
"""

import sqlite3
import uuid
import datetime
import os
import time
from pathlib import Path

# Set a fixed path for the database in the user's home directory
DB_PATH = os.path.join(os.path.expanduser("~"), "eft_chatbot.db")
print(f"Using database at: {DB_PATH}")

def ensure_db_exists():
    """Make sure the database file exists"""
    # If database doesn't exist, create it
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}, creating new database...")
        setup_database()
    else:
        print(f"Database found at {DB_PATH}, checking structure...")
        try:
            # Simple validation - try to query users table
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("Users table not found, recreating database...")
                conn.close()
                backup_and_recreate_db()
            else:
                print("Database structure appears valid")
                
                # Check for required tables
                verify_all_tables(conn)
                
            conn.close()
        except Exception as e:
            print(f"Database validation error: {e}")
            print("Recreating database...")
            try:
                conn.close()
            except:
                pass
            
            backup_and_recreate_db()

def backup_and_recreate_db():
    """Backup existing database and create a new one"""
    try:
        if os.path.exists(DB_PATH):
            # Create backup with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{DB_PATH}.backup_{timestamp}"
            
            # Copy file
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            print(f"Created backup at {backup_path}")
            
            # Remove original
            os.remove(DB_PATH)
            time.sleep(1)  # Small delay to ensure file is released
    except Exception as ex:
        print(f"Failed to backup database: {ex}")
    
    # Create fresh database
    setup_database()

def verify_all_tables(conn=None):
    """Verify all required tables exist and create them if needed"""
    should_close = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        should_close = True
        
    cursor = conn.cursor()
    
    try:
        # Check if required tables exist
        required_tables = [
            'users', 'consent', 'assessments', 'sessions', 'messages', 'tapping_steps'
        ]
        
        # Get all existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"Existing tables: {existing_tables}")
        
        # Create any missing tables
        if 'messages' not in existing_tables:
            print("Creating missing 'messages' table...")
            cursor.execute('''
            CREATE TABLE messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                sender TEXT,
                content TEXT,
                emotion TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
        
        if 'tapping_steps' not in existing_tables:
            print("Creating missing 'tapping_steps' table...")
            cursor.execute('''
            CREATE TABLE tapping_steps (
                step_id TEXT PRIMARY KEY,
                session_id TEXT,
                step_number INTEGER,
                step_content TEXT,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
        
        conn.commit()
        print("Database tables verified successfully")
    except Exception as e:
        print(f"Error verifying database tables: {e}")
    
    if should_close:
        conn.close()

def setup_database():
    """Set up the SQLite database with required tables"""
    try:
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Create fresh database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create tables
        print("Creating users table...")
        cursor.execute('''
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        print("Creating consent table...")
        cursor.execute('''
        CREATE TABLE consent (
            consent_id TEXT PRIMARY KEY,
            user_id TEXT,
            consented_at TIMESTAMP,
            consent_version TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        print("Creating assessments table...")
        cursor.execute('''
        CREATE TABLE assessments (
            assessment_id TEXT PRIMARY KEY,
            user_id TEXT,
            completed_at TIMESTAMP,
            gad7_score INTEGER,
            phq9_score INTEGER,
            is_high_risk BOOLEAN,
            has_suicide_risk BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        print("Creating sessions table...")
        cursor.execute('''
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        print("Creating messages table...")
        cursor.execute('''
        CREATE TABLE messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            sender TEXT,
            content TEXT,
            emotion TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        
        print("Creating tapping_steps table...")
        cursor.execute('''
        CREATE TABLE tapping_steps (
            step_id TEXT PRIMARY KEY,
            session_id TEXT,
            step_number INTEGER,
            step_content TEXT,
            completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database setup complete at {DB_PATH}")
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise

def create_session(user_id):
    """Create a new therapy session"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        session_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id, start_time) VALUES (?, ?, ?)",
            (session_id, user_id, now)
        )
        
        conn.commit()
        conn.close()
        
        return session_id
    except Exception as e:
        print(f"Error creating session: {e}")
        return None

def end_session(session_id):
    """End a therapy session"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "UPDATE sessions SET end_time = ? WHERE session_id = ?",
            (now, session_id)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error ending session: {e}")

def store_message(session_id, sender, content, emotion=None):
    """Store a message with emotion"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        message_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO messages (message_id, session_id, timestamp, sender, content, emotion) VALUES (?, ?, ?, ?, ?, ?)",
            (message_id, session_id, now, sender, content, emotion)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error storing message: {e}")

def record_consent(user_id, version="1.0"):
    """Record user consent"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if consent already exists
        cursor.execute(
            "SELECT consent_id FROM consent WHERE user_id = ? AND consent_version = ?",
            (user_id, version)
        )
        
        if cursor.fetchone():
            # Consent already recorded
            conn.close()
            return
        
        consent_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO consent (consent_id, user_id, consented_at, consent_version) VALUES (?, ?, ?, ?)",
            (consent_id, user_id, now, version)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording consent: {e}")

def has_given_consent(user_id, version="1.0"):
    """Check if user has given consent"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT consent_id FROM consent WHERE user_id = ? AND consent_version = ?",
            (user_id, version)
        )
        
        result = cursor.fetchone() is not None
        conn.close()
        
        return result
    except Exception as e:
        print(f"Error checking consent: {e}")
        return False

def store_assessment_results(user_id, gad7_score, phq9_score, is_high_risk, has_suicide_risk):
    """Store assessment results"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        assessment_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            """
            INSERT INTO assessments (assessment_id, user_id, completed_at, 
                                   gad7_score, phq9_score, is_high_risk, has_suicide_risk) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (assessment_id, user_id, now, gad7_score, phq9_score, is_high_risk, has_suicide_risk)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error storing assessment results: {e}")

def has_recent_assessment(user_id, days=7):
    """Check if user has completed an assessment recently"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        cursor.execute(
            "SELECT assessment_id FROM assessments WHERE user_id = ? AND completed_at > ? LIMIT 1",
            (user_id, threshold_date)
        )
        
        result = cursor.fetchone() is not None
        conn.close()
        
        return result
    except Exception as e:
        print(f"Error checking recent assessment: {e}")
        return False

def get_latest_assessment(user_id):
    """Get user's most recent assessment results"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT gad7_score, phq9_score, is_high_risk, has_suicide_risk, completed_at
            FROM assessments 
            WHERE user_id = ? 
            ORDER BY completed_at DESC 
            LIMIT 1
            """,
            (user_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "gad7_score": result[0],
                "phq9_score": result[1],
                "is_high_risk": bool(result[2]),
                "has_suicide_risk": bool(result[3]),
                "completed_at": result[4]
            }
        
        return None
    except Exception as e:
        print(f"Error getting latest assessment: {e}")
        return None

def store_tapping_sequence(session_id, tapping_steps):
    """Store a sequence of tapping steps"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for i, step in enumerate(tapping_steps):
            step_id = str(uuid.uuid4())
            
            cursor.execute(
                """
                INSERT INTO tapping_steps (step_id, session_id, step_number, step_content)
                VALUES (?, ?, ?, ?)
                """,
                (step_id, session_id, i, step)
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error storing tapping sequence: {e}")

def mark_tapping_step_completed(session_id, step_number):
    """Mark a tapping step as completed"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            """
            UPDATE tapping_steps
            SET completed = 1, completed_at = ?
            WHERE session_id = ? AND step_number = ?
            """,
            (now, session_id, step_number)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error marking tapping step completed: {e}")

def get_user_session_count(user_id):
    """Get number of sessions for a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ?",
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    except Exception as e:
        print(f"Error getting user session count: {e}")
        return 0

def get_user_recent_emotions(user_id, limit=5):
    """Get recent emotions expressed by user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT m.emotion 
            FROM messages m
            JOIN sessions s ON m.session_id = s.session_id
            WHERE s.user_id = ? AND m.sender = 'user' AND m.emotion IS NOT NULL
            ORDER BY m.timestamp DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        
        emotions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return emotions
    except Exception as e:
        print(f"Error getting user recent emotions: {e}")
        return []