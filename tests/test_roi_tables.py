import math
from os.path import join
from pathlib import Path

import pytest
from faim_ipa.hcs.acquisition import TileAlignmentOptions
from fractal_faim_ipa.md_converter_utils import ModeEnum
from fractal_faim_ipa.roi_tables import _extract_fov_sort_key, create_ROI_tables


@pytest.mark.parametrize(
    "mode", ["MD Stack Acquisition", "MD Single Plane Acquisition"]
)
def test_roi_tables(mode):
    ROOT_DIR = Path(__file__).parent
    image_dir = str(join(ROOT_DIR.parent, "resources", "Projection-Mix"))

    mode = ModeEnum(mode)
    plate_acquisition = mode.get_plate_acquisition(
        acquisition_dir=image_dir,
        alignment=TileAlignmentOptions.GRID,
    )
    roi_tables = create_ROI_tables(plate_acquisition=plate_acquisition)
    assert set(roi_tables.keys()) == {"E08", "E07"}
    assert set(roi_tables["E08"].keys()) == {"FOV_ROI_table", "well_ROI_table"}

    target_values = [
        0.0,
        0.0,
        0.0,
        1399.6031494140625,
        699.8015747070312,
        50.0,
    ]
    if mode == ModeEnum.SinglePlaneAcquisition:
        target_values[5] = 1.0

    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(
            roi_tables["E08"]["well_ROI_table"].to_df().values.flatten().tolist(),
            target_values,
        )
    )

    roi_columns = [
        "x_micrometer",
        "y_micrometer",
        "z_micrometer",
        "len_x_micrometer",
        "len_y_micrometer",
        "len_z_micrometer",
    ]

    df_fov = roi_tables["E08"]["FOV_ROI_table"].to_df()
    assert list(df_fov.columns) == roi_columns
    assert len(df_fov) == 2
    target_values = [
        699.8015747070312,
        0.0,
        0.0,
        699.8015747070312,
        699.8015747070312,
        50.0,
    ]
    if mode == ModeEnum.SinglePlaneAcquisition:
        target_values[5] = 1.0
    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(df_fov.loc["FOV_2"].values.flatten().tolist(), target_values)
    )


# @pytest.mark.parametrize("alignment", ["GridAlignment", "StageAlignment"])
@pytest.mark.parametrize("alignment", ["StageAlignment"])
def test_roi_table_overlaps(alignment):
    ROOT_DIR = Path(__file__).parent
    image_dir = str(join(ROOT_DIR.parent, "resources", "zmb_test_data"))

    mode = ModeEnum.MetaXpressStackAcquisition
    plate_acquisition = mode.get_plate_acquisition(
        acquisition_dir=image_dir,
        alignment=TileAlignmentOptions(alignment),
    )
    roi_tables = create_ROI_tables(plate_acquisition=plate_acquisition)
    assert list(roi_tables.keys()) == ["C03"]

    df_fov = roi_tables["C03"]["FOV_ROI_table"].to_df()
    assert len(df_fov) == 4

    target_values_fov = {
        "GridAlignment": [
            345.4975891113281,
            345.4975891113281,
            0.0,
            345.4975891113281,
            345.4975891113281,
            0.36000001430511475,
        ],
        "StageAlignment": [
            311.0827941894531,
            0.16869999468326569,
            0.0,
            345.4975891113281,
            345.4975891113281,
            0.36000001430511475,
        ],
    }
    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(
            df_fov.loc["FOV_2"].values.flatten().tolist(), target_values_fov[alignment]
        )
    )
    target_values_well = {
        "GridAlignment": [0.0, 0.0, 0.0, 1036.492798, 690.995178, 0.36],
        "StageAlignment": [0.0, 0.0, 0.0, 967.494507, 656.580383, 0.36],
    }
    df_well = roi_tables["C03"]["well_ROI_table"].to_df()
    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(
            df_well.loc["well_1"].values.flatten().tolist(),
            target_values_well[alignment],
        )
    )


def test_roi_sorting():
    ROOT_DIR = Path(__file__).parent
    image_dir = str(join(ROOT_DIR.parent, "resources", "Projection-Mix"))

    mode = ModeEnum("MD Stack Acquisition")
    plate_acquisition = mode.get_plate_acquisition(
        acquisition_dir=image_dir,
        alignment=TileAlignmentOptions.GRID,
    )
    well_acquisition = plate_acquisition.get_well_acquisitions(selection=["E07"])[0]
    tiles = well_acquisition.get_tiles()
    sorted_tiles = sorted(tiles, key=_extract_fov_sort_key)
    assert (
        sorted_tiles[0].path.split("/")[-1]
        == "Projection-Mix_E07_s1_w1091EB8A5-272A-466D-B8A0-7547C6BA392B.tif"
    )
    assert (
        sorted_tiles[-1].path.split("/")[-1]
        == "Projection-Mix_E07_s2_w4F95A8A9F-0939-47C2-8D3E-F6E91AF0C4ED.tif"
    )
