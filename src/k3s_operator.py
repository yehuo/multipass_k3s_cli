#!/usr/bin/env python3
"""
K3s Operator - Node management functions for starting, stopping, and managing K3s nodes
"""

import time
import click
from typing import List
from utils import get_vm_list, filter_vms_by_name, get_vm_names, run_command

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

def start_nodes():
    """Start all virtual machines (first main nodes, then worker nodes)"""
    click.echo("Getting virtual machine list...")
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return

    # Separate main and worker nodes
    main_vms = filter_vms_by_name(vms, "main")
    worker_vms = filter_vms_by_name(vms, "worker")

    # Start main nodes
    if main_vms:
        main_names = get_vm_names(main_vms)
        if not operate_vms(main_names, "start", "main"):
            return

        # Wait for main nodes to start
        click.echo("\nWaiting for main nodes to start...")
        time.sleep(3)

        if not wait_for_confirmation("Main nodes are started. Continue starting worker nodes?"):
            click.echo("Cancelled starting worker nodes")
            return

    # Start worker nodes
    if worker_vms:
        worker_names = get_vm_names(worker_vms)
        operate_vms(worker_names, "start", "worker")
    else:
        click.echo("No worker nodes found")

    click.echo("\n✅ Start operation completed")

def suspend_nodes():
    """Suspend all virtual machines (first worker nodes, then main nodes)"""
    click.echo("Getting virtual machine list...")
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return

    # Separate main and worker nodes
    main_vms = filter_vms_by_name(vms, "main")
    worker_vms = filter_vms_by_name(vms, "worker")

    # Suspend worker nodes
    if worker_vms:
        worker_names = get_vm_names(worker_vms)
        if not operate_vms(worker_names, "suspend", "worker"):
            return

        # Wait for worker nodes to suspend
        click.echo("\nWaiting for worker nodes to suspend...")
        time.sleep(2)

        if not wait_for_confirmation("Worker nodes are suspended. Continue suspending main nodes?"):
            click.echo("Cancelled suspending main nodes")
            return

    # Suspend main nodes
    if main_vms:
        main_names = get_vm_names(main_vms)
        operate_vms(main_names, "suspend", "main")
    else:
        click.echo("No main nodes found")

    click.echo("\n✅ Suspend operation completed")

def stop_nodes():
    """Stop all virtual machines (first worker nodes, then main nodes)"""
    click.echo("Getting virtual machine list...")
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return

    # Separate main and worker nodes
    main_vms = filter_vms_by_name(vms, "main")
    worker_vms = filter_vms_by_name(vms, "worker")

    # Stop worker nodes
    if worker_vms:
        worker_names = get_vm_names(worker_vms)
        if not operate_vms(worker_names, "stop", "worker"):
            return

        # Wait for worker nodes to stop
        click.echo("\nWaiting for worker nodes to stop...")
        time.sleep(2)

        if not wait_for_confirmation("Worker nodes are stopped. Continue stopping main nodes?"):
            click.echo("Cancelled stopping main nodes")
            return

    # Stop main nodes
    if main_vms:
        main_names = get_vm_names(main_vms)
        operate_vms(main_names, "stop", "main")
    else:
        click.echo("No main nodes found")

    click.echo("\n✅ Stop operation completed")