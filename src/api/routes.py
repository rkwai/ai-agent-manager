# src/api/routes.py
from fastapi import FastAPI, HTTPException, WebSocket
from typing import Dict, Any, List
import logging
import asyncio
from datetime import datetime
import os

# Import our core components
from src.core.agent_manager import AgentManager
from src.config.settings import API_HOST, API_PORT
from src.database.db_setup import initialize_database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(title="AI Agent Management System")
agent_manager = None

def initialize_app(db_path: str):
    """Initialize the application with database connection"""
    global agent_manager
    
    # Add debug logging
    logger.info(f"Attempting to initialize database at: {db_path}")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    db = initialize_database(db_path)
    agent_manager = AgentManager(database=db)

@app.post("/agents/", response_model=Dict[str, str])
async def create_agent(name: str, config: Dict[str, Any]):
    """Create a new agent with given configuration"""
    try:
        agent_id = await agent_manager.create_agent(name, config)
        return {"agent_id": agent_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/{agent_id}/start")
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

@app.post("/agents/{agent_id}/tasks")
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

@app.post("/agents/{agent_id}/stop")
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

@app.get("/agents/{agent_id}/status")
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

@app.websocket("/agents/{agent_id}/ws")
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