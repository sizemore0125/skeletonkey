import inspect
import functools

from .config import Config
from typing import Type, Any, Callable, Union, Dict

INSTANCE_KEYWORD: str = "_instance_"
PARTIAL_KEYWORD: str = "_partial_"
FETCH_KEYWORD: str = "_fetch_"

def import_target(class_string: str) -> Type[Any]:
    """
    Dynamically import a class/function using its full module path and name.

    Args:
        class_string (str): A string representing the full path to the class,
                            including the module name and class name, separated
                            by dots.

    Returns:
        type: The imported class object.
    """
    parts = class_string.split(".")
    module_name = ".".join(parts[:-1])
    name = parts[-1]
    module = __import__(module_name, fromlist=[name])
    obj = getattr(module, name)
    return obj


def instantiate(
    *configs:Union[Config, Dict[str, Any]], 
    instance_keyword:str=INSTANCE_KEYWORD,
    partial_keyword:str=PARTIAL_KEYWORD,
    fetch_keyword:str=FETCH_KEYWORD,
    _instantiate_recursive:bool=True,
    **kwargs
) -> Any:

    """
    Instantiate a class object using a Config object.
    The Config object should contain the key "_target_" to
    specify the class to instantiate.

    Args:
        *configs (Config): A Config object containing the class to instantiate. Multiple Config objects can be provided.
        instance_keyword (str, optional): The keyword to use to specify a full class instantiation. Defaults to "_instance_".
        partial_keyword (str, optional): The keyword to use to specify a partial class instantiation. Defaults to "_partial_".
        fetch_keyword (str, optional): The keyword to use to specify a fetch class instantiation. Defaults to "_fetch_".
        _instantiate_recursive (bool, optional): Whether to recursively instantiate subconfigs. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the class constructor

    Returns:
        Any: The instantiated class object (or list of objects if multiple configs are provided)

    Raises:
        ValueError: If no valid instantiation keyword is found in the config.
        TypeError: If any required parameters are missing from the instacne config
        ValueError: If a config instantiated with the _fetch_ keyword has additional arguments.
    """
    
    if len(configs) == 1:
        return _instantiate_single(configs[0], instance_keyword, partial_keyword, fetch_keyword, _instantiate_recursive, **kwargs)
    
    else:
        return [_instantiate_single(config, instance_keyword, partial_keyword, fetch_keyword, _instantiate_recursive, **kwargs)
                for config in configs]
            

def _instantiate_single(
    config: Union[Config, Dict[str, Any]],
    instance_keyword:str=INSTANCE_KEYWORD,
    partial_keyword:str=PARTIAL_KEYWORD,
    fetch_keyword:str=FETCH_KEYWORD,
    _instantiate_recursive:bool=True,
    **extra_kwargs
) -> Any:
    """
    Instantiate a single config (Config or dict), optionally recursing into subconfigs.

    Args:
        config (Config|dict): The config to instantiate.
        instance_keyword (str): Keyword for full instantiation. Defaults to "_instance_".
        partial_keyword (str): Keyword for partial instantiation. Defaults to "_partial_".
        fetch_keyword (str): Keyword for fetch-only values. Defaults to "_fetch_".
        _instantiate_recursive (bool): Whether to instantiate nested configs. Defaults to True.
        **extra_kwargs: Extra kwargs to overlay onto the instantiation call.

    Returns:
        Any: The instantiated object (or partial/fetch result).
    """
    
    kwargs: Dict[str, Any] = {}
    if not isinstance(config, dict):
        kwargs = config.to_dict().copy()
    else:
        kwargs = config.copy()

    # Recursively instantiate subconfigs
    if _instantiate_recursive:
        for k, v in kwargs.items():
            if _is_instantiatable(v, instance_keyword, partial_keyword, fetch_keyword):
                kwargs[k] = _instantiate_single(v)
    kwargs.update(extra_kwargs)

    if instance_keyword in kwargs:
        target = import_target(kwargs[instance_keyword])
        del kwargs[instance_keyword]
        
        return _instance(target, kwargs, config)
    
    elif partial_keyword in kwargs:
        target = import_target(kwargs[partial_keyword])
        del kwargs[partial_keyword]

        return _partial(target, kwargs, config)
    
    elif fetch_keyword in kwargs:
        target = import_target(kwargs[fetch_keyword])
        del kwargs[fetch_keyword]

        return _fetch(target, kwargs, config)
    
    else:
        error_str = f"No valid instantiation keyword found in config: {config}\n"
        if "_target_" in kwargs:
            error_str += 'Hint: the "_target_" keyword has been deprecated. Use "_instance_", "_partial_", or "_fetch_" instead.'
        raise ValueError(error_str)

def _is_instantiatable(value: Any, instance_keyword=INSTANCE_KEYWORD, partial_keyword=PARTIAL_KEYWORD, fetch_keyword=FETCH_KEYWORD) -> bool:
    """
    Check if a given value can be instantiated.

    Args:
        value: The value to check.
        instance_keyword (str, optional): The keyword to use to specify a full class instantiation. Defaults to "_instance_".
        partial_keyword (str, optional): The keyword to use to specify a partial class instantiation. Defaults to "_partial_".
        fetch_keyword (str, optional): The keyword to use to specify a fetch class instantiation. Defaults to "_fetch_".
    Returns:
        bool: True if the value can be instantiated, False otherwise.
    """

    return isinstance(value, dict) and any(keyword in value for keyword in [instance_keyword, partial_keyword, fetch_keyword])


def _instance(target: Callable, kwargs: dict, config: Union[Config, Dict[str, Any]]) -> Any:
    """
    Create an instance of a class target with the given keyword arguments, checking for missing parameters.

    Args:
        target: The class to instantiate.
        kwargs: The keyword arguments to pass to the class constructor
        config: The original config object, used for error messages.
    
    Returns:
        Any: The instantiated class object.
    """

   # Check for missing parameters 
    obj_parameters = inspect.signature(target).parameters
    required_parameters = [
        param_name for param_name, param in obj_parameters.items()
        if param.default == param.empty and param.kind != inspect.Parameter.VAR_KEYWORD
    ]

    valid_parameters = {k: v for k, v in kwargs.items() if k in required_parameters}
    missing_parameters = [k for k in required_parameters if k not in valid_parameters.keys()]

    if len(missing_parameters) != 0:
        raise TypeError(
              f"Error in config: {config}. "
            + f"Missing {len(missing_parameters)} required positional argument(s): {', '.join(missing_parameters)}. "
            + "Add it to your config or provide as a keyword argument during instantiation."
        )
    return target(**kwargs)

def _partial(target: Callable, kwargs: dict, config: Union[Config, Dict[str, Any]]) -> functools.partial:
    """
    Create a partial instantiation of a class target with the given keyword arguments.

    Args:
        target: The class to partially instantiate.
        kwargs: The keyword arguments to pass to the class constructor  
        config: The original config object, used for error messages.

    Returns:

    """
        
    return functools.partial(target, **kwargs)


def _fetch(target: Any, kwargs: dict, config: Union[Config, Dict[str, Any]]) -> Any:
    if kwargs != {}:
        raise ValueError(f"Error in config: {config}. Configs instantiated with the _fetch_ keyword cannot have any additional arguments.")
    
    return target
