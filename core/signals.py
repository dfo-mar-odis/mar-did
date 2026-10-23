import os
from pathlib import Path

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from core.models import DataFiles, Datasets

import logging
logger = logging.getLogger("mardid")

def cleanup_path(path: Path) -> bool:

    try:
        for p in path.iterdir():
            if p.is_file() or (p.is_dir() and not cleanup_path(p)):
                return False

        path.rmdir()
    except FileNotFoundError:
        pass

    return True

@receiver(post_delete, sender=Datasets)
def delete_files_on_directory_delete(sender, instance: Datasets, **kwargs):

    # make sure files are deleted before the directories are.
    instance.files.all().delete()
    path = Path(settings.MEDIA_OUT, instance.mission.mission_path, instance.directory)

    cleanup_path(path)


@receiver(post_delete, sender=DataFiles)
def delete_file_on_datafile_delete(sender, instance: DataFiles, **kwargs):

    try:
        root = settings.MEDIA_OUT
        mission = instance.dataset.mission.mission_path
        path = instance.dataset.directory
        name = instance.filename

        if instance.is_archived:
            abs_path = Path(root, mission, 'archive', path, name)
        else:
            abs_path = Path(root, mission, path, name)

        if abs_path.exists():
            abs_path.unlink()
            logger.info(f"File deleted: {abs_path}")
        else:
            logger.warning(f"File not found for deletion: {abs_path}")
    except Exception as e:
        logger.warning(f"Could not delete file: {instance.filename}")
        logger.exception(e)
