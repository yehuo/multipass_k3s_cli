#!/usr/bin/env python3

import sys
import subprocess
import yaml
import json
from typing import List, Dict, Tuple


def load_config(config_file):
    """Load YAML configuration file"""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

def execute(cmd):
    """Execute a multipass command and return the result"""
    try:
        result = subprocess.run(
            ["multipass"] + cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Execute a generic command and return the result"""
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
        print("Error: Unable to get virtual machine list")
        return []

    try:
        data = json.loads(output)
        return data.get("list", [])
    except json.JSONDecodeError:
        print("Error: Unable to parse virtual machine list")
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


def deep_merge(base_dict: Dict, override_dict: Dict) -> Dict:
    """
    Deep merge two dictionaries. Values from override_dict take precedence.
    
    Args:
        base_dict: Base dictionary to merge into
        override_dict: Dictionary with values that override base_dict
        
    Returns:
        Merged dictionary
    """
    result = base_dict.copy()
    
    for key, value in override_dict.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            # Recursively merge nested dictionaries
            result[key] = deep_merge(result[key], value)
        else:
            # Override with new value
            result[key] = value
    
    return result


def file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    import os
    return os.path.exists(file_path)