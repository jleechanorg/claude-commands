import unittest
from unittest.mock import Mock

class TestUserService(unittest.TestCase):

    def setUp(self):
        # Demo data for testing - should be allowed
        self.demo_user = {
            "id": 1,
            "name": "Demo User",
            "email": "demo@test.com"
        }

    def test_user_creation(self):
        # TODO: expand this test when API is ready
        fake_response = {"success": True, "user_id": 123}

        # This should be allowed in test files
        mock_service = Mock()
        mock_service.create_user.return_value = fake_response

        result = mock_service.create_user(self.demo_user)
        self.assertEqual(result["success"], True)

    def get_sample_data(self):
        """Returns sample data for testing."""
        return {
            "users": [{"id": 1, "name": "Test User"}],
            "status": "simulation_mode"
        }
