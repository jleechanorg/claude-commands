"""Simple hello module for pair programming session."""


def say_hello(name: str = "World") -> str:
    """Return a greeting message.

    Args:
        name: The name to greet

    Returns:
        A greeting string
    """
    return f"Hello, {name}!"
