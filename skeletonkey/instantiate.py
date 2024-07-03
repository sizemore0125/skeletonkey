import inspect
import functools
from typing import Type, Any, Tuple

TARGET_KEYWORD: str = "_target_"

def import_target(class_string: str) -> Type[Any]:
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
    name = parts[-1]
    module = __import__(module_name, fromlist=[name])
    obj = getattr(module, name)
    return obj


def instantiate(config, target_keyword=TARGET_KEYWORD, _instantiate_recursive=True, partial=False, **kwargs) -> Any:
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
    class_obj = import_target(obj_kwargs[target_keyword])
    del obj_kwargs[target_keyword]

    if _instantiate_recursive:
        for k, v in obj_kwargs.items():
            if isinstance(v, type(config)) and (target_keyword in vars(v)):
                obj_kwargs[k] = instantiate(v)

    obj_kwargs.update(kwargs)

    obj_parameters = inspect.signature(class_obj).parameters
    required_parameters = [
        param_name for param_name, param in obj_parameters.items()
        if param.default == param.empty and param.kind != inspect.Parameter.VAR_KEYWORD
    ]
    valid_parameters = {k: v for k, v in obj_kwargs.items() if k in required_parameters}
    missing_parameters = [k for k in required_parameters if k not in valid_parameters.keys()]

    if len(missing_parameters) != 0 and not partial:
        raise TypeError(
            f"missing {len(missing_parameters)} required positional(s) argument: {', '.join(missing_parameters)}."
            + " Add it to your config or as a keyword argument to skeletonkey.instantiate()."
        )
    if partial:
        partial = functools.partial(class_obj, **valid_parameters)
        return partial
    
    return class_obj(**obj_kwargs)

def instantiate_all(config, target_keyword=TARGET_KEYWORD, **kwargs) -> Tuple[Any]:
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

def fetch(config, target_keyword=TARGET_KEYWORD):
    """
    Fetch a value from a python module based on the "_target_" key.
    Like instantiate but does not call/instantiate the target.
    Mainly intended to retrieve functions/

    Args:
        config (Config): A Config object containing the key "_target_"
            to specify the object

    Returns:
        Any: The value associated with the specified "_target_".
    """

    obj_kwargs = vars(config).copy()
    obj = import_target(obj_kwargs[target_keyword])

    return obj
