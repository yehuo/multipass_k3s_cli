import src.utils as utils
import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class NodeStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    SUSPENDED = "suspended"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class NodeResources:
    cpus: int = 2
    memory: str = "2G"
    disk: str = "10G"


@dataclass
class NodeNetwork:
    bridged: bool = False
    extra_interfaces: Optional[List[str]] = None

    def __post_init__(self):
        if self.extra_interfaces is None:
            self.extra_interfaces = []


@dataclass
class NodeMount:
    source: str
    target: str
    readonly: bool = False


class Node:
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        self.name = name
        self.config = config
        
        # Extract node properties from config
        self.type = config.get("type", "worker")
        self.description = config.get("description", "K3s node")
        
        # Resources
        resources_config = config.get("resources", {})
        self.resources = {
            "cpus": resources_config.get("cpus", 2),
            "memory": resources_config.get("memory", "2G"),
            "disk": resources_config.get("disk", "10G")
        }
        
        # Network
        network_config = config.get("network", {})
        self.network = {
            "bridged": network_config.get("bridged", False),
            "extra_interfaces": network_config.get("extra_interfaces", [])
        }
        
        # Mounts
        self.mounts = config.get("mounts", [])
        
        # Image and cloud-init
        self.image = config.get("image", "22.04")
        self.cloud_init = config.get("cloud_init")
        
        # System settings
        self.system = config.get("system", {})
        
        # Status
        self.status = NodeStatus.UNKNOWN
    
    @classmethod
    def create_from_configs(cls, base_config_path: str, node_config_path: str, node_name: str) -> 'Node':
        """Create a node by merging base config with node-specific config"""
        # Load base configuration
        base_config = utils.load_config(base_config_path)
        base_defaults = base_config.get("default", {})
        
        # Load node-specific configuration
        node_config_list = utils.load_config(node_config_path)
        node_specific_config = {}
        
        # Find the specific node config in the list
        for node_config in node_config_list:
            if node_config.get("name") == node_name:
                node_specific_config = node_config
                break
        
        # Merge configurations (node-specific overrides base defaults)
        merged_config = utils.deep_merge(base_defaults, node_specific_config)
        
        # Generate the final config file in .generated directory
        generated_config = cls._generate_config_file(
            base_config_path, node_config_path, node_name, merged_config
        )
        
        return cls(node_name, generated_config)
    
    @staticmethod
    def _generate_config_file(base_config_path: str, node_config_path: str, 
                            node_name: str, merged_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the merged config file in .generated directory"""
        # Create .generated directory if it doesn't exist
        config_dir = os.path.dirname(node_config_path)
        generated_dir = os.path.join(config_dir, ".generated")
        os.makedirs(generated_dir, exist_ok=True)
        
        # Create the generated file path
        generated_file_path = os.path.join(generated_dir, f"{node_name}.yaml")
        
        # Write the merged config to the generated file
        with open(generated_file_path, 'w') as f:
            yaml.dump(merged_config, f, default_flow_style=False)
        
        print(f"Generated config: {generated_file_path}")
        return merged_config
    
    def build_multipass_command(self, global_config: Dict[str, Any]) -> List[str]:
        """Build multipass launch command for this node"""
        cmd = ["multipass", "launch"]
        cmd.extend(["--name", self.name])
        cmd.extend(["--cpus", str(self.resources["cpus"])])
        cmd.extend(["--memory", self.resources["memory"]])
        cmd.extend(["--disk", self.resources["disk"]])
        
        # Add image specification
        cmd.extend([self.image])
        
        # Add network configuration
        if self.network["bridged"]:
            cmd.extend(["--network", "name=bridge"])
        
        for interface in self.network["extra_interfaces"]:
            cmd.extend(["--network", interface])
        
        # Add mounts
        for mount in self.mounts:
            if isinstance(mount, dict):
                mount_cmd = f"{mount['source']}:{mount['target']}"
                if mount.get("readonly"):
                    mount_cmd += ":ro"
                cmd.extend(["--mount", mount_cmd])
        
        # Add cloud-init if specified
        if self.cloud_init:
            if utils.file_exists(self.cloud_init):
                cmd.extend(["--cloud-init", self.cloud_init])
            else:
                print(f"Warning: Cloud-init file {self.cloud_init} not found")
        
        return cmd
    
    def update_resources(self, cpus: Optional[int] = None, 
                       memory: Optional[str] = None, 
                       disk: Optional[str] = None) -> None:
        """Update node resources"""
        if cpus is not None:
            self.resources["cpus"] = cpus
        if memory is not None:
            self.resources["memory"] = memory
        if disk is not None:
            self.resources["disk"] = disk
    
    def add_mount(self, source: str, target: str, readonly: bool = False) -> None:
        """Add a mount point to the node"""
        mount = {"source": source, "target": target, "readonly": readonly}
        self.mounts.append(mount)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "resources": self.resources,
            "network": self.network,
            "mounts": self.mounts,
            "image": self.image,
            "cloud_init": self.cloud_init,
            "status": self.status.value,
            "system": self.system
        }
    
    def __str__(self) -> str:
        return f"Node(name={self.name}, type={self.type}, resources={self.resources})"


def create_node_from_config(config_path: str) -> Node:
    """Factory function to create a node from config file"""
    config = utils.load_config(config_path)
    node_name = config.get("name", "unknown-node")
    return Node(node_name, config)