import inspect
import functools

from .config import Config
from typing import Type, Any, Callable, Union, Dict

INSTANCE_KEYWORD: str = "_instance_"
PARTIAL_KEYWORD: str = "_partial_"
FETCH_KEYWORD: str = "_fetch_"


def import_target(class_string: str) -> Type[Any]:
    """Import a class or function from a dotted module path.

    Args:
        class_string (str): Full path to the class or function, including
            module and attribute name.

    Returns:
        Type[Any]: The imported class or function.
    """
    parts = class_string.split(".")
    module_name = ".".join(parts[:-1])
    name = parts[-1]
    module = __import__(module_name, fromlist=[name])
    obj = getattr(module, name)
    return obj


def instantiate(
    *configs: Union[Config, Dict[str, Any]],
    instance_keyword: str = INSTANCE_KEYWORD,
    partial_keyword: str = PARTIAL_KEYWORD,
    fetch_keyword: str = FETCH_KEYWORD,
    _instantiate_recursive: bool = True,
    **kwargs,
) -> Any:
    """Instantiate objects described by configuration mappings.

    Args:
        *configs (Config | dict): One or more configs containing instantiation
            keywords and arguments.
        instance_keyword (str, optional): Keyword indicating a full
            instantiation. Defaults to "_instance_".
        partial_keyword (str, optional): Keyword indicating a partial
            instantiation. Defaults to "_partial_".
        fetch_keyword (str, optional): Keyword indicating a fetch-only
            reference. Defaults to "_fetch_".
        _instantiate_recursive (bool, optional): Whether to instantiate nested
            configs before creating the target. Defaults to True.
        **kwargs: Extra keyword arguments merged into the instantiation call.

    Returns:
        Any: Instantiated object for a single config, or a list of objects when
        multiple configs are provided.

    Raises:
        ValueError: If no valid instantiation keyword is present.
        TypeError: If required parameters are missing in an instantiation.
    """

    if len(configs) == 1:
        return _instantiate_single(configs[0], instance_keyword, partial_keyword, fetch_keyword, _instantiate_recursive, **kwargs)

    else:
        return [
            _instantiate_single(config, instance_keyword, partial_keyword, fetch_keyword, _instantiate_recursive, **kwargs)
            for config in configs
        ]


def _instantiate_single(
    config: Union[Config, Dict[str, Any]],
    instance_keyword: str = INSTANCE_KEYWORD,
    partial_keyword: str = PARTIAL_KEYWORD,
    fetch_keyword: str = FETCH_KEYWORD,
    _instantiate_recursive: bool = True,
    **extra_kwargs,
) -> Any:
    """Instantiate a single config, optionally recursing into nested configs.

    Args:
        config (Config | dict): The config to instantiate.
        instance_keyword (str): Keyword for full instantiation. Defaults to
            "_instance_".
        partial_keyword (str): Keyword for partial instantiation. Defaults to
            "_partial_".
        fetch_keyword (str): Keyword for fetch-only values. Defaults to
            "_fetch_".
        _instantiate_recursive (bool): Whether to instantiate nested configs.
            Defaults to True.
        **extra_kwargs: Extra keyword arguments merged into the instantiation.

    Returns:
        Any: The instantiated object, partial, or fetched target.

    Raises:
        ValueError: If no valid instantiation keyword is found.
        TypeError: If required parameters are missing for instantiation.
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
    """Determine whether a value contains an instantiation keyword.

    Args:
        value: Value to evaluate.
        instance_keyword (str, optional): Keyword for full instantiation.
            Defaults to "_instance_".
        partial_keyword (str, optional): Keyword for partial instantiation.
            Defaults to "_partial_".
        fetch_keyword (str, optional): Keyword for fetch-only references.
            Defaults to "_fetch_".

    Returns:
        bool: True when the value is a dict with an instantiation keyword.
    """

    return isinstance(value, dict) and any(keyword in value for keyword in [instance_keyword, partial_keyword, fetch_keyword])


def _instance(target: Callable, kwargs: dict, config: Union[Config, Dict[str, Any]]) -> Any:
    """Instantiate a target callable, validating required arguments.

    Args:
        target: Callable to instantiate.
        kwargs (dict): Keyword arguments to pass to the constructor.
        config (Config | dict): Original config used for error messages.

    Returns:
        Any: Instantiated object.

    Raises:
        TypeError: If required parameters are missing.
    """

    # Check for missing parameters
    obj_parameters = inspect.signature(target).parameters
    required_parameters = []
    for param_name, param in obj_parameters.items():
        if param.default != param.empty:
            continue
        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            continue  # Skip **kwargs and *args; they are never required
        if param.kind is inspect.Parameter.POSITIONAL_ONLY:
            continue  # Cannot satisfy positional-only via kwargs; ignore in this check
        required_parameters.append(param_name)

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
    """Create a partial instantiation of a target callable.

    Args:
        target: Callable to partially instantiate.
        kwargs (dict): Keyword arguments to bind.
        config (Config | dict): Original config used for context.

    Returns:
        functools.partial: Partial object with bound arguments.
    """

    return functools.partial(target, **kwargs)


def _fetch(target: Any, kwargs: dict, config: Union[Config, Dict[str, Any]]) -> Any:
    """Return a fetched target reference without instantiation.

    Args:
        target: Object to return directly.
        kwargs (dict): Additional arguments provided in config.
        config (Config | dict): Original config used for context.

    Returns:
        Any: The referenced target.

    Raises:
        ValueError: If extra arguments accompany a fetch config.
    """
    if kwargs != {}:
        raise ValueError(f"Error in config: {config}. Configs instantiated with the _fetch_ keyword cannot have any additional arguments.")

    return target
