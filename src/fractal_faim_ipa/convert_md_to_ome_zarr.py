# OME-Zarr creation from MD Image Express
import logging
import shutil
from os.path import exists, join
from typing import Any, Literal

import distributed
from faim_ipa.hcs.acquisition import TileAlignmentOptions
from faim_ipa.hcs.converter import ConvertToNGFFPlate, NGFFPlate, PlateLayout
from faim_ipa.stitching import stitching_utils
from fractal_tasks_core.tables import write_table
from pydantic import validate_call

from fractal_faim_ipa.converter_utils import (
    AcquisitionInputModel,
    add_acquisition_metadata_to_wells,
    check_is_multiplexing,
)
from fractal_faim_ipa.md_converter_utils import ModeEnum
from fractal_faim_ipa.roi_tables import create_ROI_tables

logger = logging.getLogger(__name__)


@validate_call
def convert_md_to_ome_zarr(  # noqa: C901
    *,
    zarr_dir: str,
    acquisitions: list[AcquisitionInputModel],
    # # TODO: Figure out a way to use the Enums directly with working manifest building
    # mode: ModeEnum = "MD Stack Acquisition",
    # layout: PlateLayout = 96,
    # tile_alignment: TileAlignmentOptions = "GridAlignment",
    mode: Literal[
        "Stack Acquisition",
        "Single Plane Acquisition",
        "Mixed Acquisition",
    ],
    tile_alignment: Literal["StageAlignment", "GridAlignment"] = "GridAlignment",
    layout: Literal[96, 384] = 96,
    num_levels: int = 5,
    order_name: str = "example-order",
    barcode: str = "example-barcode",
    reset_plates: bool = False,
    binning: int = 1,
    parallelize: bool = True,
) -> dict[str, Any]:
    """
    Create OME-Zarr plate from MD Image Xpress files.

    This is a non-parallel task => it parses the metadata, creates the plates
    and then converts all the wells in the same process

    Args:
        zarr_dir: path of the directory where the new OME-Zarrs will be
            created.
            (standard argument for Fractal tasks, managed by Fractal server).
        acquisitions: List of acquisition directories to convert to OME-Zarr. If
            you are processing multiplexing experiments, name the plate the
            same for all acquisitions, but give them unique acquisition IDs.
            If you are processing multiple separate plates, give the plates
            unique names.
        mode: Choose conversion mode. Choose whether you have 3D data
            (StackAcquisition), 2D data (Single Plane Acquisition) or mixed
            (Mixed Acquisition).
        tile_alignment: Choose whether tiles are placed into the OME-Zarr as a
            grid or whether they are placed based on the position of field of
            views in the metadata (using fusion for shared areas).
        layout: Plate layout for the Zarr file. Valid options are 96 and 384
        order_name: Name of the order
        num_levels: Number of pyramid levels to build in an OME-Zarr. More
            levels are useful for large plates to allow easier plate
            visualization, but will also lead to more files being created.
        barcode: Barcode of the plate
        reset_plates: Whether to remove any potentially pre-existing OME-Zarr
            plates before conversion.
        binning: Binning factor to downsample the original image. If set to 2,
            an image that is 2x2 downsampled in xy will be produced.
        parallelize: The automatic distribute.Client option often fails to
            finish when running the task locally. Set parallelize to false to
            avoid that.

    Returns:
        Metadata dictionary
    """
    mode = ModeEnum(mode)
    layout = PlateLayout(layout)
    tile_alignment = TileAlignmentOptions(tile_alignment)
    zarr_dir = zarr_dir.rstrip("/")
    image_list_updates = []

    is_multiplexed = check_is_multiplexing(acquisitions)
    if is_multiplexed:
        logger.info(
            f"Processing a multiplexing acquisition with plates {acquisitions=}"
        )
    else:
        logger.info(
            f"Processing a non-multiplexing acquisition with plates {acquisitions=}"
        )

    # TO REVIEW: Overwrite checks are not exposed in faim-hcs API
    # Unclear how faim-hcs handles rerunning the plate creation
    # (the Zarr file gets a newer timestamp at least)
    # This block triggers a reset
    for acquisition in acquisitions:
        plate_name = acquisition.plate_name
        if plate_name is None:
            plate_name = acquisition.path.rstrip("/").split("/")[-1]

        # Check if folder exists. faim-ipa errors when wrong paths are
        # entered are often confusing to users. Fail early if an input path
        # doesn't even exist / isn't accessible.
        if not exists(acquisition.path):
            raise FileNotFoundError(
                f"Acquisition path {acquisition.path} does not exist or "
                "is not accessible. Make sure you specify the path in a "
                "manner that is accessible from where the task is run."
            )

        if exists(join(zarr_dir, plate_name + ".zarr")):
            if reset_plates:
                # Remove zarr if it already exists.
                shutil.rmtree(join(zarr_dir, plate_name + ".zarr"))
            else:
                logger.warning(
                    f"Zarr file {plate_name + '.zarr'} already "
                    f"exists and wasn't reset due to {reset_plates=}. This "
                    "may lead to unexpected behavior.",
                )

    # The automatic distribute.Client option often fails to finish when
    # running the task locally. Set parallelize to false to avoid that.
    if parallelize:
        client = distributed.Client()
    else:
        client = distributed.Client(
            n_workers=1,
            threads_per_worker=1,
            processes=False,
        )

    for acquisition in acquisitions:
        plate_name = acquisition.plate_name
        if plate_name is None:
            plate_name = acquisition.path.rstrip("/").split("/")[-1]

        plate_acquisition = mode.get_plate_acquisition(
            acquisition_dir=acquisition.path,
            alignment=tile_alignment,
        )

        converter = ConvertToNGFFPlate(
            ngff_plate=NGFFPlate(
                root_dir=zarr_dir,
                name=plate_name,
                layout=int(layout),
                order_name=order_name,
                barcode=barcode,
            ),
            yx_binning=binning,
            warp_func=stitching_utils.translate_tiles_2d,
            fuse_func=stitching_utils.fuse_mean,
            client=client,
        )

        plate = converter.create_zarr_plate(plate_acquisition)

        well_sub_group = str(acquisition.acquisition_id)
        well_acquisitions = plate_acquisition.get_well_acquisitions(selection=None)

        full_plate_name = plate_name + ".zarr"

        # TODO: Add more robust handling for dimensionality detection
        if mode == ModeEnum.SinglePlaneAcquisition:
            is_3D = False
        else:
            is_3D = True

        # Run conversion.
        converter.run(
            plate=plate,
            plate_acquisition=plate_acquisition,
            well_sub_group=well_sub_group,
            # chunks=(2048, 2048), # check whether that should be exposed
            max_layer=num_levels - 1,
        )

        # Manually add acquisition metadata to the wells
        plate_url = f"{zarr_dir}/{full_plate_name}"
        add_acquisition_metadata_to_wells(
            plate_url=plate_url,
            acquisition_id=acquisition.acquisition_id,
        )

        # Write ROI tables to the images
        roi_tables = create_ROI_tables(plate_acquisition=plate_acquisition, mode="MD")
        for well_acquisition in well_acquisitions:
            # Write the tables
            well_rc = well_acquisition.get_row_col()
            image_group = plate[well_rc[0]][well_rc[1]][well_sub_group]
            tables = roi_tables[well_acquisition.name].keys()
            for table_name in tables:
                write_table(
                    image_group=image_group,
                    table_name=table_name,
                    table=roi_tables[well_acquisition.name][table_name],
                    overwrite=True,
                    table_type="roi_table",
                    table_attrs=None,
                )

            # Create the metadata dictionary: needs a list of all the images
            well_id = f"{well_rc[0]}{well_rc[1]}"
            zarr_url = (
                f"{zarr_dir}/{full_plate_name}/{well_rc[0]}/"
                f"{well_rc[1]}/{well_sub_group}"
            )
            image_list_updates.append(
                {
                    "zarr_url": zarr_url,
                    "attributes": {
                        "plate": full_plate_name,
                        "well": well_id,
                        "acquisition": acquisition.acquisition_id,
                    },
                    "types": {"is_3D": is_3D},
                }
            )

    return {"image_list_updates": image_list_updates}


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(
        task_function=convert_md_to_ome_zarr,
        logger_name=logger.name,
    )
