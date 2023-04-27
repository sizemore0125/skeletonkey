import os
import yaml
import argparse
from typing import Callable, Union, List
import inspect

def open_yaml(path: str) -> dict:
    with open(os.path.expanduser(path), 'r') as handle:
        return yaml.safe_load(handle)

def flatten_dict(dictionary: dict, parent_key='', sep='/') -> dict:
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    sublist_items = flatten_dict(item, new_key, sep=sep).items()
                    items.extend(sublist_items)
                else:
                    items.append((new_key + item))
        else:
            items.append((new_key, value))
    return dict(items)

def dict_to_path(dictionary: dict) -> list:
    return [os.path.join(key, value) for key, value in dictionary.items()]

def add_yaml_extention(path):
    yaml_extention = '.yaml'
    if not path.endswith(yaml_extention):
        path += yaml_extention
    return path
    
def get_default_yaml_paths_from_dict(default_yaml: dict) -> List[str]:
    default_yaml = flatten_dict(default_yaml)
    default_yaml = dict_to_path(default_yaml)
    default_yaml = [add_yaml_extention(filename) for filename in default_yaml]
    return default_yaml

def load_yaml_config(path: str, default_keyword: str = "defaults"):
    config = open_yaml(path)
    
    if default_keyword in config:
        for default_yaml in config[default_keyword]:
            if isinstance(default_yaml, str):
                default_yaml = add_yaml_extention(default_yaml)
                default_config = open_yaml(default_yaml)
                config.update(default_config)
            elif isinstance(default_yaml, dict):
                yaml_paths = get_default_yaml_paths_from_dict(default_yaml)
                for yaml_path in yaml_paths:
                    default_config = open_yaml(yaml_path)
                    config.update(default_config)
    return config

def add_args_from_dict(arg_parser: argparse.ArgumentParser, config: dict):
    for key, value in config.items():
        arg_parser.add_argument(f"--{key}", default=value, type=type(value))

def skeleton_key(config_path: str) -> Callable:
    config = load_yaml_config(config_path)
    def _parse_config(main: Callable):
        def _inner_function():
            parser = argparse.ArgumentParser()
            add_args_from_dict(parser, config)
            args = parser.parse_args()
            main(args)
        return _inner_function
    return _parse_config

def import_class(class_string):
    parts = class_string.split(".")
    module_name = ".".join(parts[:-1])
    class_name = parts[-1]
    module = __import__(module_name, fromlist=[class_name])
    class_obj = getattr(module, class_name)
    return class_obj

def instantiate(kwargs):
    class_obj = import_class(kwargs["_target_"])
    del kwargs["_target_"]
    
    if "_kwargs_" in kwargs:
        kwargs.update(open_yaml(kwargs["_kwargs_"]))
        del kwargs["_kwargs_"]

    obj_parameters = list(inspect.signature(class_obj).parameters)
    valid_parameters = {k: v for k, v in kwargs.items() if k in obj_parameters}
    missing_parameters = [
        k for k in obj_parameters if k not in valid_parameters.keys()
    ]
    assert (
        len(missing_parameters) == 0
    ), f"Object mssing specific parameters. ({missing_parameters})"

    return class_obj(**kwargs)
