import hashlib
import os
import re
import shutil

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.db.transaction import atomic

from core.models import Missions, DataFiles, Datasets, FileTypes, DatasetStatus, DataTypes, MardidUser

import logging
logger = logging.getLogger(__name__)

def _get_file_hash(path: Path) -> str:
    hash_function = hashlib.new('sha256')
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            hash_function.update(chunk)

    return hash_function.hexdigest()


@atomic
def intake_files(
        user: User,
        mission: Missions,
        path: Path = None,
        datatype_id: int | None = None,
        copy: bool = False,
        in_root: str = settings.MEDIA_IN,
        out_root: str = settings.MEDIA_OUT
) -> dict:

    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    datetype = None
    if datatype_id:
        datetype = DataTypes.objects.get(pk=datatype_id)

    # get the directory path relative to the mission root
    mission_in_path = Path(in_root, mission.mission_path)
    rel_path = Path(str(path).replace(str(mission_in_path) + os.path.sep, ""))

    status = DatasetStatus.objects.get(name__iexact="SUBMITTED")

    # if the dataset was created then we don't have to check if this file was already indexed
    dataset, dataset_created = Datasets.objects.get_or_create(
        mission=mission, datatype=datetype, directory=rel_path, defaults={"status": status}
    )

    dataset_dir = dataset.get_dataset_root_path
    out_path = Path(out_root, dataset_dir)

    existing_files = []
    if not dataset_created:
        logger.warning(f"Dataset directory {out_path} already exists.")
        existing_files = os.listdir(out_path)

    create_files = []
    need_archive = []
    remove_files = []
    m_user = MardidUser.from_django_user(user)

    for in_file in path.iterdir():
        if in_file.is_file():

            out_file = Path(out_path, in_file.name)
            if not out_file.parent.exists():
                out_file.parent.mkdir(parents=True)

            file_props = os.path.split(in_file)
            extension = os.path.splitext(file_props[-1])[1][1:].upper()
            name = in_file.name
            if name in existing_files:
                if _get_file_hash(out_file) == _get_file_hash(in_file):
                    # if the hash of the in and out file are the same, this is the same file. Don't reupload it.
                    logger.info(f"File {name} already exists and will not be copies.")
                    continue

                # if they're not the same file, the old file needs to be archived first.
                need_archive.append(in_file.name)
                continue

            file_types = FileTypes.objects.filter(extension__iexact=extension)
            if not file_types.exists():
                file_type = FileTypes.objects.create(extension=extension, description="No Description Provided")
            else:
                file_type = file_types.first()

            file = DataFiles(
                filename=name,
                file_type=file_type,
                dataset=dataset,
                submitted_by=m_user
            )
            create_files.append(file)

            shutil.copy2(str(in_file), str(out_file))
            if not copy:
                remove_files.append(in_file)

    created: list[DataFiles] = DataFiles.objects.bulk_create(create_files)

    # We only remove files if all files have been successfully indexed and copied and
    # the user wants files "moved" as opposed to copied, but otherwise left in the initial directory
    if not copy:
        for file in remove_files:
            os.unlink(file)

    return {'created': created, 'needs_archive': need_archive}

def scan_directories(
        user: User,
        mission: Missions,
        in_path: Path | None = None,
        in_root: Path = settings.MEDIA_IN,
        out_root: Path = settings.MEDIA_OUT
) -> list[dict] | None:

    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    ret_list: list[dict] = []
    next_dir = []
    in_path = Path(in_root, mission.mission_path) if in_path is None else in_path

    for exclude in settings.INTAKE_DIR_EXCLUSIONS:
        if re.match(exclude, str(in_path).upper()) is not None:
            return None

    name = str(in_path).split(os.path.sep)[-1]
    current = {"path": in_path, "name": name, "files": [], "archive": []}

    for p in in_path.iterdir():
        if p.is_dir():
            next_dir.append(p)
        elif p.is_file():
            # Does the file already exist and has it been modified
            outfile = Path(str(p).replace(str(in_root), str(out_root)))
            if outfile.exists():
                if _get_file_hash(p) == _get_file_hash(outfile):
                    # same file has already been indexed.
                    continue
                else:
                    # todo: file exists and needs to be archived for now we'll tell the user it needs to be updated
                    #       by doing nothing and having it show up in the scanned directory list.
                    current['archive'].append(p.name)
                    continue

            current['files'].append(p.name)

    ret_list.append(current)
    if next_dir:
        for d in next_dir:
            sub = scan_directories(user, mission, d)
            if sub is not None:
                ret_list += sub

    return ret_list
