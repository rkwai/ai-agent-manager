import pytest
from unittest.mock import ANY
import uuid
import json

@pytest.mark.asyncio
async def test_create_agent(agent_manager, mock_db):
    """Test agent creation through manager"""
    agent_config = {
        "name": "test_agent",
        "model_name": "gpt-4-turbo-preview",
        "tools": [{"type": "code_interpreter"}],
        "temperature": 0.7
    }
    
    # Setup mock to return success
    mock_cursor = mock_db.get_conn.return_value.__enter__.return_value
    mock_cursor.execute.return_value.lastrowid = 1
    
    agent_id = await agent_manager.create_agent(agent_config["name"], agent_config)
    
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
    # Mock LangChain components
    mocker.patch('langchain_openai.ChatOpenAI')
    mocker.patch('langchain.agents.create_react_agent', return_value=mocker.Mock())
    
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
        "config": json.dumps(config)
    }
    
    agent_id = await agent_manager.create_agent("test_agent", config)
    
    # Test start
    started = await agent_manager.start_agent(agent_id)
    assert started is True
    assert agent_id in agent_manager.active_agents
    
    # Test stop
    stopped = await agent_manager.stop_agent(agent_id)
    assert stopped is True
    assert agent_id not in agent_manager.active_agents
    
    # Add assertions for state changes
    mock_cursor.execute.assert_any_call(
        "UPDATE agents SET status = ? WHERE agent_id = ?",
        ("active", agent_id)
    )

@pytest.mark.asyncio
async def test_run_task(agent_manager, mock_db, mocker):
    """Test task execution"""
    # Mock OpenAI and LangChain components
    mocker.patch('langchain_openai.ChatOpenAI')
    mocker.patch('langchain.agents.create_react_agent', return_value=mocker.Mock())
    
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
        "config": json.dumps(config)
    }
    
    agent_id = await agent_manager.create_agent("test_agent", config)
    
    # Start agent
    await agent_manager.start_agent(agent_id)
    
    # Mock the agent's ainvoke method to return a coroutine
    mock_agent = mocker.Mock()
    mock_agent.ainvoke = mocker.AsyncMock(return_value={"output": "Task completed successfully"})
    agent_manager.active_agents[agent_id] = mock_agent
    
    # Run task
    result = await agent_manager.run_task(agent_id, {
        "input": "test",
        "intermediate_steps": []
    })
    
    assert result["result"] == "Task completed"
    assert "run_id" in result
    
    # Add error case testing
    with pytest.raises(ValueError):
        await agent_manager.run_task("invalid-id", {"input": "test"})
    
    # Test with invalid input
    with pytest.raises(ValueError):
        await agent_manager.run_task(agent_id, {})

@pytest.mark.asyncio
async def test_delete_agent(agent_manager, mock_db, mocker):
    """Test agent deletion"""
    # Mock LangChain components
    mocker.patch('langchain_openai.ChatOpenAI')
    mocker.patch('langchain.agents.create_react_agent', return_value=mocker.Mock())
    
    config = {
        "model_name": "gpt-4-turbo-preview",
        "tools": [{"type": "code_interpreter"}],
        "temperature": 0.7
    }
    
    # Setup mock database responses
    mock_cursor = mock_db.get_conn.return_value.__enter__.return_value
    mock_cursor.execute.return_value.fetchone.return_value = {
        "agent_id": "test-id",
        "name": "test-agent",
        "status": "inactive",
        "config": json.dumps(config)
    }
    
    agent_id = await agent_manager.create_agent("test_agent", config)
    
    # Start the agent first
    started = await agent_manager.start_agent(agent_id)
    assert started is True
    assert agent_id in agent_manager.active_agents
    
    # Reset mock to track delete operations
    mock_cursor.execute.reset_mock()
    
    # Now delete it
    deleted = await agent_manager.delete_agent(agent_id)
    assert deleted is True
    assert agent_id not in agent_manager.active_agents
    
    # Verify database calls in order
    delete_calls = mock_cursor.execute.call_args_list
    assert len(delete_calls) == 5  # Should be exactly 5 operations (1 select + 1 stop + 3 deletes)
    
    # First SELECT to verify agent exists
    assert delete_calls[0].args[0] == "SELECT * FROM agents WHERE agent_id = ?"
    assert delete_calls[0].args[1] == (agent_id,)
    
    # Then update status to inactive (from stop_agent)
    assert delete_calls[1].args[0] == "UPDATE agents SET status = 'inactive' WHERE agent_id = ?"
    assert delete_calls[1].args[1] == (agent_id,)
    
    # Then delete from agent_states
    assert delete_calls[2].args[0] == "DELETE FROM agent_states WHERE agent_id = ?"
    assert delete_calls[2].args[1] == (agent_id,)
    
    # Then delete from agent_runs
    assert delete_calls[3].args[0] == "DELETE FROM agent_runs WHERE agent_id = ?"
    assert delete_calls[3].args[1] == (agent_id,)
    
    # Finally delete from agents
    assert delete_calls[4].args[0] == "DELETE FROM agents WHERE agent_id = ?"
    assert delete_calls[4].args[1] == (agent_id,)
    
    # Test deleting non-existent agent
    # Mock database to return None for non-existent agent
    mock_cursor.execute.return_value.fetchone.return_value = None
    with pytest.raises(ValueError, match="Agent non-existent-id not found"):
        await agent_manager.delete_agent("non-existent-id")
