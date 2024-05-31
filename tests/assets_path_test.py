#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from plate_simulation import assets_path


def test_assets_directory_exist():
    assert assets_path().is_dir()


def test_uijson_files_exists():
    assert (assets_path() / "uijson").is_dir()
    assert next(iter((assets_path() / "uijson").iterdir())).is_file()
