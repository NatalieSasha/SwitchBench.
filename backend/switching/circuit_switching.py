class CircuitSwitching:
    """Reserves every link on one selected route for the connection lifetime."""
    def __init__(self):
        self.reserved_links = []
        self.established = False

    def establish(self, paths, links, bandwidth):
        path = paths[0]
        if any(links[name].reserved_by is not None or links[name].bandwidth < bandwidth for name in path):
            raise ValueError("Circuit resources are unavailable")
        for name in path:
            links[name].reserved_by = "circuit-1"
        self.reserved_links = list(path)
        self.established = True
        return path

    def release(self, links):
        for name in self.reserved_links:
            links[name].reserved_by = None
        self.established = False
