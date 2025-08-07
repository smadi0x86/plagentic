import yaml
import os

global_config = {}


def load_config():
    global global_config
    
    # Try Docker config path first (mounted at /app/config.yaml)
    docker_config_path = '/app/config.yaml'
    if os.path.exists(docker_config_path):
        config_path = docker_config_path
    else:
        # Fall back to local config path (relative to package structure)
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../config.yaml'))
    
    with open(config_path, 'r') as file:
        global_config = yaml.safe_load(file)


def config():
    return global_config
