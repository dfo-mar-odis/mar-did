import os
from pathlib import Path
from datetime import date
from typing import Any

from django.conf import settings

class Mission:
    def __init__(self, name: str, start_date: date):
        self.name = name
        self.start_date = start_date

def list_in_mission_files(mission: Any, in_dir: Path = None) -> list[Path]:
    if not in_dir:
        in_dir = Path(os.path.join(Path(settings.MEDIA_IN), mission.name))

    if not in_dir.is_dir():
        print(f"{in_dir} is not a directory")
        return []

    dir_list = [d for d in in_dir.iterdir() if d.is_dir()]
    files_list = [f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))]
    for d in dir_list:
        files_list += list_in_mission_files(mission, d)

    return files_list

test_mission = Mission(name="TEST2026666", start_date=date(2024, 6, 1))

files = list_in_mission_files(test_mission)
print(files)