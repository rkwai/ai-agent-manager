# db_setup.py
import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentDB:
    def __init__(self, db_path: str = "agents.db"):
        self.db_path = db_path
        self.setup_db()
    
    @contextmanager
    def get_conn(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def setup_db(self):
        """Initialize the database with required tables"""
        with self.get_conn() as conn:
            conn.executescript("""
                -- Stores agent configurations
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    config JSON NOT NULL,
                    status TEXT DEFAULT 'inactive',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Stores current state of each agent
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_id TEXT PRIMARY KEY,
                    current_task JSON,
                    memory JSON,
                    last_active TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                );

                -- Stores execution history
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    task JSON,
                    status TEXT,
                    result JSON,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                );
            """)
            logger.info("Database initialized successfully")

    def test_connection(self):
        """Test the database connection and structure"""
        try:
            with self.get_conn() as conn:
                # Test each table
                tables = ['agents', 'agent_states', 'agent_runs']
                for table in tables:
                    conn.execute(f"SELECT * FROM {table} LIMIT 1")
                logger.info("Database connection and tables verified")
                return True
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False

# Test the setup
if __name__ == "__main__":
    db = AgentDB()
    if db.test_connection():
        print("✅ Database setup successful")
    else:
        print("❌ Database setup failed")