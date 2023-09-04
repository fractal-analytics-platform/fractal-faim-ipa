from fractal_faim_hcs.create_ome_zarr_md import create_ome_zarr_md
from fractal_faim_hcs.md_to_ome_zarr import md_to_ome_zarr

# input_paths = [
#     "/Users/joel/Dropbox/Joel/FMI/Fractal/Example_data/"
#     "ZMB_MD_data/plate1_Plate_1734"
#     ]
# mode = "ZMB-2D"
# output_name = "Test_ZMB_2D"

# input_paths = ["/Users/joel/Desktop/230219MK004EB-R1Bleach"]
output_path = "zarr-files"

order_name = "example-order"
barcode = "example-barcode"
overwrite = True
# Mode can be 3 values: "z-steps" (only parse the 3D data),
# "top-level" (only parse the 2D data), "all" (parse both)
# mode = "z-steps"
# mode = "top-level"
# mode = "top-level"


# mode = "z-steps"
# input_paths = [
#     "/Users/joel/Dropbox/Joel/BioVisionCenter/Fractal/Example_data/" \
#     "ZMB_MD_data/50um_Zstack"
# ]
# top-level:
# input_paths = [
#     "/home/flurin/Documents/ZMB/fractal/demo_data/data_for_joel/plate1_Plate_1734"
# ]
# z-steps:
# input_paths = [
#     "/home/flurin/Documents/ZMB/fractal/demo_data/40x-1time-26z-2well-6site-4channel_Plate_1795_partial"
# ]
# all:
input_paths = [
    "/home/flurin/Documents/ZMB/fractal/demo_data/lysosomes-actin-cellsignlamp1_Plate_1762"
]
# all, faim:
# input_paths = [
#     "/home/flurin/Documents/ZMB/fractal/faim-hcs/resources/Projection-Mix"
# ]

mode = "zmb"
#query = "well=='D05' and field==['s1','s2','s3']"
query = ""
grid_montage = False
output_name = "Test_ZMB_3D_new"

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
        grid_montage=grid_montage
    )
