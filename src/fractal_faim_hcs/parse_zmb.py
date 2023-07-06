import re

import pandas as pd
from faim_hcs.io.MolecularDevicesImageXpress import _list_dataset_files


def parse_files_zmb(path):
    """Parse files from a Molecular Devices ImageXpress dataset for ZMB setup."""
    _METASERIES_FILENAME_PATTERN_ZMB_2D = (
        r"(?P<name>.*)_(?P<well>[A-Z]+"
        r"\d{2})_(?P<field>s\d+)*_*"
        r"(?P<channel>w[1-9]{1})*"
        r"(?!_thumb)(?P<md_id>.*)*"
        r"(?P<ext>.tif|TIF)"
    )
    _METASERIES_ZMB_PATTERN = (
        r".*[\/\\](?P<time_point>TimePoint_[0-9]*)(?:[\/\\]" r"ZStep_(?P<z>\d+))?.*"
    )
    root_pattern = _METASERIES_ZMB_PATTERN
    files = pd.DataFrame(
        _list_dataset_files(
            root_dir=path,
            root_re=re.compile(root_pattern),
            filename_re=re.compile(_METASERIES_FILENAME_PATTERN_ZMB_2D),
        )
    )

    files = files.query("field == 's1'")
    print(files)

    # mode detection
    if files['z'].isnull().all():
        mode = 'top-level'
    elif '0' in list(files['z']):
        mode = 'all'
        files.loc[files['z']=='0', 'z'] = None
    else:
        mode = 'z-steps'

    # Ensure that field and channel are not None
    if files["field"].isnull().all():
        files["field"] = files["field"].fillna("s1")
    if files["channel"].isnull().all():
        files["channel"] = files["channel"].fillna("w1")

    return files, mode
