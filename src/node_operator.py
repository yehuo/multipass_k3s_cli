#!/usr/bin/env python3
"""
Node Operator - Virtual machine provisioning and management functions
Handles creation, deletion, and management of individual nodes
"""

import os
import time
import click
from typing import Dict, List, Optional, Any
from utils import run_command, deep_merge, load_config


def create_node(node_config: Dict[str, Any], global_config: Dict[str, Any]) -> bool:
    """
    Create a single virtual machine node using multipass
    
    Args:
        node_config: Node-specific configuration
        global_config: Global cluster configuration
        
    Returns:
        True if successful, False otherwise
    """
    node_name = node_config.get("name", "unknown-node")
    
    # Build multipass launch command
    cmd = ["multipass", "launch"]
    cmd.extend(["--name", node_name])
    
    # Add resource specifications
    resources = node_config.get("resources", {})
    cmd.extend(["--cpus", str(resources.get("cpus", 2))])
    cmd.extend(["--memory", resources.get("memory", "2G")])
    cmd.extend(["--disk", resources.get("disk", "10G")])
    
    # Add image specification
    cmd.extend([node_config.get("image", "22.04")])
    
    # Add network configuration
    network = node_config.get("network", {})
    if network.get("bridged", False):
        cmd.extend(["--network", "name=bridge"])
    
    for interface in network.get("extra_interfaces", []):
        cmd.extend(["--network", interface])
    
    # Add mounts
    for mount in node_config.get("mounts", []):
        if isinstance(mount, dict):
            mount_cmd = f"{mount['source']}:{mount['target']}"
            if mount.get("readonly"):
                mount_cmd += ":ro"
            cmd.extend(["--mount", mount_cmd])
    
    # Add cloud-init if specified
    cloud_init = node_config.get("cloud_init")
    if cloud_init and os.path.exists(cloud_init):
        cmd.extend(["--cloud-init", cloud_init])
    
    click.echo(f"Creating node {node_name}...")
    click.echo(f"Command: {' '.join(cmd)}")
    
    # Execute the command
    success, output = run_command(cmd)
    
    if success:
        click.echo(f"✓ Successfully created node {node_name}")
        
        # Execute post-creation scripts
        execute_post_creation_scripts(node_config, node_name)
        
        return True
    else:
        click.echo(f"✗ Failed to create node {node_name}: {output}", err=True)
        return False


def execute_post_creation_scripts(node_config: Dict[str, Any], node_name: str) -> None:
    """Execute post-creation scripts on the node"""
    system_config = node_config.get("system", {})
    scripts = system_config.get("post_creation_scripts", [])
    
    for script_path in scripts:
        if os.path.exists(script_path):
            click.echo(f"Executing post-creation script: {script_path}")
            
            # Copy script to node and execute
            copy_cmd = ["multipass", "transfer", script_path, f"{node_name}:/tmp/"]
            run_command(copy_cmd)
            
            # Make script executable and run
            script_name = os.path.basename(script_path)
            exec_cmd = [
                "multipass", "exec", node_name, 
                "--", "bash", "-c", f"chmod +x /tmp/{script_name} && /tmp/{script_name}"
            ]
            
            success, output = run_command(exec_cmd)
            if success:
                click.echo(f"✓ Successfully executed {script_name}")
            else:
                click.echo(f"✗ Failed to execute {script_name}: {output}", err=True)


def delete_node(node_name: str, force: bool = False) -> bool:
    """
    Delete a virtual machine node
    
    Args:
        node_name: Name of the node to delete
        force: Whether to force deletion without confirmation
        
    Returns:
        True if successful, False otherwise
    """
    if not force:
        if not click.confirm(f"Are you sure you want to delete node '{node_name}'?"):
            click.echo("Deletion cancelled")
            return False
    
    click.echo(f"Deleting node {node_name}...")
    
    # Stop the node first if it's running
    run_command(["multipass", "stop", node_name])
    
    # Delete the node
    success, output = run_command(["multipass", "delete", "--purge", node_name])
    
    if success:
        click.echo(f"✓ Successfully deleted node {node_name}")
        return True
    else:
        click.echo(f"✗ Failed to delete node {node_name}: {output}", err=True)
        return False


def get_node_info(node_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a node
    
    Args:
        node_name: Name of the node
        
    Returns:
        Dictionary with node information, or None if not found
    """
    success, output = run_command(["multipass", "info", node_name, "--format", "json"])
    
    if success:
        try:
            import json
            info = json.loads(output)
            return info.get("info", {}).get(node_name, {})
        except json.JSONDecodeError:
            return None
    
    return None


def list_nodes() -> List[Dict[str, Any]]:
    """
    List all virtual machine nodes
    
    Returns:
        List of node information dictionaries
    """
    success, output = run_command(["multipass", "list", "--format", "json"])
    
    if success:
        try:
            import json
            data = json.loads(output)
            return data.get("list", [])
        except json.JSONDecodeError:
            return []
    
    return []

def get_node_status(node_name: str) -> str:
    """
    Get the status of a specific node
    
    Args:
        node_name: Name of the node
        
    Returns:
        Node status ("running", "stopped", "suspended", "deleted", or "unknown")
    """
    info = get_node_info(node_name)
    if info:
        return info.get("state", "unknown")
    return "deleted"


def wait_for_node_status(node_name: str, target_status: str, timeout: int = 60) -> bool:
    """
    Wait for a node to reach a specific status
    
    Args:
        node_name: Name of the node
        target_status: Desired status to wait for
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if status reached, False if timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        current_status = get_node_status(node_name)
        
        if current_status == target_status:
            return True
        
        time.sleep(2)
    
    return False


def execute_on_node(node_name: str, command: str) -> bool:
    """
    Execute a command on a node
    
    Args:
        node_name: Name of the node
        command: Command to execute
        
    Returns:
        True if successful, False otherwise
    """
    cmd = ["multipass", "exec", node_name, "--"] + command.split()
    
    success, output = run_command(cmd)
    
    if success:
        click.echo(f"✓ Command executed successfully on {node_name}")
        click.echo(output)
    else:
        click.echo(f"✗ Failed to execute command on {node_name}: {output}", err=True)
    
    return success