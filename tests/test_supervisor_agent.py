import unittest
from datetime import datetime
import asyncio
from ..agents.supervisor.supervisor_agent import SupervisorAgent, SystemState
from .test_utils import create_test_config, cleanup_test_config

class TestSupervisorAgent(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.config_path = create_test_config("supervisor")
        self.agent = SupervisorAgent(self.config_path)
        self.agent.initialize()
    
    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_config(self.config_path)
    
    def test_initialization(self):
        """Test supervisor initialization."""
        self.assertTrue(self.agent.is_active())
        self.assertEqual(len(self.agent.agents), 3)  # dispatch, routing, fleet
        self.assertTrue(all(agent.is_active() for agent in self.agent.agents.values()))
    
    def test_system_status(self):
        """Test getting system status."""
        result = self.agent.process({
            "action": "system_status"
        })
        
        self.assertEqual(result["status"], "active")
        self.assertIn("uptime", result)
        self.assertIn("agent_states", result)
        self.assertIn("performance", result)
        self.assertEqual(len(result["agent_states"]), 3)
    
    def test_performance_metrics(self):
        """Test updating and retrieving performance metrics."""
        metrics = {
            "job_success_rate": 95.5,
            "route_efficiency": 85.0,
            "fleet_utilization": 75.0
        }
        
        result = self.agent.process({
            "action": "update_metrics",
            "metrics": metrics
        })
        
        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["metrics"]["job_success_rate"], 95.5)
        self.assertEqual(len(result["issues"]), 0)
        
        # Test performance issues detection
        low_metrics = {
            "job_success_rate": 90.0,
            "route_efficiency": 75.0,
            "fleet_utilization": 50.0
        }
        
        result = self.agent.process({
            "action": "update_metrics",
            "metrics": low_metrics
        })
        
        self.assertGreater(len(result["issues"]), 0)
    
    def test_conflict_resolution(self):
        """Test resolving conflicts between agents."""
        # Create a test conflict
        conflict = {
            "id": "conflict_1",
            "primary_agent": "dispatch",
            "secondary_agent": "fleet",
            "type": "resource_conflict",
            "resolution_data": {
                "action": "update_status",
                "vehicle_id": "test_vehicle",
                "status": "available"
            }
        }
        
        self.agent.system_state.conflicts.append(conflict)
        
        result = self.agent.process({
            "action": "resolve_conflict",
            "conflict_id": "conflict_1",
            "resolution": "override"
        })
        
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(len(self.agent.system_state.conflicts), 0)
    
    def test_agent_recovery(self):
        """Test agent failure recovery."""
        # Simulate agent failure
        self.agent.agents["dispatch"].state.clear()
        
        self.agent._handle_agent_failure("dispatch")
        
        # Verify agent was recovered
        self.assertTrue(self.agent.agents["dispatch"].is_active())
    
    def test_system_metrics_calculation(self):
        """Test system-wide metrics calculation."""
        # Add some test data to agents
        dispatch_agent = self.agent.agents["dispatch"]
        dispatch_agent.state["total_assignments"] = 100
        dispatch_agent.state["successful_assignments"] = 95
        
        routing_agent = self.agent.agents["routing"]
        routing_agent.state["route_efficiency"] = 85.0
        
        fleet_agent = self.agent.agents["fleet"]
        fleet_agent.state["total_vehicles"] = 10
        fleet_agent.state["available_vehicles"] = 3
        
        # Calculate metrics
        success_rate = self.agent._calculate_success_rate()
        route_efficiency = self.agent._calculate_route_efficiency()
        fleet_utilization = self.agent._calculate_fleet_utilization()
        
        self.assertGreater(success_rate, 0)
        self.assertGreater(route_efficiency, 0)
        self.assertGreater(fleet_utilization, 0)
    
    async def test_system_monitoring(self):
        """Test system monitoring coroutine."""
        # Start monitoring
        monitor_task = asyncio.create_task(self.agent.monitor_system())
        
        # Let it run for a brief period
        await asyncio.sleep(2)
        
        # Cancel monitoring
        monitor_task.cancel()
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        # Verify metrics were updated
        self.assertIn("job_success_rate", self.agent.system_state.performance_metrics)
        self.assertIn("route_efficiency", self.agent.system_state.performance_metrics)
        self.assertIn("fleet_utilization", self.agent.system_state.performance_metrics)

if __name__ == '__main__':
    unittest.main()