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


def find_yaml_path(file_path: str) -> str:
    """
    Given a file path, this function checks if a YAML file exists with either
    '.yml' or '.yaml' extension, and returns the correct path.

    Args:
        file_path (str): The file path without extension or with either '.yml' or '.yaml' extension.

    Returns:
        str: The correct file path with the existing extension.

    Raises:
        FileNotFoundError: If no YAML file is found with either extension.
    """
    base_path, ext = os.path.splitext(file_path)

    yml_path = base_path + ".yml"
    yaml_path = base_path + ".yaml"

    if os.path.isfile(yml_path):
        return yml_path
    elif os.path.isfile(yaml_path):
        return yaml_path
    else:
        raise FileNotFoundError(
            f"No YAML file found with either '.yml' or '.yaml' extension for path: {base_path}. You may have mistakenly specified an absolute path."
        )


def open_yaml(path: str) -> dict:
    """
    Read and parse the YAML file located at the given path.

    Args:
        path (str): The file path to the YAML file.

    Returns:
        dict: A dictionary representing the YAML content.
    """
    path = find_yaml_path(path)
    with open(os.path.expanduser(path), "r") as handle:
        return yaml.safe_load(handle)


def dict_to_path(dictionary: dict, parent_key="", sep="/") -> List[str]:
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
        new_key = os.path.join(parent_key, key) if parent_key else key
        if isinstance(value, dict):
            # If the value is a nested dictionary, recursively flatten it
            items.extend(dict_to_path(value, new_key))
        elif isinstance(value, list):
            # If the value is a list, iterate through the items in the list
            for item in value:
                if isinstance(item, dict):
                    # If an item in the list is a dictionary, flatten it
                    sublist_items = dict_to_path(item, new_key)
                    items.extend(sublist_items)
                else:
                    # If the item is not a dictionary, append it to the key
                    items.append(os.path.join(new_key, item))
        else:
            # If the value is neither a dictionary nor a list, add it to the items
            items.append(os.path.join(new_key, value))

    return items


def add_yaml_extension(path: str) -> str:
    """
    Append the '.yaml' extension to a given path if it doesn't already have it.

    Args:
        path (str): The input file path or name.

    Returns:
        str: The modified file path or name with the '.yaml' extension added.
    """
    yaml_extention1 = ".yaml"
    yaml_extention2 = ".yml"
    if not path.endswith(yaml_extention1) and not path.endswith(yaml_extention2):
        path += yaml_extention1
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
    default_yaml = dict_to_path(default_yaml)
    default_yaml = [add_yaml_extension(filename) for filename in default_yaml]
    return default_yaml


def get_default_args_from_dict(config_path: str, default_yaml: dict) -> dict:
    """
    Load a YAML default configuration files in dict format and returns a dictionary of args.

    Args:
        config_path (str): The file path to the YAML configuration file.
        default_yml (dict): A dictionary data structure representing the paths to many
            YAML configuration files.

    Returns:
        dict: The updated configuration dictionary."""
    yaml_paths = get_default_yaml_paths_from_dict(default_yaml)
    default_configs = [
        open_yaml(os.path.join(config_path, yaml_path)) for yaml_path in yaml_paths
    ]
    default_config = {
        key: value
        for config_dict in default_configs
        if config_dict
        for key, value in config_dict.items()
    }
    return default_config


def get_default_args_from_path(config_path: str, default_yaml: str) -> dict:
    """
    Load a YAML default configuration files and returns a dictionary of args.

    Args:
        config_path (str): The file path to the YAML base configuration file.
        default_yml (str): The relative path to to the default YAML subconfiguration file.

    Returns:
        dict: The updated configuration dictionary.
    """
    default_yaml = add_yaml_extension(default_yaml)
    default_config_path = os.path.join(config_path, default_yaml)
    default_config = open_yaml(default_config_path)
    return default_config


def load_yaml_config(
    config_path: str, config_name: str, default_keyword: str = "defaults"
) -> dict:
    """
    Load a YAML configuration file and update it with default configurations.

    Args:
        config_path (str): The file path to the YAML configuration file.
        config_name (str): The name of the YAML configuration file.
        default_keyword (str): The keyword used to identify default configurations
            in the YAML file. Defaults to "defaults".

    Returns:
        dict: The updated configuration dictionary.
    """
    path = os.path.join(config_path, config_name)
    config = open_yaml(path)

    if default_keyword in config:
        default_path_dict = config[default_keyword]
        if isinstance(default_path_dict, dict):
            default_config = get_default_args_from_dict(config_path, default_path_dict)

            if default_config:
                config.update(
                    (key, value)
                    for key, value in default_config.items()
                    if key not in config
                )
        else:
            for default_yaml in default_path_dict:
                if isinstance(default_yaml, dict):
                    default_config = get_default_args_from_dict(
                        config_path, default_yaml
                    )

                elif isinstance(default_yaml, str):
                    default_config = get_default_args_from_path(
                        config_path, default_yaml
                    )

                if default_config:
                    config.update(
                        (key, value)
                        for key, value in default_config.items()
                        if key not in config
                    )
        del config[default_keyword]

    return config


def add_args_from_dict(
    arg_parser: argparse.ArgumentParser, config: dict, prefix=""
) -> None:
    """
    Add arguments to an ArgumentParser instance using key-value pairs from a
    configuration dictionary. If the dictionary contains a nested dictionary, the
    argument will be added as --key.key value.
    Args:
        arg_parser (argparse.ArgumentParser): The ArgumentParser instance to which
                                              arguments will be added.
        config (dict): A dictionary containing key-value pairs representing
                       the arguments and their default values.
        prefix (str, optional): The prefix string for nested keys. Defaults to ''.
    """
    for key, value in config.items():
        if isinstance(value, dict):
            add_args_from_dict(arg_parser, value, f"{prefix}{key}.")
        else:
            if key.startswith("$") and key[1:] in os.environ:
                env_var = os.environ[key[1:]]
                arg_parser.add_argument(
                    f"--{prefix}{key[1:]}", default=env_var, type=type(env_var)
                )
            else:
                arg_parser.add_argument(
                    f"--{prefix}{key}", default=value, type=type(value)
                )


def dict_to_namespace(dictionary: dict) -> argparse.Namespace:
    """
    Convert a dictionary to an argparse.Namespace object recursively.

    Args:
        dictionary (dict): The dictionary to be converted.

    Returns:
        argparse.Namespace: A Namespace object representing the input dictionary.
    """
    for key, value in dictionary.items():
        if isinstance(value, dict):
            dictionary[key] = dict_to_namespace(value)
    return argparse.Namespace(**dictionary)


def namespace_to_nested_namespace(namespace: argparse.Namespace) -> argparse.Namespace:
    """
    Convert an argparse.Namespace object with 'key1.keyn' formatted keys into a nested Namespace object.

    Args:
        namespace (argparse.Namespace): The Namespace object to be converted.

    Returns:
        argparse.Namespace: A nested Namespace representation of the input Namespace object.
    """
    nested_dict = {}
    for key, value in vars(namespace).items():
        keys = key.split(".")
        current_dict = nested_dict
        for sub_key in keys[:-1]:
            if sub_key not in current_dict:
                current_dict[sub_key] = {}
            current_dict = current_dict[sub_key]
        current_dict[keys[-1]] = value

    return dict_to_namespace(nested_dict)
