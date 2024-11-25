# src/api/routes.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging

from src.core.agent_manager import AgentManager
from src.database.db_setup import Database
from src.agents.storyteller import StorytellerAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize database and agent manager
db = Database("agents.db")
agent_manager = AgentManager(database=db)

# Register available agent types
agent_manager.register_agent_class(StorytellerAgent)

@router.post("/agents")
async def create_agent(agent_data: Dict[str, Any]):
    """Create a new agent"""
    try:
        agent_id = await agent_manager.create_agent(
            name=agent_data["name"],
            agent_type=agent_data["type"],
            config=agent_data.get("config", {})
        )
        return {"agent_id": agent_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/agents/{agent_id}/tasks")
async def execute_task(agent_id: str, task: Dict[str, Any]):
    """Execute a task with specified agent"""
    try:
        result = await agent_manager.run_task(agent_id, task)
        return {
            "status": "completed",
            "agent_id": agent_id,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, config_updates: Dict[str, Any]):
    """Update an agent's configuration"""
    try:
        agent = await agent_manager.get_agent(agent_id)
        agent.config_manager.update_config(config_updates)
        return {"status": "updated", "agent_id": agent_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))