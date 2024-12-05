# fractal-faim-ipa

[![License](https://img.shields.io/pypi/l/fractal-faim-ipa.svg?color=green)](https://github.com/jluethi/fractal-faim-ipa/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fractal-faim-ipa.svg?color=green)](https://pypi.org/project/fractal-faim-ipa)
[![Python Version](https://img.shields.io/pypi/pyversions/fractal-faim-ipa.svg?color=green)](https://python.org)
[![CI](https://github.com/jluethi/fractal-faim-ipa/actions/workflows/ci.yml/badge.svg)](https://github.com/jluethi/fractal-faim-ipa/actions/workflows/ci.yml)

Provides Fractal tasks for the conversion of Molecular Devices ImageXpress microscope to OME-Zarr.

The conversion based on the [faim-ipa library](https://github.com/fmi-faim/faim-ipa). This repo also contains some of the test data from the faim-ipa library, as well as test data from the ZMB provided by @fstur.

## Installation
Install this package as:

```
pip install fractal-faim-ipa
```

## Adding tasks to Fractal server
You can add these Fractal tasks to a server by using the pypi installation and specifying the task name fractal-faim-ipa

## Making releases
1. Merge PR into main
2. Locally checkout main
3. Tag the release: git tag v0.4.3
4. Push the tag to Github: git push origin v0.4.3

The github workflow will then publish this release to PyPI & create a Github release with the corresponding whl file.
