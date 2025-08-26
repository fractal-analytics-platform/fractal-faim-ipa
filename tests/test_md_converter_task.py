# Fractal example scripts

import math
from os.path import join
from pathlib import Path

import anndata as ad
import pytest
import zarr
from fractal_faim_ipa.convert_md_to_ome_zarr import convert_md_to_ome_zarr


def count_arrays_in_group(group_url: str) -> int:
    """
    Count the number of arrays in a Zarr group.

    Parameters:
    - group_url (str): The URL or path to the Zarr group.

    Returns:
    - int: The number of arrays in the Zarr group.
    """
    group = zarr.open_group(group_url, mode="r")
    array_count = sum(
        1 for key, item in group.items() if isinstance(item, zarr.core.Array)
    )
    return array_count


def test_ome_zarr_conversion_simple(tmp_path):
    ROOT_DIR = Path(__file__).parent
    output_name = "OME-Zarr"
    acquisitions = [
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
            "plate_name": output_name,
        }
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    mode = "Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    image_list_update = convert_md_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        mode=mode,
        layout=96,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )["image_list_updates"]
    expected_image_list_update = [
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/07/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E07",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/08/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E08",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
    ]
    image_list_update.sort(key=lambda x: x["zarr_url"])
    assert expected_image_list_update == image_list_update

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
        50.0,
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
        50.0,
    ]
    assert all(
        math.isclose(a, b, rel_tol=1e-5)
        for a, b in zip(df_fov.loc["FOV_2"].values.flatten().tolist(), target_values)
    )


def test_ome_zarr_conversion_md_no_plate_name(tmp_path):
    ROOT_DIR = Path(__file__).parent
    acquisitions = [
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
        }
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    mode = "Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    image_list_update = convert_md_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        mode=mode,
        layout=96,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )["image_list_updates"]
    expected_image_list_update = [
        {
            "zarr_url": f"{zarr_root}/Projection-Mix.zarr/E/07/0",
            "attributes": {
                "plate": "Projection-Mix.zarr",
                "well": "E07",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/Projection-Mix.zarr/E/08/0",
            "attributes": {
                "plate": "Projection-Mix.zarr",
                "well": "E08",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
    ]
    image_list_update.sort(key=lambda x: x["zarr_url"])
    assert expected_image_list_update == image_list_update


@pytest.mark.parametrize("num_levels", [2, 5, 8])
def test_md_converter_pyramid_levels(tmp_path, num_levels):
    ROOT_DIR = Path(__file__).parent
    output_name = "OME-Zarr"
    acquisitions = [
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
            "plate_name": output_name,
            "acquisition_id": 0,
        }
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    mode = "Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    image_list_update = convert_md_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        mode=mode,
        layout=96,
        num_levels=num_levels,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )["image_list_updates"]

    zarr_url = image_list_update[0]["zarr_url"]
    assert count_arrays_in_group(zarr_url) == num_levels


def test_ome_zarr_conversion_multiplex(tmp_path):
    ROOT_DIR = Path(__file__).parent
    output_name = "OME-Zarr"
    acquisitions = [
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
            "plate_name": output_name,
            "acquisition_id": 0,
        },
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
            "plate_name": output_name,
            "acquisition_id": 1,
        },
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    mode = "Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    image_list_update = convert_md_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        mode=mode,
        layout=96,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )["image_list_updates"]
    expected_image_list_update = [
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/08/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E08",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/07/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E07",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/08/1",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E08",
                "acquisition": 1,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/07/1",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E07",
                "acquisition": 1,
            },
            "types": {
                "is_3D": True,
            },
        },
    ]
    assert expected_image_list_update == image_list_update


def test_ome_zarr_conversion_multi_plate(tmp_path):
    ROOT_DIR = Path(__file__).parent
    acquisitions = [
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
            "plate_name": "plate_1",
            "acquisition_id": 0,
        },
        {
            "path": str(join(ROOT_DIR.parent, "resources", "Projection-Mix")),
            "plate_name": "plate_2",
            "acquisition_id": 0,
        },
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    mode = "Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    image_list_update = convert_md_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        mode=mode,
        layout=96,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )["image_list_updates"]
    expected_image_list_update = [
        {
            "zarr_url": f"{zarr_root}/plate_1.zarr/E/08/0",
            "attributes": {"plate": "plate_1.zarr", "well": "E08", "acquisition": 0},
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/plate_1.zarr/E/07/0",
            "attributes": {"plate": "plate_1.zarr", "well": "E07", "acquisition": 0},
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/plate_2.zarr/E/08/0",
            "attributes": {"plate": "plate_2.zarr", "well": "E08", "acquisition": 0},
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/plate_2.zarr/E/07/0",
            "attributes": {"plate": "plate_2.zarr", "well": "E07", "acquisition": 0},
            "types": {
                "is_3D": True,
            },
        },
    ]
    assert expected_image_list_update == image_list_update


def test_ome_zarr_conversion_failure_non_existing_path(tmp_path):
    output_name = "OME-Zarr"
    acquisitions = [
        {
            "path": "/path/that/does/not/exist",
            "plate_name": output_name,
        }
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    mode = "Stack Acquisition"

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    with pytest.raises(FileNotFoundError):
        convert_md_to_ome_zarr(
            zarr_dir=str(zarr_root),
            acquisitions=acquisitions,
            mode=mode,
            layout=96,
            order_name=order_name,
            barcode=barcode,
            reset_plates=reset_plates,
        )
