# src/database/db_setup.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        # Create the connection first
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                model TEXT NOT NULL,
                temperature REAL NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        """)
        self.conn.commit()

    def create_agent(self, agent_data):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO agents (name, model, temperature, created_at)
            VALUES (?, ?, ?, ?)
        """, (agent_data["name"], agent_data["model"], 
              agent_data["temperature"], agent_data["created_at"]))
        self.conn.commit()
        return cursor.lastrowid

    def save_conversation(self, conversation_data):
        """
        Save a conversation to the database
        
        Args:
            conversation_data (dict): Dictionary containing:
                - agent_id: ID of the agent
                - user_message: Message from the user
                - agent_response: Response from the agent
                - timestamp: Time of the conversation
                
        Returns:
            int: ID of the saved conversation
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (agent_id, user_message, agent_response, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            conversation_data["agent_id"],
            conversation_data["user_message"],
            conversation_data["agent_response"],
            conversation_data["timestamp"]
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_agent(self, agent_id):
        """
        Retrieve an agent by ID
        
        Args:
            agent_id (int): The ID of the agent to retrieve
            
        Returns:
            dict: Agent data if found
            
        Raises:
            ValueError: If agent not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        agent = cursor.fetchone()
        
        if agent is None:
            raise ValueError(f"Agent with ID {agent_id} not found")
            
        return dict(agent)

    def get_agent_by_name(self, name):
        """
        Retrieve an agent by name
        
        Args:
            name (str): The name of the agent
            
        Returns:
            dict: Agent data if found
            
        Raises:
            ValueError: If agent not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE name = ?", (name,))
        agent = cursor.fetchone()
        
        if agent is None:
            raise ValueError(f"Agent with name {name} not found")
            
        return dict(agent)

    def update_agent(self, agent_id, updated_data):
        """
        Update an agent's configuration
        
        Args:
            agent_id (int): The ID of the agent to update
            updated_data (dict): New configuration data
        """
        cursor = self.conn.cursor()
        
        # Build SET clause dynamically based on provided fields
        set_clause = ", ".join(f"{key} = ?" for key in updated_data.keys())
        query = f"UPDATE agents SET {set_clause} WHERE id = ?"
        
        # Add agent_id to values
        values = list(updated_data.values()) + [agent_id]
        
        cursor.execute(query, values)
        self.conn.commit()

    def delete_agent(self, agent_id):
        """
        Delete an agent
        
        Args:
            agent_id (int): The ID of the agent to delete
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        self.conn.commit()

    def list_agents(self):
        """
        List all agents
        
        Returns:
            list: List of agent dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents")
        return [dict(row) for row in cursor.fetchall()]

    def get_agent_conversations(self, agent_id):
        """
        Get all conversations for a specific agent
        
        Args:
            agent_id (int): The ID of the agent
            
        Returns:
            list: List of conversation dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE agent_id = ? 
            ORDER BY timestamp DESC
        """, (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_conn(self):
        """Get the database connection"""
        return self.conn


def initialize_database(db_path):
    """Initialize database with all required tables"""
    db = Database(db_path)
    with db.get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT NOT NULL,
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
        """)
        conn.commit()
    return db