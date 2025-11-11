import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
import sys

# Add the parent directory to Python path to import app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import create_app, socketio


class WebSocketIOTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.socketio_client = socketio.test_client(self.app, namespace='/')

    def tearDown(self):
        if self.socketio_client.is_connected():
            self.socketio_client.disconnect()

    def test_websocket_connection(self):
        """Test that clients can connect to the WebSocket server"""
        self.assertTrue(self.socketio_client.is_connected())

    def test_iot_data_streaming(self):
        """Test that mock IoT data is streamed to connected clients"""
        # Clear any existing events
        self.socketio_client.get_received()

        # Simulate IoT data emission (this would normally be triggered by a background task)
        with self.app.app_context():
            from flask_app import emit_mock_iot_data
            emit_mock_iot_data()

        # Check that data was received
        received = self.socketio_client.get_received()
        self.assertGreater(len(received), 0)

        # Verify the structure of the received data
        iot_data_event = None
        for event in received:
            if event['name'] == 'iot_data':
                iot_data_event = event
                break

        self.assertIsNotNone(iot_data_event)
        self.assertIn('device_id', iot_data_event['args'][0])
        self.assertIn('timestamp', iot_data_event['args'][0])
        self.assertIn('temperature', iot_data_event['args'][0])
        self.assertIn('humidity', iot_data_event['args'][0])

    def test_multiple_client_connections(self):
        """Test that multiple clients can connect and receive data"""
        client1 = socketio.test_client(self.app, namespace='/')
        client2 = socketio.test_client(self.app, namespace='/')

        self.assertTrue(client1.is_connected())
        self.assertTrue(client2.is_connected())

        # Emit data
        with self.app.app_context():
            from flask_app import emit_mock_iot_data
            emit_mock_iot_data()

        # Both clients should receive the data
        received1 = client1.get_received()
        received2 = client2.get_received()

        self.assertGreater(len(received1), 0)
        self.assertGreater(len(received2), 0)

        # Data should be identical
        self.assertEqual(received1[0]['args'][0], received2[0]['args'][0])

        # Clean up
        client1.disconnect()
        client2.disconnect()

    def test_device_authentication(self):
        """Test device authentication functionality"""
        # Test valid authentication
        auth_data = {'device_id': 'device_001', 'token': 'valid_token_123'}
        self.socketio_client.emit('authenticate', auth_data)

        received = self.socketio_client.get_received()
        auth_response = None
        for event in received:
            if event['name'] == 'auth_response':
                auth_response = event
                break

        self.assertIsNotNone(auth_response)
        self.assertTrue(auth_response['args'][0]['success'])

        # Test invalid authentication
        invalid_auth_data = {'device_id': 'device_001', 'token': 'invalid_token'}
        self.socketio_client.emit('authenticate', invalid_auth_data)

        received = self.socketio_client.get_received()
        auth_response = None
        for event in received:
            if event['name'] == 'auth_response':
                auth_response = event
                break

        self.assertIsNotNone(auth_response)
        self.assertFalse(auth_response['args'][0]['success'])

    def test_data_storage_in_influxdb(self):
        """Test that IoT data is properly stored in InfluxDB"""
        with patch('flask_app.InfluxDBClient') as mock_influx_client:
            mock_write_api = MagicMock()
            mock_influx_client.return_value.write_api.return_value = mock_write_api

            # Create a new app instance to ensure the mock is used
            app = create_app()
            socketio_client = socketio.test_client(app, namespace='/')

            # Emit data from client (simulating device)
            test_data = {
                'device_id': 'test_device',
                'temperature': 23.5,
                'humidity': 65.0
            }
            socketio_client.emit('iot_data', test_data)

            # Verify that write_api.write was called with correct parameters
            mock_write_api.write.assert_called()

            # Get the actual call arguments
            call_args = mock_write_api.write.call_args
            self.assertIsNotNone(call_args)

            # Check bucket and org parameters
            self.assertEqual(call_args[1]['bucket'], 'iot_data')
            self.assertEqual(call_args[1]['org'], 'iot_org')

            socketio_client.disconnect()

    def test_error_handling_for_invalid_data(self):
        """Test error handling when invalid data is sent"""
        # Send invalid data (missing required fields)
        invalid_data = {'temperature': 23.5}  # Missing device_id
        self.socketio_client.emit('iot_data', invalid_data)

        received = self.socketio_client.get_received()
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break

        self.assertIsNotNone(error_event)
        self.assertIn('Missing device_id', error_event['args'][0]['message'])

    def test_websocket_disconnection(self):
        """Test client disconnection handling"""
        self.socketio_client.disconnect()
        self.assertFalse(self.socketio_client.is_connected())

if __name__ == '__main__':
    unittest.main()
