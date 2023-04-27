"""
Author: Logan Sizemore
Date: 4/27/23

This code provides decorator for parsing and injecting configuration arguments into a main function 
and an instantiate funtion that can dynamically instantiate classes with their configurations. 
It facilitates the management of complex configurations for applications using YAML files and enables 
the dynamic loading of classes and their arguments at runtime.
"""

import argparse
import functools
import inspect
import os
from typing import Callable, Optional, Type, Any, Dict

from .utils import open_yaml, load_yaml_config, add_args_from_dict

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
