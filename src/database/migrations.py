import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def migrate_database(db_path: str) -> None:
    """
    Migrate existing database to new schema
    """
    if not Path(db_path).exists() or db_path == ":memory:":
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if migration is needed
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='agents'")
        table_def = cursor.fetchone()[0]
        
        if 'timestamp' in table_def.lower():
            # Backup existing tables
            cursor.executescript("""
                BEGIN TRANSACTION;
                
                -- Backup agents table
                CREATE TABLE agents_backup (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    model TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    created_at datetime NOT NULL
                );
                INSERT INTO agents_backup SELECT * FROM agents;
                
                -- Backup conversations table
                CREATE TABLE conversations_backup (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    user_message TEXT NOT NULL,
                    agent_response TEXT NOT NULL,
                    timestamp datetime NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                );
                INSERT INTO conversations_backup SELECT * FROM conversations;
                
                -- Drop original tables
                DROP TABLE conversations;
                DROP TABLE agents;
                
                -- Rename backup tables
                ALTER TABLE agents_backup RENAME TO agents;
                ALTER TABLE conversations_backup RENAME TO conversations;
                
                COMMIT;
            """)
            logger.info(f"Successfully migrated database: {db_path}")
    except Exception as e:
        logger.error(f"Failed to migrate database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close() 