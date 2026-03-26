import os
from pathlib import Path

from django.contrib.auth.models import User

from core import models

import logging
logger = logging.getLogger('mardid')


# Returns a list of files that area already tracked by the database for the given dataset.
def validate_files(user: User, dataset: models.Datasets, files: list) -> list | None:
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    file_names = [file.name for file in files]

    # Fetch all existing file names in the dataset in one query
    existing_file_names = set(dataset.files.filter(file_name__in=file_names).values_list('file_name', flat=True))
    existing_files = list(existing_file_names)

    return existing_files if len(existing_files) > 0 else None


def save_files(user: User, dataset: models.Datasets, files: list, output_path: Path):

    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    if len(files) <= 0:
        return

    if not os.path.exists(output_path):
        os.makedirs(output_path)
        logger.info(f"Directory created: {output_path}")
    else:
        logger.info(f"Directory already exists: {output_path}")

    file_type = models.FileTypes.objects.get_or_create(extension=".tst", description="this is for testing purposes")[0]
    for file in files:
        file_path = os.path.join(output_path, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        models.DataFiles.objects.create(dataset=dataset, file_name=file.name, file_type=file_type, submitted_by=user, is_archived=False)
        logger.info(f"File saved: {file_path}")


# Takes a list of files, that can be produced by the validate_files function, and locates them in the dataset
# The files are then moved to an archive location, marked as archived and a message is logged for each file.
# for why it was arcived.
def archive_files(user: User, dataset: models.Datasets, file_names: list[str], message: str):
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    # archived files get put in the missions archive directory
    archive_path = Path(dataset.mission.mission_path, 'mardid_archive')
    for file_name in file_names:
        try:
            file_record = dataset.files.get(file_name=file_name, is_archived=False)
            file_record.is_archived = True
            file_record.save()
            logger.info(f"File archived: {file_name} - Reason: {message}")
        except models.DataFiles.DoesNotExist:
            logger.warning(f"File not found for archiving: {file_name}")