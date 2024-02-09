# OME-Zarr creation from MD Image Express
import logging
import shutil
from collections.abc import Sequence
from os.path import exists, join
from typing import Any

import distributed
from faim_hcs.hcs.acquisition import TileAlignmentOptions
from faim_hcs.hcs.converter import ConvertToNGFFPlate, NGFFPlate
from faim_hcs.hcs.imagexpress import StackAcquisition
from faim_hcs.hcs.plate import PlateLayout
from faim_hcs.stitching import stitching_utils
from pydantic.decorator import validate_arguments

logger = logging.getLogger(__name__)


@validate_arguments
def md_create_ome_zarr(
    *,
    input_paths: Sequence[str],
    output_path: str,
    metadata: dict[str, Any],
    zarr_name: str = "Plate",
    mode: str = "all",
    # TODO: Verify whether this works for building the manifest
    layout: PlateLayout = 96,
    # query: str = "",  # FIXME: Is filtering still possible?
    order_name: str = "example-order",
    barcode: str = "example-barcode",
    overwrite: bool = True,  # FIXME: Are overwrite checks still possible?
    coarsening_xy: int = 2,  # TODO: Only add to second task?
) -> dict[str, Any]:
    """
    Create OME-Zarr plate from MD Image Xpress files.

    This is a non-parallel task => it parses the metadata, creates the plates
    and then converts all the wells in the same process

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
        coarsening_xy: Linear coarsening factor between subsequent levels.
            If set to `2`, level 1 is 2x downsampled, level 2 is
            4x downsampled etc.

    Returns:
        Metadata dictionary
    """
    if len(input_paths) > 1:
        raise NotImplementedError(
            "MD Create OME-Zarr task is not implemented to handle multiple "
            "input paths"
        )

    # TO REVIEW: Overwrite checks are not exposed in faim-hcs API
    # Unclear how faim-hcs handles rerunning the plate creation
    # (the Zarr file gets a newer timestamp at least)
    # This block triggers a reset
    if overwrite and exists(join(output_path, zarr_name + ".zarr")):
        # Remove zarr if it already exists.
        shutil.rmtree(join(output_path, zarr_name + ".zarr"))

    # TO REVIEW: Any options for using queries / subset filters in new mode?

    # Parse MD plate acquisition.
    # FIXME: Handle different acquisition modes
    plate_acquisition = StackAcquisition(
        acquisition_dir=input_paths[0],
        alignment=TileAlignmentOptions.GRID,
    )

    # TO REVIEW: Check if we want to handle the dask client differently?
    # Is there good auto-detection? Any potential issues with memory handling?
    client = distributed.Client(
        n_workers=1,
        threads_per_worker=1,
        processes=False,
    )

    converter = ConvertToNGFFPlate(
        ngff_plate=NGFFPlate(
            root_dir=output_path,
            name=zarr_name,
            layout=int(layout),
            order_name=order_name,
            barcode=barcode,
        ),
        yx_binning=coarsening_xy,
        # TO REVIEW: Unsure what stitching_yx_chunk_size_factor really does
        stitching_yx_chunk_size_factor=coarsening_xy,
        warp_func=stitching_utils.translate_tiles_2d,
        fuse_func=stitching_utils.fuse_mean,
        client=client,
    )

    plate = converter.create_zarr_plate(plate_acquisition)

    # TODO: Remove hard-coded well sub group? Or make flexible for multiplexing
    well_sub_group = "0"

    # Run conversion.
    converter.run(
        plate=plate,
        plate_acquisition=plate_acquisition,
        well_sub_group=well_sub_group,
        # chunks=(1, 512, 512), # check whether that should be exposed
        # max_layer=2, # check whether that should be exposed
    )

    # Create the metadata dictionary: needs a list of all the images
    plate_name = zarr_name + ".zarr"
    well_paths = []
    image_paths = []
    # TODO: Find a better way than using the internal _wells
    for well in plate_acquisition._wells:
        well_rc = well.get_row_col()
        well_path = f"{plate_name}/{well_rc[0]}/{well_rc[1]}"
        well_paths.append(well_path)

        # To add multiplexing, need to add a bigger image list here
        # (multiple well subgroups)
        image_path = f"{well_path}/{well_sub_group}"
        image_paths.append(image_path)

    metadata_update = {
        "plate": [plate_name],
        "well": well_paths,
        "image": image_paths,
    }

    return metadata_update


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(
        task_function=md_create_ome_zarr,
        logger_name=logger.name,
    )
