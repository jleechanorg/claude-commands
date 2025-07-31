# Enhanced A/B Test - API Design Challenge
def create_user_endpoint(user_data):
    # This API endpoint has several issues
    username = user_data.get("username")
    email = user_data.get("email")
    password = user_data.get("password")

    # Issue 1: No input validation
    # Issue 2: No security considerations
    # Issue 3: No error handling
    # Issue 4: Password stored in plain text
    # Issue 5: No duplicate prevention

    user = {
        "id": username,  # Bad: username as ID
        "username": username,
        "email": email,
        "password": password,  # Bad: plain text
        "created": "today",  # Bad: not a real timestamp
    }

    # Simulated database operation
    database.save(user)
    return user


# Task: Analyze this API endpoint and provide a secure, robust implementation
