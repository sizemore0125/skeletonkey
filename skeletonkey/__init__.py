"""Public API surface for SkeletonKey.

Provides helpers for parsing YAML-based configurations into CLI arguments and
for instantiating classes from those configurations.

Attributes:
    __version__ (str): skeletonkey package version.
"""

__version__ = "0.3.2.0"

from .core import unlock, Config
from .instantiate import instantiate

# Names to import with wildcard import
__all__ = ["unlock", "instantiate", "Config"]
