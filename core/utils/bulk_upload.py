import logging
from pathlib import Path

from django.conf import settings

from core.models import Missions

logger = logging.getLogger('mardid')

def build_file_structure(mission: Missions):
    input_path = Path(settings.MEDIA_IN, mission.mission_path)
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
