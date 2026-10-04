class VirtualCircuit:
    def __init__(self, vc_id: int = 1):
        self.vc_id = vc_id
        self.forwarding_table = {}
        self.path = ()

    def establish(self, paths):
        self.path = paths[0]
        self.forwarding_table = {("Source", self.vc_id): self.path[0], ("Router 1", self.vc_id): self.path[1], ("Router 2", self.vc_id): self.path[2]}
        return self.path

    def release(self):
        self.forwarding_table.clear()
        self.path = ()
