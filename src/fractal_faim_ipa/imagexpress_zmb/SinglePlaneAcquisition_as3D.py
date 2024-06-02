import re
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from faim_ipa.hcs.acquisition import TileAlignmentOptions
from fractal_faim_ipa.imagexpress_zmb import ImageXpressPlateAcquisition


class SinglePlaneAcquisition_as3D(ImageXpressPlateAcquisition):
    """XXX
    """

    _z_spacing: float = None

    def __init__(
        self,
        acquisition_dir: Union[Path, str],
        alignment: TileAlignmentOptions,
        background_correction_matrices: Optional[dict[str, Union[Path, str]]] = None,
        illumination_correction_matrices: Optional[dict[str, Union[Path, str]]] = None,
        query: str = None,
    ):
        super().__init__(
            acquisition_dir=acquisition_dir,
            alignment=alignment,
            background_correction_matrices=background_correction_matrices,
            illumination_correction_matrices=illumination_correction_matrices,
            query=query,
        )

    def _parse_files(self) -> pd.DataFrame:
        files = super()._parse_files()
        if len(files.z.unique()) != 1:
            raise RuntimeError("More than one z-plane found. One can filter the files using a query, e.g. query=\"z=='0'\"")
        self._z_spacing = self._compute_z_spacing(files)
        return files

    def _get_root_re(self) -> re.Pattern:
        return re.compile(
            r".*[\/\\]TimePoint_(?P<t>\d+)[\/\\]ZStep_(?P<z>\d+)"
        )

    def _get_filename_re(self) -> re.Pattern:
        return re.compile(
            r"(?P<name>.*)_(?P<well>[A-Z]+\d{2})_(?P<field>s\d+)_(?P<channel>w[1-9]{1})(?P<ext>.TIF)"
        )

    def _get_z_spacing(self) -> Optional[float]:
        return self._z_spacing

    def _compute_z_spacing(self, files: pd.DataFrame) -> Optional[float]:
        return 1
