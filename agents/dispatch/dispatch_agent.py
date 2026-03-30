from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from ..base_agent import BaseAgent

class Job:
    def __init__(self, job_id: str, pickup: str, delivery: str, time_window: tuple):
        self.job_id = job_id
        self.pickup = pickup
        self.delivery = delivery
        self.time_window = time_window
        self.assigned_driver = None
        self.status = "pending"
        self.created_at = datetime.utcnow()

class Driver:
    def __init__(self, driver_id: str, status: str = "available"):
        self.driver_id = driver_id
        self.status = status
        self.current_job = None
        self.location = None

class DispatchAgent(BaseAgent):
    def __init__(self, config_path: str):
        super().__init__("dispatch", config_path)
        self.jobs: Dict[str, Job] = {}
        self.drivers: Dict[str, Driver] = {}
        self.assignments: Dict[str, str] = {}  # job_id -> driver_id
    
    def initialize(self) -> bool:
        """Initialize dispatch agent resources."""
        self.logger.info("Initializing Dispatch Agent")
        self.update_state({
            "active_jobs": 0,
            "available_drivers": 0,
            "total_assignments": 0
        })
        return True
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dispatch requests and assignments."""
        action = data.get("action")
        if action == "new_job":
            return self._handle_new_job(data)
        elif action == "assign_driver":
            return self._assign_driver(data)
        elif action == "complete_job":
            return self._complete_job(data)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _handle_new_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming job requests."""
        job = Job(
            data["job_id"],
            data["pickup"],
            data["delivery"],
            (data["pickup_time"], data["delivery_time"])
        )
        self.jobs[job.job_id] = job
        self.state["active_jobs"] = len(self.jobs)
        
        # Try immediate assignment if drivers available
        available_drivers = [d for d in self.drivers.values() if d.status == "available"]
        if available_drivers:
            assignment = self._find_best_driver(job, available_drivers)
            if assignment:
                return self._assign_driver({
                    "job_id": job.job_id,
                    "driver_id": assignment.driver_id
                })
        
        return {"status": "job_queued", "job_id": job.job_id}
    
    def _assign_driver(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a driver to a job."""
        job_id = data["job_id"]
        driver_id = data["driver_id"]
        
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        if driver_id not in self.drivers:
            raise ValueError(f"Driver {driver_id} not found")
        
        job = self.jobs[job_id]
        driver = self.drivers[driver_id]
        
        if driver.status != "available":
            return {"status": "error", "message": "Driver not available"}
        
        job.assigned_driver = driver_id
        job.status = "assigned"
        driver.status = "busy"
        driver.current_job = job_id
        
        self.assignments[job_id] = driver_id
        self.state["total_assignments"] += 1
        
        return {
            "status": "assigned",
            "job_id": job_id,
            "driver_id": driver_id
        }
    
    def _complete_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a job as completed."""
        job_id = data["job_id"]
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        driver_id = job.assigned_driver
        
        if driver_id:
            driver = self.drivers[driver_id]
            driver.status = "available"
            driver.current_job = None
        
        job.status = "completed"
        del self.assignments[job_id]
        self.state["active_jobs"] -= 1
        
        return {"status": "completed", "job_id": job_id}
    
    def _find_best_driver(self, job: Job, available_drivers: List[Driver]) -> Optional[Driver]:
        """Find the best driver for a job based on location and availability."""
        # TODO: Implement actual driver selection logic
        # For now, return the first available driver
        return available_drivers[0] if available_drivers else None
    
    def is_active(self) -> bool:
        """Check if dispatch agent is active and functioning."""
        return bool(self.state)