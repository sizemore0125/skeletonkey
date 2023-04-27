"""
Author: Logan Sizemore
Date: 4/27/23

This code provides a set of utility functions to handle YAML configurations. 
It facilitates the management of complex configurations for applications using YAML 
files and enables the dynamic loading of classes and their arguments at runtime.
"""

import argparse
import inspect
import os
from typing import List

import yaml

def open_yaml(path: str) -> dict:
    """
    Read and parse the YAML file located at the given path.
    
    Args:
        path (str): The file path to the YAML file.
        
    Returns:
        dict: A dictionary representing the YAML content.
    """
    with open(os.path.expanduser(path), 'r') as handle:
        return yaml.safe_load(handle)

def flatten_dict(dictionary: dict, parent_key='', sep='/') -> dict:
    """
    Flatten a nested dictionary into a single-level dictionary by concatenating 
    nested keys using a specified separator.

    Args:
        dictionary (dict): The nested dictionary to be flattened.
        parent_key (str): The initial parent key, default is an empty string.
        sep (str): The separator used to concatenate nested keys, default is '/'.

    Returns:
        dict: A flattened dictionary with single-level keys.
    """
    items = []
    for key, value in dictionary.items():
        # Create a new key by concatenating the parent key and the current key
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, dict):
            # If the value is a nested dictionary, recursively flatten it
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # If the value is a list, iterate through the items in the list
            for item in value:
                if isinstance(item, dict):
                    # If an item in the list is a dictionary, flatten it
                    sublist_items = flatten_dict(item, new_key, sep=sep).items()
                    items.extend(sublist_items)
                else:
                    # If the item is not a dictionary, append it to the key
                    items.append((new_key, item))
        else:
            # If the value is neither a dictionary nor a list, add it to the items
            items.append((new_key, value))

    return dict(items)

def dict_to_path(dictionary: dict) -> List[str]:
    """
    Convert a dictionary with key-value pairs into a list of paths by joining 
    the keys and values with the appropriate path separator.

    Args:
        dictionary (dict): A dictionary containing key-value pairs where both
                           keys and values are strings.

    Returns:
        List[str]: A list of paths created by joining each key-value pair in the 
                   input dictionary.
    """
    return [os.path.join(key, value) for key, value in dictionary.items()]

def add_yaml_extension(path: str) -> str:
    """
    Append the '.yaml' extension to a given path if it doesn't already have it.

    Args:
        path (str): The input file path or name.

    Returns:
        str: The modified file path or name with the '.yaml' extension added.
    """
    yaml_extention = '.yaml'
    if not path.endswith(yaml_extention):
        path += yaml_extention
    return path
    
def get_default_yaml_paths_from_dict(default_yaml: dict) -> List[str]:
    """
    Process a nested dictionary of default YAML file paths, flattening the
    dictionary, converting it to a list of paths, and ensuring each path has
    a '.yaml' extension.

    Args:
        default_yaml (dict): A nested dictionary containing default YAML file paths.

    Returns:
        List[str]: A list of processed and validated default YAML file paths.
    """
    default_yaml = flatten_dict(default_yaml)
    default_yaml = dict_to_path(default_yaml)
    default_yaml = [add_yaml_extension(filename) for filename in default_yaml]
    return default_yaml

def load_yaml_config(path: str, default_keyword: str = "defaults") ->  dict:
    """
    Load a YAML configuration file and update it with default configurations.

    Args:
        path (str): The file path to the YAML configuration file.
        default_keyword (str): The keyword used to identify default configurations
                               in the YAML file. Defaults to "defaults".

    Returns:
        dict: The updated configuration dictionary.
    """
    config = open_yaml(path)
    
    if default_keyword in config:
        for default_yaml in config[default_keyword]:
            if isinstance(default_yaml, str):
                default_yaml = add_yaml_extension(default_yaml)
                default_config = open_yaml(default_yaml)
            elif isinstance(default_yaml, dict):
                yaml_paths = get_default_yaml_paths_from_dict(default_yaml)
                default_configs = [open_yaml(yaml_path) for yaml_path in yaml_paths]
                default_config = {key: value for config_dict in default_configs for key, value in config_dict.items()}
            config.update(default_config)

    return config

def add_args_from_dict(arg_parser: argparse.ArgumentParser, config: dict) -> None:
    """
    Add arguments to an ArgumentParser instance using key-value pairs from a 
    configuration dictionary.

    Args:
        arg_parser (argparse.ArgumentParser): The ArgumentParser instance to which
                                              arguments will be added.
        config (dict): A dictionary containing key-value pairs representing
                       the arguments and their default values.
    """
    for key, value in config.items():
        arg_parser.add_argument(f"--{key}", default=value, type=type(value))