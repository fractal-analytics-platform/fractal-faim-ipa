"""Provides Fractal tasks for the MD to OME-Zarr conversion of faim-hcs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal-faim-hcs")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Joel Luethi"
__email__ = "joel.luethi@uzh.ch"
