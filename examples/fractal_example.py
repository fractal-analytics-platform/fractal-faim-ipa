# Fractal example scripts

from fractal_faim_hcs.md_create_ome_zarr import md_create_ome_zarr

# from fractal_faim_hcs.md_to_ome_zarr import md_to_ome_zarr


image_dir = "../resources/Projection-Mix"
# input_paths = [
#     "/Users/joel/Library/CloudStorage/Dropbox/Joel/BioVisionCenter"
#     "/Code/fractal/fractal-faim-hcs/resources/Projection-Mix"
# ]
# Input data 2D
# input_paths = [
#     "/Users/joel/Library/CloudStorage/Dropbox/Joel/BioVisionCenter"
#     "/Fractal/Example_data/230219MK004EB-R1Bleach"
# ]
output_path = "zarr-files"
zarr_root = output_path

order_name = "example-order"
barcode = "example-barcode"
overwrite = True
# Mode can be 3 values: "z-steps" (only parse the 3D data),
# "top-level" (only parse the 2D data), "all" (parse both)
# mode = "z-steps"
# mode = "top-level"
mode = "all"

mode = "MD Stack Acquisition"

order_name = "example-order"
barcode = "example-barcode"
overwrite = True

output_name = "OME-Zarr-Test"

# metatada_update
md_create_ome_zarr(
    zarr_urls=[],
    zarr_dir=str(zarr_root),
    image_dir=image_dir,
    zarr_name=output_name,
    mode=mode,
    layout=96,
    order_name=order_name,
    barcode=barcode,
    overwrite=overwrite,
    parallelize=False,
)
