#!/usr/bin/env python3
"""
Multipass VM Provisioner
Reads YAML configuration and creates virtual machines using Multipass
"""

import subprocess
import os
import sys, yaml
from pathlib import Path
import click

from utils import load_config, execute


def build_multipass_command(vm_config, global_config):
    """Build multipass launch command for a VM"""
    cmd = ["multipass", "launch"]
    
    # Set VM name
    cmd.extend(["--name", vm_config.get('name', 'unnamed-vm')])
    
    # Set CPU cores (use VM-specific or global default)
    cpus = vm_config.get('resources', {}).get('cpus', 
               global_config.get('resources', {}).get('cpus', 2))
    cmd.extend(["--cpus", str(cpus)])
    
    # Set memory (use VM-specific or global default)
    memory = vm_config.get('resources', {}).get('memory',
                global_config.get('resources', {}).get('memory', '4G'))
    cmd.extend(["--memory", memory])
    
    # Set disk size (use VM-specific or global default)
    disk = vm_config.get('resources', {}).get('disk',
              global_config.get('resources', {}).get('disk', '20G'))
    cmd.extend(["--disk", disk])
    
    # Set image (use VM-specific or global default)
    image = vm_config.get('image', global_config.get('base_image', '22.04'))
    cmd.append(image)
    
    # Add cloud-init configuration if specified
    cloud_init = vm_config.get('cloud_init')
    if cloud_init and os.path.exists(cloud_init):
        cmd.extend(["--cloud-init", cloud_init])
    
    # Add mounts if specified
    mounts = vm_config.get('mounts', [])
    for mount in mounts:
        source = mount.get('source')
        target = mount.get('target')
        if source and target:
            cmd.extend(["--mount", f"{source}:{target}"])
    
    # Add bridged network if enabled
    if vm_config.get('network', {}).get('bridged', False):
        cmd.append("--bridged")
    
    # Add any extra options
    extra_options = vm_config.get('extra_options', [])
    for option in extra_options:
        cmd.append(option)
    
    return cmd

def create_virtual_machines(config):
    """Create virtual machines based on configuration"""
    global_config = config.get('global', {})
    vms = config.get('virtual_machines', [])
    
    if not vms:
        print("No virtual machines defined in configuration")
        return
    
    print(f"Found {len(vms)} virtual machine(s) to create")
    
    for i, vm in enumerate(vms, 1):
        name = vm.get('name', f'vm-{i}')
        vm_type = vm.get('type', 'unknown')
        description = vm.get('description', '')
        
        print(f"\n{'='*60}")
        print(f"Creating VM {i}/{len(vms)}:")
        print(f"  Name: {name}")
        print(f"  Type: {vm_type}")
        if description:
            print(f"  Description: {description}")
        print(f"{'='*60}")
        
        # Build and execute multipass command
        cmd = build_multipass_command(vm, global_config)
        print(f"Command: {' '.join(cmd)}")
        
        # Ask for confirmation
        if click.confirm("Proceed with VM creation?"):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"✓ Successfully created VM: {name}")
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to create VM {name}:")
                print(f"Error: {e.stderr}")
                if click.confirm("Continue with next VM?"):
                    continue
                else:
                    print("Aborting...")
                    break
        else:
            print(f"Skipping VM: {name}")
    
    print("\n" + "="*60)
    print("VM creation process completed!")
    print("="*60)

def update_hosts_file(config):
    """Update /etc/hosts with VM IP addresses (Linux/macOS)"""
    if not config.get('cluster', {}).get('hosts_file_update', False):
        return
    
    print("\nUpdating /etc/hosts with VM IP addresses...")
    
    # Get list of running VMs and their IPs
    try:
        result = subprocess.run(
            ["multipass", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        import json
        vm_data = json.loads(result.stdout)
        
        hosts_entries = []
        for vm in vm_data.get('list', []):
            name = vm.get('name')
            ipv4 = vm.get('ipv4', [])
            if name and ipv4:
                # Use the first IPv4 address
                primary_ip = ipv4[0]
                hosts_entries.append(f"{primary_ip}\t{name}")
        
        if hosts_entries:
            # This part requires sudo privileges
            hosts_content = "\n".join(hosts_entries)
            print(f"Hosts entries to add:\n{hosts_content}")
            
            if click.confirm("Update /etc/hosts? (requires sudo)"):
                try:
                    subprocess.run(
                        ["sudo", "bash", "-c", f'echo "{hosts_content}" >> /etc/hosts'],
                        check=True
                    )
                    print("✓ /etc/hosts updated successfully")
                except subprocess.CalledProcessError:
                    print("✗ Failed to update /etc/hosts (permission denied)")
    
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Warning: Could not update /etc/hosts: {e}")

@click.command()
@click.option('--config', '-c', default='multipass-config.yaml',
              help='Path to configuration YAML file')
@click.option('--dry-run', '-d', is_flag=True,
              help='Show commands without executing')
@click.option('--skip-hosts', is_flag=True,
              help='Skip updating /etc/hosts file')
def main(config, dry_run, skip_hosts):
    """Provision virtual machines using Multipass based on YAML configuration"""
    
    print("="*60)
    print("Multipass VM Provisioner")
    print("="*60)
    
    # Load configuration
    print(f"Loading configuration from: {config}")
    config_data = load_config(config)
    
    # Show configuration summary
    vms = config_data.get('virtual_machines', [])
    main_nodes = [vm for vm in vms if vm.get('type') == 'main']
    worker_nodes = [vm for vm in vms if vm.get('type') == 'worker']
    other_nodes = [vm for vm in vms if vm.get('type') not in ['main', 'worker']]
    
    print(f"\nConfiguration Summary:")
    print(f"  Total VMs: {len(vms)}")
    print(f"  Main nodes: {len(main_nodes)}")
    print(f"  Worker nodes: {len(worker_nodes)}")
    print(f"  Other nodes: {len(other_nodes)}")
    
    if dry_run:
        print("\nDRY RUN MODE - Commands will not be executed")
        global_config = config_data.get('global', {})
        for i, vm in enumerate(vms, 1):
            cmd = build_multipass_command(vm, global_config)
            print(f"\nVM {i}: {vm.get('name')}")
            print(f"  Command: {' '.join(cmd)}")
        return
    
    # Create virtual machines
    create_virtual_machines(config_data)
    
    # Update /etc/hosts if requested
    if not skip_hosts:
        update_hosts_file(config_data)
    
    # Show final status
    print("\nFinal VM Status:")
    subprocess.run(["multipass", "list"])

if __name__ == "__main__":
    main()