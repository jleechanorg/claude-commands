import os
import random
import time

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key')
socketio = SocketIO(app, cors_allowed_origins="*")

# InfluxDB configuration
INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'my-token')
INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG', 'iot_org')
INFLUXDB_BUCKET = os.environ.get('INFLUXDB_BUCKET', 'iot_data')

# Device authentication tokens (in production, this would be in a database)
DEVICE_TOKENS = {
    'device_001': 'valid_token_123',
    'device_002': 'valid_token_456',
    'device_003': 'valid_token_789'
}

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

@app.route('/')
def index():
    return render_template('websocket_client.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('authenticate')
def handle_authentication(data):
    device_id = data.get('device_id')
    token = data.get('token')

    if not device_id or not token:
        emit('auth_response', {'success': False, 'message': 'Missing device_id or token'})
        return

    if DEVICE_TOKENS.get(device_id) == token:
        emit('auth_response', {'success': True, 'message': f'Device {device_id} authenticated'})
    else:
        emit('auth_response', {'success': False, 'message': 'Invalid authentication token'})

@socketio.on('iot_data')
def handle_iot_data(data):
    # Validate required fields
    required_fields = ['device_id']
    for field in required_fields:
        if field not in data:
            emit('error', {'message': f'Missing {field} in data'})
            return

    # Add timestamp if not present
    if 'timestamp' not in data:
        data['timestamp'] = time.time()

    # Create InfluxDB point
    point = Point("iot_measurements") \
        .tag("device_id", data['device_id']) \
        .field("temperature", float(data.get('temperature', 0))) \
        .field("humidity", float(data.get('humidity', 0))) \
        .time(data['timestamp'])

    # Write to InfluxDB
    try:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        emit('data_stored', {'success': True, 'message': 'Data stored successfully'})
    except Exception as e:
        emit('error', {'message': f'Failed to store data: {str(e)}'})

def emit_mock_iot_data():
    """Emit mock IoT data for testing purposes"""
    mock_data = {
        'device_id': f'device_{random.randint(1, 10):03d}',
        'temperature': round(random.uniform(15.0, 35.0), 2),
        'humidity': round(random.uniform(30.0, 80.0), 2),
        'timestamp': time.time()
    }
    socketio.emit('iot_data', mock_data)

def background_data_emitter():
    """Background task to emit mock data periodically"""
    while True:
        socketio.sleep(5)  # Emit data every 5 seconds
        emit_mock_iot_data()

def create_app():
    """Application factory function"""
    # Start background task
    socketio.start_background_task(background_data_emitter)
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
