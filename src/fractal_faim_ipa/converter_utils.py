import ngio
from pydantic import BaseModel, Field


class AcquisitionInputModel(BaseModel):
    """Acquisition metadata.

    Based on
    https://github.com/fractal-analytics-platform/fractal-hcs-converters

    Attributes:
        path: Path to the acquisition directory. For the MD, this is the folder
            that contains a date folder and an ID folder. If the images are in
            /path/to/project_name/2025-05-12/1234, then the path should be
            /path/to/project_name.
        plate_name: Optional custom name for the plate. If not provided, the name will
            be the acquisition directory name.
        acquisition_id: Acquisition ID,
            used to identify the acquisition in case of multiple acquisitions.
    """

    path: str
    plate_name: str | None = None
    acquisition_id: int = Field(default=0, ge=0)


def add_acquisition_metadata_to_wells(plate_url, acquisition_id):
    """
    Add acquisition metadata to all the wells in the plate.

    Args:
        plate_url: Plate url of the OME-Zarr plate.
        acquisition_id: Acquisition ID to add to the wells.
    """
    ngio_plate = ngio.open_ome_zarr_plate(plate_url, cache=True, parallel_safe=False)
    wells = ngio_plate.wells_paths()
    for well in wells:
        row, col = well.split("/")
        ngio_well = ngio_plate.get_well(row=row, column=col)
        if str(acquisition_id) in ngio_well.paths():
            # To add acquisition metadata, remove the image & add it fresh
            # Only modifies plate metadata, not the image data
            ngio_plate.remove_image(row=row, column=col, image_path=str(acquisition_id))
            ngio_plate.add_image(
                row=row,
                column=col,
                image_path=str(acquisition_id),
                acquisition_id=acquisition_id,
                acquisition_name=str(acquisition_id),
            )


def check_is_multiplexing(acquisitions: list[AcquisitionInputModel]):
    """
    Check that the acquisitions are valid & whether it's multiplexing.

    The acquisitions .plate_name should either be unique (=> non-multiplexing)
    or they should be all the same, but the acquisition_ids should be unique
    (=> multiplexing). If the acquisitions are not valid, raise an error.

    Args:
        acquisitions: List of acquisition directories to convert to OME-Zarr.
            If you are processing multiplexing experiments, name the plate the
            same for all acquisitions, but give them unique acquisition IDs.
            If you are processing multiple separate plates, give the plates
            unique names.
    """
    plate_names = [acquisition.plate_name for acquisition in acquisitions]
    acquisition_ids = [acquisition.acquisition_id for acquisition in acquisitions]

    if len(plate_names) == 0:
        raise ValueError("No plate acquisitions provided. Please check your input.")

    if len(plate_names) == 1:
        return False
    if len(set(plate_names)) == 1:
        # All the same plate name
        if len(set(acquisition_ids)) == len(acquisition_ids):
            # All the acquisition IDs are unique
            return True
        else:
            raise ValueError(
                "Acquisition IDs should be unique for multiplexing "
                "experiments. Please check your input.",
            )
    else:
        # All the plate names are different
        return False
