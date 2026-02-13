#!/usr/bin/env python3
"""
Cluster Operator - Cluster management functions for starting, stopping, and managing Kubernetes clusters
Supports multiple cluster types (K3s, K8s, etc.)
"""

import time
import click
from typing import List, Dict, Optional
from utils import get_vm_list, filter_vms_by_name, get_vm_names, run_command
from node_operator import get_node_info, get_node_status

def wait_for_confirmation(message: str) -> bool:
    """Wait for user confirmation"""
    return click.confirm(message, default=True)

def operate_vms(vm_names: List[str], operation: str, vm_type: str = "") -> bool:
    """Perform an operation on a group of virtual machines"""
    if not vm_names:
        click.echo(f"No {vm_type} nodes found")
        return True

    click.echo(f"\nPreparing to {operation} {vm_type} nodes: {', '.join(vm_names)}")

    # Map operation to multipass command
    operation_map = {
        "start": "start",
        "suspend": "suspend",
        "stop": "stop"
    }

    if operation not in operation_map:
        click.echo(f"Error: Unsupported operation {operation}", err=True)
        return False

    cmd = operation_map[operation]

    # Execute command
    success, output = run_command(["multipass", cmd] + vm_names)

    if success:
        click.echo(f"✓ Successfully {operation}ed {vm_type} nodes")
        return True
    else:
        click.echo(f"✗ Failed to {operation} {vm_type} nodes: {output}", err=True)
        return False

def start_cluster(cluster_type: str = "k3s") -> bool:
    """
    Start a Kubernetes cluster
    
    Args:
        cluster_type: Type of cluster to start (k3s, k8s, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    click.echo(f"Starting {cluster_type.upper()} cluster...")
    click.echo("Getting virtual machine list...")
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return False

    # Separate control plane and worker nodes based on cluster type
    if cluster_type == "k3s":
        control_plane_vms = filter_vms_by_name(vms, "main")
        worker_vms = filter_vms_by_name(vms, "worker")
    else:
        # For other cluster types, use different naming patterns
        control_plane_vms = filter_vms_by_name(vms, "control")
        worker_vms = filter_vms_by_name(vms, "worker")

    # Start control plane nodes
    if control_plane_vms:
        control_names = get_vm_names(control_plane_vms)
        if not operate_vms(control_names, "start", "control-plane"):
            return False

        # Wait for control plane nodes to start
        click.echo("\nWaiting for control plane nodes to start...")
        time.sleep(5)

        if not wait_for_confirmation("Control plane nodes are started. Continue starting worker nodes?"):
            click.echo("Cancelled starting worker nodes")
            return True

    # Start worker nodes
    if worker_vms:
        worker_names = get_vm_names(worker_vms)
        if not operate_vms(worker_names, "start", "worker"):
            return False
    else:
        click.echo("No worker nodes found")

    click.echo(f"\n✅ {cluster_type.upper()} cluster start operation completed")
    return True

def suspend_cluster(cluster_type: str = "k3s") -> bool:
    """
    Suspend a Kubernetes cluster
    
    Args:
        cluster_type: Type of cluster to suspend (k3s, k8s, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    click.echo(f"Suspending {cluster_type.upper()} cluster...")
    click.echo("Getting virtual machine list...")
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return False

    # Separate control plane and worker nodes based on cluster type
    if cluster_type == "k3s":
        control_plane_vms = filter_vms_by_name(vms, "main")
        worker_vms = filter_vms_by_name(vms, "worker")
    else:
        control_plane_vms = filter_vms_by_name(vms, "control")
        worker_vms = filter_vms_by_name(vms, "worker")

    # Suspend worker nodes
    if worker_vms:
        worker_names = get_vm_names(worker_vms)
        if not operate_vms(worker_names, "suspend", "worker"):
            return False

        # Wait for worker nodes to suspend
        click.echo("\nWaiting for worker nodes to suspend...")
        time.sleep(3)

        if not wait_for_confirmation("Worker nodes are suspended. Continue suspending control plane nodes?"):
            click.echo("Cancelled suspending control plane nodes")
            return True

    # Suspend control plane nodes
    if control_plane_vms:
        control_names = get_vm_names(control_plane_vms)
        if not operate_vms(control_names, "suspend", "control-plane"):
            return False
    else:
        click.echo("No control plane nodes found")

    click.echo(f"\n✅ {cluster_type.upper()} cluster suspend operation completed")
    return True

def stop_cluster(cluster_type: str = "k3s") -> bool:
    """
    Stop a Kubernetes cluster
    
    Args:
        cluster_type: Type of cluster to stop (k3s, k8s, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    click.echo(f"Stopping {cluster_type.upper()} cluster...")
    click.echo("Getting virtual machine list...")
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return False

    # Separate control plane and worker nodes based on cluster type
    if cluster_type == "k3s":
        control_plane_vms = filter_vms_by_name(vms, "main")
        worker_vms = filter_vms_by_name(vms, "worker")
    else:
        control_plane_vms = filter_vms_by_name(vms, "control")
        worker_vms = filter_vms_by_name(vms, "worker")

    # Stop worker nodes
    if worker_vms:
        worker_names = get_vm_names(worker_vms)
        if not operate_vms(worker_names, "stop", "worker"):
            return False

        # Wait for worker nodes to stop
        click.echo("\nWaiting for worker nodes to stop...")
        time.sleep(3)

        if not wait_for_confirmation("Worker nodes are stopped. Continue stopping control plane nodes?"):
            click.echo("Cancelled stopping control plane nodes")
            return True

    # Stop control plane nodes
    if control_plane_vms:
        control_names = get_vm_names(control_plane_vms)
        if not operate_vms(control_names, "stop", "control-plane"):
            return False
    else:
        click.echo("No control plane nodes found")

    click.echo(f"\n✅ {cluster_type.upper()} cluster stop operation completed")
    return True