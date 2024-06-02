"""Fractal Task list for Fractal Helper Tasks."""

from fractal_tasks_core.dev.task_models import NonParallelTask

TASK_LIST = [
    NonParallelTask(
        name="FAIM IPA OME-Zarr Converter",
        executable="convert_ome_zarr.py",
        meta={"cpus_per_task": 8, "mem": 32000},
    ),
]
