from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from sqlite3 import Connection

@dataclass
class Agent:
    """Represents an AI agent with its configuration and state"""
    id: str
    name: str
    model_name: str
    tools: list
    temperature: float
    status: str = 'inactive'
    type: str = 'default'
    created_at: Optional[datetime] = None
    db_conn: Optional[Connection] = None
    
    def __post_init__(self):
        """Validate agent attributes after initialization"""
        if not 0 <= self.temperature <= 1:
            raise ValueError(f"Temperature must be between 0 and 1, got {self.temperature}")
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
        if self.name.strip() == "":
            raise ValueError("Agent name cannot be empty")
        # Convert temperature to float if it's a string
        if isinstance(self.temperature, str):
            self.temperature = float(self.temperature)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create an Agent instance from a dictionary"""
        # Extract db_conn from data if present
        db_conn = data.pop('db_conn', None)
        agent = cls(
            id=data['agent_id'],
            name=data['name'],
            type=data.get('type', 'default'),
            model_name=data.get('model_name', 'gpt-3.5-turbo'),
            tools=data.get('tools', []),
            temperature=float(data.get('temperature', 0.7)),
            status=data.get('status', 'inactive'),
            created_at=data.get('created_at'),
            db_conn=db_conn
        )
        # Put db_conn back in data if it was present
        if db_conn is not None:
            data['db_conn'] = db_conn
        return agent
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Agent instance to dictionary"""
        # Exclude db_conn from serialization as it's not JSON-serializable
        return {
            "agent_id": self.id,
            "name": self.name,
            "type": self.type,
            "model_name": self.model_name,
            "tools": self.tools,
            "temperature": self.temperature,
            "status": self.status,
            "created_at": self.created_at,
            "config": {
                "model_name": self.model_name,
                "tools": self.tools,
                "temperature": self.temperature
            }
        }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with this agent
        
        Args:
            task: Dictionary containing task details
            
        Returns:
            Dictionary containing task results
            
        This is a base implementation that should be overridden by specific agent types.
        """
        raise NotImplementedError("Agent subclasses must implement execute_task")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return {
            "model_name": self.model_name,
            "tools": self.tools,
            "temperature": self.temperature
        } 