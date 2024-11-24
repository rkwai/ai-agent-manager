from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Agent:
    """Represents an AI agent with its configuration and state"""
    id: str
    name: str
    model_name: str
    tools: list
    temperature: float
    status: str = 'inactive'
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate agent attributes after initialization"""
        if not 0 <= self.temperature <= 1:
            raise ValueError(f"Temperature must be between 0 and 1, got {self.temperature}")
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
        if self.name.strip() == "":
            raise ValueError("Agent name cannot be empty")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create an Agent instance from a dictionary"""
        return cls(
            id=data['agent_id'],
            name=data['name'],
            model_name=data.get('model_name', 'gpt-3.5-turbo'),
            tools=data.get('tools', []),
            temperature=data.get('temperature', 0.7),
            status=data.get('status', 'inactive'),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Agent instance to dictionary"""
        return {
            "agent_id": self.id,
            "name": self.name,
            "model_name": self.model_name,
            "tools": self.tools,
            "temperature": self.temperature,
            "status": self.status,
            "created_at": self.created_at
        }
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return {
            "model_name": self.model_name,
            "tools": self.tools,
            "temperature": self.temperature
        } 