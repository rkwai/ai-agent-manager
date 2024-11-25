# src/core/agent_manager.py
from typing import Dict, Any, List, Type
import uuid
import json
from datetime import datetime
import logging
from sqlite3 import Connection, Row
from src.database.db_setup import Database
from .agent import Agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentManager:
    """Manages agent lifecycle and task execution"""
    
    def __init__(self, database=None, db_path=":memory:"):
        """Initialize AgentManager with either a database instance or path"""
        self.db = database if database is not None else Database(db_path)
        self.active_agents = {}
        self._agent_classes = {}
        
    def register_agent_class(self, agent_class: Type[Agent]) -> None:
        """Register an agent class with its type identifier
        
        Args:
            agent_class: The agent class to register
        """
        if hasattr(agent_class, 'AGENT_TYPE'):
            self._agent_classes[agent_class.AGENT_TYPE] = agent_class
        else:
            logger.warning(f"Agent class {agent_class.__name__} has no AGENT_TYPE defined")
        
    def _row_to_agent(self, row: Row) -> Agent:
        """Convert database row to Agent instance"""
        config = json.loads(row['config'])
        agent_type = row.get('type', 'default')
        
        # Get the appropriate agent class
        agent_class = self._agent_classes.get(agent_type, Agent)
        
        # Create agent instance
        return agent_class(
            id=row['agent_id'],
            name=row['name'],
            model_name=config.get('model_name', 'gpt-3.5-turbo'),
            tools=config.get('tools', []),
            temperature=config.get('temperature', 0.7),
            status=row['status'],
            created_at=row['created_at']
        )
        
    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent by ID"""
        with self.db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()
            
            if not row:
                raise ValueError(f"Agent {agent_id} not found")
                
            return self._row_to_agent(row)
        
    async def create_agent(
        self, 
        name: str, 
        agent_type: str,
        config: Dict[str, Any]
    ) -> str:
        """Create a new agent
        
        Args:
            name: Name of the agent
            agent_type: Type identifier for the agent
            config: Initial configuration for the agent
            
        Returns:
            The ID of the created agent
        """
        agent_id = str(uuid.uuid4())
        
        try:
            with self.db.get_conn() as conn:
                # Create the agent record
                conn.execute("""
                    INSERT INTO agents (agent_id, name, config, status, type)
                    VALUES (?, ?, ?, ?, ?)
                """, (agent_id, name, json.dumps(config), "inactive", agent_type))
                
                # Initialize agent state
                conn.execute("""
                    INSERT INTO agent_states (agent_id, memory)
                    VALUES (?, ?)
                """, (agent_id, json.dumps({})))
                
            logger.info(f"Created {agent_type} agent: {agent_id} ({name})")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
            
    async def run_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a task with the specified agent"""
        agent = await self.get_agent(agent_id)
        return await agent.execute_task(task)