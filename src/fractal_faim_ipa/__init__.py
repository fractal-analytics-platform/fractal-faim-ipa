"""Provides Fractal tasks for the MD to OME-Zarr conversion of faim-ipa."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal-faim-ipa")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Joel Luethi"
__email__ = "joel.luethi@uzh.ch"
