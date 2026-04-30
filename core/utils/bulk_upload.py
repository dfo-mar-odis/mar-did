import logging
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User

from core.models import Missions, DataFiles, FileTypes
from core.utils.file_handler import  get_output_path, archive_files

logger = logging.getLogger('mardid')


def get_mission_input_path(mission: Missions) -> Path:
    return Path(settings.MEDIA_IN, mission.mission_path)


def build_file_structure(mission: Missions):
    input_path = get_mission_input_path(mission)
    logger.info(f"Building file structure for mission: {mission.name}")

    if not input_path.exists():
        logger.debug(f"Creating mission input directory: {input_path}")
        input_path.mkdir(parents=True)

    for dataset in mission.datasets.filter(datatype__location__input_dir__isnull=False):
        if dataset.datatype.location:
            datatype_path = Path(input_path, dataset.datatype.location.input_dir)
            if not datatype_path.exists():
                logger.debug(f"Creating datatype input directory: {datatype_path}")
                datatype_path.mkdir(parents=True)


def index_files(mission: Missions) -> dict:
    datatype_dict = {}

    input_path = get_mission_input_path(mission)
    for dataset in mission.datasets.filter(datatype__location__input_dir__isnull=False):
        if not dataset.datatype.location.input_dir:
            continue

        datatype_path = Path(input_path, dataset.datatype.location.input_dir)
        if not datatype_path.exists():
            continue

        datatype_dict[dataset.datatype.name] = [file.name for file in datatype_path.iterdir() if file.is_file()]

    return datatype_dict


def find_existing_files(mission: Missions, datatype_dict: dict) -> list[Path]:
    existing_files = []
    input_path = get_mission_input_path(mission)
    for dataset in mission.datasets.filter(datatype__location__input_dir__isnull=False):
        if not dataset.datatype.location.input_dir:
            continue

        datatype_path = Path(input_path, dataset.datatype.location.input_dir)
        if not datatype_path.exists():
            continue

        for file in datatype_path.iterdir():
            if file.is_file() and file.name in datatype_dict.get(dataset.datatype.name, []):
                destination_path = Path(settings.MEDIA_OUT, mission.mission_path, dataset.datatype.location.output_dir,
                                        file.name)
                if destination_path.exists():
                    existing_files.append(file.name)

    return existing_files


def move_files(user: User, mission: Missions, datatype_dict: dict, message=None):
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    # This will raise issues if some files cannot be moved. If some things can't be moved, nothing should be moved.
    existing_files = find_existing_files(mission, datatype_dict)

    if existing_files:
        if not message:
            raise FileExistsError("One or more files already exist")

    input_path = get_mission_input_path(mission)
    for dataset in mission.datasets.filter(datatype__location__input_dir__isnull=False):
        if not dataset.datatype.location.input_dir:
            continue

        datatype_path = Path(input_path, dataset.datatype.location.input_dir)
        if not datatype_path.exists():
            continue

        for file in datatype_path.iterdir():

            if file.is_file():
                file_extension = os.path.splitext(file)[1][1:]
                file_type = FileTypes.objects.get(extension__iexact=file_extension.upper())

                if file.name in existing_files:
                    archive = dataset.files.filter(file_name__in=existing_files)
                    archive_files(user, dataset.pk, archive, message=message)

                if file.name in datatype_dict.get(dataset.datatype.name, []):
                    destination_path = Path(get_output_path(dataset.pk), file.name)
                    logger.info(f"Moving file {file} to {destination_path}")
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    file.rename(destination_path)

                    DataFiles.objects.create(dataset=dataset, file_name=file.name, file_type=file_type,
                                             submitted_by=user,
                                             file_path=dataset.datatype.location.output_dir, is_archived=False)

    return None
