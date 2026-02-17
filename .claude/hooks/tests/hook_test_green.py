def calculate_shipping_cost(weight, distance, express=False):
    """Calculate shipping cost based on weight, distance, and service level."""
    if not isinstance(weight, int | float) or weight <= 0:
        raise ValueError("Weight must be positive number")

    if not isinstance(distance, int | float) or distance <= 0:
        raise ValueError("Distance must be positive number")

    base_rate = 0.50 + (weight * 0.10) + (distance * 0.05)

    if express:
        base_rate *= 1.5

    return round(base_rate, 2)
