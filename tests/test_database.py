import pytest
from datetime import datetime
from src.database.db_setup import Database

@pytest.fixture
def database():
    # Use an in-memory database for testing
    db = Database(":memory:")
    return db

def test_create_agent(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    agent_id = database.create_agent(agent_data)
    assert agent_id is not None

def test_get_agent(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    agent_id = database.create_agent(agent_data)
    agent = database.get_agent(agent_id)
    
    assert agent["name"] == agent_data["name"]
    assert agent["model"] == agent_data["model"]
    assert agent["temperature"] == agent_data["temperature"]

def test_get_agent_by_name(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    database.create_agent(agent_data)
    agent = database.get_agent_by_name("test_agent")
    
    assert agent["name"] == agent_data["name"]
    assert agent["model"] == agent_data["model"]
    assert agent["temperature"] == agent_data["temperature"]

def test_update_agent(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    agent_id = database.create_agent(agent_data)
    
    updated_data = {
        "model": "gpt-4",
        "temperature": 0.9
    }
    
    database.update_agent(agent_id, updated_data)
    updated_agent = database.get_agent(agent_id)
    
    assert updated_agent["model"] == updated_data["model"]
    assert updated_agent["temperature"] == updated_data["temperature"]
    assert updated_agent["name"] == agent_data["name"]

def test_delete_agent(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    agent_id = database.create_agent(agent_data)
    database.delete_agent(agent_id)
    
    with pytest.raises(ValueError):
        database.get_agent(agent_id)

def test_list_agents(database):
    agents_data = [
        {
            "name": "agent1",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "created_at": datetime.now()
        },
        {
            "name": "agent2",
            "model": "gpt-4",
            "temperature": 0.5,
            "created_at": datetime.now()
        }
    ]
    
    for agent_data in agents_data:
        database.create_agent(agent_data)
    
    agents = database.list_agents()
    assert len(agents) == 2

def test_save_conversation(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    agent_id = database.create_agent(agent_data)
    
    conversation_data = {
        "agent_id": agent_id,
        "user_message": "Hello",
        "agent_response": "Hi there!",
        "timestamp": datetime.now()
    }
    
    conversation_id = database.save_conversation(conversation_data)
    assert conversation_id is not None

def test_get_agent_conversations(database):
    agent_data = {
        "name": "test_agent",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "created_at": datetime.now()
    }
    
    agent_id = database.create_agent(agent_data)
    
    conversations_data = [
        {
            "agent_id": agent_id,
            "user_message": "Hello",
            "agent_response": "Hi there!",
            "timestamp": datetime.now()
        },
        {
            "agent_id": agent_id,
            "user_message": "How are you?",
            "agent_response": "I'm doing well!",
            "timestamp": datetime.now()
        }
    ]
    
    for conversation in conversations_data:
        database.save_conversation(conversation)
    
    conversations = database.get_agent_conversations(agent_id)
    assert len(conversations) == 2
