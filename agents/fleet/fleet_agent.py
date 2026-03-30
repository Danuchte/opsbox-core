from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..base_agent import BaseAgent

class Vehicle:
    def __init__(self, vehicle_id: str, vehicle_type: str):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.status = "available"
        self.location = None
        self.driver_id = None
        self.maintenance_due = datetime.utcnow() + timedelta(days=30)
        self.last_inspection = datetime.utcnow()
        self.total_distance = 0

class FleetAgent(BaseAgent):
    def __init__(self, config_path: str):
        super().__init__("fleet", config_path)
        self.vehicles: Dict[str, Vehicle] = {}
        self.maintenance_schedule: Dict[str, datetime] = {}
    
    def initialize(self) -> bool:
        """Initialize fleet agent resources."""
        self.logger.info("Initializing Fleet Agent")
        self.update_state({
            "total_vehicles": 0,
            "available_vehicles": 0,
            "maintenance_required": 0
        })
        return True
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process fleet management requests."""
        action = data.get("action")
        if action == "add_vehicle":
            return self._add_vehicle(data)
        elif action == "assign_vehicle":
            return self._assign_vehicle(data)
        elif action == "update_status":
            return self._update_vehicle_status(data)
        elif action == "schedule_maintenance":
            return self._schedule_maintenance(data)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _add_vehicle(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new vehicle to the fleet."""
        vehicle = Vehicle(
            data["vehicle_id"],
            data["vehicle_type"]
        )
        self.vehicles[vehicle.vehicle_id] = vehicle
        
        self.state["total_vehicles"] = len(self.vehicles)
        self.state["available_vehicles"] = len([v for v in self.vehicles.values() if v.status == "available"])
        
        return {
            "status": "added",
            "vehicle_id": vehicle.vehicle_id,
            "vehicle_type": vehicle.vehicle_type
        }
    
    def _assign_vehicle(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a vehicle to a driver."""
        vehicle_id = data["vehicle_id"]
        driver_id = data["driver_id"]
        
        if vehicle_id not in self.vehicles:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        vehicle = self.vehicles[vehicle_id]
        if vehicle.status != "available":
            return {
                "status": "error",
                "message": f"Vehicle {vehicle_id} is not available"
            }
        
        vehicle.status = "assigned"
        vehicle.driver_id = driver_id
        self.state["available_vehicles"] -= 1
        
        return {
            "status": "assigned",
            "vehicle_id": vehicle_id,
            "driver_id": driver_id
        }
    
    def _update_vehicle_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update vehicle status and location."""
        vehicle_id = data["vehicle_id"]
        if vehicle_id not in self.vehicles:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        vehicle = self.vehicles[vehicle_id]
        old_status = vehicle.status
        
        if "status" in data:
            vehicle.status = data["status"]
        if "location" in data:
            vehicle.location = data["location"]
        if "distance" in data:
            vehicle.total_distance += data["distance"]
        
        # Check if maintenance is due
        if vehicle.total_distance > 5000:  # Example threshold
            self._schedule_maintenance({
                "vehicle_id": vehicle_id,
                "maintenance_type": "routine",
                "due_date": datetime.utcnow() + timedelta(days=1)
            })
        
        # Update available vehicles count if status changed
        if old_status != vehicle.status:
            self.state["available_vehicles"] = len([v for v in self.vehicles.values() if v.status == "available"])
        
        return {
            "status": "updated",
            "vehicle_id": vehicle_id,
            "current_status": vehicle.status,
            "total_distance": vehicle.total_distance
        }
    
    def _schedule_maintenance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule vehicle maintenance."""
        vehicle_id = data["vehicle_id"]
        if vehicle_id not in self.vehicles:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        vehicle = self.vehicles[vehicle_id]
        maintenance_date = data.get("due_date", vehicle.maintenance_due)
        
        self.maintenance_schedule[vehicle_id] = maintenance_date
        vehicle.maintenance_due = maintenance_date
        
        # Update maintenance counter
        self.state["maintenance_required"] = len([
            v for v in self.vehicles.values()
            if v.maintenance_due <= datetime.utcnow()
        ])
        
        return {
            "status": "scheduled",
            "vehicle_id": vehicle_id,
            "maintenance_date": maintenance_date.isoformat()
        }
    
    def get_available_vehicles(self, vehicle_type: Optional[str] = None) -> List[Vehicle]:
        """Get list of available vehicles, optionally filtered by type."""
        available = [v for v in self.vehicles.values() if v.status == "available"]
        if vehicle_type:
            available = [v for v in available if v.vehicle_type == vehicle_type]
        return available
    
    def is_active(self) -> bool:
        """Check if fleet agent is active and functioning."""
        return bool(self.state)