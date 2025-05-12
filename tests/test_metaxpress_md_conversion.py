from os.path import join
from pathlib import Path

import dask.array as da
import pytest
from fractal_faim_ipa.convert_md_to_ome_zarr import convert_md_to_ome_zarr

ROOT_DIR = Path(__file__).parent
image_dir = str(join(ROOT_DIR.parent, "resources", "zmb-test-data_Plate_0000"))
order_name = "example-order"
barcode = "example-barcode"
reset_plates = True
output_name = "Test_ZMB_3D"


@pytest.mark.parametrize(
    "tile_alignment, expected_shape",
    [("GridAlignment", (2, 2, 4096, 6144)), ("StageAlignment", (2, 2, 3892, 5735))],
)
def test_montage(tmp_path, tile_alignment, expected_shape):
    mode = "Stack Acquisition"
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()

    acquisitions = [
        {
            "path": image_dir,
            "plate_name": output_name,
            "acquisition_id": 0,
        }
    ]

    convert_md_to_ome_zarr(
        zarr_dir=str(zarr_root),
        acquisitions=acquisitions,
        mode=mode,
        tile_alignment=tile_alignment,
        order_name=order_name,
        barcode=barcode,
        reset_plates=reset_plates,
    )
    print(zarr_root)
    print(f"{zarr_root!s}/{output_name}.zarr/C/03/0/0")
    image = da.from_zarr(f"{zarr_root!s}/{output_name}.zarr/C/03/0/0")

    assert image.shape == expected_shape
