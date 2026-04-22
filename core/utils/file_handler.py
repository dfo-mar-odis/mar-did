import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils import timezone

from django.contrib.auth.models import User

from core import models

import logging
logger = logging.getLogger('mardid')


def get_output_path(dataset_id) -> Path:
    dataset = models.Datasets.objects.get(pk=dataset_id)
    datatype_output = dataset.datatype.locations.first().output_dir
    output_path = Path(settings.MEDIA_OUT, dataset.mission.mission_path, datatype_output)
    return output_path


def get_archive_path(dataset_id) -> Path:
    dataset = models.Datasets.objects.get(pk=dataset_id)
    datatype_output = dataset.datatype.locations.first().output_dir
    archive_path = Path(settings.MEDIA_OUT, dataset.mission.mission_path, "archive", datatype_output)
    return archive_path


# Returns a list of files that area already tracked by the database for the given dataset.
def validate_files(user: User, dataset_id: int, files: list) -> list | None:
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    file_names = [file.name for file in files]

    dataset = models.Datasets.objects.get(pk=dataset_id)

    # Fetch all existing file names in the dataset in one query
    existing_file_names = set(dataset.files.filter(file_name__in=file_names, is_archived=False).values_list('file_name', flat=True))
    existing_files = list(existing_file_names)

    return existing_files if len(existing_files) > 0 else None


def save_files(user: User, dataset_id: int, files: list[File]):

    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    if len(files) <= 0:
        return

    dataset = models.Datasets.objects.get(pk=dataset_id)

    output_path = get_output_path(dataset.pk)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        logger.info(f"Directory created: {output_path}")
    else:
        logger.info(f"Directory already exists: {output_path}")

    # Todo: extract the file typ from the file name, validate the file type is allowed from the provided datatype
    file_type = models.FileTypes.objects.get_or_create(extension=".tst", description="this is for testing purposes")[0]
    for file in files:
        file_path = os.path.join(output_path, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        models.DataFiles.objects.create(dataset=dataset, file_name=file.name,
                                        file_type=file_type, submitted_by=user,
                                        file_path=dataset.datatype.locations.first().output_dir, is_archived=False)
        logger.info(f"File saved: {file_path}")


def archive_files(user: User, dataset_id: int, files: list[models.DataFiles], message: str):
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    if message is None:
        raise ValidationError("A reason must be given for why files are being archived.")

    output_path = get_output_path(dataset_id)
    archive_path = get_archive_path(dataset_id)

    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        logger.info(f"Archive directory created: {archive_path}")

    for file in files:
        original_file_path = os.path.join(output_path, file.file_name)
        if not os.path.exists(original_file_path):
            logger.warning(f"File not found: {original_file_path}")
            continue

        # Prepend timestamp to the file name
        archive_date = timezone.now()

        if file:
            file.is_archived = True
            file.archived_date = archive_date
            file.save()
            models.DataFileComments.objects.create(datafile=file, comment=message, author=user)

            logger.info(f"File record updated: {file.file_name} marked as archived.")

        archived_file_path = os.path.join(archive_path, file.archived_file_name)

        # Move the file to the archive directory
        shutil.move(original_file_path, archived_file_path)
        logger.info(f"File archived: {archived_file_path}")


def get_files_by_name(dataset_id: int, file_names: list[str]=None) -> list[models.DataFiles]:
    dataset = models.Datasets.objects.get(pk=dataset_id)
    if file_names is None:
        files = dataset.current_files
    else:
        files = dataset.files.filter(file_name__in=file_names, is_archived=False)

    return files


def get_files_by_id(dataset_id: int, file_ids: list[int]=None) -> list[models.DataFiles]:
    if not file_ids:
        raise ValidationError("No files were selected for archiving. Please select files and try again.")

    dataset = models.Datasets.objects.get(pk=dataset_id)
    if 'all' in file_ids:
        files = dataset.current_files
    else:
        files = dataset.files.filter(pk__in=file_ids, is_archived=False)

    return files


def archive_files_by_name(user: User, dataset_id: int, file_names: list[str]=None, message: str=None):
    files = get_files_by_name(dataset_id, file_names)
    archive_files(user, dataset_id, files, message)


def archive_files_by_id(user: User, dataset_id: int, file_ids: list, message: str):
    files = get_files_by_id(dataset_id, file_ids)
    archive_files(user, dataset_id, files, message)


def delete_files(user: User, dataset_id: int, files: list[models.DataFiles]=None, archived=True):

    if user is None or not user.is_superuser:
        raise PermissionError("Only authenticated superusers can delete files.")

    dataset = models.Datasets.objects.get(pk=dataset_id)

    archive_file_path = get_archive_path(dataset.pk)
    working_file_path = get_output_path(dataset.pk)

    for file in files:
        file_path = archive_file_path if file.is_archived else working_file_path
        abs_path = Path(file_path, file.file_name)
        if abs_path.exists():
            abs_path.unlink()
            logger.info(f"File deleted: {file_path}")
        else:
            logger.warning(f"File not found for deletion: {file_path}")

        file.delete()
        logger.info(f"File record deleted: {file.file_name}")



def delete_files_by_name(user: User, dataset_id: int, file_names: list[str]=None):
    files = get_files_by_name(dataset_id, file_names)
    delete_files(user, dataset_id, files)


def delete_files_by_id(user: User, dataset_id: int, file_ids: list):
    files = get_files_by_id(dataset_id, file_ids)
    delete_files(user, dataset_id, files)
