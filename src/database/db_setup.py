# src/database/db_setup.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        """Initialize database with schema"""
        self.db_path = db_path
        self.conn = self._create_connection()
        
        # Enable foreign keys
        with self.get_conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create tables with consistent schema
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    status TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_id TEXT PRIMARY KEY,
                    memory TEXT NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                );
                
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                );
                
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    agent_response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                );
            """)
    
    def _create_connection(self):
        """Create a new database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_conn(self):
        """Get a properly configured database connection"""
        if self.conn is None:
            self.conn = self._create_connection()
        return self.conn

    def list_agents(self):
        """List all agents"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents")
        return [dict(row) for row in cursor.fetchall()]

    def delete_agent(self, agent_id: str):
        """Delete an agent and all related records"""
        cursor = self.conn.cursor()
        try:
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Check for any remaining foreign key references
            tables = ['conversations', 'agent_runs', 'agent_states']
            for table in tables:
                count = cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE agent_id = ?", (agent_id,)).fetchone()[0]
                if count > 0:
                    logger.info(f"Found {count} records in {table} for agent {agent_id}")
            
            # Delete related records first
            cursor.execute("DELETE FROM conversations WHERE agent_id = ?", (agent_id,))
            logger.info(f"Deleted conversations for agent {agent_id}")
            
            cursor.execute("DELETE FROM agent_runs WHERE agent_id = ?", (agent_id,))
            logger.info(f"Deleted agent_runs for agent {agent_id}")
            
            cursor.execute("DELETE FROM agent_states WHERE agent_id = ?", (agent_id,))
            logger.info(f"Deleted agent_states for agent {agent_id}")
            
            # Finally delete the agent
            cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
            logger.info(f"Deleted agent {agent_id}")
            
            # Commit transaction
            self.conn.commit()
            logger.info(f"Successfully deleted agent {agent_id} and all related records")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
            # Check if agent still exists
            exists = cursor.execute("SELECT COUNT(*) FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()[0]
            logger.error(f"Agent still exists: {exists}")
            raise

    def update_agent(self, agent_id: str, updated_data: dict):
        """Update an agent's data"""
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in updated_data.keys())
        query = f"UPDATE agents SET {set_clause} WHERE agent_id = ?"
        values = list(updated_data.values()) + [agent_id]
        cursor.execute(query, values)
        self.conn.commit()
