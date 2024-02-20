from os.path import join
from pathlib import Path

import dask.array as da
import pytest
import zarr
from fractal_faim_hcs.create_ome_zarr_md import create_ome_zarr_md
from fractal_faim_hcs.md_to_ome_zarr import md_to_ome_zarr

ROOT_DIR = Path(__file__).parent
input_paths = [str(join(ROOT_DIR.parent, "resources", "zmb_test_data"))]
order_name = "example-order"
barcode = "example-barcode"
overwrite = True
mode = "zmb"
query = ""
output_name = "Test_ZMB_3D"


@pytest.mark.parametrize(
    "grid_montage, expected_shape",
    [(True, (2, 2, 4096, 6144)), (False, (2, 2, 3892, 5735))],
)
def test_montage(tmp_path, grid_montage, expected_shape):
    output_path = str(tmp_path)

    metatada_update = create_ome_zarr_md(
        input_paths=input_paths,
        output_path=output_path,
        metadata={},
        zarr_name=output_name,
        mode=mode,
        query=query,
        order_name=order_name,
        barcode=barcode,
        overwrite=overwrite,
    )

    for component in metatada_update["image"]:
        md_to_ome_zarr(
            input_paths=[output_path],
            output_path=output_path,
            component=component,
            metadata=metatada_update,
            grid_montage=grid_montage,
        )

    image = da.from_zarr(f"{output_path}/{output_name}.zarr/C/3/0/0")

    assert image.shape == expected_shape


def test_lazy_loading(tmp_path):
    output_path = str(tmp_path)
    grid_montage = True
    output_name1 = "Test_ZMB_3D_regular"
    output_name2 = "Test_ZMB_3D_lazy"

    metatada_update = create_ome_zarr_md(
        input_paths=input_paths,
        output_path=output_path,
        metadata={},
        zarr_name=output_name1,
        mode=mode,
        query=query,
        order_name=order_name,
        barcode=barcode,
        overwrite=overwrite,
    )

    for component in metatada_update["image"]:
        md_to_ome_zarr(
            input_paths=[output_path],
            output_path=output_path,
            component=component,
            metadata=metatada_update,
            grid_montage=grid_montage,
            memory_efficient=False,
        )

    metatada_update = create_ome_zarr_md(
        input_paths=input_paths,
        output_path=output_path,
        metadata={},
        zarr_name=output_name2,
        mode=mode,
        query=query,
        order_name=order_name,
        barcode=barcode,
        overwrite=overwrite,
    )

    for component in metatada_update["image"]:
        md_to_ome_zarr(
            input_paths=[output_path],
            output_path=output_path,
            component=component,
            metadata=metatada_update,
            grid_montage=grid_montage,
            memory_efficient=True,
        )

    image1 = da.from_zarr(f"{output_path}/{output_name1}.zarr/C/3/0/0")
    image2 = da.from_zarr(f"{output_path}/{output_name2}.zarr/C/3/0/0")

    assert image1.shape == image2.shape

    zarr1 = zarr.open(f"{output_path}/{output_name1}.zarr/C/3/0")
    zattr1 = zarr1.attrs.asdict()
    zarr2 = zarr.open(f"{output_path}/{output_name2}.zarr/C/3/0")
    zattr2 = zarr2.attrs.asdict()

    assert zattr1["multiscales"] == zattr2["multiscales"]

    # TODO: test omero metadata. Currently not always the same, because we
    # calculate histograms differently.
