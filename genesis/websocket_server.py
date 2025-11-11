import logging
import random
import threading
import time

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from influx import get_tenant_bucket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active client connections by tenant
active_connections = {}

def generate_mock_iot_data(tenant_id):
    """Generate mock IoT sensor data for a tenant"""
    while True:
        try:
            if tenant_id in active_connections and active_connections[tenant_id]:
                data = {
                    'timestamp': time.time(),
                    'sensor_id': f'sensor_{random.randint(1, 100)}',
                    'temperature': round(random.uniform(15.0, 35.0), 2),
                    'humidity': round(random.uniform(30.0, 80.0), 2),
                    'pressure': round(random.uniform(950.0, 1050.0), 2)
                }

                # Get tenant-specific bucket
                try:
                    bucket = get_tenant_bucket(tenant_id)
                    if bucket:
                        # In a real implementation, you would write to InfluxDB here
                        # bucket.write(...data...)
                        pass
                except Exception as e:
                    logger.warning(f"Could not access InfluxDB for tenant {tenant_id}: {e}")

                # Broadcast to all connected clients for this tenant
                socketio.emit('iot_data', data, room=tenant_id)

            time.sleep(1)  # Generate data every second
        except Exception as e:
            logger.error(f"Error generating mock data for tenant {tenant_id}: {e}")
            break

@socketio.on('connect')
def handle_connect():
    """Handle new client connections"""
    tenant_id = None
    try:
        # In a real implementation, you would authenticate the client and extract tenant_id
        # For this example, we'll use a default tenant
        tenant_id = 'default_tenant'

        # Add client to tenant room
        join_room(tenant_id)

        # Initialize tenant connections tracking if needed
        if tenant_id not in active_connections:
            active_connections[tenant_id] = []

        # Add client to active connections
        active_connections[tenant_id].append(request.sid)
        logger.info(f"Client connected to tenant {tenant_id}. Total connections: {len(active_connections[tenant_id])}")

        # Start background task for this tenant if it's the first connection
        if len(active_connections[tenant_id]) == 1:
            thread = threading.Thread(target=generate_mock_iot_data, args=(tenant_id,))
            thread.daemon = True
            thread.start()

        emit('connected', {'tenant_id': tenant_id})
    except Exception as e:
        logger.error(f"Error handling connect event: {e}")
        emit('error', {'message': 'Connection failed'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    try:
        # Remove client from active connections
        for tenant_id, connections in active_connections.items():
            if request.sid in connections:
                connections.remove(request.sid)
                logger.info(f"Client disconnected from tenant {tenant_id}. Remaining connections: {len(connections)}")

                # Stop background task if no more connections for this tenant
                if len(connections) == 0 and tenant_id in active_connections:
                    del active_connections[tenant_id]
                break
    except Exception as e:
        logger.error(f"Error handling disconnect event: {e}")

@socketio.on('join_tenant')
def handle_join_tenant(data):
    """Handle tenant joining requests"""
    try:
        tenant_id = data.get('tenant_id')
        if not tenant_id:
            emit('error', {'message': 'Missing tenant_id'})
            return

        # Leave current room if in one
        for room in request.rooms:
            if room != request.sid:  # Don't leave the default room
                leave_room(room)

        # Join new tenant room
        join_room(tenant_id)

        # Update active connections
        if tenant_id not in active_connections:
            active_connections[tenant_id] = []
        active_connections[tenant_id].append(request.sid)

        logger.info(f"Client joined tenant {tenant_id}")
        emit('tenant_joined', {'tenant_id': tenant_id})
    except Exception as e:
        logger.error(f"Error handling join_tenant event: {e}")
        emit('error', {'message': 'Failed to join tenant'})

@app.route('/')
def index():
    """Serve the WebSocket client test page"""
    return render_template('websocket_client.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
