"""Utilities for handling YAML configurations in skeletonkey.

Provides helpers for loading, transforming, and updating configuration data.
"""

import argparse
import copy
import os
import sys
import uuid
from typing import Any, Dict, List, Tuple, Union, Optional

import yaml


class classonlymethod(classmethod):
    def __get__(self, instance, owner=None):
        if instance is not None:
            raise AttributeError(f"{owner.__name__}.unlock() must be called on the class, not an instance.")
        return super().__get__(instance, owner)


class Config:
    def __init__(self, config_dict: Optional[dict] = None):
        """Initialize the config from a dictionary.

        Args:
            config_dict (dict): Source dictionary.
        """
        if config_dict is None:
            config_dict = dict()
        if not isinstance(config_dict, dict):
            raise ValueError("Supplied arg must be a dictionary")
        self._init_from_dict(config_dict)

    def update(self, update_config: Union[dict, "Config"]):
        """Place values from another config into this one.

        This overwrites values if they are present or creates them if they are not.

        Args:
            update_config (dict | Config): Keys/values to place into the config.
                When provided as a dictionary, keys are expected in dot notation.

        Returns:
            Config: The updated config.
        """
        if not isinstance(update_config, Config):
            update_config = config_to_nested_config(Config(update_config))
        self._update_from_config(update_config)
        return self

    def _update_from_config(self, update_config: "Config"):
        """Recursively place values from another config into this one.

        Args:
            update_config (Config): Config whose values should be merged.
        """
        for k, v in update_config.__dict__.items():

            if isinstance(v, Config):
                if k not in self.__dict__.keys():
                    self[k] = Config({})

                self[k]._update_from_config(update_config[k])

            else:
                self[k] = update_config[k]

    def _init_from_dict(self, dictionary: dict):
        """Initialize the config from a dictionary.

        Args:
            dictionary (dict): The dictionary to be converted.
        """
        for key, value in dictionary.items():
            if isinstance(value, dict):
                value = Config(value)

            self[key] = value

    def __getitem__(self, key: str):
        return self.__getattribute__(key)

    def __setitem__(self, key: str, value):
        self.__setattr__(key, value)

    def __delitem__(self, key: str):
        self.__delattr__(key)

    def __str__(self):
        return self._subconfig_str(self, 0)[1:]

    def __repr__(self):
        return f"Config({self._subconfig_str(self, 1)})"

    def __call__(self, **kwargs):
        return self.instantiate(**kwargs)

    def __getattr__(self, name):
        message = f"'Config' object has no attribute '{name}'."
        raise AttributeError(message + f" Please specify '{name}' in your config yaml.")

    def __iter__(self):
        return iter(self._to_dict(self).items())

    def instantiate(self, **kwargs):
        from .instantiate import instantiate

        return instantiate(self, **kwargs)

    def _subconfig_str(self, subspace: "Config", tab_depth: int):
        """Convert a given subconfig to a string with the given tab-depth.

        Args:
            subspace (Config): Config to render.
            tab_depth (int): Current tab depth.

        Returns:
            str: Rendered subconfig string.
        """
        s = ""
        for k, v in subspace.__dict__.items():
            if not k.startswith("_Config__"):
                s += "\n" + "  " * tab_depth + k + ": "

                if isinstance(v, Config):
                    s += "\n"
                    s += self._subconfig_str(v, tab_depth + 1)[1:]  # [1:] gets rid of uneccesary leading \n
                else:
                    s += str(v)

        return s

    def to_dict(self) -> dict:
        return self._to_dict(self)

    def _to_dict(self, subspace: "Config"):
        config_dict = {}
        for k, v in subspace.__dict__.items():
            if not k.startswith("_Config__"):
                if isinstance(v, Config):
                    config_dict[k] = self._to_dict(v)
                else:
                    config_dict[k] = v
        return config_dict

    def copy(self):
        return Config(copy.deepcopy(self.to_dict()))

    def to_yaml(self, path: str, **kwargs) -> str:
        """Save Config to YAML at the given path.

        Extra `yaml.safe_dump` kwargs can be passed via `kwargs`.

        Args:
            path (str): Destination path for the YAML file.
            **kwargs: Extra keyword arguments forwarded to `yaml.safe_dump`.

        Returns:
            str: The saved path.
        """
        config_dict = self.to_dict()
        with open(path, "w") as f:
            yaml.safe_dump(config_dict, f, sort_keys=False, **kwargs)
        return path

    @classonlymethod
    def unlock(
        cls,
        config_name: Optional[str] = None,
        config_dir: Optional[str] = None,
        prefix: Optional[str] = None,
        config_argument_keyword: str = "config",
        profiles_keyword: str = "profiles",
        profile_argument_keyword: str = "profile",
        collection_keyword: str = "keyring",
    ) -> "Config":
        """Load a YAML config using the same parsing flow as ``@unlock``.

        Args:
            config_name (Optional[str]): Name or path of the YAML configuration
                file; relative or absolute.
            config_dir (Optional[str]): Directory to resolve the config from.
            prefix (Optional[str]): Optional prefix to nest this unlock's
                arguments under.
            config_argument_keyword (str): Command line flag to override the
                config path. Defaults to "config".
            profiles_keyword (str): Keyword for profile selection in the YAML.
                Defaults to "profiles".
            profile_argument_keyword (str): Command line flag for selecting
                profiles. Defaults to "profile".
            collection_keyword (str): Keyword for collections in the YAML.
                Defaults to "keyring".

        Returns:
            Config: Parsed configuration.

        Raises:
            ValueError: If neither the method nor the command line supplies a
                config path.
        """
        from .core import get_config_dir_path

        parser = argparse.ArgumentParser(allow_abbrev=False, add_help=False)
        config_dir_command_line, profile, profile_specifiers, temp_args = parse_initial_args(
            arg_parser=parser,
            config_argument_keyword=config_argument_keyword,
            profile_argument_keyword=profile_argument_keyword,
        )

        if config_dir_command_line is not None:
            config_name = os.path.abspath(config_dir_command_line)
            config_dir = None

        if config_name is not None:
            config_dir = get_config_dir_path(os.path.dirname(config_name))
        else:
            raise ValueError("config path is neither specified in 'Config.unlock' nor via the command line.")

        config_name = os.path.basename(add_yaml_extension(config_name))

        config_dict = load_yaml_config(
            config_path=config_dir,
            config_name=config_name,
            profile=profile,
            profile_specifiers=profile_specifiers,
            profiles_keyword=profiles_keyword,
            collection_keyword=collection_keyword,
        )

        parser_prefix = prefix + "." if prefix is not None else ""
        add_args_from_dict(
            arg_parser=parser,
            config_dict=config_dict,
            prefix=parser_prefix,
        )

        args_for_parser = sys.argv[1:]
        while args_for_parser and not args_for_parser[0].startswith("-"):
            args_for_parser = args_for_parser[1:]

        parsed_args, remaining_args = parser.parse_known_args(args_for_parser)
        args = namespace_to_config(parsed_args)

        for temp_arg in temp_args:
            del args[temp_arg]

        args = config_to_nested_config(args)
        interpolate_config(args)

        if remaining_args:
            parser.error(f"unrecognized arguments: {' '.join(remaining_args)}")

        return args


