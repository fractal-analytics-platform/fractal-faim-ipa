# Convert a well of MD Image Xpress data to OME-Zarr
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import zarr
from faim_hcs.Zarr import (
    write_cyx_image_to_well,
    write_czyx_image_to_well,
    write_roi_table,
)
from fractal_faim_hcs.parse_zmb import parse_files_zmb
from pydantic.decorator import validate_arguments

logger = logging.getLogger(__name__)


@validate_arguments
def md_to_ome_zarr(
    *,
    input_paths: Sequence[str],
    output_path: str,
    component: str,
    metadata: dict[str, Any],
    grid_montage: bool = True,
) -> dict[str, Any]:
    """
    Converts the image data from the MD image Xpress into OME-Zarr.

    Args:
        input_paths: List of paths to the input files (Fractal managed)
        output_path: Path to the output file (Fractal managed)
        component: Component name, e.g. "plate_name.zarr/B/03/0"
                      (Fractal managed)
        metadata: Metadata dictionary (Fractal managed)
        grid_montage: Force FOVs into closest grid cells
        memory_efficient: Load images via dask (more memory efficient for 3D)

    Returns:
        Metadata dictionary (no updated metadata => empty dict)
    """
    channels = metadata["channels"]
    well = component.split("/")[1] + component.split("/")[2].zfill(2)
    mode = metadata["mode"]
    images_path = metadata["original_paths"][0]
    query = metadata["query"]

    if grid_montage:
        montage_fn = montage_grid_image_YX
    else:
        montage_fn = montage_stage_pos_image_YX

    valid_modes = ("z-steps", "top-level", "all", "zmb")
    if mode not in valid_modes:
        raise NotImplementedError(
            f"Only implemented for modes {valid_modes}, but got mode {mode=}"
        )

    # TODO: Only open the image in the well, not the whole plate to avoid
    # concurrency issues?
    # Can probably build this from input_path + component?
    plate = zarr.open(Path(output_path) / component.split("/")[0], mode="r+")

    if mode == "zmb":
        files, mode = parse_files_zmb(images_path, query)
    else:
        if not query == "":
            raise NotImplementedError("Filtering is only implemented in zmb mode")
        files = parse_files(images_path, mode=mode)

    well_files = files[files["well"] == well]

    # Get the zeroth field of the well.
    field: zarr.Group = plate[well[0]][str(int(well[1:]))][0]

    if mode == "all":
        projection_files = well_files[well_files["z"].isnull()]
        stack_files = well_files[~well_files["z"].isnull()]

        if len(stack_files) == 0:
            raise ValueError(
                f"Could not find any 3D stack files for well {well} in "
                f"{images_path}, but {mode=} was selected."
            )
        if len(projection_files) == 0:
            raise ValueError(
                f"Could not find any 2D files for well {well} in "
                f"{images_path}, but {mode=} was selected."
            )

        (
            projection,
            proj_hists,
            proj_ch_metadata,
            proj_metadata,
            proj_roi_tables,
        ) = get_well_image_CYX(
            well_files=projection_files,
            channels=channels,
            assemble_fn=montage_fn,
        )
        # Should we also write proj_roi_tables? Unclear whether we should have
        # separate ROI tables for projections

        # Create projections group
        projections = field.create_group("projections")

        # Write projections
        write_cyx_image_to_well(
            projection, proj_hists, proj_ch_metadata, proj_metadata, projections, True
        )

    else:
        stack_files = well_files

    if mode == "top-level":
        img, hists, ch_metadata, metadata, roi_tables = get_well_image_CYX(
            well_files=stack_files,
            channels=channels,
            assemble_fn=montage_fn,
        )
        write_cyx_image_to_well(img, hists, ch_metadata, metadata, field)
    else:
        (
            stack,
            stack_hist,
            stack_ch_metadata,
            stack_metadata,
            roi_tables,
        ) = get_well_image_CZYX_callable(
            well_files=stack_files,
            channels=channels,
            assemble_fn=montage_fn,
        )
        write_czyx_image_to_well(
            stack, stack_hist, stack_ch_metadata, stack_metadata, field, True
        )

    # Write all ROI tables
    for roi_table in roi_tables:
        write_roi_table(roi_tables[roi_table], roi_table, field)

    return {}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(
        task_function=md_to_ome_zarr,
        logger_name=logger.name,
    )
