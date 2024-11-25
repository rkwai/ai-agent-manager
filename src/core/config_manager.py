import json
import logging
from typing import Dict, Any
from sqlite3 import Connection

class ConfigManager:
    """Manages agent configurations stored in the database"""

    def __init__(self, agent_id: str, db_conn: Connection, agent_type: str):
        self.agent_id = agent_id
        self.db_conn = db_conn
        self.agent_type = agent_type
        self._config = None

    def get_config(self) -> Dict[str, Any]:
        """Get the configuration for this agent"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from database, falling back to defaults if not found"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT config FROM agents WHERE agent_id = ?", (self.agent_id,))
            result = cursor.fetchone()
            
            if result and result['config']:
                return json.loads(result['config'])
            return {}
            
        except Exception as e:
            logging.warning(f"Failed to load config from database: {e}. Using empty config.")
            return {}

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save agent configuration to database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "UPDATE agents SET config = ? WHERE agent_id = ?",
                (json.dumps(config), self.agent_id)
            )
            self.db_conn.commit()
        except Exception as e:
            logging.error(f"Failed to save config to database: {e}")

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        current_config = self.get_config()
        new_config = {**current_config, **updates}
        self._save_config(new_config)
        self._config = new_config  # Update cache