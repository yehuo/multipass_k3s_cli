import utils
from typing import Dict, String

class nodeConfig:
    def __init__(self, node_config_path: str) -> None:
        self.raw_config=utils.load_config(node_config_path)
        self.os = self.raw_config.os
        self.resources = {}
        self.network = {}
        self.mounts = []
    def update_resources(self, cpus: int, memory: str, disk: str) -> None:
        self.resources = {"cpus": cpus, "memory": memory, "disk": disk}