import os
from pathlib import Path

from django.db.models.signals import post_delete
from django.dispatch import receiver
from core.models import DataFiles  # Replace with the correct import path for your DataFiles model
from core.utils.file_handler import get_archive_path, get_output_path

import logging
logger = logging.getLogger("mardid")

@receiver(post_delete, sender=DataFiles)
def delete_file_on_datafile_delete(sender, instance: DataFiles, **kwargs):
    dataset = instance.dataset

    if instance.is_archived:
        file_path = get_archive_path(dataset.pk)
    else:
        file_path = get_output_path(dataset.pk)

    abs_path = Path(file_path, instance.file_name)
    if abs_path.exists():
        abs_path.unlink()
        logger.info(f"File deleted: {file_path}")
    else:
        logger.warning(f"File not found for deletion: {file_path}")
