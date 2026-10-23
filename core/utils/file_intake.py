from pathlib import Path

from django.conf import settings

from core import models

def scan_directories(mission: models.Missions):
    path = Path(settings.MEDIA_IN, mission.mission_path)
    print(path)

    for p in path.iterdir():
        print(p)