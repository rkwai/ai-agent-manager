# src/api/routes.py
from fastapi import APIRouter, HTTPException, WebSocket
from typing import Dict, Any, List
import logging
import asyncio
from datetime import datetime

from src.core.agent_manager import AgentManager
from src.database.db_setup import Database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instead of app
router = APIRouter()

# Initialize database and agent manager
db = Database("agents.db")
agent_manager = AgentManager(database=db)

@router.get("/agents")
async def list_agents():
    """List all agents"""
    try:
        agents = await agent_manager.list_agents()
        return agents
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents")
async def create_agent(agent_data: Dict[str, Any]):
    """Create a new agent"""
    try:
        agent_id = await agent_manager.create_agent(
            name=agent_data["name"],
            config={
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.7,
                "tools": []
            }
        )
        return {"agent_id": agent_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
    try:
        agent = await agent_manager.get_agent(agent_id)
        return agent
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an existing agent"""
    try:
        success = await agent_manager.start_agent(agent_id)
        if success:
            return {"status": "started", "agent_id": agent_id}
        raise HTTPException(status_code=500, detail="Failed to start agent")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/tasks")
async def execute_task(agent_id: str, task: Dict[str, Any]):
    """Execute a task with specified agent"""
    try:
        result = await agent_manager.run_task(agent_id, task)
        return {
            "status": "completed",
            "agent_id": agent_id,
            "run_id": result["run_id"],
            "result": result["result"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop a running agent"""
    try:
        success = await agent_manager.stop_agent(agent_id)
        if success:
            return {"status": "stopped", "agent_id": agent_id}
        raise HTTPException(status_code=500, detail="Failed to stop agent")
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get current status of an agent"""
    try:
        state = await agent_manager.get_agent_state(agent_id)
        if state:
            return {
                "agent_id": agent_id,
                "state": state,
                "last_updated": datetime.utcnow().isoformat()
            }
        raise HTTPException(status_code=404, detail="Agent not found")
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/agents/{agent_id}/ws")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    try:
        while True:
            state = await agent_manager.get_agent_state(agent_id)
            if state:
                await websocket.send_json({
                    "agent_id": agent_id,
                    "state": state,
                    "timestamp": datetime.utcnow().isoformat()
                })
            await asyncio.sleep(1)  # Update every second
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, config: Dict[str, Any]):
    """Update agent configuration"""
    try:
        await agent_manager.update_agent(agent_id, config)
        return {"status": "updated", "agent_id": agent_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        await agent_manager.delete_agent(agent_id)
        return {"status": "deleted", "agent_id": agent_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/output")
async def get_agent_output(agent_id: str):
    """Get agent output"""
    try:
        output = await agent_manager.get_agent_output(agent_id)
        return {"output": output if output else []}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get agent output: {e}")
        raise HTTPException(status_code=500, detail=str(e))