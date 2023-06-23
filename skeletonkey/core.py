import argparse
import functools
import inspect
import os
import sys
from typing import Callable, Optional, Type, Any, Dict

from .config import (
    load_yaml_config,
    add_args_from_dict,
    add_yaml_extension,
    namespace_to_nested_namespace,
)


def get_config_dir_path(config_path: str) -> str:
    """
    Convert a given relative or absolute config file path to its absolute directory path.

    Args:
        config_path (str): The path to the configuration file. Can be either relative or absolute.

    Returns:
        str: The absolute directory path containing the configuration file.
    """
    # Check if the given config_path is a relative path
    if not os.path.isabs(config_path):
        # Get the directory of the main script file (entry point) in absolute form
        path_from_main = os.path.dirname(
            os.path.abspath(str(sys.modules["__main__"].__file__))
        )

        if config_path.startswith("./"):
            config_path = config_path[len("./") :]

        # Traverse up the directory structure for each "../" in config_path
        # Remove the "../" string from the path, and remove a directory from main.
        while config_path.startswith("../"):
            config_path = config_path[len("../") :]
            path_from_main = os.path.dirname(path_from_main)

        # Create absolute path.
        config_path = os.path.join(path_from_main, config_path)
    return config_path


def unlock(config_name: str, config_path: Optional[str] = None) -> Callable:
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
    config_path = config_path if config_path else os.path.dirname(config_name)
    config_path = get_config_dir_path(config_path)

    config_name = add_yaml_extension(config_name)
    config_name = os.path.basename(config_name)

    config = load_yaml_config(config_path, config_name)

    def _parse_config(main: Callable):
        @functools.wraps(main)
        def _inner_function():
            parser = argparse.ArgumentParser()
            add_args_from_dict(parser, config)
            args = parser.parse_args()
            args = namespace_to_nested_namespace(args)
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


def instantiate(namespace: argparse.Namespace) -> Any:
    """
    Instantiate a class object using a dictionary of keyword arguments.
    The dictionary should contain the keys "_kwargs_" and "_target_" to
    specify the class to instantiate and its arguments.

    Args:
        namespace (argparse.Namespace): A Namespace object containing the key "_kwargs_"
            to specify the class and its arguments, along with any additional keyword
            arguments for the class.

    Returns:
        Any: An instance of the specified class.

    Raises:
        AssertionError: If the class is missing specific parameters.
    """
    kwargs = vars(namespace)
    target_keyword = "_target_"
    class_obj = import_class(kwargs[target_keyword])
    del kwargs[target_keyword]

    obj_parameters = list(inspect.signature(class_obj).parameters)
    valid_parameters = {k: v for k, v in kwargs.items() if k in obj_parameters}
    missing_parameters = [k for k in obj_parameters if k not in valid_parameters.keys()]
    assert (
        len(missing_parameters) == 0
    ), f"Object mssing specific parameters. ({missing_parameters})"

    return class_obj(**kwargs)
