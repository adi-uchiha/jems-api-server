import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_db_connection, init_connection_pool
from seed_data.users import USERS
from seed_data.words import WORD_DIFFICULTY
from seed_data.utils import generate_session_times, generate_drawing_metrics
from seed_data.metrics import generate_user_metrics  # Add this import
import random
import logging
from datetime import timedelta, datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def seed_users(conn, users):
    with conn.cursor() as cur:
        # Batch insert all users at once
        args_str = ','.join(cur.mogrify("(%s,%s,%s,%s)", 
            (user['username'], user['password'], user['email'], user['name'])).decode('utf-8') 
            for user in users)
        cur.execute(f"""
            INSERT INTO users (username, password, email, name)
            VALUES {args_str}
            RETURNING id;
        """)
        conn.commit()
        return [row[0] for row in cur.fetchall()]

def seed_game_sessions_and_attempts(conn, user_ids):
    with conn.cursor() as cur:
        all_session_values = []
        all_attempt_values = [] 
        
        # First, generate all sessions and attempts data
        for user_id in user_ids:
            num_sessions = random.randint(3, 5) * 4  # 12-20 sessions per user
            sessions = generate_session_times(num_sessions)
            
            # Generate session values
            for start_time, end_time in sessions:
                total_time = int((end_time - start_time).total_seconds())
                total_attempts = random.randint(12, 15)
                successful = random.randint(int(total_attempts * 0.7), total_attempts)
                avg_time = random.randint(2300, 2800)
                
                all_session_values.append((
                    user_id, start_time, end_time, total_time,
                    total_attempts, successful, successful,
                    avg_time, random.randint(3, 5)
                ))

        # Batch insert all sessions first
        if all_session_values:
            args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s)", v).decode('utf-8') 
                               for v in all_session_values)
            cur.execute(f"""
                INSERT INTO game_sessions 
                (user_id, start_time, end_time, total_time_seconds, 
                 total_attempts, successful_attempts, total_score,
                 avg_drawing_time_ms, streak_count)
                VALUES {args_str}
                RETURNING id, user_id, start_time;
            """)
            session_results = cur.fetchall()  # Get all session IDs with their user_ids and start_times

        # Now generate attempts for each session
        for session_id, user_id, session_start in session_results:
            num_attempts = next(s[4] for s in all_session_values if s[0] == user_id)  # total_attempts
            
            # Generate attempts for this session
            for i in range(num_attempts):
                difficulty = random.choice(['EASY', 'MEDIUM', 'HARD'])
                word = random.choice(WORD_DIFFICULTY[difficulty])
                metrics = generate_drawing_metrics()
                attempt_time = session_start + timedelta(seconds=i*3)
                
                all_attempt_values.append((
                    user_id, session_id,
                    word, difficulty,
                    random.choices([True, False], weights=[85, 15])[0],
                    metrics['drawing_time_ms'],
                    metrics['recognition_accuracy'],
                    attempt_time
                ))

        # Batch insert all attempts
        if all_attempt_values:
            args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", v).decode('utf-8') 
                               for v in all_attempt_values)
            cur.execute(f"""
                INSERT INTO drawing_attempts 
                (user_id, session_id, word_prompt, difficulty, 
                 is_correct, drawing_time_ms, recognition_accuracy, created_at)
                VALUES {args_str};
            """)
        
        conn.commit()

def seed_user_metrics(conn, user_ids):
    with conn.cursor() as cur:
        metrics_values = [
            (user_id, *[v for v in generate_user_metrics(user_id, random.randint(3, 5)).values()][1:])
            for user_id in user_ids
        ]
        
        args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", v).decode('utf-8') 
                           for v in metrics_values)
        cur.execute(f"""
            INSERT INTO user_metrics 
            (user_id, total_games_played, total_attempts, successful_attempts,
             total_time_spent_seconds, current_level, experience_points,
             best_score, fastest_correct_ms, highest_streak,
             easy_accuracy, medium_accuracy, hard_accuracy, avg_drawing_time_ms)
            VALUES {args_str}
            ON CONFLICT (user_id) DO UPDATE SET
                current_level = EXCLUDED.current_level,
                experience_points = EXCLUDED.experience_points
        """)
        conn.commit()

def main():
    try:
        init_connection_pool()
        logger.info("Connected to database successfully!")

        with get_db_connection() as conn:
            logger.info("Seeding users...")
            user_ids = seed_users(conn, USERS)
            
            logger.info("Initializing user metrics...")
            seed_user_metrics(conn, user_ids)
            
            logger.info("Batch seeding sessions and attempts...")
            seed_game_sessions_and_attempts(conn, user_ids)
            
            # Verify data counts
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM game_sessions")
                sessions_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM drawing_attempts")
                attempts_count = cur.fetchone()[0]
                logger.info(f"Created {sessions_count} game sessions")
                logger.info(f"Created {attempts_count} drawing attempts")
        
        logger.info("Seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        raise
    finally:
        from app.db.connection import close_all_connections
        close_all_connections()
        logger.info("Closed all database connections")

if __name__ == "__main__":
    main()
