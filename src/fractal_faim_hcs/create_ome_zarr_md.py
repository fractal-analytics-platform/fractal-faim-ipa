# OME-Zarr creation from MD Image Express
import logging
import shutil
from collections.abc import Sequence
from os.path import exists, join
from typing import Any

from faim_hcs.io.MolecularDevicesImageXpress import parse_files
from faim_hcs.Zarr import build_zarr_scaffold
from pydantic.decorator import validate_arguments

from fractal_faim_hcs.parse_zmb import parse_files_zmb

logger = logging.getLogger(__name__)


@validate_arguments
def create_ome_zarr_md(
    *,
    input_paths: Sequence[str],
    output_path: str,
    metadata: dict[str, Any],
    zarr_name: str = "Plate",
    mode: str = "all",
    layout: int = 96,
    query: str = "",
    order_name: str = "example-order",
    barcode: str = "example-barcode",
    overwrite: bool = True,
    num_levels=5,
) -> dict[str, Any]:
    """
    Create OME-Zarr plate from MD Image Xpress files.

    Args:
        input_paths: List of paths to the input files (Fractal managed)
        output_path: Path to the output file (Fractal managed)
        metadata: Metadata dictionary (Fractal managed)
        zarr_name: Name of the zarr plate file that will be created
        mode: Mode can be 4 values: "z-steps" (only parse the 3D data),
                 "top-level" (only parse the 2D data), "all" (parse both),
                 "zmb" (zmb-parser, detect mode automatically)
        layout: Plate layout for the Zarr file. Valid options are 96 and 384
        query: Pandas query to filter intput-filenames
        order_name: Name of the order
        barcode: Barcode of the plate
        overwrite: Whether to overwrite the zarr file if it already exists
        num_levels: Number of levels to generate in the zarr file
    Returns:
        Metadata dictionary
    """
    # FIXME: Find a way to figure out here how many levels will be generated
    # (to be able to put it into the num_levels metadata)
    # Currently, we're asking the user or setting it to 5, even if there are
    # a different number of pyramids then created. The calculation of levels
    # is only done during the actual conversion though, so that's tricky.
    if len(input_paths) > 1:
        raise NotImplementedError(
            "MD Create OME-Zarr task is not implemented to handle multiple input paths"
        )
    order_name = (order_name,)

    valid_modes = ("z-steps", "top-level", "all", "zmb")
    if mode not in valid_modes:
        raise NotImplementedError(
            f"Only implemented for modes {valid_modes}, but got mode {mode=}"
        )
    if mode == "zmb":
        files, _ = parse_files_zmb(input_paths[0], query)
    else:
        if not query == "":
            raise NotImplementedError("Filtering is only implemented in zmb mode")
        files = parse_files(input_paths[0], mode=mode)

    if overwrite and exists(join(output_path, zarr_name + ".zarr")):
        # Remove zarr if it already exists.
        shutil.rmtree(join(output_path, zarr_name + ".zarr"))

    # Build empty zarr plate scaffold.
    build_zarr_scaffold(
        root_dir=output_path,
        name=zarr_name,
        files=files,
        layout=layout,
        order_name=order_name,
        barcode=barcode,
    )

    # Create the metadata dictionary
    plate_name = zarr_name + ".zarr"
    well_paths = []
    image_paths = []
    for well in sorted(files["well"].unique()):
        curr_well = plate_name + "/" + well[0] + "/" + str(int(well[1:])) + "/"
        well_paths.append(curr_well)
        image_paths.append(curr_well + "0/")

    metadata_update = {
        "plate": [plate_name],
        "well": well_paths,
        "image": image_paths,
        "num_levels": num_levels,
        "coarsening_xy": 2,
        "channels": sorted(files["channel"].unique().tolist()),
        "mode": mode,
        "query": query,
        "original_paths": input_paths[:],
    }
    return metadata_update


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(
        task_function=create_ome_zarr_md,
        logger_name=logger.name,
    )
