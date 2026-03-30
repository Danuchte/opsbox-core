from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from ..base_agent import BaseAgent
from ..dispatch.dispatch_agent import DispatchAgent
from ..routing.routing_agent import RoutingAgent
from ..fleet.fleet_agent import FleetAgent

class SystemState:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.conflicts: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {
            "job_success_rate": 100.0,
            "route_efficiency": 100.0,
            "fleet_utilization": 0.0
        }

class SupervisorAgent(BaseAgent):
    def __init__(self, config_path: str):
        super().__init__("supervisor", config_path)
        self.system_state = SystemState()
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all managed agents."""
        try:
            self.agents["dispatch"] = DispatchAgent("agents/dispatch/config.json")
            self.agents["routing"] = RoutingAgent("agents/routing/config.json")
            self.agents["fleet"] = FleetAgent("agents/fleet/config.json")
            
            for agent_id, agent in self.agents.items():
                agent.initialize()
                self.system_state.agent_states[agent_id] = agent.get_status()
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def initialize(self) -> bool:
        """Initialize supervisor agent resources."""
        self.logger.info("Initializing Supervisor Agent")
        self.update_state({
            "active_agents": len(self.agents),
            "system_uptime": 0,
            "conflict_count": 0
        })
        return True
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process system-wide operations and monitoring."""
        action = data.get("action")
        if action == "system_status":
            return self._get_system_status()
        elif action == "resolve_conflict":
            return self._resolve_conflict(data)
        elif action == "update_metrics":
            return self._update_metrics(data)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        # Update agent states
        for agent_id, agent in self.agents.items():
            self.system_state.agent_states[agent_id] = agent.get_status()
        
        # Calculate system uptime
        uptime = (datetime.utcnow() - self.system_state.start_time).total_seconds()
        self.state["system_uptime"] = uptime
        
        return {
            "status": "active",
            "uptime": uptime,
            "agent_states": self.system_state.agent_states,
            "performance": self.system_state.performance_metrics,
            "conflicts": len(self.system_state.conflicts)
        }
    
    def _resolve_conflict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between agents."""
        conflict_id = data["conflict_id"]
        resolution = data["resolution"]
        
        # Find the conflict
        conflict = next((c for c in self.system_state.conflicts if c["id"] == conflict_id), None)
        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        # Apply resolution
        if resolution == "override":
            # Override one agent's decision
            primary_agent = self.agents[conflict["primary_agent"]]
            primary_agent.process(conflict["resolution_data"])
        elif resolution == "compromise":
            # Apply compromise solution
            for agent_id in [conflict["primary_agent"], conflict["secondary_agent"]]:
                agent = self.agents[agent_id]
                agent.process(conflict["resolution_data"])
        
        # Remove resolved conflict
        self.system_state.conflicts = [c for c in self.system_state.conflicts if c["id"] != conflict_id]
        self.state["conflict_count"] = len(self.system_state.conflicts)
        
        return {
            "status": "resolved",
            "conflict_id": conflict_id,
            "resolution": resolution
        }
    
    def _update_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update system performance metrics."""
        metrics = data.get("metrics", {})
        self.system_state.performance_metrics.update(metrics)
        
        # Check for performance issues
        issues = []
        if metrics.get("job_success_rate", 100) < 95:
            issues.append("Job success rate below threshold")
        if metrics.get("route_efficiency", 100) < 80:
            issues.append("Route efficiency below threshold")
        if metrics.get("fleet_utilization", 0) < 60:
            issues.append("Low fleet utilization")
        
        return {
            "status": "updated",
            "metrics": self.system_state.performance_metrics,
            "issues": issues
        }
    
    async def monitor_system(self):
        """Continuous system monitoring coroutine."""
        while True:
            try:
                # Check agent health
                for agent_id, agent in self.agents.items():
                    if not agent.is_active():
                        self.logger.warning(f"Agent {agent_id} is inactive")
                        self._handle_agent_failure(agent_id)
                
                # Update system metrics
                self._update_metrics({
                    "metrics": {
                        "job_success_rate": self._calculate_success_rate(),
                        "route_efficiency": self._calculate_route_efficiency(),
                        "fleet_utilization": self._calculate_fleet_utilization()
                    }
                })
                
                await asyncio.sleep(60)  # Monitor every minute
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    def _handle_agent_failure(self, agent_id: str):
        """Handle agent failure or inactivity."""
        self.logger.error(f"Attempting to recover agent {agent_id}")
        try:
            # Attempt to reinitialize the agent
            self.agents[agent_id].initialize()
            self.logger.info(f"Successfully recovered agent {agent_id}")
        except Exception as e:
            self.logger.error(f"Failed to recover agent {agent_id}: {e}")
            # TODO: Implement fallback logic or notification system
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall job success rate."""
        dispatch_agent = self.agents.get("dispatch")
        if not dispatch_agent:
            return 100.0
        
        total_jobs = dispatch_agent.state.get("total_assignments", 0)
        if total_jobs == 0:
            return 100.0
        
        successful_jobs = total_jobs - len(self.system_state.conflicts)
        return (successful_jobs / total_jobs) * 100
    
    def _calculate_route_efficiency(self) -> float:
        """Calculate overall route efficiency."""
        routing_agent = self.agents.get("routing")
        if not routing_agent:
            return 100.0
        
        # Simple efficiency calculation based on optimized routes
        return routing_agent.state.get("route_efficiency", 100.0)
    
    def _calculate_fleet_utilization(self) -> float:
        """Calculate fleet utilization percentage."""
        fleet_agent = self.agents.get("fleet")
        if not fleet_agent:
            return 0.0
        
        total = fleet_agent.state.get("total_vehicles", 0)
        if total == 0:
            return 0.0
        
        available = fleet_agent.state.get("available_vehicles", 0)
        return ((total - available) / total) * 100
    
    def is_active(self) -> bool:
        """Check if supervisor agent is active and functioning."""
        return bool(self.state) and all(agent.is_active() for agent in self.agents.values())