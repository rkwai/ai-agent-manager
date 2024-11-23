# src/core/agent_manager.py
from typing import Dict, Any, Optional, List, cast
import uuid
from datetime import datetime
import logging
import openai
from dataclasses import dataclass
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from src.database.db_setup import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Agent:
    name: str
    model: str
    temperature: float
    created_at: datetime = None
    id: Optional[int] = None

class AgentManager:
    def __init__(self, db_path: str = "agents.db"):
        self.db = Database(db_path)
        self.active_agents = {}  # In-memory cache of active agents
        
    def _dict_to_agent(self, agent_dict: Dict[str, Any]) -> Agent:
        """Convert a dictionary to an Agent object"""
        return Agent(
            id=agent_dict.get('id'),
            name=agent_dict['name'],
            model=agent_dict['model'],
            temperature=agent_dict['temperature'],
            created_at=agent_dict.get('created_at')
        )
        
    async def create_agent(self, config: Dict[str, Any]) -> Agent:
        """Create a new agent with given configuration"""
        try:
            # Validate required fields
            if not all(k in config for k in ['name', 'model', 'temperature']):
                raise ValueError("Missing required fields in configuration")

            agent_data = {
                "name": config["name"],
                "model": config["model"],
                "temperature": config["temperature"],
                "created_at": datetime.now()
            }
            
            # Store in database
            agent_id = self.db.create_agent(agent_data)
            agent_data['id'] = agent_id
            
            # Return the created agent data as an Agent object
            return self._dict_to_agent(agent_data)
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    async def get_agent(self, name: str) -> Agent:
        """Get agent by name"""
        try:
            agent_dict = self.db.get_agent_by_name(name)
            return self._dict_to_agent(agent_dict)
        except Exception as e:
            logger.error(f"Failed to get agent: {e}")
            raise KeyError(f"Agent {name} not found")

    async def list_agents(self) -> List[Agent]:
        """List all agents"""
        try:
            agents = self.db.list_agents()
            return [self._dict_to_agent(agent) for agent in agents]
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    async def update_agent_config(self, name: str, config: Dict[str, Any]) -> Agent:
        """Update agent configuration"""
        try:
            agent = self.db.get_agent_by_name(name)
            self.db.update_agent(agent["id"], config)
            updated_agent = self.db.get_agent_by_name(name)
            return self._dict_to_agent(updated_agent)
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            raise

    async def delete_agent(self, name: str) -> None:
        """Delete an agent by name"""
        try:
            agent = self.db.get_agent_by_name(name)
            self.db.delete_agent(agent["id"])
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            raise KeyError(f"Agent {name} not found")

    async def send_message(self, agent_name: str, message: str) -> str:
        """Send a message to an agent"""
        try:
            agent = await self.get_agent(agent_name)
            
            response = openai.ChatCompletion.create(
                model=agent.model,
                messages=[{"role": "user", "content": message}],
                temperature=agent.temperature
            )
            
            return response.choices[0].message["content"]
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise