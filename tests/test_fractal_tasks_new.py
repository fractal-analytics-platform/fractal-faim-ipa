# Fractal example scripts

import math
import tempfile
from os.path import join
from pathlib import Path

import anndata as ad
from fractal_faim_hcs.md_create_ome_zarr import md_create_ome_zarr


def test_ome_zarr_conversion():
    ROOT_DIR = Path(__file__).parent
    input_paths = [str(join(ROOT_DIR.parent, "resources", "Projection-Mix"))]
    tmp_dir = tempfile.mkdtemp()
    zarr_root = Path(tmp_dir, "zarr-files")
    zarr_root.mkdir()

    mode = "MD Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    overwrite = True

    output_name = "OME-Zarr"

    md_create_ome_zarr(
        input_paths=input_paths,
        output_path=str(zarr_root),
        metadata={},
        zarr_name=output_name,
        mode=mode,
        layout=96,
        order_name=order_name,
        barcode=barcode,
        overwrite=overwrite,
    )

    assert (
        zarr_root
        / f"{output_name}.zarr"
        / "E"
        / "07"
        / "0"
        / "tables"
        / "well_ROI_table"
    ).exists()
    assert (
        zarr_root
        / f"{output_name}.zarr"
        / "E"
        / "07"
        / "0"
        / "tables"
        / "FOV_ROI_table"
    ).exists()

    # Check ROI table content
    table = ad.read_zarr(
        zarr_root
        / f"{output_name}.zarr"
        / "E"
        / "07"
        / "0"
        / "tables"
        / "well_ROI_table"
    )
    df_well = table.to_df()
    roi_columns = [
        "x_micrometer",
        "y_micrometer",
        "z_micrometer",
        "len_x_micrometer",
        "len_y_micrometer",
        "len_z_micrometer",
    ]
    assert list(df_well.columns) == roi_columns
    assert len(df_well) == 1
    target_values = [
        0.0,
        0.0,
        0.0,
        1399.6031494140625,
        699.8015747070312,
        49.900001525878906,
    ]
    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(df_well.loc["well_1"].values.flatten().tolist(), target_values)
    )

    table = ad.read_zarr(
        zarr_root
        / f"{output_name}.zarr"
        / "E"
        / "07"
        / "0"
        / "tables"
        / "FOV_ROI_table"
    )
    df_fov = table.to_df()
    assert list(df_fov.columns) == roi_columns
    assert len(df_fov) == 2
    target_values = [
        699.8015747070312,
        0.0,
        0.0,
        699.8015747070312,
        699.8015747070312,
        49.900001525878906,
    ]
    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(df_fov.loc["FOV_2"].values.flatten().tolist(), target_values)
    )
