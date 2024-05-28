import re
from pathlib import Path
from typing import Callable

import dask.array as da
import numpy as np
import pandas as pd
from faim_hcs.MetaSeriesUtils import (
    _build_ch_metadata,
    compute_z_sampling,
    get_img_YX,
    montage_grid_image_YX,
)
from faim_hcs.UIntHistogram import UIntHistogram
from numpy._typing import ArrayLike
from tifffile import tifffile


def create_filename_structure(
    well_files: pd.DataFrame,
    channels: list[str],
) -> ArrayLike:
    """
    Assemble filenames in a numpy-array with ordering (field,channel,plane).
    This allows us to later easily map over the filenames to create a
    dask-array of the images.
    """
    planes = sorted(well_files["z"].unique(), key=int)
    fields = sorted(
        well_files["field"].unique(),
        key=lambda s: int(re.findall(r"(\d+)", s)[0])
    )

    # Create an empty np array to store the filenames in the correct structure
    fn_dtype = f"<U{max([len(fn) for fn in well_files['path']])}"
    fns_np = np.zeros(
        (len(fields), len(channels), len(planes)),
        dtype=fn_dtype,
    )

    # Store fns in correct position
    for s, field in enumerate(fields):
        field_files = well_files[well_files["field"] == field]
        for c, channel in enumerate(channels):
            channel_files = field_files[field_files["channel"] == channel]
            for z, plane in enumerate(planes):
                plane_files = channel_files[channel_files["z"] == plane]
                if len(plane_files) == 1:
                    fns_np[s, c, z] = list(plane_files["path"])[0]
                elif len(plane_files) > 1:
                    raise RuntimeError("Multiple files found for one FCZ")
    
    return fns_np


def get_planes_params(
        stage_positions_da: ArrayLike,
        channels_full_planes:  list[int],
    ):
    """Calculate z_sampling, lowest plane min_z, and number of planes n_z."""
    z_positions_full_planes = da.mean(
        stage_positions_da[:,channels_full_planes,:,2],
        axis=0
    ).compute()
    z_sampling = compute_z_sampling(z_positions_full_planes)
    min_z = z_positions_full_planes.min(axis = 1).mean()
    n_z = z_positions_full_planes.shape[1]
    return z_sampling, min_z, n_z

def roll_single_planes(
        stage_positions_da: ArrayLike,
        channels_one_plane: list[int],
        z_sampling: float,
        min_z: float,
        n_z: int,
        fns_np: ArrayLike,
    ):
    """
    Calculate z-position of single-plane-channels, and roll the filenames to
    the correct position
    """
    z_positions_one_plane = da.mean(
        stage_positions_da[:,channels_one_plane,0,2],
        axis=0
    ).compute()

    for c, z_position in zip(channels_one_plane, z_positions_one_plane):
        shift_z = round((z_position - min_z) / z_sampling)
        # if plane lies outside region of z-stack: clip to lowest/highest plane
        if shift_z < 0:
            shift_z = 0
        elif n_z <= shift_z:
            shift_z = n_z - 1
        fns_np[:,c,:] = np.roll(fns_np[:,c,:], shift_z, axis=1)

def load_UIntHistograms(imgs_fused_da, channels_empty):
    # TODO: See if this can be done more efficiently
    def _load_histo(x):
        histo = UIntHistogram(x)
        return np.array([[histo]])

    histos_da = da.map_blocks(
        _load_histo,
        imgs_fused_da,
        chunks=(1, 1),
        drop_axis=(
            2,
            3,
        ),
        meta=np.asanyarray([UIntHistogram()]),
    )
    histos = histos_da.compute()

    channel_histograms = []
    for c in range(histos.shape[0]):
        channel_histogram = UIntHistogram()
        for z in range(histos.shape[1]):
            channel_histogram.combine(histos[c, z])
        channel_histograms.append(channel_histogram)
    for c in channels_empty:
        channel_histograms[c] = UIntHistogram()

    return channel_histograms