def find_yaml_path(file_path: str) -> str:
    """Resolve a file path to an existing YAML file.

    Checks for either `.yml` or `.yaml` extensions and returns the correct path.

    Args:
        file_path (str): File path without extension or with either `.yml` or
            `.yaml` extension.

    Returns:
        str: Path with the existing YAML extension.

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
    """Read and parse the YAML file located at the given path.

    Args:
        path (str): File path to the YAML file.

    Returns:
        dict: YAML content.
    """
    path = find_yaml_path(path)
    with open(os.path.expanduser(path), "r") as handle:
        return yaml.safe_load(handle)


def dict_to_path(dictionary: dict, parent_key="") -> List[str]:
    """Flatten a nested dictionary into path-like strings.

    Args:
        dictionary (dict): Nested dictionary to be flattened.
        parent_key (str, optional): Initial parent key. Defaults to "".

    Returns:
        List[str]: Flattened paths derived from keys and list values.
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
    """Append the `.yaml` extension to a path if missing.

    Args:
        path (str): Input file path or name.

    Returns:
        str: Path with a YAML extension.
    """
    yaml_extention1 = ".yaml"
    yaml_extention2 = ".yml"
    if not path.endswith(yaml_extention1) and not path.endswith(yaml_extention2):
        path += yaml_extention1
    return path


