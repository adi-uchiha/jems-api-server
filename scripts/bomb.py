import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_db_connection, init_connection_pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def truncate_data():
    # Order matters due to foreign key constraints
    truncate_commands = [
        """DELETE FROM drawing_attempts;""",
        """DELETE FROM game_sessions;""",
        """DELETE FROM user_metrics;""",
        """DELETE FROM token_blacklist;""",
        """DELETE FROM users;""",  # This will cascade to all dependent tables
        """ALTER SEQUENCE users_id_seq RESTART WITH 1;""",
        """ALTER SEQUENCE game_sessions_id_seq RESTART WITH 1;""",
        """ALTER SEQUENCE drawing_attempts_id_seq RESTART WITH 1;""",
        """ALTER SEQUENCE user_metrics_id_seq RESTART WITH 1;""",
        """ALTER SEQUENCE token_blacklist_id_seq RESTART WITH 1;"""
    ]
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                for command in truncate_commands:
                    logger.info(f"Executing: {command}")
                    cur.execute(command)
                conn.commit()
                logger.info("All data cleared successfully!")
                
            except Exception as e:
                logger.error(f"Error clearing data: {e}")
                conn.rollback()
                raise

def main():
    try:
        init_connection_pool()
        logger.info("Connected to database successfully!")
        
        # Confirm with user
        confirm = input("⚠️ WARNING: This will delete ALL DATA while preserving the database structure. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            logger.info("Operation cancelled.")
            return
        
        logger.info("🧹 Starting data cleanup...")
        truncate_data()
        logger.info("✨ Database data cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise
    finally:
        from app.db.connection import close_all_connections
        close_all_connections()
        logger.info("Closed all database connections")

if __name__ == "__main__":
    main()
