import argparse
import functools
import inspect
import os
import sys
from typing import Callable, Optional, Type, Any, Tuple

from .config import (
    load_yaml_config,
    add_args_from_dict,
    add_yaml_extension,
    config_to_nested_config,
    Config
)

TARGET_KEYWORD: str = "_target_"

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
            args = config_to_nested_config(args)
            return main(args)

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


def instantiate(config: Config, target_keyword=TARGET_KEYWORD, _instantiate_recursive=True, **kwargs) -> Any:
    """
    Instantiate a class object using a Config object.
    The Config object should contain the key "_target_" to
    specify the class to instantiate.

    Args:
        config (Config): A Config object containing the key "_target_"
            to specify the class, along with any additional keyword
            arguments for the class.

    Returns:
        Any: An instance of the specified class.

    Raises:
        TypeError: If the class is missing specific parameters.
    """
    obj_kwargs = vars(config).copy()
    class_obj = import_class(obj_kwargs[target_keyword])
    del obj_kwargs[target_keyword]

    if _instantiate_recursive:
        for k, v in obj_kwargs.items():
            if isinstance(v, Config) and (target_keyword in vars(v)):
                obj_kwargs[k] = instantiate(v)

    obj_kwargs.update(kwargs)

    obj_parameters = inspect.signature(class_obj).parameters
    required_parameters = [
        param_name for param_name, param in obj_parameters.items()
        if param.default == param.empty and param.kind != inspect.Parameter.VAR_KEYWORD
    ]
    valid_parameters = {k: v for k, v in obj_kwargs.items() if k in required_parameters}
    missing_parameters = [k for k in required_parameters if k not in valid_parameters.keys()]

    if len(missing_parameters) != 0:
        raise TypeError(
            f"missing {len(missing_parameters)} required positional(s) argument: {', '.join(missing_parameters)}."
            + " Add it to your config or as a keyword argument to skeletonkey.instantiate()."
        )
    
    return class_obj(**obj_kwargs)

def instantiate_all(config: Config, target_keyword=TARGET_KEYWORD, **kwargs) -> Tuple[Any]:
    """
    Instantiate a tuple of class objects using a Config object.
    The Config object should contain other Config objects where the key 
    "_target_" is at the top level, which specifies the class to instantiate.

    Args:
        config (Config): A Config object containing the key "_target_"
            to specify the class , along with any additional keyword arguments for the class.

    Returns:
        Tuple[Any]: An tuple of instances of the specified class.

    Raises:
        ValueError: If any subconfig does not have "_target_" key.
    """
    collection_dict = vars(config).copy()

    objects = []

    for obj_key in collection_dict.keys():
        obj_namespace = collection_dict[obj_key]

        if not hasattr(obj_namespace, target_keyword):
            raise ValueError(f"subconfig ({obj_key}) in collection does not have '_target_' key at the top level.")
        
        obj = instantiate(obj_namespace, **kwargs)
        objects.append(obj)
    
    return tuple(objects)
