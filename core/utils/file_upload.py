import os
import shutil
from pathlib import Path
from datetime import datetime

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
    existing_file_names = set(dataset.files.filter(file_name__in=file_names, is_archived=False).values_list('file_name', flat=True))
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

        models.DataFiles.objects.create(dataset=dataset, file_name=file.name,
                                        file_type=file_type, submitted_by=user,
                                        file_path=dataset.datatype.locations.first().output_dir, is_archived=False)
        logger.info(f"File saved: {file_path}")


# Takes a list of files, that can be produced by the validate_files function, and locates them in the dataset
# The files are then moved to an archive location, marked as archived and a message is logged for each file.
# for why it was arcived.
def archive_files(user: User, dataset: models.Datasets, file_names: list[str], output_path: Path, archive_path: Path, message: str):
    if user is None or not user.is_authenticated:
        raise PermissionError("Only authenticated users can upload files.")

    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        logger.info(f"Archive directory created: {archive_path}")

    for file_name in file_names:
        original_file_path = os.path.join(output_path, file_name)
        if not os.path.exists(original_file_path):
            logger.warning(f"File not found: {original_file_path}")
            continue

        # Prepend timestamp to the file name
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        archived_file_name = f"{timestamp}_{file_name}"
        archived_file_path = os.path.join(archive_path, archived_file_name)

        # Move the file to the archive directory
        shutil.move(original_file_path, archived_file_path)
        logger.info(f"File archived: {archived_file_path}")

        # Update the dataset file record, there should only ever be one unarchived file.
        # if there's more this will throw a multiple objects returned error, which is what we want because it means
        # there's a problem with the database records that needs to be fixed.
        dataset_file = dataset.files.get(file_name=file_name, is_archived=False)
        if dataset_file:
            dataset_file.is_archived = True
            dataset_file.save()
            models.DataFileComments.objects.create(datafile=dataset_file, comment=message, author=user)

            logger.info(f"File record updated: {file_name} marked as archived.")
