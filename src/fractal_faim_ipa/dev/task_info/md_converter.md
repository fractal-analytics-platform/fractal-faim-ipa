### Purpose
- Converts **2D and 3D images from MD Molecular Devices** systems into OME-Zarr format, creating OME-Zarr HCS plates and combining all fields of view in a well into a single image.
- Saves Fractal **region-of-interest (ROI) tables** for both individual fields of view and the entire well.
- Handles overlapping fields of view by either fusing images or saving them in grid tiles (depending on the `tile_alignment` option).

### Limitations
- The `image_dir` needs to be set to the the parent folder containing the following sub-folders: YYYY-MM-DD / Project_ID / Actual image files (potentially in ZStep folders). If it is run directly from the folder containing the images, it will fail.
