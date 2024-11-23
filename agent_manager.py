# agent_manager.py
from typing import Dict, Any, Optional
import uuid
import json
from datetime import datetime
import logging
from langchain.llms import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from db_setup import AgentDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, db_path: str = "agents.db"):
        self.db = AgentDB(db_path)
        self.active_agents = {}  # In-memory cache of active agents
        
    async def create_agent(self, name: str, config: Dict[str, Any]) -> str:
        """Create a new agent with given configuration"""
        agent_id = str(uuid.uuid4())
        
        # Validate config has required fields
        required_fields = ['tools', 'model_name']
        if not all(field in config for field in required_fields):
            raise ValueError(f"Config missing required fields: {required_fields}")
            
        try:
            # Store in database
            with self.db.get_conn() as conn:
                conn.execute("""
                    INSERT INTO agents (agent_id, name, config, status)
                    VALUES (?, ?, ?, ?)
                """, (agent_id, name, json.dumps(config), 'inactive'))
                
                # Initialize state
                conn.execute("""
                    INSERT INTO agent_states (agent_id, memory)
                    VALUES (?, ?)
                """, (agent_id, json.dumps({})))
                
            logger.info(f"Created agent: {agent_id} ({name})")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    async def start_agent(self, agent_id: str) -> bool:
        """Start an agent and load it into memory"""
        try:
            with self.db.get_conn() as conn:
                # Get agent config
                agent_row = conn.execute(
                    "SELECT config FROM agents WHERE agent_id = ?",
                    (agent_id,)
                ).fetchone()
                
                if not agent_row:
                    raise ValueError(f"Agent {agent_id} not found")
                
                config = json.loads(agent_row['config'])
                
                # Initialize LangChain agent
                memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
                
                llm = OpenAI(
                    temperature=config.get('temperature', 0),
                    model_name=config['model_name']
                )
                
                agent = initialize_agent(
                    tools=config['tools'],
                    llm=llm,
                    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                    memory=memory,
                    verbose=True
                )
                
                # Store in memory and update status
                self.active_agents[agent_id] = agent
                conn.execute(
                    "UPDATE agents SET status = 'active' WHERE agent_id = ?",
                    (agent_id,)
                )
                
                logger.info(f"Started agent: {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {e}")
            return False

    async def run_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with specified agent"""
        try:
            # Get agent instance
            agent = self.active_agents.get(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not active")
            
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
            result = await agent.arun(task)
            
            # Update run record
            with self.db.get_conn() as conn:
                conn.execute("""
                    UPDATE agent_runs 
                    SET status = ?, result = ?, completed_at = ?
                    WHERE run_id = ?
                """, ('completed', json.dumps(result), datetime.utcnow(), run_id))
            
            return {"run_id": run_id, "result": result}
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            if 'run_id' in locals():
                with self.db.get_conn() as conn:
                    conn.execute("""
                        UPDATE agent_runs 
                        SET status = ?, result = ?, completed_at = ?
                        WHERE run_id = ?
                    """, ('failed', json.dumps(str(e)), datetime.utcnow(), run_id))
            raise

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent and remove from memory"""
        try:
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
                
            with self.db.get_conn() as conn:
                conn.execute(
                    "UPDATE agents SET status = 'inactive' WHERE agent_id = ?",
                    (agent_id,)
                )
            
            logger.info(f"Stopped agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False

# Test basic functionality
if __name__ == "__main__":
    import asyncio
    
    async def test_manager():
        manager = AgentManager()
        
        # Create test agent
        config = {
            "model_name": "gpt-3.5-turbo",
            "tools": [],  # Empty for testing
            "temperature": 0.7
        }
        
        agent_id = await manager.create_agent("Test Agent", config)
        print(f"Created agent: {agent_id}")
        
        # Start agent
        started = await manager.start_agent(agent_id)
        print(f"Started agent: {started}")
        
        # Stop agent
        stopped = await manager.stop_agent(agent_id)
        print(f"Stopped agent: {stopped}")
    
    asyncio.run(test_manager())