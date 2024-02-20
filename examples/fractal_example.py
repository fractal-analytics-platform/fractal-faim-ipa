# Fractal example scripts

from fractal_faim_hcs.md_create_ome_zarr import md_create_ome_zarr

# from fractal_faim_hcs.md_to_ome_zarr import md_to_ome_zarr


input_paths = ["../resources/Projection-Mix"]
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

memory_efficient = False

mode = "MD Stack Acquisition"

order_name = "example-order"
barcode = "example-barcode"
overwrite = True

output_name = "OME-Zarr-Test"

# metatada_update
plate = md_create_ome_zarr(
    input_paths=input_paths,
    output_path=str(zarr_root),
    metadata={},
    zarr_name=output_name,
    mode=mode,
    order_name=order_name,
    barcode=barcode,
    overwrite=overwrite,
)

# for component in metatada_update["image"]:
#     md_to_ome_zarr(
#         input_paths=[str(zarr_root)],
#         output_path=str(zarr_root),
#         component=component,
#         metadata=metatada_update,
#         memory_efficient=memory_efficient,
#     )
