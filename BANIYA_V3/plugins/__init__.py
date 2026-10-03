# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pathlib import Path


def _list_modules():
    """
    List all Python module filenames (without extension):
    - Top-level .py files in plugins/
    - All .py files inside subfolders (like Manager/)
    """
    mod_dir = Path(__file__).parent
    modules = []

    # Top-level .py files
    for file in mod_dir.glob("*.py"):
        if file.is_file() and file.name != "__init__.py":
            modules.append(file.stem)

    # Subfolder .py files
    for subfolder in mod_dir.iterdir():
        if subfolder.is_dir() and (subfolder / "__init__.py").exists():
            for file in subfolder.glob("*.py"):
                if file.is_file() and file.name != "__init__.py":
                    modules.append(f"{subfolder.name}.{file.stem}")

    return modules


all_modules = frozenset(sorted(_list_modules()))
