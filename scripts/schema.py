import sys
from pathlib import Path
import logging

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.db.connection import get_db_connection, init_connection_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_sql_file():
    """Read the schema.sql file"""
    sql_file_path = Path(project_root) / 'sql' / 'schema.sql'
    with open(sql_file_path, 'r') as file:
        return file.read()

def get_table_names(sql_content):
    """Extract table names from CREATE TABLE statements"""
    return [
        line.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
        for line in sql_content.split('\n')
        if line.strip().startswith('CREATE TABLE IF NOT EXISTS')
    ]

def create_schema():
    """Execute the schema creation SQL"""
    try:
        # Read SQL file
        sql_content = read_sql_file()
        table_names = get_table_names(sql_content)
        
        # Show info and get confirmation
        print("\n🏗️  Database Schema Creation")
        print("\nThis will create/update the following tables:")
        for table in table_names:
            print(f"  - {table}")
        
        confirm = input("\n⚙️  Do you want to proceed with schema creation? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("\n🚫 Schema creation aborted!")
            return
        
        # Execute the schema creation
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print("\n🔨 Creating database schema...")
                cur.execute(sql_content)
                conn.commit()
                print("\n✅ Schema created successfully!")
                
                # Verify tables
                print("\n🔍 Verifying created tables:")
                for table in table_names:
                    cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (table,))
                    exists = cur.fetchone()[0]
                    print(f"  {'✅' if exists else '❌'} {table}")
                
    except Exception as e:
        logger.error(f"❌ Error during schema creation: {e}")
        raise
    finally:
        from app.db.connection import close_all_db_connections
        close_all_db_connections()
        logger.info("🏁 Database connections closed.")

if __name__ == "__main__":
    try:
        init_connection_pool()
        create_schema()
    except Exception as e:
        print(f"\n❌ Schema creation failed: {e}")
        sys.exit(1)
