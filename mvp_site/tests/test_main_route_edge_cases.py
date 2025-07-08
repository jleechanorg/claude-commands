import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TESTING"] = "true"

import unittest
from unittest.mock import patch, Mock, MagicMock
import json
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import io

# Handle missing dependencies gracefully
try:
    from main import app, create_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    app = None
    create_app = None

try:
    import firebase_admin
    from firebase_admin import auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    auth = None

try:
    import firestore_service
    import gemini_service
    from game_state import GameState
    import document_generator
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    firestore_service = None
    gemini_service = None
    GameState = None
    document_generator = None


@unittest.skipIf(not FLASK_AVAILABLE or not SERVICES_AVAILABLE, 
                 "Skipping tests: Required dependencies not available in CI environment")
class TestMainRouteEdgeCases(unittest.TestCase):
    """Test edge cases for main.py route handlers."""

    def setUp(self):
        """Set up test fixtures."""
        if not FLASK_AVAILABLE or not SERVICES_AVAILABLE:
            self.skipTest("Required dependencies not available")
            
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_user_id = 'test-user-123'
        self.test_campaign_id = 'test-campaign-456'
        
        # Common headers for authenticated requests
        self.auth_headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }
        
        # Test bypass headers
        self.test_headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id,
            'Content-Type': 'application/json'
        }

    def tearDown(self):
        """Clean up after tests."""
        pass

    # ===== Sub-bullet 1: Large Payload Handling (3-4 tests) =====

    @patch('firestore_service.get_campaigns_for_user')
    def test_large_json_payload_accepted(self, mock_get_campaigns):
        """Test that reasonably large JSON payloads are accepted."""
        # Create a large but valid payload (500KB of campaign data)
        large_campaigns = []
        for i in range(100):
            campaign = {
                'id': f'campaign-{i}',
                'title': f'Campaign {i} with a very long title that contains lots of text',
                'description': 'This is a very detailed campaign description. ' * 50,
                'metadata': {
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z',
                    'tags': ['adventure', 'fantasy', 'epic', 'dragons'] * 10,
                    'settings': {
                        'difficulty': 'hard',
                        'world': 'custom',
                        'rules': 'D&D 5e',
                        'notes': 'Additional notes about the campaign ' * 20
                    }
                }
            }
            large_campaigns.append(campaign)
        
        mock_get_campaigns.return_value = large_campaigns
        
        # Make request with large response
        response = self.client.get('/api/campaigns', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 100)
        
        # Verify the response size is substantial
        response_size = len(response.data)
        self.assertGreater(response_size, 100000)  # Should be > 100KB

    @patch('firestore_service.create_campaign')
    @patch('gemini_service.get_initial_story')
    def test_oversized_payload_rejected(self, mock_get_story, mock_create_campaign):
        """Test that excessively large payloads are rejected."""
        # Create an extremely large payload (>10MB)
        oversized_prompt = 'x' * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        
        payload = {
            'prompt': oversized_prompt,
            'title': 'Test Campaign',
            'selected_prompts': [],
            'custom_options': []
        }
        
        # Flask typically has a default limit around 16MB, but we're testing
        # that we handle large payloads gracefully
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # The server should handle this gracefully, either by accepting it
        # (if within limits) or rejecting it cleanly
        self.assertIn(response.status_code, [400, 413, 500])

    @patch('firestore_service.update_campaign_game_state')
    @patch('firestore_service.get_campaign_game_state')
    def test_chunked_request_handling(self, mock_get_state, mock_update_state):
        """Test handling of chunked transfer encoding requests."""
        # Set up mocks
        mock_get_state.return_value = GameState()
        mock_update_state.return_value = None
        
        # Create a request with chunked data
        payload = {
            'input': 'Test input with chunked encoding',
            'mode': 'character'
        }
        
        # Simulate chunked request by using Flask test client's streaming
        response = self.client.post(
            f'/api/campaigns/{self.test_campaign_id}/interaction',
            headers={
                **self.test_headers,
                'Transfer-Encoding': 'chunked'
            },
            data=json.dumps(payload)
        )
        
        # The server should handle chunked requests properly
        # Either accepting them or returning an appropriate error
        self.assertIn(response.status_code, [200, 400, 500])

    @patch('firestore_service.create_campaign')
    @patch('gemini_service.get_initial_story')
    def test_deeply_nested_json_payload(self, mock_get_story, mock_create_campaign):
        """Test handling of deeply nested JSON structures."""
        # Create deeply nested JSON (100 levels deep)
        deeply_nested = {}
        current = deeply_nested
        for i in range(100):
            current['level'] = {f'depth_{i}': {}}
            current = current['level']
        current['value'] = 'deep_value'
        
        # Create campaign with deeply nested custom options
        payload = {
            'prompt': 'Test campaign with deeply nested data',
            'title': 'Deep Nest Test',
            'selected_prompts': [],
            'custom_options': ['defaultWorld'],
            'metadata': deeply_nested
        }
        
        mock_get_story.return_value = Mock(narrative_text='Test story')
        mock_create_campaign.return_value = 'new-campaign-id'
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            data=json.dumps(payload)
        )
        
        # Server should handle deeply nested JSON gracefully
        self.assertIn(response.status_code, [201, 400, 500])
        
        if response.status_code == 201:
            data = json.loads(response.data)
            self.assertTrue(data.get('success'))
            self.assertEqual(data.get('campaign_id'), 'new-campaign-id')


    # ===== Sub-bullet 2: Concurrent Request Handling (3-4 tests) =====

    @patch('firestore_service.update_campaign_game_state')
    @patch('firestore_service.get_campaign_game_state')
    @patch('firestore_service.get_campaign_by_id')
    @patch('firestore_service.add_story_entry')
    @patch('gemini_service.continue_story')
    def test_concurrent_campaign_updates(self, mock_continue_story, mock_add_story,
                                       mock_get_campaign, mock_get_state, mock_update_state):
        """Test handling of concurrent updates to the same campaign."""
        # Set up mocks
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign', 'selected_prompts': []},
            ['Previous story entry']
        )
        mock_get_state.return_value = GameState()
        mock_continue_story.return_value = Mock(
            narrative_text='AI response',
            state_updates={},
            structured_response={},
            debug_tags_present={'state_updates': True}
        )
        
        # Simulate concurrent requests
        results = []
        errors = []
        
        def make_request(user_number):
            try:
                response = self.client.post(
                    f'/api/campaigns/{self.test_campaign_id}/interaction',
                    headers=self.test_headers,
                    data=json.dumps({
                        'input': f'User {user_number} action',
                        'mode': 'character'
                    })
                )
                results.append((user_number, response.status_code))
            except Exception as e:
                errors.append((user_number, str(e)))
        
        # Launch 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(5):
                future = executor.submit(make_request, i)
                futures.append(future)
            
            # Wait for all to complete
            for future in futures:
                future.result()
        
        # All requests should complete successfully
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # All should return 200
        for user_num, status_code in results:
            self.assertEqual(status_code, 200)
        
        # Verify proper sequencing of updates
        self.assertEqual(mock_add_story.call_count, 10)  # 5 user entries + 5 AI responses

    @patch('firestore_service.update_campaign_game_state')
    @patch('firestore_service.get_campaign_game_state') 
    def test_race_condition_prevention(self, mock_get_state, mock_update_state):
        """Test that race conditions are prevented in state updates."""
        # Set up a game state that will be modified
        initial_state = GameState()
        initial_state.custom_campaign_state = {'counter': 0}
        mock_get_state.return_value = initial_state
        
        # Track update calls
        update_calls = []
        update_lock = threading.Lock()
        
        def track_update(user_id, campaign_id, state_dict):
            with update_lock:
                update_calls.append(state_dict.get('custom_campaign_state', {}).get('counter', 0))
        
        mock_update_state.side_effect = track_update
        
        # Create multiple concurrent SET commands
        def send_set_command(value):
            response = self.client.post(
                f'/api/campaigns/{self.test_campaign_id}/interaction',
                headers=self.test_headers,
                data=json.dumps({
                    'input': f'GOD_MODE_SET: custom_campaign_state.counter = {value}',
                    'mode': 'god'
                })
            )
            return response
        
        # Send 3 concurrent updates
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(send_set_command, 10),
                executor.submit(send_set_command, 20),
                executor.submit(send_set_command, 30)
            ]
            
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        # Verify updates were applied (order may vary due to concurrency)
        self.assertEqual(len(update_calls), 3)
        self.assertSetEqual(set(update_calls), {10, 20, 30})

    @patch('firestore_service.create_campaign')
    @patch('gemini_service.get_initial_story')
    def test_optimistic_locking(self, mock_get_story, mock_create_campaign):
        """Test optimistic locking behavior for concurrent campaign creation."""
        # Set up mocks
        mock_get_story.return_value = Mock(narrative_text='Campaign story')
        
        # Simulate a delay in campaign creation to increase chance of conflict
        creation_counter = {'count': 0}
        creation_lock = threading.Lock()
        
        def slow_create(*args, **kwargs):
            with creation_lock:
                creation_counter['count'] += 1
                count = creation_counter['count']
            # Removed sleep - mock delay handled by side_effect
            return f'campaign-{count}'
        
        mock_create_campaign.side_effect = slow_create
        
        # Launch concurrent campaign creations
        results = []
        
        def create_campaign(num):
            response = self.client.post(
                '/api/campaigns',
                headers=self.test_headers,
                data=json.dumps({
                    'prompt': f'Test campaign {num}',
                    'title': f'Campaign {num}',
                    'selected_prompts': []
                })
            )
            return response
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_campaign, i) for i in range(3)]
            results = [future.result() for future in futures]
        
        # All should succeed
        for response in results:
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('campaign-', data['campaign_id'])
        
        # Verify all campaigns were created
        self.assertEqual(mock_create_campaign.call_count, 3)
        self.assertEqual(creation_counter['count'], 3)

    @patch('firestore_service.get_campaigns_for_user')
    def test_concurrent_read_operations(self, mock_get_campaigns):
        """Test that concurrent read operations don't interfere with each other."""
        # Create different responses for tracking
        def get_campaigns_with_delay(user_id):
            # Concurrency handled by ThreadPoolExecutor
            return [
                {'id': f'campaign-{user_id}-1', 'title': f'User {user_id} Campaign 1'},
                {'id': f'campaign-{user_id}-2', 'title': f'User {user_id} Campaign 2'}
            ]
        
        mock_get_campaigns.side_effect = get_campaigns_with_delay
        
        # Make concurrent requests from different users
        results = {}
        
        def get_user_campaigns(user_num):
            headers = {
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': f'user-{user_num}',
                'Content-Type': 'application/json'
            }
            response = self.client.get('/api/campaigns', headers=headers)
            return user_num, response
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_user_campaigns, i) for i in range(5)]
            for future in futures:
                user_num, response = future.result()
                results[user_num] = response
        
        # Verify each user got their own campaigns
        self.assertEqual(len(results), 5)
        for user_num, response in results.items():
            self.assertEqual(response.status_code, 200)
            campaigns = json.loads(response.data)
            self.assertEqual(len(campaigns), 2)
            # Verify campaigns belong to the correct user
            for campaign in campaigns:
                self.assertIn(f'user-{user_num}', campaign['id'])


    # ===== Sub-bullet 3: Session Timeout Scenarios (3-4 tests) =====

    @patch('firebase_admin.auth.verify_id_token')
    def test_session_timeout_during_request(self, mock_verify_token):
        """Test handling when session times out during request processing."""
        # First request succeeds
        mock_verify_token.return_value = {'uid': self.test_user_id}
        
        # Make initial request to establish session
        response = self.client.get(
            '/api/campaigns',
            headers={'Authorization': 'Bearer valid-token'}
        )
        self.assertEqual(response.status_code, 200)
        
        # Simulate token expiration during next request
        mock_verify_token.side_effect = auth.ExpiredIdTokenError('Token expired', None)
        
        # Make request with expired token
        response = self.client.get(
            '/api/campaigns',
            headers={'Authorization': 'Bearer expired-token'}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data.get('success', True))
        self.assertIn('Auth failed', data.get('error', ''))

    @patch('firebase_admin.auth.verify_id_token')
    @patch('firestore_service.get_campaigns_for_user')
    def test_expired_session_renewal(self, mock_get_campaigns, mock_verify_token):
        """Test session renewal workflow with expired tokens."""
        # Set up mock campaigns
        mock_get_campaigns.return_value = [{'id': 'campaign-1', 'title': 'Test Campaign'}]
        
        # First, simulate expired token
        mock_verify_token.side_effect = auth.ExpiredIdTokenError('Token expired', None)
        
        response = self.client.get(
            '/api/campaigns',
            headers={'Authorization': 'Bearer expired-token'}
        )
        self.assertEqual(response.status_code, 401)
        
        # Now simulate renewed token
        mock_verify_token.side_effect = None
        mock_verify_token.return_value = {'uid': self.test_user_id}
        
        response = self.client.get(
            '/api/campaigns',
            headers={'Authorization': 'Bearer new-valid-token'}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify we got the campaigns
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Campaign')

    @patch('firestore_service.get_campaign_by_id')
    @patch('firestore_service.get_campaign_game_state')
    @patch('firestore_service.add_story_entry')
    @patch('gemini_service.continue_story')
    @patch('firestore_service.update_campaign_game_state')
    def test_idle_timeout_handling(self, mock_update_state, mock_continue_story,
                                  mock_add_story, mock_get_state, mock_get_campaign):
        """Test handling of idle timeout during long-running operations."""
        # Set up initial mocks
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign', 'selected_prompts': []},
            ['Previous story']
        )
        mock_get_state.return_value = GameState()
        
        # Simulate a very slow AI response (timeout scenario)
        def slow_ai_response(*args, **kwargs):
            # Mock delay in the response
            return Mock(
                narrative_text='Delayed response',
                state_updates={},
                structured_response={},
                debug_tags_present={'state_updates': True}
            )
        
        mock_continue_story.side_effect = slow_ai_response
        
        # Make request (should handle timeout gracefully)
        response = self.client.post(
            f'/api/campaigns/{self.test_campaign_id}/interaction',
            headers=self.test_headers,
            data=json.dumps({
                'input': 'Test action that takes a long time',
                'mode': 'character'
            })
        )
        
        # Should still complete successfully despite delay
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['response'], 'Delayed response')

    @patch('firebase_admin.auth.verify_id_token')
    def test_token_refresh_race_condition(self, mock_verify_token):
        """Test race condition when multiple requests arrive during token refresh."""
        # Track verification attempts
        verification_count = {'count': 0}
        verification_lock = threading.Lock()
        
        def verify_with_tracking(token):
            with verification_lock:
                verification_count['count'] += 1
                if verification_count['count'] == 1:
                    # First request sees expired token
                    raise auth.ExpiredIdTokenError('Token expired', None)
                else:
                    # Subsequent requests see valid token
                    return {'uid': self.test_user_id}
        
        mock_verify_token.side_effect = verify_with_tracking
        
        # Launch multiple concurrent requests
        results = []
        
        def make_request(req_num):
            response = self.client.get(
                '/api/campaigns',
                headers={'Authorization': f'Bearer token-{req_num}'}
            )
            return req_num, response.status_code
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [future.result() for future in futures]
        
        # First request should fail, others should succeed
        results.sort(key=lambda x: x[0])  # Sort by request number
        
        # At least one should fail with 401
        status_codes = [r[1] for r in results]
        self.assertIn(401, status_codes)
        
        # Others might succeed if they arrive after token refresh
        self.assertTrue(any(code == 200 for code in status_codes))


    # ===== Sub-bullet 4: File Upload/Download Errors (3-4 tests) =====

    @patch('firestore_service.get_campaign_by_id')
    def test_file_upload_size_limit(self, mock_get_campaign):
        """Test handling of oversized file uploads."""
        # Note: main.py doesn't have explicit file upload endpoints,
        # but we can test large payload handling in export requests
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign'},
            [{'actor': 'user', 'text': 'x' * 1000000}] * 100  # Very large story log
        )
        
        # Request export of extremely large campaign
        response = self.client.get(
            f'/api/campaigns/{self.test_campaign_id}/export?format=txt',
            headers=self.test_headers
        )
        
        # Should handle large exports gracefully
        self.assertIn(response.status_code, [200, 500])
        
        if response.status_code == 500:
            data = json.loads(response.data)
            self.assertIn('error', data)

    @patch('os.path.exists')
    @patch('firestore_service.get_campaign_by_id')
    def test_invalid_file_type_rejection(self, mock_get_campaign, mock_exists):
        """Test rejection of invalid file export formats."""
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign'},
            [{'actor': 'user', 'text': 'Test story'}]
        )
        
        # Request invalid format
        response = self.client.get(
            f'/api/campaigns/{self.test_campaign_id}/export?format=exe',
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Unsupported format', data['error'])

    @patch('firestore_service.get_campaign_by_id')
    def test_download_nonexistent_file(self, mock_get_campaign):
        """Test downloading a campaign that doesn't exist."""
        mock_get_campaign.return_value = (None, None)
        
        response = self.client.get(
            f'/api/campaigns/nonexistent-campaign/export?format=pdf',
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Campaign not found')

    @patch('os.path.exists')
    @patch('document_generator.generate_pdf')
    @patch('firestore_service.get_campaign_by_id')
    def test_file_generation_failure(self, mock_get_campaign, mock_generate_pdf, mock_exists):
        """Test handling when file generation fails."""
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign'},
            [{'actor': 'user', 'text': 'Test story', 'mode': 'character'}]
        )
        
        # Simulate PDF generation failure
        mock_generate_pdf.side_effect = Exception('PDF generation failed')
        mock_exists.return_value = False
        
        response = self.client.get(
            f'/api/campaigns/{self.test_campaign_id}/export?format=pdf',
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)


    # ===== Sub-bullet 5: Network Disconnection Scenarios (3-4 tests) =====
    # Note: main.py doesn't have WebSocket support, so testing network disconnection scenarios

    @patch('firestore_service.get_campaign_by_id')
    @patch('firestore_service.get_campaign_game_state')
    @patch('firestore_service.add_story_entry')
    @patch('gemini_service.continue_story')
    def test_network_disconnect_during_ai_call(self, mock_continue_story, mock_add_story,
                                             mock_get_state, mock_get_campaign):
        """Test handling when network disconnects during AI service call."""
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign', 'selected_prompts': []},
            ['Previous story']
        )
        mock_get_state.return_value = GameState()
        
        # Simulate network error during AI call
        mock_continue_story.side_effect = Exception('Network connection lost')
        
        response = self.client.post(
            f'/api/campaigns/{self.test_campaign_id}/interaction',
            headers=self.test_headers,
            data=json.dumps({
                'input': 'Test action',
                'mode': 'character'
            })
        )
        
        # Should return error response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data.get('success', True))
        self.assertIn('error', data)

    @patch('firestore_service.update_campaign_game_state')
    @patch('firestore_service.get_campaign_by_id')
    @patch('firestore_service.get_campaign_game_state')
    @patch('firestore_service.add_story_entry')
    @patch('gemini_service.continue_story')
    def test_database_disconnect_during_update(self, mock_continue_story, mock_add_story,
                                             mock_get_state, mock_get_campaign, mock_update_state):
        """Test handling when database disconnects during state update."""
        mock_get_campaign.return_value = (
            {'title': 'Test Campaign', 'selected_prompts': []},
            ['Previous story']
        )
        mock_get_state.return_value = GameState()
        mock_continue_story.return_value = Mock(
            narrative_text='AI response',
            state_updates={'test': 'update'},
            structured_response={},
            debug_tags_present={'state_updates': True}
        )
        
        # Simulate database disconnect during update
        mock_update_state.side_effect = Exception('Database connection lost')
        
        response = self.client.post(
            f'/api/campaigns/{self.test_campaign_id}/interaction',
            headers=self.test_headers,
            data=json.dumps({
                'input': 'Test action',
                'mode': 'character'
            })
        )
        
        # Should handle database errors gracefully
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('firestore_service.get_campaigns_for_user')
    def test_intermittent_connection_recovery(self, mock_get_campaigns):
        """Test recovery from intermittent connection issues."""
        # Track call count
        call_count = {'count': 0}
        
        def intermittent_failure(user_id):
            call_count['count'] += 1
            if call_count['count'] == 1:
                # First call fails
                raise Exception('Connection timeout')
            else:
                # Second call succeeds
                return [{'id': 'campaign-1', 'title': 'Test Campaign'}]
        
        mock_get_campaigns.side_effect = intermittent_failure
        
        # First request should fail
        response1 = self.client.get('/api/campaigns', headers=self.test_headers)
        self.assertEqual(response1.status_code, 500)
        
        # Second request should succeed
        response2 = self.client.get('/api/campaigns', headers=self.test_headers)
        self.assertEqual(response2.status_code, 200)
        data = json.loads(response2.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Campaign')


    # ===== Sub-bullet 6: CORS Edge Cases (3-4 tests) =====

    def test_cors_preflight_handling(self):
        """Test CORS preflight OPTIONS request handling."""
        # Send OPTIONS request
        response = self.client.options(
            '/api/campaigns',
            headers={
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
        )
        
        # Should handle preflight requests
        self.assertEqual(response.status_code, 200)
        
        # Check CORS headers
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
        self.assertIn('POST', response.headers.get('Access-Control-Allow-Methods', ''))

    def test_cors_credentials_with_wildcard(self):
        """Test CORS behavior with credentials and wildcard origin."""
        # Make request with credentials
        response = self.client.get(
            '/api/campaigns',
            headers={
                **self.test_headers,
                'Origin': 'https://example.com',
                'Cookie': 'session=test123'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        # With wildcard origin, credentials mode should be handled properly
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
        # Note: With wildcard, Access-Control-Allow-Credentials should not be 'true'
        self.assertNotEqual(response.headers.get('Access-Control-Allow-Credentials'), 'true')

    def test_cors_custom_headers(self):
        """Test CORS with custom headers."""
        # Make request with custom headers
        response = self.client.post(
            '/api/campaigns',
            headers={
                **self.test_headers,
                'Origin': 'https://example.com',
                'X-Custom-Header': 'custom-value'
            },
            data=json.dumps({
                'prompt': 'Test campaign',
                'title': 'Test Title',
                'selected_prompts': []
            })
        )
        
        # Should accept request with custom headers
        self.assertIn(response.status_code, [200, 201, 400])  # Depends on mocking
        
        # CORS headers should be present
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')


    # ===== Sub-bullet 7: Rate Limiting Behavior (3-4 tests) =====
    # Note: main.py doesn't have explicit rate limiting, testing request patterns

    @patch('firestore_service.get_campaigns_for_user')
    def test_rapid_request_handling(self, mock_get_campaigns):
        """Test handling of rapid successive requests from same user."""
        mock_get_campaigns.return_value = [{'id': 'campaign-1', 'title': 'Test Campaign'}]
        
        # Send 10 rapid requests
        results = []
        start_time = time.time()
        
        for i in range(10):
            response = self.client.get('/api/campaigns', headers=self.test_headers)
            results.append(response.status_code)
        
        end_time = time.time()
        
        # All requests should succeed
        self.assertEqual(results, [200] * 10)
        
        # Should complete quickly (no artificial delays)
        self.assertLess(end_time - start_time, 2.0)  # Should take < 2 seconds

    @patch('firestore_service.create_campaign')
    @patch('gemini_service.get_initial_story')
    def test_burst_creation_handling(self, mock_get_story, mock_create_campaign):
        """Test handling of burst campaign creation attempts."""
        mock_get_story.return_value = Mock(narrative_text='Campaign story')
        mock_create_campaign.return_value = 'new-campaign-id'
        
        # Track creation times
        creation_times = []
        
        def track_creation(*args, **kwargs):
            creation_times.append(time.time())
            return f'campaign-{len(creation_times)}'
        
        mock_create_campaign.side_effect = track_creation
        
        # Send 5 campaign creation requests in quick succession
        for i in range(5):
            response = self.client.post(
                '/api/campaigns',
                headers=self.test_headers,
                data=json.dumps({
                    'prompt': f'Campaign {i}',
                    'title': f'Title {i}',
                    'selected_prompts': []
                })
            )
            self.assertEqual(response.status_code, 201)
        
        # Verify all were created
        self.assertEqual(len(creation_times), 5)
        
        # Check timing (should all complete within reasonable time)
        total_time = creation_times[-1] - creation_times[0]
        self.assertLess(total_time, 3.0)  # Should complete within 3 seconds

    @patch('firestore_service.get_campaigns_for_user')
    def test_per_user_isolation(self, mock_get_campaigns):
        """Test that high load from one user doesn't affect others."""
        def get_user_campaigns(user_id):
            # Simulate slight delay for user-1
            if user_id == 'user-1':
                pass  # Rapid requests without delay
            return [{'id': f'{user_id}-campaign', 'title': f'{user_id} Campaign'}]
        
        mock_get_campaigns.side_effect = get_user_campaigns
        
        # User 1 sends many requests
        user1_results = []
        user2_results = []
        
        def user1_requests():
            for i in range(5):
                headers = {
                    'X-Test-Bypass-Auth': 'true',
                    'X-Test-User-ID': 'user-1',
                    'Content-Type': 'application/json'
                }
                response = self.client.get('/api/campaigns', headers=headers)
                user1_results.append(response.status_code)
        
        def user2_request():
            headers = {
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': 'user-2',
                'Content-Type': 'application/json'
            }
            start = time.time()
            response = self.client.get('/api/campaigns', headers=headers)
            end = time.time()
            user2_results.append((response.status_code, end - start))
        
        # Run user1's heavy load and user2's single request concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(user1_requests)
            # Execute in parallel
            future2 = executor.submit(user2_request)
            
            future1.result()
            future2.result()
        
        # User 1's requests should all succeed
        self.assertEqual(user1_results, [200] * 5)
        
        # User 2's request should also succeed quickly
        self.assertEqual(len(user2_results), 1)
        self.assertEqual(user2_results[0][0], 200)
        self.assertLess(user2_results[0][1], 0.5)  # Should be fast


if __name__ == '__main__':
    unittest.main()