def _da_read_stage_positions(x: ArrayLike):
    """
    Load stage positions of a file (used to map over a dask-array)
    x: One filename in an array
    returns: Array of xyz positions, in the shape of the input array (plus 3)
    """
    fn = x.flatten()[0]
    if fn=='':
        raise RuntimeError(
            'File not found. This channel probably either only has projections'
            ' or only one plane.'
        )
    ms_metadata = load_metaseries_tiff_metadata(fn)
    x_pos = ms_metadata["stage-position-x"]
    y_pos = ms_metadata["stage-position-y"]
    z_pos = ms_metadata["z-position"]
    output = np.array([x_pos, y_pos, z_pos], dtype="float64")
    newshape = x.shape + output.shape
    return np.reshape(output, newshape)

def _fuse_xy(
    x: ArrayLike,
    assemble_fn: Callable,
    img_shape: tuple[int] = None,
    img_dtype: np.dtype = None
) -> ArrayLike:
    """
    Load images and fuse them
    """
    fns = x.flatten()
    if '' not in fns:
        # TODO: Rewrite get_img_YX to reduce unnecessary computations
        files = pd.DataFrame(fns, columns=["path"])
        _, img, *_ = get_img_YX(assemble_fn, files)
    else:
        # return zeros if plane is empty
        if img_shape != None and img_dtype != None:
            img = np.zeros(img_shape, dtype=img_dtype)
        else:
            raise RuntimeError(
                "'img_dimension' and 'img_dtype' must be provided if plane is"
                " empty"
            )
    return img.reshape(x.shape[1:] + img.shape)

def get_well_image_CZYX_lazy(  # noqa: C901
    well_files: pd.DataFrame,
    channels: list[str],
    assemble_fn: Callable = montage_grid_image_YX,
) -> tuple[ArrayLike, list[UIntHistogram], list[dict], dict]:
    """Assemble image data for the given well-files."""

    fns_np = create_filename_structure(well_files, channels)

    # distinguish between channels with
    #   - all z-planes
    #   - only one z-plane (stored in first plane)
    #   - no z-planes (only projections = empty channel)
    channels_full_planes = []
    channels_one_plane = []
    channels_empty = []
    for c in range(fns_np.shape[1]):
        if '' not in fns_np[:,c,:]:
            channels_full_planes.append(c)
        elif '' not in fns_np[:,c,0]:
            channels_one_plane.append(c)
        else:
            channels_empty.append(c)


    # LOAD STAGE POSITIONS, CALCULATE Z_SAMPLING & ARRANGE SINGLE PLANES:
    # TODO: maybe only read z-positions
    # stage_positions_da: dask array of image coordinates with shape 
    # (fields,channels,planes,(x-coord,y-coord,z-coord))
    stage_positions_da = da.map_blocks(
        _da_read_stage_positions,
        da.from_array(fns_np, chunks=1),
        chunks=da.core.normalize_chunks(
            (1,) * len(fns_np.shape) + (3,), (*fns_np.shape, 3)
        ),
        new_axis=len(fns_np.shape),
        meta=np.asanyarray([]).astype("float64"),
    )

    z_sampling, min_z, n_z = get_planes_params(
        stage_positions_da, channels_full_planes
    )

    roll_single_planes(
        stage_positions_da, channels_one_plane, z_sampling, min_z, n_z, fns_np
    )

    # GENERATE ROI_TABLES AND PX_METADATA:
    # (by only loading one plane)
    # TODO: Could also be done without loading images of entire plane
    fns_sel = fns_np[:, channels_full_planes[0], 0]
    files = pd.DataFrame(fns_sel, columns=["path"])
    px_metadata, sample_fused, *_, roi_tables = get_img_YX(assemble_fn, files)

    px_metadata["z-scaling"] = z_sampling

    for roi_table in roi_tables.values():
        roi_table["len_z_micrometer"] = z_sampling * (fns_np.shape[2] - 1)

    (nx_tot, ny_tot) = sample_fused.shape
    img_dtype = sample_fused.dtype


    # MONTAGE PLANES
    # imgs_fused_da: fused planes of shape (channels, planes, x, y)
    imgs_fused_da = da.map_blocks(
        _fuse_xy,
        da.from_array(
            fns_np,
            chunks=((fns_np.shape[0],)+(1,)*len(fns_np.shape[1:]))
        ),
        chunks=da.core.normalize_chunks(
            (1,) * len(fns_np.shape[1:]) + (nx_tot, ny_tot),
            shape=fns_np.shape[1:] + (nx_tot, ny_tot),
        ),
        drop_axis=0,
        new_axis=range(len(fns_np.shape) - 1, len(fns_np.shape) + 1),
        meta=np.asanyarray([]).astype(sample_fused.dtype),


        assemble_fn=assemble_fn,
        img_shape=(nx_tot, ny_tot),
        img_dtype=img_dtype
    )


    # LOAD CHANNEL-METADATA
    def load_channel_metadata(fn):
        ms_metadata = load_metaseries_tiff_metadata(fn)
        return _build_ch_metadata(ms_metadata)
    
    channel_metadata = []
    for c in range(fns_np.shape[1]):
        if (c in channels_full_planes) or (c in channels_one_plane):
            for z in range(fns_np.shape[2]):
                if fns_np[0,c,z] != '':
                    channel_metadata.append(
                        load_channel_metadata(fns_np[0,c,z])
                    )
                    break
        else:
            channel_metadata.append(
                {
                    "channel-name": "empty",
                    "display-color": "000000",
                }
            )


    # LOAD UINTHISTOGRAMS
    # NOTE: for now, we only calculate UIntHistograms for middle z-planes
    # because there are to be documented issues with overflows in
    # UIntHistograms, if large datasets are processed
    # For single-plane channels, it will probably return non-meaningfull
    # histograms
    channel_histograms = load_UIntHistograms(
        imgs_fused_da[:,[imgs_fused_da.shape[1]//2]],
        channels_empty
    )

    return (
        imgs_fused_da,
        channel_histograms,
        channel_metadata,
        px_metadata,
        roi_tables,
    )



def load_metaseries_tiff_metadata(path: Path) -> dict:
    """Load metaseries tiff file and return parts of its metadata.
    Only load metadata, and not entire image for faster loading. -> PixelType
    is not returned.

    The following metadata is collected:
    * _IllumSetting_
    * spatial-calibration-x
    * spatial-calibration-y
    * spatial-calibration-units
    * stage-position-x
    * stage-position-y
    * z-position
    * PixelType
    * _MagNA_
    * _MagSetting_
    * Exposure Time
    * ShadingCorrection
    * stage-label
    * SiteX
    * SiteY
    * wavelength
    * Z Step (if existent)
    * Z Projection Method (if existent)

    :param path:
    :return:
    metadata-dict
    """
    with tifffile.TiffFile(path) as tiff:
        assert tiff.is_metaseries, f"{path} is not a metamorph file."
        selected_keys = [
            "_IllumSetting_",
            "spatial-calibration-x",
            "spatial-calibration-y",
            "spatial-calibration-units",
            "stage-position-x",
            "stage-position-y",
            "z-position",
            "_MagNA_",
            "_MagSetting_",
            "Exposure Time",
            "ShadingCorrection",
            "stage-label",
            "SiteX",
            "SiteY",
            "wavelength",
            "Z Step",  # optional
            "Z Projection Method",  # optional
            "Z Projection Step Size",  # optional
        ]
        plane_info = tiff.metaseries_metadata["PlaneInfo"]
        metadata = {k: plane_info[k] for k in selected_keys if k in plane_info}
        for metadata_key in plane_info:
            if metadata_key.endswith("Intensity"):
                metadata[metadata_key] = plane_info[metadata_key]

    return metadata