def load_yaml_config(
    config_path: str,
    config_name: str,
    profile: str,
    profile_specifiers: List[str],
    profiles_keyword: str,
    collection_keyword: str,
) -> dict:
    """Load a YAML configuration file and update with profiles and collections.

    Args:
        config_path (str): File path to the YAML configuration file.
        config_name (str): Name of the YAML configuration file.
        profile (str): Selected profile name, if provided.
        profile_specifiers (List[str]): Additional dotted profile specifiers to
            merge into the selected profile.
        profiles_keyword (str): Keyword used to identify profiles in the YAML
            file. Defaults to "profiles".
        collection_keyword (str): Keyword used to identify collections in the
            YAML file. Defaults to "keyring".

    Returns:
        dict: The updated configuration dictionary.
    """
    path = os.path.join(config_path, config_name)
    config = open_yaml(path)

    if profiles_keyword in config:
        unpack_profiles(config, config_path, profile, profile_specifiers, profiles_keyword)

    if collection_keyword in config:
        unpack_collection(config, config_path, collection_keyword)

    return config


def override_profile_with_specifier(profile_dict: dict, specifier: str, config: dict) -> None:
    """Merge a subconfig referenced by a specifier into a profile.

    If the referenced section does not exist in the profile, it will be created;
    otherwise, it will be overwritten.

    Args:
        profile_dict (dict): Dictionary holding the profile to be overwritten.
        specifier (str): Dot-notation specifier referencing which subconfig to
            bring into the profile.
        config (dict): Profiles config dictionary holding all of the profiles.

    Raises:
        ValueError: If the specifier cannot be matched to any profiles.
    """

    alt_profile, *split_specifier, final_key = specifier.split(".")
    config = config[alt_profile]

    for key in split_specifier:
        if key not in config:
            raise ValueError(f"The given profile specifier ({specifier}) can't be matched to any profiles.")
        elif key not in profile_dict.keys():
            profile_dict[key] = {}

        config = config[key]
        profile_dict = profile_dict[key]

    profile_dict[final_key] = config[final_key]


def get_default_args_from_path(config_path: str, default_yaml: str) -> dict:
    """Load a YAML default configuration file and return its arguments.

    Args:
        config_path (str): File path to the YAML base configuration file.
        default_yaml (str): Relative path to the default YAML subconfiguration
            file.

    Returns:
        dict: The loaded configuration dictionary.
    """
    default_yaml = add_yaml_extension(default_yaml)
    default_config_path = os.path.join(config_path, default_yaml)
    default_config = open_yaml(default_config_path)
    return default_config


def unpack_profiles(
    config,
    config_path: str,
    profile: str,
    profile_specifiers: List[str],
    profiles_keyword: str,
):
    """Resolve a profiles section by selecting and merging referenced configs.

    Args:
        config (dict): Loaded base config containing a profiles section.
        config_path (str): Base path to resolve referenced YAML files.
        profile (str): Selected profile name (or None to use the default "~"
            profile).
        profile_specifiers (List[str]): Dotted specifiers to merge additional
            profile fragments.
        profiles_keyword (str): Key name in the config that holds profiles.

    Raises:
        ValueError: If profile selection or default profile resolution is invalid.
    """
    default_paths = None

    if isinstance(config[profiles_keyword], dict):
        # Get the default profile or the given profile
        default_profile = []
        for key, val in list(config[profiles_keyword].items()):
            if key[0] == "~":
                default_profile.append(key[1:])

                config[profiles_keyword][key[1:]] = val
                del config[profiles_keyword][key]

        if len(default_profile) > 1:
            raise ValueError("Only one profile may be specified as default.")
        elif len(default_profile) == 0 and profile is None:
            raise ValueError("You must specify a profile or assign one to as default using the '~' prefix.")
        elif profile is None:
            profile = default_profile[0]

        # If a profile is simply a path to another config, convert it to a profile_dict.
        profile_select = config[profiles_keyword][profile]
        if isinstance(profile_select, dict):
            profile_dict = profile_select
        elif isinstance(profile_select, str):
            profile_dict_key = str(uuid.uuid4())
            profile_dict = {profile_dict_key: profile_select}
        else:
            raise ValueError(f" The value '{profile_select}' is not valid for profiles.")

        for specifier in profile_specifiers:
            override_profile_with_specifier(profile_dict, specifier, config[profiles_keyword])

        # Perform BFS on the profile to get all of the paths
        default_paths = []
        queue = [profile_dict]
        while len(queue) != 0:
            current_subdict = queue.pop(0)
            for k, v in current_subdict.items():
                if isinstance(v, dict):
                    queue.append(v)
                elif isinstance(v, str):
                    default_paths.append(v)
                elif isinstance(v, list):
                    default_paths.extend(v)
                else:
                    ValueError(f"The type of {v} ({type(v)}) is not a valid path to a default config.")

    elif isinstance(config[profiles_keyword], list):
        default_paths = config[profiles_keyword]

    elif isinstance(config[profiles_keyword], str):
        default_paths = [config[profiles_keyword]]

    else:
        ValueError(f" The value '{config[profiles_keyword]}' is not valid for profiles.")

    # Apply all of the paths to the config
    for default_path in default_paths:
        default_config = get_default_args_from_path(config_path, default_path)

        if default_config:
            config.update((key, value) for key, value in default_config.items() if key not in config)

    del config[profiles_keyword]


