import utils
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ClusterStatus(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PARTIAL = "partial"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ClusterResources:
    total_cpus: int = 0
    total_memory: str = "0G"
    total_disk: str = "0G"


class Cluster:
    def __init__(self, config_path: str = "config/cluster.yaml") -> None:
        self.config = utils.load_config(config_path)
        self.cluster_config = self.config.get("cluster", {})
        self.name = self.cluster_config.get("name", "k3s-cluster")
        self.description = self.cluster_config.get("description", "K3s Kubernetes Cluster")
        self.node_common_config_path = self.cluster_config.get("node_common_config", "k3s-cluster.base.yaml")
        self.inventory = self.cluster_config.get("inventory", {})
        
        self.nodes: Dict[str, Any] = {}
        self.controller_nodes: List[str] = []
        self.worker_nodes: List[str] = []
        self.resources = ClusterResources()
        self.status = ClusterStatus.INITIALIZING
        
        self._load_nodes()
        self._calculate_resources()
    
    def _load_nodes(self) -> None:
        """Load all nodes from inventory"""
        from .node import Node
        
        # Load controller nodes
        for controller_item in self.inventory.get("controller", []):
            for node_name, config_path in controller_item.items():
                node = Node.create_from_configs(
                    base_config_path=f"config/{self.node_common_config_path}",
                    node_config_path=f"config/{config_path}",
                    node_name=node_name
                )
                self.nodes[node_name] = node
                self.controller_nodes.append(node_name)
        
        # Load worker nodes
        for worker_item in self.inventory.get("worker", []):
            for node_name, config_path in worker_item.items():
                node = Node.create_from_configs(
                    base_config_path=f"config/{self.node_common_config_path}",
                    node_config_path=f"config/{config_path}",
                    node_name=node_name
                )
                self.nodes[node_name] = node
                self.worker_nodes.append(node_name)
    
    def _calculate_resources(self) -> None:
        """Calculate total cluster resources"""
        total_cpus = 0
        total_memory_gb = 0
        total_disk_gb = 0
        
        for node in self.nodes.values():
            total_cpus += node.resources.get("cpus", 0)
            
            # Parse memory (e.g., "4G" -> 4)
            memory_str = node.resources.get("memory", "0G")
            if memory_str.endswith("G"):
                total_memory_gb += int(memory_str[:-1])
            elif memory_str.endswith("M"):
                total_memory_gb += int(memory_str[:-1]) / 1024
            
            # Parse disk (e.g., "20G" -> 20)
            disk_str = node.resources.get("disk", "0G")
            if disk_str.endswith("G"):
                total_disk_gb += int(disk_str[:-1])
            elif disk_str.endswith("M"):
                total_disk_gb += int(disk_str[:-1]) / 1024
        
        self.resources = ClusterResources(
            total_cpus=total_cpus,
            total_memory=f"{total_memory_gb}G",
            total_disk=f"{total_disk_gb}G"
        )
    
    def get_node(self, node_name: str) -> Optional[Any]:
        """Get node by name"""
        return self.nodes.get(node_name)
    
    def get_nodes_by_type(self, node_type: str) -> List[str]:
        """Get nodes by type (controller/worker)"""
        if node_type == "controller":
            return self.controller_nodes
        elif node_type == "worker":
            return self.worker_nodes
        return []
    
    def update_cluster_status(self) -> None:
        """Update cluster status based on node status"""
        # TODO: Implement actual status checking
        self.status = ClusterStatus.RUNNING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cluster to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "resources": {
                "total_cpus": self.resources.total_cpus,
                "total_memory": self.resources.total_memory,
                "total_disk": self.resources.total_disk
            },
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
            "controller_nodes": self.controller_nodes,
            "worker_nodes": self.worker_nodes
        }


def create_cluster(config_path: str = "config/cluster.yaml") -> Cluster:
    """Factory function to create a cluster"""
    return Cluster(config_path)