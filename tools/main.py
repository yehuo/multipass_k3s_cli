#!/usr/bin/env python3
"""
Multipass Control Tool (mpc)
A tool for managing Multipass virtual machines
"""

import click
import subprocess
import json
import time
from typing import List, Dict, Tuple
import sys


def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Execute a command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def get_vm_list() -> List[Dict]:
    """Get list of all virtual machines"""
    success, output = run_command(["multipass", "list", "--format", "json"])
    if not success:
        click.echo("Error: Unable to get virtual machine list", err=True)
        return []

    try:
        data = json.loads(output)
        return data.get("list", [])
    except json.JSONDecodeError:
        click.echo("Error: Unable to parse virtual machine list", err=True)
        return []


def get_vm_list_plain() -> str:
    """Get raw output from multipass list command"""
    success, output = run_command(["multipass", "list"])
    if success:
        return output
    return "Error: Unable to get virtual machine status"


def filter_vms_by_name(vms: List[Dict], keyword: str) -> List[Dict]:
    """Filter virtual machines by name keyword"""
    return [vm for vm in vms if keyword.lower() in vm["name"].lower()]


def get_vm_names(vms: List[Dict]) -> List[str]:
    """Extract names from list of virtual machine dictionaries"""
    return [vm["name"] for vm in vms]


def wait_for_confirmation(message: str) -> bool:
    """Wait for user confirmation"""
    return click.confirm(message, default=True)


def operate_vms(vm_names: List[str], operation: str, vm_type: str = "") -> bool:
    """Perform an operation on a group of virtual machines"""
    if not vm_names:
        click.echo(f"No {vm_type} nodes found")
        return True

    click.echo(
        f"\nPreparing to {operation} {vm_type} nodes: {', '.join(vm_names)}")

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
        click.echo(
            f"✗ Failed to {operation} {vm_type} nodes: {output}", err=True)
        return False


@click.group()
def cli():
    """Multipass Control Tool (mpc) - Management tool for Multipass virtual machines"""
    pass


@cli.command()
def start():
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


@cli.command()
def suspend():
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


@cli.command()
def stop():
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


@cli.command()
@click.option('--all', '-a', is_flag=True, help='Show status of all nodes')
@click.option('--main', '-m', is_flag=True, help='Show only main nodes')
@click.option('--worker', '-w', is_flag=True, help='Show only worker nodes')
def status(all, main, worker):
    """Check virtual machine status"""
    click.echo("Getting virtual machine status...")

    # Get plain output from multipass list for better formatting
    plain_output = get_vm_list_plain()

    # Also get structured data for filtering if needed
    vms = get_vm_list()

    if not vms:
        click.echo("No virtual machines found")
        return

    # Apply filters if specified
    if main or worker:
        if main:
            vms = filter_vms_by_name(vms, "main")
            title = "MAIN NODES STATUS:"
        else:
            vms = filter_vms_by_name(vms, "worker")
            title = "WORKER NODES STATUS:"

        if not vms:
            click.echo(f"No matching virtual machines found")
            return

        # Show filtered view with table
        click.echo(f"\n{title}")
        click.echo("-" * 80)
        click.echo(f"{'Name':<20} {'State':<15} {'IPv4':<30} {'Image':<20}")
        click.echo("-" * 80)

        for vm in vms:
            name = vm.get("name", "Unknown")
            state = vm.get("state", "Unknown")

            # Handle IPv4 addresses - show first one or indicate none
            ipv4_list = vm.get("ipv4", [])
            if ipv4_list:
                # Show first IP and indicate if there are more
                ipv4_display = ipv4_list[0]
                if len(ipv4_list) > 1:
                    ipv4_display += f" (+{len(ipv4_list)-1} more)"
            else:
                ipv4_display = "No IP address"

            # Get image information
            image = vm.get("image", "Unknown image")

            click.echo(
                f"{name:<20} {state:<15} {ipv4_display:<30} {image:<20}")

        click.echo("-" * 80)
        click.echo(f"Total: {len(vms)} virtual machine(s)")
    else:
        # Show all virtual machines with raw multipass list output
        click.echo(plain_output)


if __name__ == "__main__":
    cli()
