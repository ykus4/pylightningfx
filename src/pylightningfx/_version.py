"""Package version, resolved from installed distribution metadata."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pylightningfx")
except PackageNotFoundError:  # pragma: no cover - running from an uninstalled source tree
    __version__ = "0.0.0.dev0"
