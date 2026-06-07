"""State manager for tracking robot state history."""


class StateManager:
    def __init__(self):
        self.history: list = []
        self.max_history: int = 100

    def record(self, state: dict):
        """Append state to history, trim to max_history."""
        self.history.append(state)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def last(self) -> dict | None:
        """Return most recent state or None."""
        return self.history[-1] if self.history else None
