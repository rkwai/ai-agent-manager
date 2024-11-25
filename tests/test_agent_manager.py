import pytest
from unittest.mock import ANY
import uuid
import json
from datetime import datetime
from src.core.agent import Agent

@pytest.fixture
def agent_manager(mock_db):
    """Create an AgentManager instance with mocked database"""
    from src.core.agent_manager import AgentManager
    manager = AgentManager(database=mock_db)
    # Register the default Agent class
    Agent.AGENT_TYPE = "default"  # Add type identifier to base Agent class
    manager.register_agent_class(Agent)
    return manager

@pytest.mark.asyncio
async def test_create_agent(agent_manager, mock_db):
    """Test agent creation through manager"""
    agent_config = {
        "model_name": "gpt-4-turbo-preview",
        "tools": [{"type": "code_interpreter"}],
        "temperature": 0.7
    }
    
    # Setup mock to return success
    mock_cursor = mock_db.get_conn.return_value.__enter__.return_value
    mock_cursor.execute.return_value.lastrowid = 1
    
    agent_id = await agent_manager.create_agent(
        name="test_agent",
        agent_type="default",
        config=agent_config
    )
    
    # Add this to debug the actual calls
    print("Database calls:", [
        call.args for call in mock_cursor.execute.call_args_list
    ])
    
    assert agent_id is not None
    assert isinstance(agent_id, str)
    assert uuid.UUID(agent_id)  # Verify it's a valid UUID
    
    # Verify database calls
    mock_db.get_conn.assert_called()
    assert mock_cursor.execute.call_count >= 2  # Two inserts expected

@pytest.mark.asyncio
async def test_agent_lifecycle(agent_manager, mock_db, mocker):
    """Test agent lifecycle operations"""
    config = {
        "model_name": "gpt-4-turbo-preview",
        "tools": [{"type": "code_interpreter"}],
        "temperature": 0.7,
        "system_message": "You are a helpful assistant"
    }
    
    # Setup mock database responses
    mock_cursor = mock_db.get_conn.return_value.__enter__.return_value
    mock_cursor.execute.return_value.fetchone.return_value = {
        "agent_id": "test-id",
        "name": "test-agent",
        "status": "inactive",
        "type": "default",
        "config": json.dumps(config),
        "created_at": datetime.now().isoformat()
    }
    
    agent_id = await agent_manager.create_agent(
        name="test_agent",
        agent_type="default",
        config=config
    )
    
    # Get agent
    agent = await agent_manager.get_agent(agent_id)
    assert agent.id == "test-id"
    assert agent.name == "test-agent"
    assert agent.status == "inactive"
    assert agent.model_name == config["model_name"]
    assert agent.temperature == config["temperature"]

@pytest.mark.asyncio
async def test_run_task(agent_manager, mock_db, mocker):
    """Test task execution"""
    config = {
        "model_name": "gpt-4-turbo-preview",
        "tools": [{"type": "code_interpreter"}],
        "temperature": 0.7
    }
    
    # Setup mock to return agent data
    mock_cursor = mock_db.get_conn.return_value.__enter__.return_value
    mock_cursor.execute.return_value.fetchone.return_value = {
        "agent_id": "test-id",
        "name": "test-agent",
        "status": "inactive",
        "type": "default",
        "config": json.dumps(config),
        "created_at": datetime.now().isoformat()
    }
    
    agent_id = await agent_manager.create_agent(
        name="test_agent",
        agent_type="default",
        config=config
    )
    
    # Mock the execute_task method
    mock_execute = mocker.AsyncMock(return_value={"output": "Task completed successfully"})
    mocker.patch.object(Agent, "execute_task", mock_execute)
    
    # Run task
    result = await agent_manager.run_task(agent_id, {
        "task": "test_task",
        "params": {"key": "value"}
    })
    
    assert result == {"output": "Task completed successfully"}
    mock_execute.assert_called_once()
    
    # Test with invalid agent ID
    mock_cursor.execute.return_value.fetchone.return_value = None
    with pytest.raises(ValueError, match="Agent invalid-id not found"):
        await agent_manager.run_task("invalid-id", {"task": "test"})

@pytest.mark.asyncio
async def test_register_agent_class(agent_manager, mock_db):
    """Test agent class registration"""
    class TestAgent:
        AGENT_TYPE = "test_type"
    
    # Register the test agent class
    agent_manager.register_agent_class(TestAgent)
    assert agent_manager._agent_classes["test_type"] == TestAgent
    
    # Test registering class without AGENT_TYPE
    class InvalidAgent:
        pass
    
    agent_manager.register_agent_class(InvalidAgent)
    assert "InvalidAgent" not in agent_manager._agent_classes
