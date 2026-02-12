#!/usr/bin/env python3
"""
Multipass Control Tool (mpc)
A tool for managing Multipass virtual machines
"""

import click
from utils import get_vm_list, filter_vms_by_name, get_vm_names, get_vm_list_plain
from k3s_operator import start_nodes, suspend_nodes, stop_nodes


@click.group()
def cli():
    """Multipass Control Tool (mpc) - Management tool for Multipass virtual machines"""
    pass


@cli.command()
def start():
    """Start all virtual machines (first main nodes, then worker nodes)"""
    start_nodes()


@cli.command()
def suspend():
    """Suspend all virtual machines (first worker nodes, then main nodes)"""
    suspend_nodes()


@cli.command()
def stop():
    """Stop all virtual machines (first worker nodes, then main nodes)"""
    stop_nodes()


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
