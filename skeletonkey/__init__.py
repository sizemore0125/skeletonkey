"""
Author: Logan Sizemore
Date: 4/30/23

This code provides decorator for parsing and injecting configuration arguments into a main function 
and an instantiate funtion that can dynamically instantiate classes with their configurations. 
It facilitates the management of complex configurations for applications using YAML files and enables 
the dynamic loading of classes and their arguments at runtime.
"""

__version__ = "0.0.11"

from .core import unlock, instantiate

# Names to import with wildcard import
__all__ = ["unlock", "instantiate"]