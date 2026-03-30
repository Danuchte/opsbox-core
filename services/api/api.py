from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime

# Import agents
from ...agents.supervisor.supervisor_agent import SupervisorAgent

# Initialize FastAPI app
app = FastAPI(title="OPSBOX API", version="1.0.0")
logger = logging.getLogger("opsbox.api")

# Initialize supervisor agent
supervisor = SupervisorAgent("/root/.openclaw/workspace/opsbox-core/agents/supervisor/config.json")

# Request/Response Models
class JobRequest(BaseModel):
    pickup: str
    delivery: str
    pickup_time: datetime
    delivery_time: datetime

class RouteRequest(BaseModel):
    waypoints: list
    vehicle_type: str = "car"

class VehicleRequest(BaseModel):
    vehicle_id: str
    vehicle_type: str

class SystemActionRequest(BaseModel):
    action: str
    data: Dict[str, Any] = {}

# API Routes
@app.post("/jobs")
async def create_job(job: JobRequest):
    """Create a new delivery job."""
    try:
        result = supervisor.agents["dispatch"].process({
            "action": "new_job",
            "job_id": f"job_{datetime.utcnow().timestamp()}",
            "pickup": job.pickup,
            "delivery": job.delivery,
            "pickup_time": job.pickup_time,
            "delivery_time": job.delivery_time
        })
        return result
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/routes")
async def create_route(route: RouteRequest):
    """Generate a new route."""
    try:
        result = supervisor.agents["routing"].process({
            "action": "generate_route",
            "route_id": f"route_{datetime.utcnow().timestamp()}",
            "waypoints": route.waypoints,
            "vehicle_type": route.vehicle_type
        })
        return result
    except Exception as e:
        logger.error(f"Error generating route: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fleet/vehicles")
async def add_vehicle(vehicle: VehicleRequest):
    """Add a new vehicle to the fleet."""
    try:
        result = supervisor.agents["fleet"].process({
            "action": "add_vehicle",
            "vehicle_id": vehicle.vehicle_id,
            "vehicle_type": vehicle.vehicle_type
        })
        return result
    except Exception as e:
        logger.error(f"Error adding vehicle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def get_system_status():
    """Get current system status."""
    try:
        return supervisor.process({
            "action": "system_status"
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/action")
async def system_action(request: SystemActionRequest):
    """Execute a system-wide action."""
    try:
        return supervisor.process({
            "action": request.action,
            **request.data
        })
    except Exception as e:
        logger.error(f"Error executing system action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error Handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return {
        "status": "error",
        "message": str(exc),
        "timestamp": datetime.utcnow().isoformat()
    }