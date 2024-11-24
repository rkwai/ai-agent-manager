# src/core/agent_manager.py
from typing import Dict, Any, List
import uuid
import json
from datetime import datetime
import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain.memory import ConversationBufferMemory
from src.database.db_setup import Database
from .agent import Agent
import sqlite3
from langchain_core.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, database=None, db_path=":memory:"):
        """Initialize AgentManager with either a database instance or path"""
        self.db = database if database is not None else Database(db_path)
        self.active_agents = {}
        
    def _row_to_agent(self, row: sqlite3.Row) -> Agent:
        """Convert database row to Agent instance"""
        config = json.loads(row['config'])
        return Agent(
            id=row['agent_id'],
            name=row['name'],
            model_name=config['model_name'],
            tools=config['tools'],
            temperature=config['temperature'],
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
        
    async def create_agent(self, name: str, config: Dict[str, Any]) -> str:
        """Create a new agent with given configuration"""
        # Validate config has required fields
        required_fields = ['tools', 'model_name']
        if not all(field in config for field in required_fields):
            raise ValueError(f"Config missing required fields: {required_fields}")
        
        try:
            agent_id = str(uuid.uuid4())
            
            # Store in database
            with self.db.get_conn() as conn:
                conn.execute("""
                    INSERT INTO agents (agent_id, name, config, status)
                    VALUES (?, ?, ?, ?)
                """, (agent_id, name, json.dumps(config), 'inactive'))
                
                # Initialize agent state
                conn.execute("""
                    INSERT INTO agent_states (agent_id, memory)
                    VALUES (?, ?)
                """, (agent_id, json.dumps({})))
                
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    async def start_agent(self, agent_id: str) -> bool:
        """Start an agent and load it into memory"""
        try:
            with self.db.get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM agents WHERE agent_id = ?",
                    (agent_id,)
                ).fetchone()
                
                if not row:
                    raise ValueError(f"Agent {agent_id} not found")
                
                config = json.loads(row['config'])
                
                # Initialize tools
                tools = self._initialize_tools(config['tools'])
                
                # Create prompt template
                prompt = self._create_prompt_template()
                
                # Initialize LangChain components
                llm = ChatOpenAI(
                    temperature=config.get('temperature', 0),
                    model=config['model_name']
                )
                
                # Create the agent
                agent_executor = create_react_agent(
                    llm=llm,
                    tools=tools,
                    prompt=prompt
                )
                
                # Store in memory
                self.active_agents[agent_id] = agent_executor
                
                # Update status
                conn.execute(
                    "UPDATE agents SET status = ? WHERE agent_id = ?",
                    ("active", agent_id)
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {e}")
            return False

    def _initialize_tools(self, tool_configs: List[Dict[str, Any]]) -> List[Any]:
        """Initialize agent tools based on configuration"""
        from langchain.tools import Tool
        
        tools = []
        for tool_config in tool_configs:
            if tool_config["type"] == "code_interpreter":
                tools.append(
                    Tool(
                        name="code_interpreter",
                        func=lambda x: "Code execution not implemented",
                        description="Execute code snippets"
                    )
                )
        return tools

    def _create_prompt_template(self) -> PromptTemplate:
        """Create the agent prompt template"""
        template = """You are a helpful AI assistant.

Available tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}"""

        return PromptTemplate.from_template(template)

    async def run_task(self, agent_id: str, task: dict) -> dict:
        if "input" not in task:
            raise ValueError("Task must contain 'input' field")
        """Execute a task with specified agent"""
        try:
            # Get agent instance
            agent = self.active_agents.get(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not active")
            
            # Execute task
            result = await agent.ainvoke(task)
            
            # Store run in database
            run_id = str(uuid.uuid4())
            with self.db.get_conn() as conn:
                conn.execute("""
                    INSERT INTO agent_runs (run_id, agent_id, task, status, result, started_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (run_id, agent_id, json.dumps(task), "completed", 
                      json.dumps(result), datetime.now()))
            
            return {
                "run_id": run_id,
                "result": "Task completed",
                "output": result
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
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

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents"""
        try:
            with self.db.get_conn() as conn:
                rows = conn.execute(
                    "SELECT agent_id, name, status, config FROM agents"
                ).fetchall()
                
                return [
                    {
                        "id": row["agent_id"],
                        "name": row["name"],
                        "status": row["status"]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise