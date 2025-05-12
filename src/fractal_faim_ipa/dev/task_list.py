"""Fractal Task list for Fractal Helper Tasks."""

from fractal_task_tools.task_models import ConverterNonParallelTask

DOCS_LINK = "https://github.com/fractal-analytics-platform/fractal-faim-ipa"
INPUT_MODELS = [
    ["fractal_faim_ipa", "converter_utils.py", "AcquisitionInputModel"],
]
TASK_LIST = [
    ConverterNonParallelTask(
        name="Convert MD to OME-Zarr",
        executable="convert_md_to_ome_zarr.py",
        meta={"cpus_per_task": 8, "mem": 32000},
        category="Conversion",
        modality="HCS",
        tags=["Molecular Devices", "Image Xpress", "MD"],
        docs_info="file:task_info/md_converter.md",
    ),
    ConverterNonParallelTask(
        name="FAIM-IPA Convert Cellvoyager to OME-Zarr",
        executable="convert_cellvoyager_to_ome_zarr.py",
        meta={"cpus_per_task": 8, "mem": 32000},
        category="Conversion",
        modality="HCS",
        tags=["Molecular Devices", "Image Xpress", "MD"],
        docs_info="file:task_info/md_converter.md",
    ),
]
