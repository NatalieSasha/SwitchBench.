class PacketSwitching:
    setup_time = 0.0
    def path_for(self, packet_id, paths):
        return paths[packet_id % len(paths)]