def unpack_collection(config: dict, config_path: str, collection_keyword: str):
    """Expand a keyring/collection section into concrete subconfigs.

    Args:
        config (dict): Loaded base config containing a collection section.
        config_path (str): Base path to resolve referenced YAML files.
        collection_keyword (str): Key name in the config that holds the
            collection definitions.

    Raises:
        ValueError: If a collection name conflicts with an existing argument.
    """
    collections_dict = config[collection_keyword]

    for collection_key in collections_dict.keys():
        if collection_key in config:
            raise ValueError("You cannot have a collection with the same name as an argument.")

        collection_entry = collections_dict[collection_key]

        if isinstance(collection_entry, dict):
            # The collection entry contains multiple sub-entries, add all of them to the sub-config
            config[collection_key] = {}
            for subconfig_key in collection_entry.keys():
                subconfig = get_default_args_from_path(config_path, collection_entry[subconfig_key])
                config[collection_key].update({subconfig_key: subconfig})
        else:
            # The collection entry is a single entry, add it to the config
            subconfig = get_default_args_from_path(config_path, collection_entry)
            config[collection_key] = subconfig

    del config[collection_keyword]


def interpolate_config(config, root_config=None):
    """
    Recursively search through a config and replace any string values enclosed in a dollar sign
    and brackets. For example: ${key.in.config}.

    The string value will be treated as a dot notation reference to another value in the config.
    That value will be extracted and placed in the original string's location, modifying the config
    in place.

    If that value is not found, a ValueError will be raised.

    Args:
        config (any): The sub-config to be searched for interpolations. This can be any yaml value,
            but it will be ignored if it is not a dictionary, list, or Config.
        root_config (Any): The root config where any referenced values are extracted from by the
            interpolation. If not specified, the root config is assumed to be the config itself.

    """
    if root_config is None:
        root_config = config

    if isinstance(config, Config):
        items = ((key, value) for key, value in config.__dict__.items() if not key.startswith("_Config__"))
    elif isinstance(config, dict):
        items = config.items()
    elif isinstance(config, list):
        items = enumerate(config)
    else:
        return

    for key, value in items:
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            config[key] = _interpolate_value(value[2:-1], root_config)
        else:
            interpolate_config(value, root_config)


def _interpolate_value(reference: str, root_config: Any) -> Any:
    """
    Given a config key in dot notation, extract the reference to another value in the config and return that value.

    Args:
        reference (str): The dot notation reference to another value in the config.
        root_config (Any): The root config where the referenced value is extracted from.

    Returns:
        any: The value indicated by the dot notation reference.
    """
    keys = reference.split(".")
    current_dict = root_config
    for key in keys:
        if isinstance(current_dict, Config):
            if key not in current_dict.__dict__:
                raise ValueError(f"Error while interpolating: {reference} is not a valid reference to a config value.")
            current_dict = current_dict[key]
        elif isinstance(current_dict, dict):
            if key not in current_dict:
                raise ValueError(f"Error while interpolating: {reference} is not a valid reference to a config value.")
            current_dict = current_dict[key]
        elif isinstance(current_dict, list):
            try:
                current_dict = current_dict[int(key)]
            except (ValueError, IndexError):
                raise ValueError(f"Error while interpolating: {reference} is not a valid reference to a config value.")
        else:
            raise ValueError(f"Error while interpolating: {reference} is not a valid reference to a config value.")
    return current_dict


