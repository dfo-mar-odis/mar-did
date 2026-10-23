import os
import re
import shutil

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.db.transaction import atomic

from core.models import Missions, DataFiles, Datasets, FileTypes, DatasetStatus, DataTypes


@atomic
def intake_files(user: User, mission: Missions, path: Path = None, datatype_id: int | None = None) -> list[dict]:

    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    dataset = None
    datetype = None
    if datatype_id:
        datetype = DataTypes.objects.get(pk=datatype_id)

    mission_path_idx = str(path).index(str(mission.mission_path))
    rel_path = Path(str(path)[mission_path_idx + len(str(mission.mission_path)) + 1:])

    status = DatasetStatus.objects.get(name__iexact="SUBMITTED")
    dataset = Datasets.objects.get_or_create(
        mission=mission, datatype=datetype, directory=rel_path, defaults={"status": status}
    )[0]

    create_files = []
    remove_files = []
    for in_file in path.iterdir():
        if in_file.is_file():

            out_file = Path(settings.MEDIA_OUT, str(in_file)[str(in_file).find(settings.MEDIA_IN)+len(settings.MEDIA_IN)+1:])
            if not out_file.parent.exists():
                out_file.parent.mkdir(parents=True)

            file_props = os.path.split(in_file)
            extension = os.path.splitext(file_props[-1])[1][1:].upper()
            file_types = FileTypes.objects.filter(extension__iexact=extension)
            if not file_types.exists():
                file_type = FileTypes.objects.create(extension=extension, description="No Description Provided")
            else:
                file_type = file_types.first()

            name = file_props[1]

            file = DataFiles(
                filename=name,
                file_type=file_type,
                dataset=dataset,
                submitted_by=user
            )
            create_files.append(file)

            shutil.copy2(str(in_file), str(out_file))
            remove_files.append(in_file)

    created: list[DataFiles] = DataFiles.objects.bulk_create(create_files)
    for f in created:
        print(f)

    for file in remove_files:
        os.unlink(file)

    return None

def scan_directories(user: User, mission: Missions, path: Path | None = None) -> list[dict] | None:

    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    ret_list: list[dict] = []
    next_dir = []
    if path is None:
        path = Path(settings.MEDIA_IN, mission.mission_path)

    for exclude in settings.INTAKE_DIR_EXCLUSIONS:
        if re.match(exclude, str(path).upper()) is not None:
            return None

    name = str(path).split(os.path.sep)[-1]
    current = {"path": path, "name": name, "files": []}

    for p in path.iterdir():
        if p.is_dir():
            next_dir.append(p)
        elif p.is_file():
            filename = str(p).replace(str(path), '')[1:]
            current['files'].append(filename)

    ret_list.append(current)
    if next_dir:
        for d in next_dir:
            sub = scan_directories(user, mission, d)
            if sub is not None:
                ret_list += sub

    return ret_list
