from abc import ABC, abstractmethod
import json
import logging
from typing import Dict, Any

class BaseAgent(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources and connections"""
        pass
        
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming data and return results"""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources before shutdown"""
        pass
        
    async def handle_error(self, error: Exception) -> None:
        """Handle errors during processing"""
        self.logger.error(f"Error in {self.__class__.__name__}: {str(error)}")
        
    def load_config(self) -> Dict[str, Any]:
        """Load agent-specific configuration"""
        with open("config/config.json", "r") as f:
            config = json.load(f)
        return config["agents"][self.__class__.__name__.lower()]