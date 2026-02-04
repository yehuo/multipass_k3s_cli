#!/usr/bin/env python3

import sys
import subprocess
import yaml



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
    """Execute a command and return the result"""
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