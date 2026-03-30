import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from test_dispatch_agent import TestDispatchAgent
from test_routing_agent import TestRoutingAgent
from test_fleet_agent import TestFleetAgent
from test_supervisor_agent import TestSupervisorAgent

def run_tests():
    """Run all test cases."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDispatchAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRoutingAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFleetAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSupervisorAgent))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())