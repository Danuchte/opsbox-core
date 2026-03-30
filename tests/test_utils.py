import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

def create_test_config(agent_name: str) -> str:
    """Create a temporary test configuration file."""
    config = {
        "name": f"{agent_name}_agent",
        "description": f"Test configuration for {agent_name}",
        "version": "1.0.0",
        "capabilities": ["test"],
        "dependencies": []
    }
    
    config_path = f"/tmp/test_{agent_name}_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    return config_path

def cleanup_test_config(config_path: str):
    """Remove temporary test configuration file."""
    if os.path.exists(config_path):
        os.remove(config_path)

def create_test_job() -> Dict[str, Any]:
    """Create a test job request."""
    now = datetime.utcnow()
    return {
        "job_id": f"test_job_{now.timestamp()}",
        "pickup": "Test Pickup Location",
        "delivery": "Test Delivery Location",
        "pickup_time": now.isoformat(),
        "delivery_time": (now + timedelta(hours=1)).isoformat()
    }

def create_test_route() -> Dict[str, Any]:
    """Create a test route request."""
    return {
        "route_id": f"test_route_{datetime.utcnow().timestamp()}",
        "waypoints": [
            {"lat": 0, "lng": 0, "type": "pickup"},
            {"lat": 1, "lng": 1, "type": "delivery"}
        ],
        "vehicle_type": "car"
    }

def create_test_vehicle() -> Dict[str, Any]:
    """Create a test vehicle request."""
    return {
        "vehicle_id": f"test_vehicle_{datetime.utcnow().timestamp()}",
        "vehicle_type": "car",
        "status": "available"
    }