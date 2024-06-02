from os.path import join
from pathlib import Path

import dask.array as da
import pytest
from fractal_faim_ipa.convert_ome_zarr import convert_ome_zarr

ROOT_DIR = Path(__file__).parent
image_dir = str(join(ROOT_DIR.parent, "resources", "zmb_test_data"))
order_name = "example-order"
barcode = "example-barcode"
overwrite = True
query = ""
output_name = "Test_ZMB_3D"


@pytest.mark.parametrize(
    "tile_alignment, expected_shape",
    [("GridAlignment", (2, 2, 4096, 6144)), ("StageAlignment", (2, 2, 3892, 5735))],
)
def test_montage(tmp_path, tile_alignment, expected_shape):
    mode = "MetaXpress MD Stack Acquisition"
    zarr_root = Path(tmp_path, "zarr-files")
    zarr_root.mkdir()
    convert_ome_zarr(
        zarr_urls=[],
        zarr_dir=str(zarr_root),
        image_dir=image_dir,
        zarr_name=output_name,
        mode=mode,
        tile_alignment=tile_alignment,
        query=query,
        order_name=order_name,
        barcode=barcode,
        overwrite=overwrite,
    )
    print(zarr_root)
    print(f"{zarr_root!s}/{output_name}.zarr/C/03/0/0")
    image = da.from_zarr(f"{zarr_root!s}/{output_name}.zarr/C/03/0/0")

    assert image.shape == expected_shape
