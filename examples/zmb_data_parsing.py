import os
import re
from pathlib import Path
from typing import Union

import pandas as pd

path = "/Users/joel/Desktop/230219MK004EB-R1Bleach"
# files = parse_files(path, mode="all")
# print(files)

path = "/Users/joel/Dropbox/Joel/FMI/Fractal/Example_data/ZMB_MD_data/plate1_Plate_1734"
path = "/Users/joel/Dropbox/Joel/FMI/Fractal/Example_data/ZMB_MD_data/50um_Zstack"
# files = parse_files(path, mode="all")


def parse_files_zmb(path):
    """TBD."""
    _METASERIES_FILENAME_PATTERN_ZMB_2D = (
        r"(?P<name>.*)_(?P<well>"
        r"[A-Z]+\d{2})_(?P<field>s\d+)*_*"
        r"(?P<channel>w[1-9]{1})*(?!_thumb)"
        r"(?P<md_id>.*)*(?P<ext>.tif|TIF)"
    )
    _METASERIES_ZMB_PATTERN = (
        r".*[\/\\](?P<time_point>TimePoint_[0-9]*)(?:[\/\\]" r"ZStep_(?P<z>\d+))?.*"
    )
    root_pattern = _METASERIES_ZMB_PATTERN
    files = pd.DataFrame(
        _list_dataset_files_new(
            root_dir=path,
            root_re=re.compile(root_pattern),
            filename_re=re.compile(_METASERIES_FILENAME_PATTERN_ZMB_2D),
        )
    )

    print(files)


def _list_dataset_files_new(
    root_dir: Union[Path, str], root_re: re.Pattern, filename_re: re.Pattern
) -> list[str]:
    files = []
    for root, _, filenames in os.walk(root_dir):
        m_root = root_re.fullmatch(root)
        if m_root:
            for f in filenames:
                m_filename = filename_re.fullmatch(f)
                if m_filename:
                    row = m_root.groupdict()
                    row |= m_filename.groupdict()
                    row["path"] = str(Path(root).joinpath(f))
                    files.append(row)
    return files
