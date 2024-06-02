# fractal-faim-ipa

[![License](https://img.shields.io/pypi/l/fractal-faim-ipa.svg?color=green)](https://github.com/jluethi/fractal-faim-ipa/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fractal-faim-ipa.svg?color=green)](https://pypi.org/project/fractal-faim-ipa)
[![Python Version](https://img.shields.io/pypi/pyversions/fractal-faim-ipa.svg?color=green)](https://python.org)
[![CI](https://github.com/jluethi/fractal-faim-ipa/actions/workflows/ci.yml/badge.svg)](https://github.com/jluethi/fractal-faim-ipa/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jluethi/fractal-faim-ipa/branch/main/graph/badge.svg)](https://codecov.io/gh/jluethi/fractal-faim-ipa)

Provides Fractal tasks for the conversion of Molecular Devices ImageXpress microscope to OME-Zarr.

The conversion based on the [faim-ipa library](https://github.com/fmi-faim/faim-ipa). This repo also contains some of the test data from the faim-ipa library, as well as test data from the ZMB provided by @fstur.

To use the MD Converter Task in Fractal, add the package form PyPI to your Fractal server by installing fractal-faim-ipa.

## Development
You can install it locally in this way:

```
git clone https://github.com/jluethi/fractal-faim-ipa
cd fractal-faim-ipa
pip install -e .
```

### Adding tasks to Fractal server
You can trigger a manual collection of the tasks:
1. Create a package wheel: 
```
pip install build
python -m build
```

This wheel is put into the `dist` folder. 

2. Collect your package from Fractal web: use the local task collection in fractal web and provide the `/path/to/package/dist/faim-ipa-version-details.whl`

Alternatively, you can collect the task in Fractal via the CLI tool:
```
fractal task collect /path/to/package/dist/faim-ipa-version-details.whl
```
