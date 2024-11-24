import pytest
from datetime import datetime
from src.core.agent import Agent

def test_agent_creation():
    """Test basic agent creation"""
    agent = Agent(
        id="test-id",
        name="test-agent",
        model_name="gpt-3.5-turbo",
        tools=[],
        temperature=0.7
    )
    
    assert agent.id == "test-id"
    assert agent.name == "test-agent"
    assert agent.model_name == "gpt-3.5-turbo"
    assert agent.tools == []
    assert agent.temperature == 0.7
    assert agent.status == "inactive"
    assert agent.created_at is None

def test_agent_from_dict():
    """Test creating agent from dictionary"""
    now = datetime.now()
    data = {
        "agent_id": "test-id",
        "name": "test-agent",
        "model_name": "gpt-3.5-turbo",
        "tools": ["tool1", "tool2"],
        "temperature": 0.5,
        "status": "active",
        "created_at": now
    }
    
    agent = Agent.from_dict(data)
    
    assert agent.id == "test-id"
    assert agent.name == "test-agent"
    assert agent.model_name == "gpt-3.5-turbo"
    assert agent.tools == ["tool1", "tool2"]
    assert agent.temperature == 0.5
    assert agent.status == "active"
    assert agent.created_at == now

def test_agent_to_dict():
    """Test converting agent to dictionary"""
    now = datetime.now()
    agent = Agent(
        id="test-id",
        name="test-agent",
        model_name="gpt-3.5-turbo",
        tools=["tool1"],
        temperature=0.7,
        status="active",
        created_at=now
    )
    
    data = agent.to_dict()
    
    assert data["agent_id"] == "test-id"
    assert data["name"] == "test-agent"
    assert data["model_name"] == "gpt-3.5-turbo"
    assert data["tools"] == ["tool1"]
    assert data["temperature"] == 0.7
    assert data["status"] == "active"
    assert data["created_at"] == now

def test_agent_config():
    """Test getting agent configuration"""
    agent = Agent(
        id="test-id",
        name="test-agent",
        model_name="gpt-3.5-turbo",
        tools=["tool1", "tool2"],
        temperature=0.7
    )
    
    config = agent.config
    
    assert config == {
        "model_name": "gpt-3.5-turbo",
        "tools": ["tool1", "tool2"],
        "temperature": 0.7
    }

def test_agent_from_dict_defaults():
    """Test agent creation with minimal dictionary"""
    data = {
        "agent_id": "test-id",
        "name": "test-agent"
    }
    
    agent = Agent.from_dict(data)
    
    assert agent.id == "test-id"
    assert agent.name == "test-agent"
    assert agent.model_name == "gpt-3.5-turbo"
    assert agent.tools == []
    assert agent.temperature == 0.7
    assert agent.status == "inactive"
    assert agent.created_at is None

def test_agent_invalid_temperature():
    """Test agent creation with invalid temperature"""
    with pytest.raises(ValueError):
        Agent(
            id="test-id",
            name="test-agent",
            model_name="gpt-3.5-turbo",
            tools=[],
            temperature=2.0  # Invalid temperature > 1.0
        ) 