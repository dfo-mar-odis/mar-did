import logging
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Any, Generator

from django.conf import settings
from django.contrib.auth.models import User

from core.models import Missions, DataFiles, FileTypes, Datasets
from core.utils.file_handler import  get_output_path, archive_files

logger = logging.getLogger('mardid')


class FileStatus:
    class Status(Enum):
        success = "success"
        failure = "failure"

    file: Path
    status: Status
    error: Exception

    def set_status(self, status: Status):
        self.status = status

    def set_error(self, error: Exception):
        self.status = FileStatus.Status.failure
        self.error = error

    def get_file_name(self):
        return self.file.name

    def __init__(self, file: Path, status: Status, error: Exception = None):
        self.file = file
        self.status = status
        self.error = error


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
    """
    Generates a dictionary mapping dataset datatypes to a list of file names in their respective input directories.

    Args:
        mission (Missions): The mission object containing datasets with associated datatypes and input directories.

    Returns:
        dict: A dictionary where the keys are dataset datatype names (str) and the values are lists of file names (str)
              found in the corresponding input directories.

              Example:
              {
                  "CTD": ["file1.xml", "file2.hex"],
                  "BTL": ["file3.btl", "file4.ros"]
              }

              - "CTD" and "BTL" are dataset datatype names.
              - The lists contain the names of files found in the input directories for each datatype.
    """
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
    """
    Identifies files that already exist in the destination directory for a given mission.

    Args:
        mission (Missions): The mission object containing datasets with associated datatypes and input directories.
        datatype_dict (dict): A dictionary mapping dataset datatype names to lists of file names to check.

    Returns:
        list[Path]: A list of file names (as Path objects) that already exist in the destination directory.
    """
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


def file_itr(user: User, existing_files: list[Path], datatype_path: Path, datatype_dict, dataset, message=None) -> Generator[FileStatus, Any, None]:
    for file in datatype_path.iterdir():
        status_object = FileStatus(file, FileStatus.Status.failure)
        # status_objects[dataset].append(status_object)
        if file.is_file():
            file_extension = os.path.splitext(file)[1][1:]
            try:
                file_type = FileTypes.objects.get(extension__iexact=file_extension.upper())

                if file.name in existing_files:
                    archive = dataset.files.filter(file_name__iexact=file.name, is_archived=False)
                    archive_files(user, dataset.pk, archive, message=message)

                if file.name in datatype_dict.get(dataset.datatype.name, []):
                    destination_path = Path(get_output_path(dataset.pk), file.name)
                    logger.info(f"Moving file {file} to {destination_path}")
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file), str(destination_path))

                    DataFiles.objects.create(dataset=dataset, file_name=file.name, file_type=file_type, submitted_by=user,
                                             file_path=dataset.datatype.location.output_dir, is_archived=False)
                    status_object.set_status(FileStatus.Status.success)
            except FileTypes.DoesNotExist as e:
                logger.warning(f"Provided file type '{file_extension}' in bulk input folder does not exist and needs to be added as a FileType before it can be uploaded.")
                status_object.set_error(e)
            except Exception as e:
                logger.exception(f"Error processing file {file}", e)
                status_object.set_error(e)
            finally:
                yield status_object


def move_files(user: User, mission: Missions, datatype_dict: dict, message: str = None) -> dict[Datasets, Generator[FileStatus, Any, None]]:
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    # This will raise issues if some files cannot be moved. If some things can't be moved, nothing should be moved.
    existing_files: list[Path] = find_existing_files(mission, datatype_dict)

    if existing_files:
        if not message:
            raise FileExistsError("One or more files already exist")

    input_path = get_mission_input_path(mission)
    status_objects: dict[Datasets, Generator[FileStatus, Any, None]] = {}
    for dataset in mission.datasets.filter(datatype__location__input_dir__isnull=False):
        if not dataset.datatype.location.input_dir:
            continue

        datatype_path = Path(input_path, dataset.datatype.location.input_dir)
        if not datatype_path.exists():
            continue

        status_objects[dataset]: Generator[FileStatus, Any, None] = file_itr(user, existing_files, datatype_path, datatype_dict, dataset, message)

    return status_objects
