from typing import Optional, Dict, Any
from dataclasses import dataclass
import openai
import uuid

from src.core.agent import Agent
from src.core.config_manager import ConfigManager

@dataclass
class StorytellerConfig:
    """Configuration for the storyteller agent"""
    target_age_range: Dict[str, int]
    story_length: int
    system_prompt: str
    story_prompt_template: str
    theme_prompt_template: str

    def format_theme(self, theme: Optional[str]) -> str:
        """Format the theme prompt"""
        return self.theme_prompt_template.format(theme=theme) if theme else ""

    def format_story_prompt(self, theme_prompt: str) -> str:
        """Format the main story prompt"""
        return self.story_prompt_template.format(
            word_count=self.story_length,
            min_age=self.target_age_range['min'],
            max_age=self.target_age_range['max'],
            theme_prompt=theme_prompt
        )

class StorytellerAgent(Agent):
    """An AI agent specialized in generating children's stories"""
    
    AGENT_TYPE = "storyteller"  # Class-level agent type identifier
    
    DEFAULT_CONFIG = {
        'target_age_range': {
            'min': 5,
            'max': 10
        },
        'story_length': 500,
        'system_prompt': (
            "You are a skilled children's book author who writes engaging, "
            "imaginative stories with positive messages."
        ),
        'story_prompt_template': (
            "Write a children's story that is engaging, age-appropriate, and has a good moral lesson. "
            "The story should be around {word_count} words long and suitable for children "
            "aged {min_age}-{max_age}. {theme_prompt}"
        ),
        'theme_prompt_template': "The story should be about or involve: {theme}."
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager(
            agent_id=self.id,
            db_conn=self.db_conn,
            agent_type=self.AGENT_TYPE
        )
        self._ensure_default_config()
    
    def _ensure_default_config(self) -> None:
        """Ensure default configuration exists in database"""
        config = self.config_manager.get_config()
        if not config:
            self.config_manager.update_config(self.DEFAULT_CONFIG)
    
    def get_config(self) -> StorytellerConfig:
        """Get the typed configuration for this agent"""
        config_dict = self.config_manager.get_config()
        # Merge with defaults to ensure all required fields exist
        config_dict = {**self.DEFAULT_CONFIG, **config_dict}
        return StorytellerConfig(**config_dict)
    
    async def generate_story(self, theme: Optional[str] = None) -> str:
        """Generate a children's story
        
        Args:
            theme: Optional theme or topic for the story
            
        Returns:
            The generated story as a string
        """
        config = self.get_config()
        
        # Format theme prompt if theme is provided
        theme_prompt = config.format_theme(theme) if theme else ""
        
        # Format main prompt using configuration
        prompt = config.format_story_prompt(theme_prompt)
            
        try:
            response = await openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{
                    "role": "system",
                    "content": config.system_prompt
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Failed to generate story: {str(e)}")
            
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task specific to the storyteller agent
        
        Args:
            task: Dictionary containing task details
            
        Returns:
            Dictionary containing task results
        """
        task_type = task.get("task")
        
        if task_type == "generate_story":
            story = await self.generate_story(task.get("params", {}).get("theme"))
            return {
                "run_id": str(uuid.uuid4()),
                "result": story
            }
            
        # For unknown task types, fall back to parent class implementation
        return await super().execute_task(task)