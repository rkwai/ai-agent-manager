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
        try:
            # Parse config with error handling
            try:
                config = json.loads(row['config']) if row['config'] else {}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config JSON: {e}")
                config = {}
            
            # Get agent type from row, default to 'default' if not present
            agent_type = row['type'] if 'type' in row.keys() else 'default'
            logger.info(f"Creating agent with type: {agent_type}")
            
            # Get the appropriate agent class
            agent_class = self._agent_classes.get(agent_type, Agent)
            logger.info(f"Using agent class: {agent_class.__name__}")
            
            # Create agent instance with safe type conversion
            with self.db.get_conn() as conn:
                agent = agent_class(
                    id=row['agent_id'],
                    name=row['name'],
                    type=agent_type,
                    model_name=config.get('model_name', 'gpt-3.5-turbo'),
                    tools=config.get('tools', []),
                    temperature=float(config.get('temperature', 0.7)),
                    status=row['status'],
                    created_at=row['created_at'],
                    db_conn=conn
                )
            
            logger.info(f"Successfully created agent instance: {agent.to_dict()}")
            return agent
            
        except Exception as e:
            logger.error(f"Error converting database row to agent: {str(e)}", exc_info=True)
            raise
        
    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent by ID
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent not found
        """
        with self.db.get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            
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
        """Execute a task with specified agent"""
        try:
            # Get agent instance
            agent = await self.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            run_id = str(uuid.uuid4())
            started_at = datetime.utcnow()
            
            # Record task start
            with self.db.get_conn() as conn:
                conn.execute("""
                    INSERT INTO agent_runs 
                    (run_id, agent_id, task, status, started_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (run_id, agent_id, json.dumps(task), 'running', started_at))
            
            # Execute task
            result = await agent.execute_task(task)
            
            # Update run record
            with self.db.get_conn() as conn:
                conn.execute("""
                    UPDATE agent_runs 
                    SET status = ?, result = ?, completed_at = ?
                    WHERE run_id = ?
                """, ('completed', json.dumps(result), datetime.utcnow(), run_id))
            
            return result
        except Exception as e:
            logger.error(f"Failed to run task: {e}")
            raise

    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents from the database"""
        try:
            with self.db.get_conn() as conn:
                rows = conn.execute("SELECT * FROM agents").fetchall()
                agents = []
                for row in rows:
                    try:
                        config = json.loads(row["config"]) if row["config"] else {}
                        agents.append({
                            "id": row["agent_id"],
                            "name": row["name"],
                            "type": row["type"] if "type" in row.keys() else "default",
                            "status": row["status"],
                            "config": config,
                            "created_at": row["created_at"]
                        })
                    except Exception as e:
                        logger.error(f"Error processing agent row {row['agent_id']}: {e}")
                        continue
                return agents
        except Exception as e:
            logger.error(f"Failed to get all agents: {e}")
            raise

    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> None:
        """Update an existing agent
        
        Args:
            agent_id: ID of the agent to update
            agent_data: New agent data including name, type, and config
        
        Raises:
            ValueError: If agent not found
        """
        try:
            with self.db.get_conn() as conn:
                # Check if agent exists
                existing = conn.execute(
                    "SELECT agent_id FROM agents WHERE agent_id = ?",
                    (agent_id,)
                ).fetchone()
                
                if not existing:
                    raise ValueError(f"Agent {agent_id} not found")
                
                # Update the agent
                conn.execute("""
                    UPDATE agents 
                    SET name = ?, config = ?, type = ?
                    WHERE agent_id = ?
                """, (
                    agent_data["name"],
                    json.dumps(agent_data["config"]),
                    agent_data["type"],
                    agent_id
                ))
                conn.commit()
                
                logger.info(f"Updated agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise

    async def delete_agent(self, agent_id: str) -> None:
        """Delete an agent and its related data
        
        Args:
            agent_id: ID of the agent to delete
        
        Raises:
            ValueError: If agent not found
        """
        try:
            with self.db.get_conn() as conn:
                # Check if agent exists
                existing = conn.execute(
                    "SELECT agent_id FROM agents WHERE agent_id = ?",
                    (agent_id,)
                ).fetchone()
                
                if not existing:
                    raise ValueError(f"Agent {agent_id} not found")
                
                # First delete from agent_states (due to foreign key constraint)
                conn.execute("DELETE FROM agent_states WHERE agent_id = ?", (agent_id,))
                
                # Then delete the agent
                conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
                conn.commit()
                
                logger.info(f"Deleted agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise