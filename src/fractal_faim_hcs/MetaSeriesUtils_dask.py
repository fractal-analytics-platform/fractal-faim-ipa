from decimal import Decimal
from typing import Any, Callable, Optional, Union
from pathlib import Path

import re
import dask.array as da
import numpy as np
import pandas as pd
from tifffile import tifffile
from numpy._typing import ArrayLike

from faim_hcs.UIntHistogram import UIntHistogram

from faim_hcs.MetaSeriesUtils import montage_grid_image_YX
from faim_hcs.MetaSeriesUtils import get_img_YX
from faim_hcs.MetaSeriesUtils import _build_ch_metadata
from faim_hcs.MetaSeriesUtils import compute_z_sampling


# def compute_z_sampling(ch_z_positions: ArrayLike):
#     z_samplings = []
#     for z_positions in ch_z_positions:
#         if z_positions is not None and None not in z_positions:
#             precision = -Decimal(str(z_positions[0])).as_tuple().exponent
#             z_step = np.round(np.mean(np.diff(z_positions)), decimals=precision)
#             z_samplings.append(z_step)

#     return np.mean(z_samplings)


def get_well_image_CZYX_lazy(
    well_files: pd.DataFrame,
    channels: list[str],
    assemble_fn: Callable = montage_grid_image_YX,
) -> tuple[ArrayLike, list[UIntHistogram], list[dict], dict]:
    """Assemble image data for the given well-files."""
    # TODO: This function assumes that there are no gaps in data (i.e. that
    # there are no images missing to fill a full FCZ-stack)
    # -> maybe implement checks
    
    planes = sorted(well_files["z"].unique(),
                    key=int)
    fields = sorted(well_files["field"].unique(),
                    key=lambda s: int(re.findall('(\d+)',s)[0]))
    
    # Create an empty np array to store the filenames in the correct structure
    fn_dtype = f"<U{max([len(fn) for fn in well_files['path']])}"
    fns_np = np.empty((
        len(fields),
        len(channels),
        len(planes),
        ),
        dtype=fn_dtype)
    
    # Store fns in correct position
    for s, field in enumerate(fields):
        field_files = well_files[well_files["field"] == field]
        for c, channel in enumerate(channels):
            channel_files = field_files[field_files["channel"] == channel]
            for z, plane in enumerate(planes):
                plane_files = channel_files[channel_files["z"] == plane]
                assert len(plane_files) == 1, "Multiple files for one FCZ found"
                fns_np[s,c,z] = list(plane_files['path'])[0]
    
    # TODO: combine fields into one chunk
    fns_da = da.from_array(fns_np, chunks=(1,)*len(fns_np.shape))


    # MONTAGE PLANES
    def _fuse_xy(x):
        fns = x.flatten()
        # TODO: Rewrite get_img_YX to reduce unnecessary computations
        files = pd.DataFrame(fns, columns=["path"])
        _, img, *_ = get_img_YX(assemble_fn, files)
        return img.reshape(x.shape[1:] + img.shape)
    
    # TODO: could be done without loading images
    # calculate one plane to get dimensions and dtype
    sample_fused = _fuse_xy(fns_da[:,0,0].compute())
    (nx_tot, ny_tot) = sample_fused.shape
    
    # create dask array of assembled planes
    imgs_fused_da = da.map_blocks(
        _fuse_xy,
        fns_da,
        chunks=da.core.normalize_chunks(
            (1,)*len(fns_da.shape[1:]) + (nx_tot,ny_tot),
            shape=fns_da.shape[1:]+(nx_tot,ny_tot)
        ),
        drop_axis = 0,
        new_axis = range(len(fns_da.shape)-1, len(fns_da.shape)+1),
        meta=np.asanyarray([]).astype(sample_fused.dtype)
    )


    # LOAD STAGE POSITIONS:
    # TODO: maybe only read z-positions
    def da_read_metadata(x):
        fn = x.flatten()[0]
        ms_metadata = load_metaseries_tiff_metadata(fn)
        x_pos = ms_metadata['stage-position-x']
        y_pos = ms_metadata['stage-position-y']
        z_pos = ms_metadata['z-position']
        output = np.array([x_pos, y_pos, z_pos], dtype='float64')
        newshape = x.shape + output.shape
        return np.reshape(output, newshape)

    stage_positions_da = fns_da.map_blocks(
        da_read_metadata,
        chunks=da.core.normalize_chunks(
            (1,)*len(fns_da.shape) + (3,),
            fns_da.shape + (3,)
        ),
        new_axis=len(fns_da.shape),
        meta=np.asanyarray([]).astype('float64')
    )
    stage_positions = stage_positions_da.compute()
    z_positions = np.mean(stage_positions[:,:,:,2], axis=0)
    # TODO: This gives slightly different results than in the original code
    # possibly due to different precisions being used
    z_sampling = compute_z_sampling(z_positions)


    # GENERATE ROI_TABLES AND PX_METADATA:
    # (by only loading one plane)
    # TODO: Could also be done without loading images of entire plane
    fns_sel = fns_da[:,0,0].compute()
    files = pd.DataFrame(fns_sel, columns=["path"])
    px_metadata, _, _, _, roi_tables = get_img_YX(assemble_fn, files)
    
    px_metadata["z-scaling"] = z_sampling
    
    for roi_table in roi_tables.values():
        roi_table["len_z_micrometer"] = z_sampling*(imgs_fused_da.shape[1] - 1)
    

    # LOAD CHANNEL-METADATA
    def load_channel_metadata(fn):
        ms_metadata = load_metaseries_tiff_metadata(fn)
        return _build_ch_metadata(ms_metadata)

    channel_metadata = []
    for c in range(len(channels)):
        fn = fns_np[0,c,0]
        channel_metadata.append(load_channel_metadata(fn))


    # LOAD UINTHISTOGRAMS
    # TODO: See if this can be done more efficiently
    def _load_histo(x):
        histo = UIntHistogram(x)
        return np.array([[histo]])
    
    histos_da = imgs_fused_da.map_blocks(
        _load_histo,
        chunks=(1,1),
        drop_axis = (2,3,),
        meta=np.asanyarray([UIntHistogram()])
    )
    histos = histos_da.compute()
    channel_histograms = []
    for c, _ in enumerate(channels):
        channel_histogram = UIntHistogram()
        for z, _ in enumerate(planes):
            channel_histogram.combine(histos[c,z])
        channel_histograms.append(channel_histogram)


    return (
        imgs_fused_da,
        channel_histograms,
        channel_metadata,
        px_metadata,
        roi_tables
    )



def get_well_image_CYX_lazy(
    well_files: pd.DataFrame,
    channels: list[str],
    assemble_fn: Callable = montage_grid_image_YX,
) -> tuple[ArrayLike, list[UIntHistogram], list[dict], dict]:
    """Assemble image data for the given well-files.

    For each channel a single 2D image is computed. If the well has multiple
    fields per channel the `assemble_fn` has to montage or stitch the fields
    accordingly.

    :param well_files: all files corresponding to the well
    :param channels: list of required channels
    :param assemble_fn: creates a single image for each channel
    :return: CYX image, channel-histograms, channel-metadata, general-metadata,
                roi-tables dictionary
    """

    fields = sorted(well_files["field"].unique(),
                    key=lambda s: int(re.findall('(\d+)',s)[0]))

    # Create an empty np array to store the filenames in the correct structure
    fn_dtype = f"<U{max([len(fn) for fn in well_files['path']])}"
    fns_np = np.empty((
        len(fields),
        len(channels),
        ),
        dtype=fn_dtype)
    
    # Store fns in correct position
    for s, field in enumerate(fields):
        field_files = well_files[well_files["field"] == field]
        for c, channel in enumerate(channels):
            channel_files = field_files[field_files["channel"] == channel]
            fns_np[s,c] = list(channel_files['path'])[0]
    
    fns_da = da.from_array(fns_np, chunks=(1,)*len(fns_np.shape))


    # MONTAGE PLANES
    def _fuse_xy(x):
        fns = x.flatten()
        # TODO: Rewrite get_img_YX to reduce unnecessary computations
        files = pd.DataFrame(fns, columns=["path"])
        _, img, *_ = get_img_YX(assemble_fn, files)
        return img.reshape(x.shape[1:] + img.shape)
    
    # calculate one channel to get dimensions and dtype
    sample_fused = _fuse_xy(fns_da[:,0].compute())
    (nx_tot, ny_tot) = sample_fused.shape
    
    # create dask array of assembled planes
    imgs_fused_da = da.map_blocks(
        _fuse_xy,
        fns_da,
        chunks=da.core.normalize_chunks(
            (1,)*len(fns_da.shape[1:]) + (nx_tot,ny_tot),
            shape=fns_da.shape[1:]+(nx_tot,ny_tot)
        ),
        drop_axis = 0,
        new_axis = range(len(fns_da.shape)-1, len(fns_da.shape)+1),
        meta=np.asanyarray([]).astype(sample_fused.dtype)
    )

    # LOAD ROI_TABLES AND PX_METADATA:
    # (by only loading one channel)
    # TODO: Could also be done without loading images of entire plane
    fns_sel = fns_da[:,0].compute()
    files = pd.DataFrame(fns_sel, columns=["path"])
    px_metadata, _, _, _, roi_tables = get_img_YX(assemble_fn, files)
    

    # LOAD CHANNEL-METADATA
    def load_channel_metadata(fn):
        ms_metadata = load_metaseries_tiff_metadata(fn)
        return _build_ch_metadata(ms_metadata)

    channel_metadata = []
    for c in range(len(channels)):
        fn = fns_np[0,c]
        channel_metadata.append(load_channel_metadata(fn))


    # LOAD UINTHISTOGRAMS
    # TODO: See if this can be done more efficiently
    def _load_histo(x):
        histo = UIntHistogram(x)
        return np.array([histo])
        
    histos_da = imgs_fused_da.map_blocks(
        _load_histo,
        chunks=(1,),
        drop_axis = (1,2,),
        meta=np.asanyarray([UIntHistogram()])
    )
    histos = histos_da.compute()
    channel_histograms = []
    for c, _ in enumerate(channels):
        channel_histograms.append(histos[c])

    return (
        imgs_fused_da,
        channel_histograms,
        channel_metadata,
        px_metadata,
        roi_tables
    )



def load_metaseries_tiff_metadata(path: Path) -> dict:
    """Load metaseries tiff file and return parts of its metadata.

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
    * Lumencor Cyan Intensity
    * Lumencor Green Intensity
    * Lumencor Red Intensity
    * Lumencor Violet Intensity
    * Lumencor Yellow Intensity
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
        #metadata["PixelType"] = str(data.dtype)

    return metadata
