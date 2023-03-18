import json

def read_config():
    """ Parse json configuration file """
    with open("config/config.json", 'r') as f:
        config_data = json.load(f)
        return config_data
