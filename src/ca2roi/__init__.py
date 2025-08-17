"""Calcium imaging ROI and bleaching analysis CLI tool."""

try:
    from importlib.metadata import version, PackageNotFoundError

    __version__ = version("ca2roi")
except PackageNotFoundError:
    # Package is not installed, fallback to development version
    __version__ = "0.0.0-dev"

__all__ = ["__version__"]
