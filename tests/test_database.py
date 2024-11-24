import pytest
from datetime import datetime
from src.database.db_setup import Database
import json
import sqlite3

@pytest.fixture
def setup_database():
    """Setup a fresh database for each test"""
    db = Database(":memory:")
    
    # Enable foreign keys
    with db.get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        conn.executescript("""
            DROP TABLE IF EXISTS agent_runs;
            DROP TABLE IF EXISTS agent_states;
            DROP TABLE IF EXISTS agents;
            
            CREATE TABLE agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE agent_states (
                agent_id TEXT PRIMARY KEY,
                memory TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            );
            
            CREATE TABLE agent_runs (
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

def test_database_connection(setup_database):
    """Test database connection and basic operations"""
    db = setup_database
    with db.get_conn() as conn:
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1

def test_database_tables_exist(setup_database):
    """Test that all required tables exist"""
    db = setup_database
    with db.get_conn() as conn:
        tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        table_names = [table[0] for table in tables]
        
        assert "agents" in table_names
        assert "agent_states" in table_names
        assert "agent_runs" in table_names

def test_database_schema(setup_database):
    """Test database schema is correct"""
    db = setup_database
    with db.get_conn() as conn:
        # Test agents table schema
        agents_info = conn.execute("PRAGMA table_info(agents)").fetchall()
        agent_columns = {col[1]: col[2] for col in agents_info}
        
        assert "agent_id" in agent_columns
        assert "name" in agent_columns
        assert "config" in agent_columns
        assert "status" in agent_columns
        assert "created_at" in agent_columns

def test_foreign_key_constraints(setup_database):
    """Test foreign key constraints are enforced"""
    db = setup_database
    with db.get_conn() as conn:
        # Try to insert agent_state without corresponding agent
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO agent_states (agent_id, memory)
                VALUES (?, ?)
            """, ("nonexistent-id", "{}"))
