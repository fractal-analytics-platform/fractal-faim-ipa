# fractal-faim-hcs

[![License](https://img.shields.io/pypi/l/fractal-faim-hcs.svg?color=green)](https://github.com/jluethi/fractal-faim-hcs/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fractal-faim-hcs.svg?color=green)](https://pypi.org/project/fractal-faim-hcs)
[![Python Version](https://img.shields.io/pypi/pyversions/fractal-faim-hcs.svg?color=green)](https://python.org)
[![CI](https://github.com/jluethi/fractal-faim-hcs/actions/workflows/ci.yml/badge.svg)](https://github.com/jluethi/fractal-faim-hcs/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jluethi/fractal-faim-hcs/branch/main/graph/badge.svg)](https://codecov.io/gh/jluethi/fractal-faim-hcs)

Provides Fractal tasks for the MD to OME-Zarr conversion of faim-hcs

Example data is from https://github.com/fmi-faim/faim-hcs, just in this repo to allow easier automated testing.

While the package is not on pypi yet, you can install it locally in this way:

```
git clone https://github.com/jluethi/fractal-faim-hcs
cd fractal-faim-hcs
pip install -e .
```

### Adding tasks to Fractal server
While the package is not on pypi yet, you can trigger a manual collection of the tasks:
1. Create a package wheel: 
```
pip install build
python -m build
```
This wheel is put into the `dist` folder. To collect the task in Fractal, one can load the Python wheel (see instructions below):
```
fractal task collect /path/to/faim-hcs-version-details.whl
```

### Developer notes on manual task collection
To create a new Fractal task, one needs to create a linux executable (e.g. a Python file with a `if __name__ == "__main__":` section) and this executable needs to follow the Fractal standards on how to read in inputs & store outputs ([see details here](https://fractal-analytics-platform.github.io/fractal-tasks-core/task_howto.html)). Fractal tasks use pydantic for input validation.

To make the task installable by a Fractal server, there needs to be a `__FRACTAL_MANIFEST__.json` file in the src/fractal_faim_hcs folder. This file contains a list of all available tasks and their schemas, as created by the dev tools from the dev folder.

The manifest needs to be included when a package is built.

For local creation of a Python whl, it means that the setup.cfg contains the following:
```
[options.package_data]
faim_hcs = __FRACTAL_MANIFEST__.json
```

For projects like this one using a pyproject.toml, that is not necessary anymore.


### Working with a Fractal task in development
The above instructions work well to install the Fractal task as it is available in the package. If you want to run a task through Fractal server that you keep changing, it's not advisable to use the fractal task collection, but instead manually register your task.

For that purpose, create a Python environment that the task runs in (with all dependencies installed) and then use manual task registration pointing to the task Python file that you're working with. [See here for an example](https://github.com/fractal-analytics-platform/fractal-demos/tree/d241c7e29e5016bca6e0fd7647f44947e1501509/examples/08_scMultipleX_task).

For example, add this via the web interface:
```
command: /path/to/python-env/fractal-faim-hcs-dev/bin/python /path/to/fractal-faim-hcs/src/fractal_faim_hcs/create_ome_zarr_md.py
source: local:create-ome-zarr-md:0.0.1
input type: image
output type: zarr
```

Then set the default args correctly for the task:
```
fractal task edit 9 --meta-file /path/to/fractal-faim-hcs/examples/fractal/meta_create_ome_zarr_md.json
```
