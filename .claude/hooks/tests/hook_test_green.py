def calculate_shipping_cost(weight, distance, express=False):
    """Calculate shipping cost based on weight, distance, and service level."""
    if not isinstance(weight, (int, float)) or weight <= 0:
        raise ValueError("Weight must be positive number")
    
    if not isinstance(distance, (int, float)) or distance <= 0:
        raise ValueError("Distance must be positive number")
    
    base_rate = 0.50 + (weight * 0.10) + (distance * 0.05)
    
    if express:
        base_rate *= 1.5
    
    return round(base_rate, 2)

class DatabaseConnection:
    def __init__(self, host, port, database):
        self.host = host
        self.port = port
        self.database = database
        self.connection = None
    
    def connect(self):
        try:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database
            )
            return self.connection
        except Exception as e:
            raise ConnectionError(f"Failed to connect: {e}")