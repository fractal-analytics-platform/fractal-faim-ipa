from os.path import join
from pathlib import Path

from fractal_faim_ipa.convert_cellvoyager_to_ome_zarr import (
    convert_cellvoyager_to_ome_zarr,
)


def test_ome_zarr_conversion_simple(tmp_path):
    ROOT_DIR = Path(__file__).parent
    output_name = "OME-Zarr"
    acquisitions = [
        {
            "path": str(
                join(
                    ROOT_DIR.parent,
                    "resources",
                    "CV8000",
                    "CV8000-Minimal-DataSet-2C-3W-4S-FP2-stack_20230918_135839",
                    "CV8000-Minimal-DataSet-2C-3W-4S-FP2-stack",
                )
            ),
            "plate_name": output_name,
        }
    ]
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    order_name = "example-order"
    barcode = "example-barcode"
    reset_plates = True

    image_list_update = convert_cellvoyager_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        layout=96,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )["image_list_updates"]
    print(image_list_update)
    expected_image_list_update = [
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/D/08/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "D08",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/E/03/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "E03",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
        {
            "zarr_url": f"{zarr_root}/{output_name}.zarr/F/08/0",
            "attributes": {
                "plate": output_name + ".zarr",
                "well": "F08",
                "acquisition": 0,
            },
            "types": {
                "is_3D": True,
            },
        },
    ]
    assert image_list_update == expected_image_list_update
