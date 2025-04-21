import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.db.connection import get_db_connection, init_connection_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_sql_file():
    """Read the nuke.sql file"""
    sql_file_path = Path(project_root) / 'sql' / 'nuke.sql'
    with open(sql_file_path, 'r') as file:
        return file.read()

def get_table_names(sql_content):
    """Extract table names from DROP TABLE statements"""
    return [
        line.split('DROP TABLE IF EXISTS')[1].split(';')[0].strip()
        for line in sql_content.split('\n')
        if line.strip().startswith('DROP TABLE IF EXISTS')
    ]

def nuke_database():
    """Execute the nuclear option - drop all tables"""
    try:
        # Read SQL file
        sql_content = read_sql_file()
        table_names = get_table_names(sql_content)
        
        # Show warning and get confirmation
        print("\n💣 WARNING: Nuclear Launch Detected 💣")
        print("\nThis will delete the following tables:")
        for table in table_names:
            print(f"  - {table}")
        
        confirm = input("\n☢️  Are you absolutely sure? This cannot be undone! (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("\n🚫 Nuclear launch aborted!")
            return
        
        # Execute the nuke
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print("\n🚀 Launching nukes...")
                cur.execute(sql_content)
                conn.commit()
                print("\n💥 BOOM! Database has been nuked successfully!")
                
    except Exception as e:
        logger.error(f"💀 Error during nuclear strike: {e}")
        raise
    finally:
        from app.db.connection import close_all_db_connections
        close_all_db_connections()
        logger.info("🏁 Mission completed. All connections closed.")

if __name__ == "__main__":
    try:
        init_connection_pool()
        nuke_database()
    except Exception as e:
        print(f"\n❌ Mission failed: {e}")
        sys.exit(1)
