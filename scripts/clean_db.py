import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_db_connection, init_connection_pool
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_schema_sql():
    """Parse schema.sql to get tables and their dependencies"""
    schema_path = Path(__file__).parent.parent / 'sql' / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_content = f.read()

    # Extract table names and their foreign keys
    tables = {}
    table_pattern = r'CREATE TABLE (\w+)'
    fk_pattern = r'FOREIGN KEY.*REFERENCES (\w+)'
    
    # Find all CREATE TABLE statements
    for match in re.finditer(table_pattern, schema_content):
        table_name = match.group(1)
        tables[table_name] = []
    
    # Find all foreign key relationships
    for table in tables:
        table_start = schema_content.find(f"CREATE TABLE {table}")
        table_end = schema_content.find(");", table_start) + 2
        table_def = schema_content[table_start:table_end]
        
        for fk_match in re.finditer(fk_pattern, table_def):
            referenced_table = fk_match.group(1)
            tables[table].append(referenced_table)
    
    return tables

def get_deletion_order(tables):
    """Sort tables based on dependencies for safe deletion"""
    deletion_order = []
    visited = set()
    
    def visit(table):
        if table in visited:
            return
        visited.add(table)
        for dep in tables[table]:
            visit(dep)
        deletion_order.append(table)
    
    for table in tables:
        visit(table)
    
    return deletion_order[::-1]  # Reverse to get correct deletion order

def truncate_data():
    tables = parse_schema_sql()
    deletion_order = get_deletion_order(tables)
    
    truncate_commands = []
    # Add DELETE commands
    for table in deletion_order:
        truncate_commands.append(f"""DELETE FROM {table};""")
    
    # Add sequence reset commands
    for table in deletion_order:
        truncate_commands.append(f"""ALTER SEQUENCE {table}_id_seq RESTART WITH 1;""")
    
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
