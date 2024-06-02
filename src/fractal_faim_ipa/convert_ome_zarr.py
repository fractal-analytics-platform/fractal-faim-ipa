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
from pydantic.decorator import validate_arguments

from fractal_faim_ipa.md_converter_utils import ModeEnum
from fractal_faim_ipa.roi_tables import create_ROI_tables

logger = logging.getLogger(__name__)


@validate_arguments
def convert_ome_zarr(
    *,
    zarr_urls: list[str],
    zarr_dir: str,
    image_dir: str,
    # # TODO: Figure out a way to use the Enums directly with working manifest building
    # mode: ModeEnum = "MD Stack Acquisition",
    # layout: PlateLayout = 96,
    # tile_alignment: TileAlignmentOptions = "GridAlignment",
    mode: Literal[
        "MD Stack Acquisition",
        "MD Single Plane Acquisition",
        "MD Mixed Acquisition",
        "MetaXpress MD Stack Acquisition",
        "MetaXpress MD Single Plane Acquisition",
        "MetaXpress MD Single Plane Acquisition as 3D",
        "MetaXpress MD Mixed Acquisition",
    ],
    zarr_name: str = "Plate",
    tile_alignment: Literal["StageAlignment", "GridAlignment"] = "GridAlignment",
    layout: Literal[96, 384] = 96,
    query: str = "",
    order_name: str = "example-order",
    barcode: str = "example-barcode",
    overwrite: bool = False,
    binning: int = 1,
    parallelize: bool = True,
) -> dict[str, Any]:
    """
    Create OME-Zarr plate from MD Image Xpress files.

    This is a non-parallel task => it parses the metadata, creates the plates
    and then converts all the wells in the same process

    Args:
        zarr_urls: List of paths or urls to the individual OME-Zarr image to
            be processed. Not used by the converter task.
            (standard argument for Fractal tasks, managed by Fractal server).
        zarr_dir: path of the directory where the new OME-Zarrs will be
            created.
            (standard argument for Fractal tasks, managed by Fractal server).
        image_dir: Path to the folder containing the images to be converted.
        zarr_name: Name of the zarr plate file that will be created
        mode: Choose conversion mode. MetaXpress modes are used when data is
            exported via MetaXpress. Choose whether you have 3D data
            (StackAcquisition), 2D data (Single Plane Acquisition) or mixed.
        tile_alignment: Choose whether tiles are placed into the OME-Zarr as a
            grid or whether they are placed based on the position of field of
            views in the metadata (using fusion for shared areas).
        layout: Plate layout for the Zarr file. Valid options are 96 and 384
        query: Pandas query to filter the file list.
        order_name: Name of the order
        barcode: Barcode of the plate
        overwrite: Whether to overwrite the zarr file if it already exists
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

    # TO REVIEW: Overwrite checks are not exposed in faim-hcs API
    # Unclear how faim-hcs handles rerunning the plate creation
    # (the Zarr file gets a newer timestamp at least)
    # This block triggers a reset
    if overwrite and exists(join(zarr_dir, zarr_name + ".zarr")):
        # Remove zarr if it already exists.
        shutil.rmtree(join(zarr_dir, zarr_name + ".zarr"))

    # Query handling (only implemented in MetaXpress modes)
    if query == "":
        query = None

    plate_acquisition = mode.get_plate_acquisition(
        acquisition_dir=image_dir,
        alignment=tile_alignment,
        query=query,
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

    converter = ConvertToNGFFPlate(
        ngff_plate=NGFFPlate(
            root_dir=zarr_dir,
            name=zarr_name,
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

    # TODO: Remove hard-coded well sub group? Or make flexible for multiplexing
    well_sub_group = "0"
    well_acquisitions = plate_acquisition.get_well_acquisitions(selection=None)

    plate_name = zarr_name + ".zarr"

    image_list_updates = []
    # TODO: Add more robust handling for dimensionality detection
    if (
        mode == ModeEnum.SinglePlaneAcquisition
        or mode == ModeEnum.MetaXpressSinglePlaneAcquisition
        or mode == ModeEnum.MetaXpressSinglePlaneAcquisition_as3D
    ):
        is_3D = False
    else:
        is_3D = True

    # Run conversion.
    converter.run(
        plate=plate,
        plate_acquisition=plate_acquisition,
        well_sub_group=well_sub_group,
        # chunks=(1, 512, 512), # check whether that should be exposed
        # max_layer=2, # check whether that should be exposed
    )

    # Write ROI tables to the images
    roi_tables = create_ROI_tables(plate_acquisition=plate_acquisition)
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
                overwrite=overwrite,
                table_type="roi_table",
                table_attrs=None,
            )

        # Create the metadata dictionary: needs a list of all the images
        well_id = f"{well_rc[0]}{well_rc[1]}"
        zarr_url = f"{zarr_dir}/{plate_name}/{well_rc[0]}/{well_rc[1]}/{well_sub_group}"
        image_list_updates.append(
            {
                "zarr_url": zarr_url,
                "attributes": {
                    "plate": plate_name,
                    "well": well_id,
                },
                "types": {"is_3D": is_3D},
            }
        )

    return {"image_list_updates": image_list_updates}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(
        task_function=convert_ome_zarr,
        logger_name=logger.name,
    )
