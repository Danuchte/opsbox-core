import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, agent_id: str, config_path: str):
        self.agent_id = agent_id
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.state: Dict[str, Any] = {}
        self.last_update = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load agent configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup agent-specific logging."""
        logger = logging.getLogger(f"agent.{self.agent_id}")
        logger.setLevel(logging.INFO)
        return logger
    
    def update_state(self, new_state: Dict[str, Any]):
        """Update agent's internal state."""
        self.state.update(new_state)
        self.last_update = datetime.utcnow()
        self.logger.debug(f"State updated: {new_state}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "last_update": self.last_update,
            "status": "active" if self.is_active() else "inactive"
        }
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize agent resources and connections."""
        pass
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming data and return results."""
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if agent is currently active and healthy."""
        pass
    
    def shutdown(self):
        """Clean shutdown of agent resources."""
        self.logger.info(f"Agent {self.agent_id} shutting down")
        self.state.clear()