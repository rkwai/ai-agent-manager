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
        """Delete an agent"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
        self.conn.commit()

    def update_agent(self, agent_id: str, updated_data: dict):
        """Update an agent's data"""
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in updated_data.keys())
        query = f"UPDATE agents SET {set_clause} WHERE agent_id = ?"
        values = list(updated_data.values()) + [agent_id]
        cursor.execute(query, values)
        self.conn.commit()
