"""
Author: Logan Sizemore
Date: 4/26/23

This code provides a set of utility functions to handle YAML configurations and dynamically instantiate classes 
with their configurations. It facilitates the management of complex configurations for applications using YAML 
files and enables the dynamic loading of classes and their arguments at runtime.
"""

import argparse
import functools
import inspect
import os
from typing import Callable, List, Union, Optional, Type, Any

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

def skeleton_key(config_name: str, config_path: Optional[str]="./") -> Callable:
     """
    Create a decorator for parsing and injecting configuration arguments into a
    main function from a YAML file.

    Args:
        config_name (str): The name of the YAML configuration file.
        config_path (str): The path to the directory containing the configuration
                           file. Defaults to the current directory.

    Returns:
        Callable: A decorator function that, when applied to a main function, will
                  parse the configuration file and inject the arguments into the
                  main function.
    """
    config_path = os.path.abspath(config_path)
    config = load_yaml_config(os.path.join(config_path, config_name))

    def _parse_config(main: Callable):
        @functools.wraps(main)
        def _inner_function():
            parser = argparse.ArgumentParser()
            add_args_from_dict(parser, config)
            args = parser.parse_args()
            main(args)

        return _inner_function

    return _parse_config

def import_class(class_string: str) -> Type[Any]:
    """
    Dynamically import a class using its full module path and class name.

    Args:
        class_string (str): A string representing the full path to the class,
                            including the module name and class name, separated
                            by dots.

    Returns:
        type: The imported class object.
    """
    parts = class_string.split(".")
    module_name = ".".join(parts[:-1])
    class_name = parts[-1]
    module = __import__(module_name, fromlist=[class_name])
    class_obj = getattr(module, class_name)
    return class_obj

def instantiate(kwargs: Dict[str, Any]) -> Any:
    """
    Instantiate a class object using a dictionary of keyword arguments.
    The dictionary should contain the keys "_kwargs_" and "_target_" to
    specify the class to instantiate and its arguments.

    Args:
        kwargs (Dict[str, Any]): A dictionary containing the keys "_kwargs_"
                                 and "_target_" to specify the class and its
                                 arguments, along with any additional keyword
                                 arguments for the class.

    Returns:
        Any: An instance of the specified class.

    Raises:
        AssertionError: If the class is missing specific parameters.
    """
    if "_kwargs_" in kwargs:
        kwargs.update(open_yaml(kwargs["_kwargs_"]))
        del kwargs["_kwargs_"]

    class_obj = import_class(kwargs["_target_"])
    del kwargs["_target_"]
    
    obj_parameters = list(inspect.signature(class_obj).parameters)
    valid_parameters = {k: v for k, v in kwargs.items() if k in obj_parameters}
    missing_parameters = [
        k for k in obj_parameters if k not in valid_parameters.keys()
    ]
    assert (
        len(missing_parameters) == 0
    ), f"Object mssing specific parameters. ({missing_parameters})"

    return class_obj(**kwargs)
