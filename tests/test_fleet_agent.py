import unittest
from datetime import datetime, timedelta
from ..agents.fleet.fleet_agent import FleetAgent, Vehicle
from .test_utils import create_test_config, cleanup_test_config, create_test_vehicle

class TestFleetAgent(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.config_path = create_test_config("fleet")
        self.agent = FleetAgent(self.config_path)
        self.agent.initialize()
    
    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_config(self.config_path)
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertTrue(self.agent.is_active())
        self.assertEqual(self.agent.state["total_vehicles"], 0)
        self.assertEqual(self.agent.state["available_vehicles"], 0)
        self.assertEqual(self.agent.state["maintenance_required"], 0)
    
    def test_add_vehicle(self):
        """Test adding a new vehicle."""
        vehicle_data = create_test_vehicle()
        result = self.agent.process({
            "action": "add_vehicle",
            **vehicle_data
        })
        
        self.assertEqual(result["status"], "added")
        self.assertEqual(result["vehicle_id"], vehicle_data["vehicle_id"])
        self.assertEqual(self.agent.state["total_vehicles"], 1)
        self.assertEqual(self.agent.state["available_vehicles"], 1)
    
    def test_assign_vehicle(self):
        """Test assigning a vehicle to a driver."""
        # Add a vehicle
        vehicle_data = create_test_vehicle()
        self.agent.process({
            "action": "add_vehicle",
            **vehicle_data
        })
        
        # Assign to driver
        result = self.agent.process({
            "action": "assign_vehicle",
            "vehicle_id": vehicle_data["vehicle_id"],
            "driver_id": "test_driver_1"
        })
        
        self.assertEqual(result["status"], "assigned")
        self.assertEqual(self.agent.vehicles[vehicle_data["vehicle_id"]].status, "assigned")
        self.assertEqual(self.agent.state["available_vehicles"], 0)
    
    def test_vehicle_status_update(self):
        """Test updating vehicle status."""
        # Add a vehicle
        vehicle_data = create_test_vehicle()
        self.agent.process({
            "action": "add_vehicle",
            **vehicle_data
        })
        
        # Update status
        result = self.agent.process({
            "action": "update_status",
            "vehicle_id": vehicle_data["vehicle_id"],
            "status": "maintenance",
            "location": {"lat": 0, "lng": 0}
        })
        
        self.assertEqual(result["status"], "updated")
        self.assertEqual(
            self.agent.vehicles[vehicle_data["vehicle_id"]].status,
            "maintenance"
        )
    
    def test_maintenance_scheduling(self):
        """Test scheduling vehicle maintenance."""
        # Add a vehicle
        vehicle_data = create_test_vehicle()
        self.agent.process({
            "action": "add_vehicle",
            **vehicle_data
        })
        
        # Schedule maintenance
        maintenance_date = datetime.utcnow() + timedelta(days=7)
        result = self.agent.process({
            "action": "schedule_maintenance",
            "vehicle_id": vehicle_data["vehicle_id"],
            "maintenance_type": "routine",
            "due_date": maintenance_date
        })
        
        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(
            self.agent.maintenance_schedule[vehicle_data["vehicle_id"]],
            maintenance_date
        )
    
    def test_vehicle_distance_tracking(self):
        """Test tracking vehicle distance and triggering maintenance."""
        # Add a vehicle
        vehicle_data = create_test_vehicle()
        self.agent.process({
            "action": "add_vehicle",
            **vehicle_data
        })
        
        # Update with distance
        result = self.agent.process({
            "action": "update_status",
            "vehicle_id": vehicle_data["vehicle_id"],
            "distance": 5001  # Above maintenance threshold
        })
        
        self.assertEqual(result["status"], "updated")
        self.assertEqual(self.agent.state["maintenance_required"], 1)
    
    def test_get_available_vehicles(self):
        """Test getting available vehicles."""
        # Add multiple vehicles
        vehicles = [
            {"vehicle_id": "v1", "vehicle_type": "car"},
            {"vehicle_id": "v2", "vehicle_type": "van"},
            {"vehicle_id": "v3", "vehicle_type": "car"}
        ]
        
        for vehicle in vehicles:
            self.agent.process({
                "action": "add_vehicle",
                **vehicle
            })
        
        # Test filtering by type
        cars = self.agent.get_available_vehicles("car")
        self.assertEqual(len(cars), 2)
        
        vans = self.agent.get_available_vehicles("van")
        self.assertEqual(len(vans), 1)
    
    def test_invalid_vehicle_operations(self):
        """Test invalid vehicle operations."""
        # Try to assign non-existent vehicle
        with self.assertRaises(ValueError):
            self.agent.process({
                "action": "assign_vehicle",
                "vehicle_id": "non_existent_vehicle",
                "driver_id": "test_driver"
            })
        
        # Try to update non-existent vehicle
        with self.assertRaises(ValueError):
            self.agent.process({
                "action": "update_status",
                "vehicle_id": "non_existent_vehicle",
                "status": "available"
            })

if __name__ == '__main__':
    unittest.main()