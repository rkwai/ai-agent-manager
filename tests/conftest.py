import warnings
import pytest
from unittest.mock import Mock, MagicMock
from src.core.agent_manager import AgentManager
import json

@pytest.fixture(autouse=True)
def ignore_pydantic_warnings():
    warnings.filterwarnings(
        "ignore",
        message=".*'type_params' parameter of 'typing.ForwardRef._evaluate'.*",
        category=DeprecationWarning
    ) 

@pytest.fixture
def mock_db():
    """Provide a mock database with context manager support"""
    mock = Mock()
    
    # Create mock connection with context manager
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Setup the context manager protocol
    mock_conn.__enter__.return_value = mock_cursor
    mock_conn.__exit__.return_value = None
    
    # Setup the mock database connection
    mock.get_conn.return_value = mock_conn
    
    # Setup default return values
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    
    return mock

@pytest.fixture
def setup_database():
    """Setup a fresh database for each test"""
    db = mock_db
    
    # Enable foreign keys and create tables
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

@pytest.fixture
def agent_manager(mock_db):
    """Fixture for AgentManager with mocked database"""
    return AgentManager(database=mock_db) 