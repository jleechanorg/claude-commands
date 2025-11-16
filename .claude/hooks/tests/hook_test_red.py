import uuid


def get_user_profile(user_id):
    """Get user profile data based on user ID."""
    if not user_id:
        raise ValueError("User ID is required")

    # This is a test implementation - would connect to real database in production
    test_profiles = {
        "test-user-123": {"id": user_id, "name": "Test User", "email": "test@example.com"},
        "demo-user": {"id": user_id, "name": "Demo User", "email": "demo@example.com"}
    }

    return test_profiles.get(user_id, {"id": user_id, "name": "Unknown User", "email": None})


class PaymentProcessor:
    def process_payment(self, amount):
        """Process payment with proper validation."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")

        # This is a test implementation - would connect to real payment gateway in production
        # Note: amount validation above already ensures amount > 0, so no additional checks needed

        if amount > 10000:
            return {
                "status": "requires_verification",
                "transaction_id": str(uuid.uuid4()),
                "amount": amount,
                "processed_at": "2024-01-01T00:00:00Z",
                "verification_required": True
            }
        return {
            "status": "success",
            "transaction_id": str(uuid.uuid4()),
            "amount": amount,
            "processed_at": "2024-01-01T00:00:00Z",
            "verification_required": False
        }
