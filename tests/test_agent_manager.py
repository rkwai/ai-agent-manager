import pytest
from src.core.agent_manager import AgentManager
from unittest.mock import Mock, patch

@pytest.fixture
def agent_manager():
    # Use in-memory database for testing
    return AgentManager(db_path=":memory:")

@pytest.mark.asyncio
async def test_create_agent(agent_manager):
    # Test creating a new agent
    agent_config = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
    
    agent = await agent_manager.create_agent(config=agent_config)
    
    assert agent is not None
    assert agent.name == "test_agent"
    assert agent.model == "gpt-3.5-turbo"
    assert agent.temperature == 0.7

@pytest.mark.asyncio
async def test_create_agent_invalid_config(agent_manager):
    # Test creating an agent with invalid configuration
    invalid_config = {
        "name": "test_agent"
        # Missing required fields
    }
    
    with pytest.raises(ValueError):
        await agent_manager.create_agent(invalid_config)

@pytest.mark.asyncio
async def test_get_agent(agent_manager):
    # Test retrieving an agent
    agent_config = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
    
    created_agent = await agent_manager.create_agent(agent_config)
    retrieved_agent = await agent_manager.get_agent("test_agent")
    
    assert retrieved_agent is not None
    assert retrieved_agent.name == created_agent.name
    assert retrieved_agent.model == created_agent.model

@pytest.mark.asyncio
async def test_get_nonexistent_agent(agent_manager):
    # Test retrieving a non-existent agent
    with pytest.raises(KeyError):
        await agent_manager.get_agent("nonexistent_agent")

@pytest.mark.asyncio
async def test_list_agents(agent_manager):
    # Test listing all agents
    agent_configs = [
        {
            "name": "agent1",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        },
        {
            "name": "agent2",
            "model": "gpt-4",
            "temperature": 0.5
        }
    ]
    
    for config in agent_configs:
        await agent_manager.create_agent(config)
    
    agents = await agent_manager.list_agents()
    
    assert len(agents) == 2
    assert any(agent.name == "agent1" for agent in agents)
    assert any(agent.name == "agent2" for agent in agents)

@pytest.mark.asyncio
async def test_delete_agent(agent_manager):
    # Test deleting an agent
    agent_config = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
    
    await agent_manager.create_agent(agent_config)
    await agent_manager.delete_agent("test_agent")
    
    with pytest.raises(KeyError):
        await agent_manager.get_agent("test_agent")

@pytest.mark.asyncio
async def test_delete_nonexistent_agent(agent_manager):
    # Test deleting a non-existent agent
    with pytest.raises(KeyError):
        await agent_manager.delete_agent("nonexistent_agent")

@pytest.mark.asyncio
async def test_agent_conversation(agent_manager):
    # Test agent conversation with mocked OpenAI response
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_create.return_value.choices = [
            type('obj', (object,), {'message': {'content': 'Test response'}})()
        ]
        
        agent_config = {
            "name": "test_agent",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
        
        await agent_manager.create_agent(agent_config)
        response = await agent_manager.send_message("test_agent", "Hello")
        
        assert response == "Test response"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_update_agent_config(agent_manager):
    # Test updating agent configuration
    initial_config = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
    
    agent = await agent_manager.create_agent(initial_config)
    
    updated_config = {
        "model": "gpt-4",
        "temperature": 0.9
    }
    
    await agent_manager.update_agent_config("test_agent", updated_config)
    updated_agent = await agent_manager.get_agent("test_agent")
    
    assert updated_agent.model == "gpt-4"
    assert updated_agent.temperature == 0.9
    assert updated_agent.name == "test_agent"
