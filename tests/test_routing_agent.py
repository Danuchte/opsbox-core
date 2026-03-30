import unittest
from ..agents.routing.routing_agent import RoutingAgent, Route
from .test_utils import create_test_config, cleanup_test_config, create_test_route

class TestRoutingAgent(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.config_path = create_test_config("routing")
        self.agent = RoutingAgent(self.config_path)
        self.agent.initialize()
    
    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_config(self.config_path)
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertTrue(self.agent.is_active())
        self.assertEqual(self.agent.state["active_routes"], 0)
        self.assertEqual(self.agent.state["total_distance"], 0)
    
    def test_route_generation(self):
        """Test generating a new route."""
        route_data = create_test_route()
        result = self.agent.process({
            "action": "generate_route",
            **route_data
        })
        
        self.assertEqual(result["status"], "generated")
        self.assertIn("distance", result)
        self.assertIn("duration", result)
        self.assertEqual(len(result["waypoints"]), len(route_data["waypoints"]))
        self.assertEqual(self.agent.state["active_routes"], 1)
    
    def test_route_optimization(self):
        """Test route optimization."""
        # Create initial route
        route_data = create_test_route()
        initial_result = self.agent.process({
            "action": "generate_route",
            **route_data
        })
        
        # Optimize the route
        optimize_result = self.agent.process({
            "action": "optimize_route",
            "route_id": initial_result["route_id"],
            "vehicle_type": "car"
        })
        
        self.assertEqual(optimize_result["status"], "optimized")
        self.assertIn("improvement", optimize_result)
        self.assertIn("new_duration", optimize_result)
    
    def test_traffic_update(self):
        """Test updating traffic conditions."""
        # Create a route
        route_data = create_test_route()
        initial_result = self.agent.process({
            "action": "generate_route",
            **route_data
        })
        
        # Update traffic
        traffic_result = self.agent.process({
            "action": "update_traffic",
            "traffic_factor": 1.5
        })
        
        self.assertEqual(traffic_result["status"], "updated")
        self.assertGreater(len(traffic_result["affected_routes"]), 0)
    
    def test_vehicle_type_constraints(self):
        """Test route generation with different vehicle types."""
        for vehicle_type in ["car", "van", "truck"]:
            route_data = create_test_route()
            route_data["vehicle_type"] = vehicle_type
            
            result = self.agent.process({
                "action": "generate_route",
                **route_data
            })
            
            self.assertEqual(result["status"], "generated")
            # Verify that larger vehicles have longer duration
            if vehicle_type in ["van", "truck"]:
                self.assertGreater(
                    result["duration"],
                    self.agent._calculate_route_metrics(
                        route_data["waypoints"],
                        "car"
                    )[1]
                )
    
    def test_invalid_route_optimization(self):
        """Test optimizing non-existent route."""
        with self.assertRaises(ValueError):
            self.agent.process({
                "action": "optimize_route",
                "route_id": "non_existent_route",
                "vehicle_type": "car"
            })
    
    def test_route_metrics_calculation(self):
        """Test route metrics calculation."""
        waypoints = [
            {"lat": 0, "lng": 0},
            {"lat": 1, "lng": 1},
            {"lat": 2, "lng": 2}
        ]
        
        distance, duration = self.agent._calculate_route_metrics(waypoints, "car")
        
        self.assertGreater(distance, 0)
        self.assertGreater(duration, 0)
        
        # Test that trucks take longer
        truck_distance, truck_duration = self.agent._calculate_route_metrics(
            waypoints,
            "truck"
        )
        self.assertGreater(truck_duration, duration)

if __name__ == '__main__':
    unittest.main()