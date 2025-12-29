"""Configuration helpers for skeletonkey.

Utilities for resolving configuration paths and building the `unlock`
decorator.

Attributes:
    BASE_PROFILES_KEYWORD (str): YAML key for profiles sections.
    BASE_PROFILE_ARGUMENT_KEYWORD (str): CLI flag used to select profiles.
    BASE_COLLECTION_KEYWORD (str): YAML key for collections/keyrings.
    BASE_CL_CONFIG_KEYWORD (str): CLI flag used to override the config path.
    _COMMAND_LINE_UNLOCK (dict[str, int]): Counter tracking uses of command-line
        config overrides per keyword.
"""

import argparse
import functools
import os
import sys
import warnings
from typing import Callable, Dict, Optional, Set

from .config import (
    parse_initial_args,
    load_yaml_config,
    add_args_from_dict,
    add_yaml_extension,
    namespace_to_config,
    config_to_nested_config,
    Config,
)

BASE_PROFILES_KEYWORD: str = "profiles"
BASE_PROFILE_ARGUMENT_KEYWORD: str = "profile"
BASE_COLLECTION_KEYWORD: str = "keyring"
BASE_CL_CONFIG_KEYWORD: str = "config"


def get_config_dir_path(config_path: str) -> str:
    """Resolve a config path to an absolute directory path.

    Args:
        config_path (str): Relative or absolute path to the configuration file.

    Returns:
        str: Absolute directory containing the configuration file.
    """
    # Check if the given config_path is a relative path
    if not os.path.isabs(config_path):
        # Get the directory of the main script file (entry point) in absolute form
        try:
            path_from_main = os.path.dirname(os.path.abspath(str(sys.modules["__main__"].__file__)))
        except:
            path_from_main = os.getcwd()

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


class UnlockMeta(type):
    _COMMAND_LINE_UNLOCK: Dict[str, int] = {}
    _WRAPPED_FUNCTIONS: Set[int] = set()


class unlock(metaclass=UnlockMeta):
    def __init__(
        self,
        config_name: Optional[str] = None,
        config_dir: Optional[str] = None,
        prefix: Optional[str] = None,
        config_argument_keyword: str = BASE_CL_CONFIG_KEYWORD,
        profiles_keyword: str = BASE_PROFILES_KEYWORD,
        profile_argument_keyword: str = BASE_PROFILE_ARGUMENT_KEYWORD,
        collection_keyword: str = BASE_COLLECTION_KEYWORD,
    ) -> None:
        """Create a decorator that injects parsed YAML configuration into a function.

        Args:
            config_name (Optional[str]): Name or path of the YAML configuration
                file; relative or absolute.
            config_dir (Optional[str]): Directory to resolve the config from;
                defaults to the directory of `config_name`.
            prefix (Optional[str]): Optional prefix to nest this unlock's arguments
                under.
            config_argument_keyword (str): Command line flag to override the config
                path. Defaults to "config".
            profiles_keyword (str): Keyword for profile selection in the YAML.
                Defaults to "profiles".
            profile_argument_keyword (str): Command line flag for selecting
                profiles. Defaults to "profile".
            collection_keyword (str): Keyword for collections in the YAML. Defaults
                to "keyring".

        Returns:
            Callable: Decorator that parses the configuration file and injects the
                resulting arguments into the decorated function.

        Raises:
            ValueError: If neither the decorator nor the command line supplies a
                config path.
        """
        self.prefix = prefix
        self.profiles_keyword = profiles_keyword
        self.collection_keyword = collection_keyword

        parser = argparse.ArgumentParser(allow_abbrev=False, add_help=False)
        initial_args = parse_initial_args(
            arg_parser=parser,
            config_argument_keyword=config_argument_keyword,
            profile_argument_keyword=profile_argument_keyword,
        )
        config_dir_command_line, self.profile, self.profile_specifiers, self.temp_args = initial_args

        if config_dir_command_line is not None:
            config_name = os.path.abspath(config_dir_command_line)
            config_dir = None

            # If they have more than one unlock, warn user than the command-line config will
            # overwrite all the configs for all unlocks.
            unlock._COMMAND_LINE_UNLOCK[config_argument_keyword] = unlock._COMMAND_LINE_UNLOCK.get(config_argument_keyword, 0) + 1
            if unlock._COMMAND_LINE_UNLOCK.get(config_argument_keyword, 0) > 1:
                warnings.warn(
                    f"Multiple @unlock decorators are present with the same command line keyword "
                    + f"'{config_argument_keyword}'. The command line configurations will be used for all @unlock calls."
                )

        if config_name is not None:
            config_dir = get_config_dir_path(os.path.dirname(config_name))
        else:
            raise ValueError("config path is neither specified in 'unlock' nor via the command line.")
        config_name = os.path.basename(add_yaml_extension(config_name))

        self.config_dir = config_dir
        self.config_name = config_name
        self.parser = parser

    def __call__(self, main: Callable) -> Callable:
        @functools.wraps(main)
        def _inner_function(config: Optional[Config] = None):
            config_dict = load_yaml_config(
                config_path=self.config_dir,
                config_name=self.config_name,
                profile=self.profile,
                profile_specifiers=self.profile_specifiers,
                profiles_keyword=self.profiles_keyword,
                collection_keyword=self.collection_keyword,
            )

            add_args_from_dict(
                arg_parser=self.parser,
                config_dict=config_dict,
                prefix=self.prefix + "." if self.prefix is not None else "",
            )

            args_for_parser = sys.argv[1:]
            if args_for_parser and self.profile is not None and args_for_parser[0] == self.profile:
                args_for_parser = args_for_parser[1:]
            elif args_for_parser and not args_for_parser[0].startswith("-"):
                args_for_parser = args_for_parser[1:]

            parsed_args, remaining_args = self.parser.parse_known_args(args_for_parser)
            args = namespace_to_config(parsed_args)

            for temp_arg in self.temp_args:
                del args[temp_arg]

            args = config_to_nested_config(args)

            if config is not None:
                args.update(config)

            sys.argv = [sys.argv[0], *remaining_args]

            if remaining_args and id(main) not in unlock._WRAPPED_FUNCTIONS:
                self.parser.error(f"unrecognized arguments: {' '.join(remaining_args)}")

            return main(args)

        unlock._WRAPPED_FUNCTIONS.add(id(_inner_function))
        return _inner_function
