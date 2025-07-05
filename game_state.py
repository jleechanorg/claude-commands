class GameState:
    """Simple container for game state data used in tests."""
    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data
