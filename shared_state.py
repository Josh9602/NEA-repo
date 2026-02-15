class SharedState:
    """
    Manages shared state for UI layout calculations.
    Used by state configuration panels to coordinate vertical positioning.
    """
    def __init__(self):
        self.total = 0
        self.update_callback = None

shared = SharedState()