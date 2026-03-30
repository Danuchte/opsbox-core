import unittest
from datetime import datetime
from ..agents.dispatch.dispatch_agent import DispatchAgent, Job, Driver
from .test_utils import create_test_config, cleanup_test_config, create_test_job

class TestDispatchAgent(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.config_path = create_test_config("dispatch")
        self.agent = DispatchAgent(self.config_path)
        self.agent.initialize()
    
    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_config(self.config_path)
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertTrue(self.agent.is_active())
        self.assertEqual(self.agent.state["active_jobs"], 0)
        self.assertEqual(self.agent.state["available_drivers"], 0)
    
    def test_new_job_creation(self):
        """Test creating a new job."""
        job_data = create_test_job()
        result = self.agent.process({
            "action": "new_job",
            **job_data
        })
        
        self.assertEqual(result["status"], "job_queued")
        self.assertIn(result["job_id"], self.agent.jobs)
        self.assertEqual(self.agent.state["active_jobs"], 1)
    
    def test_driver_assignment(self):
        """Test assigning a driver to a job."""
        # Create a job
        job_data = create_test_job()
        job_result = self.agent.process({
            "action": "new_job",
            **job_data
        })
        job_id = job_result["job_id"]
        
        # Add a test driver
        driver_id = "test_driver_1"
        self.agent.drivers[driver_id] = Driver(driver_id)
        
        # Assign driver to job
        result = self.agent.process({
            "action": "assign_driver",
            "job_id": job_id,
            "driver_id": driver_id
        })
        
        self.assertEqual(result["status"], "assigned")
        self.assertEqual(result["driver_id"], driver_id)
        self.assertEqual(self.agent.jobs[job_id].assigned_driver, driver_id)
        self.assertEqual(self.agent.drivers[driver_id].status, "busy")
    
    def test_job_completion(self):
        """Test completing a job."""
        # Create and assign a job
        job_data = create_test_job()
        job_result = self.agent.process({
            "action": "new_job",
            **job_data
        })
        job_id = job_result["job_id"]
        
        driver_id = "test_driver_1"
        self.agent.drivers[driver_id] = Driver(driver_id)
        self.agent.process({
            "action": "assign_driver",
            "job_id": job_id,
            "driver_id": driver_id
        })
        
        # Complete the job
        result = self.agent.process({
            "action": "complete_job",
            "job_id": job_id
        })
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(self.agent.jobs[job_id].status, "completed")
        self.assertEqual(self.agent.drivers[driver_id].status, "available")
    
    def test_invalid_job_assignment(self):
        """Test assigning job to non-existent driver."""
        job_data = create_test_job()
        job_result = self.agent.process({
            "action": "new_job",
            **job_data
        })
        
        with self.assertRaises(ValueError):
            self.agent.process({
                "action": "assign_driver",
                "job_id": job_result["job_id"],
                "driver_id": "non_existent_driver"
            })
    
    def test_driver_availability(self):
        """Test driver availability tracking."""
        driver_id = "test_driver_1"
        self.agent.drivers[driver_id] = Driver(driver_id)
        
        # Initially available
        self.assertEqual(self.agent.drivers[driver_id].status, "available")
        
        # Assign to job
        job_data = create_test_job()
        job_result = self.agent.process({
            "action": "new_job",
            **job_data
        })
        
        self.agent.process({
            "action": "assign_driver",
            "job_id": job_result["job_id"],
            "driver_id": driver_id
        })
        
        # Should be busy
        self.assertEqual(self.agent.drivers[driver_id].status, "busy")
        
        # Complete job
        self.agent.process({
            "action": "complete_job",
            "job_id": job_result["job_id"]
        })
        
        # Should be available again
        self.assertEqual(self.agent.drivers[driver_id].status, "available")

if __name__ == '__main__':
    unittest.main()