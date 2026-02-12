#!/usr/bin/env python3
"""
Enhanced Multipass VM Provisioner
Reads common.yaml and node-specific configurations, merges them, and creates virtual machines
"""

import os
import yaml
import subprocess
import click
from pathlib import Path
from typing import Dict, List, Any
from utils import load_config, execute

def merge_configs(common_config: Dict, node_config: Dict) -> Dict:
    """Merge common configuration with node-specific configuration"""
    merged = common_config.copy()
    
    # Deep merge for nested dictionaries
    for key, value in node_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_configs(merged[key], value)
        else:
            # Override with node-specific value
            merged[key] = value
    
    return merged

def load_node_configs(common_config: Dict) -> List[Dict]:
    """Load all node configurations from inventory and merge with common defaults"""
    inventory = common_config.get('inventory', [])
    node_defaults = common_config.get('node_defaults', {})
    
    nodes = []
    
    for item in inventory:
        for node_name, config_path in item.items():
            try:
                # Load node-specific configuration
                node_config_path = os.path.join('config', config_path)
                node_config = load_config(node_config_path)
                
                # Extract node configuration from the nodes list
                node_data = node_config.get('nodes', [{}])[0]
                
                # Ensure node has a name
                if 'name' not in node_data:
                    node_data['name'] = node_name
                
                # Merge with common defaults
                merged_config = merge_configs(node_defaults, node_data)
                nodes.append(merged_config)
                
            except Exception as e:
                click.echo(f"Error loading node config for {node_name}: {e}", err=True)
    
    return nodes

def build_multipass_command(vm_config: Dict, global_config: Dict) -> List[str]:
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

def create_virtual_machines(common_config: Dict, dry_run: bool = False) -> bool:
    """Create virtual machines based on merged configuration"""
    global_config = common_config.get('global', {})
    
    # Load and merge all node configurations
    nodes = load_node_configs(common_config)
    
    if not nodes:
        click.echo("No virtual machines defined in configuration")
        return False
    
    click.echo(f"Found {len(nodes)} virtual machine(s) to create")
    
    success_count = 0
    
    for i, vm_config in enumerate(nodes, 1):
        name = vm_config.get('name', f'vm-{i}')
        vm_type = vm_config.get('type', 'unknown')
        description = vm_config.get('description', '')
        
        click.echo(f"\n{'='*60}")
        click.echo(f"Creating VM {i}/{len(nodes)}:")
        click.echo(f"  Name: {name}")
        click.echo(f"  Type: {vm_type}")
        if description:
            click.echo(f"  Description: {description}")
        click.echo(f"{'='*60}")
        
        # Build and execute multipass command
        cmd = build_multipass_command(vm_config, global_config)
        click.echo(f"Command: {' '.join(cmd)}")
        
        if dry_run:
            click.echo("✓ Dry run - command not executed")
            success_count += 1
            continue
        
        # Ask for confirmation
        if click.confirm("Proceed with VM creation?"):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                click.echo(f"✓ Successfully created VM: {name}")
                click.echo(result.stdout)
                success_count += 1
            except subprocess.CalledProcessError as e:
                click.echo(f"✗ Failed to create VM {name}:", err=True)
                click.echo(f"Error: {e.stderr}", err=True)
                if click.confirm("Continue with next VM?"):
                    continue
                else:
                    click.echo("Aborting...")
                    break
        else:
            click.echo(f"Skipping VM: {name}")
    
    click.echo("\n" + "="*60)
    click.echo(f"VM creation process completed! ({success_count}/{len(nodes)} successful)")
    click.echo("="*60)
    
    return success_count == len(nodes)

def generate_config_files(common_config: Dict, output_dir: str = "generated") -> None:
    """Generate individual configuration files in the generated directory"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load and merge all node configurations
    nodes = load_node_configs(common_config)
    
    for vm_config in nodes:
        name = vm_config.get('name', 'unnamed-vm')
        output_file = os.path.join(output_dir, f"{name}.yaml")
        
        # Write merged configuration to file
        with open(output_file, 'w') as f:
            yaml.dump(vm_config, f, default_flow_style=False, sort_keys=False)
        
        click.echo(f"✓ Generated configuration: {output_file}")

@click.command()
@click.option('--common-config', '-c', default='config/common.yaml',
              help='Path to common configuration YAML file')
@click.option('--dry-run', '-d', is_flag=True,
              help='Show commands without executing')
@click.option('--generate', '-g', is_flag=True,
              help='Generate configuration files in generated directory')
@click.option('--output-dir', '-o', default='generated',
              help='Output directory for generated config files')
def main(common_config, dry_run, generate, output_dir):
    """Enhanced VM Provisioner with common + nodes config merging"""
    
    click.echo("="*60)
    click.echo("Enhanced Multipass VM Provisioner")
    click.echo("="*60)
    
    # Load common configuration
    click.echo(f"Loading common configuration from: {common_config}")
    config_data = load_config(common_config)
    
    # Load node configurations to show summary
    nodes = load_node_configs(config_data)
    
    # Show configuration summary
    main_nodes = [node for node in nodes if node.get('type') == 'controller']
    worker_nodes = [node for node in nodes if node.get('type') == 'worker']
    other_nodes = [node for node in nodes if node.get('type') not in ['controller', 'worker']]
    
    click.echo(f"\nConfiguration Summary:")
    click.echo(f"  Total VMs: {len(nodes)}")
    click.echo(f"  Controller nodes: {len(main_nodes)}")
    click.echo(f"  Worker nodes: {len(worker_nodes)}")
    click.echo(f"  Other nodes: {len(other_nodes)}")
    
    if generate:
        click.echo(f"\nGenerating configuration files in: {output_dir}")
        generate_config_files(config_data, output_dir)
        return
    
    if dry_run:
        click.echo("\nDRY RUN MODE - Commands will not be executed")
        global_config = config_data.get('global', {})
        for i, vm_config in enumerate(nodes, 1):
            cmd = build_multipass_command(vm_config, global_config)
            click.echo(f"\nVM {i}: {vm_config.get('name')}")
            click.echo(f"  Command: {' '.join(cmd)}")
        return
    
    # Create virtual machines
    success = create_virtual_machines(config_data, dry_run)
    
    if success:
        click.echo("\n✅ All virtual machines created successfully!")
    else:
        click.echo("\n❌ Some virtual machines failed to create", err=True)

if __name__ == "__main__":
    main()