def add_args_from_dict(arg_parser: argparse.ArgumentParser, config_dict: dict, prefix="") -> None:
    """Add arguments to an ArgumentParser from a configuration dictionary.

    If the dictionary contains a nested dictionary, the argument will be added
    as `--key.key value`.

    Args:
        arg_parser (argparse.ArgumentParser): ArgumentParser instance to extend.
        config_dict (dict): Key-value pairs representing arguments and defaults.
        prefix (str, optional): Prefix string for nested keys. Defaults to "".
    """
    for key, value in config_dict.items():
        if isinstance(value, dict):
            add_args_from_dict(arg_parser, value, f"{prefix}{key}.")
        else:
            if key.startswith("$"):
                if key[1:] in os.environ:
                    value = os.environ[key[1:]]
                arg_parser.add_argument(f"--{prefix}{key[1:]}", default=value)
            elif key.startswith("?"):
                if not isinstance(value, bool):
                    raise ValueError(f"Flag '{prefix}{key[1:]}' must be a boolean in the config.")
                action = "store_false" if value else "store_true"
                arg_parser.add_argument(f"--{prefix}{key[1:]}", default=value, action=action)
            else:
                arg_parser.add_argument(f"--{prefix}{key}", default=value)


def namespace_to_config(flat_config: argparse.Namespace) -> Config:
    """Parse argparse Namespace values as YAML and return a Config.

    Args:
        flat_config (argparse.Namespace): Flat Config whose values should be parsed.

    Returns:
        Config: Config with parsed values.
    """
    return Config({key: yaml.safe_load(value) if isinstance(value, str) else value for key, value in vars(flat_config).items()})


def parse_initial_args(
    arg_parser: argparse.ArgumentParser,
    config_argument_keyword: str,
    profile_argument_keyword: str,
) -> Tuple[Any, Any, Any, list[str]]:
    """Parse initial CLI arguments for config and profile information.

    Args:
        arg_parser (argparse.ArgumentParser): Argparse object to add the config
            arg to.
        config_argument_keyword (str): Default keyword to accept new config path
            from the command line.
        profile_argument_keyword (str): Command line keyword for selecting
            profiles. Defaults to "profile".

    Returns:
        Tuple[Any, Any, List[str], List[str]]: Config path, specified profile,
            profile specifiers, and argument names to ignore later.
    """

    arg_parser.add_argument(f"--{config_argument_keyword}", default=None, type=str)
    arg_parser.add_argument(
        f"--{profile_argument_keyword}", metavar="Profile Specifiers", dest="_profile_specifiers", type=str, nargs="*", default=[]
    )

    args_list = sys.argv[1:]
    profile = None
    positional_profile_specifiers = []
    while len(args_list) > 0 and not args_list[0].startswith("-"):
        positional_profile_specifiers.append(args_list[0])
        args_list = args_list[1:]

    if len(positional_profile_specifiers) > 0 and "." not in positional_profile_specifiers[0]:
        profile = positional_profile_specifiers[0]
        del positional_profile_specifiers[0]

    known_args, _ = arg_parser.parse_known_args(args_list)

    profile_specifiers = positional_profile_specifiers + known_args._profile_specifiers

    if len(profile_specifiers) > 0 and "." not in profile_specifiers[0]:
        if profile is not None:
            raise ValueError(f"Cannot specify profile in two places: {profile} vs. {profile_specifiers[0]}")
        profile = profile_specifiers[0]
        del profile_specifiers[0]

    config_path = getattr(known_args, config_argument_keyword)
    return config_path, profile, profile_specifiers, [config_argument_keyword, "_profile_specifiers"]


def config_to_nested_config(config: Config) -> Config:
    """Convert a Config with dotted keys into a nested Config object.

    Args:
        config (Config): Config object to be converted.

    Returns:
        Config: Nested Config representation of the input.
    """
    nested_dict: Dict[str, Any] = {}
    for key, value in vars(config).items():
        keys = key.split(".")
        current_dict = nested_dict
        for sub_key in keys[:-1]:
            if sub_key not in current_dict:
                current_dict[sub_key] = {}
            current_dict = current_dict[sub_key]
        current_dict[keys[-1]] = value

    return Config(nested_dict)
