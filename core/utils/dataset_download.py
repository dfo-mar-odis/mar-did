import io
import zipfile
import logging

from pathlib import Path

from django.conf import settings

from core import models

logger = logging.getLogger(__name__)

def get_current_working_path(dataset_id) -> Path:
    dataset = models.Datasets.objects.get(pk=dataset_id)

    datatype_output = dataset.directory
    output_path = Path(settings.MEDIA_OUT, dataset.mission.mission_path, datatype_output)
    return output_path


def download_biochem_dataset(mission: models.Missions):
    # Create an in-memory file-like object
    zip_buffer = io.BytesIO()

    dataset_dict = [
        ('events', ['ELOG', 'ANDES']),
        ('btl', ['BTL_CALIBRATED', 'BTL']),
        ('oxygen', ['WINK']),
        ('salinity', ['PSAL']),
        ('chlorophyll', ['CPHL']),
    ]
    datasets = [
        {
            'name': item[0],
            'dataset': (dataset:=dataset.first()),
            'path': get_current_working_path(dataset.pk) if dataset else None,
        } for item in dataset_dict if (dataset:=mission.datasets.filter(datatype__name__in=item[1])).exists()
    ]

    # Create a zip file in the buffer
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for dataset in datasets:
            for file in dataset['dataset'].files.filter(is_archived=False):
                data_file = Path(dataset["path"], file.filename)
                if data_file.exists() and data_file.is_file():
                    logger.debug(data_file)
                    # Add each file to the zip archive
                    zip_file.write(data_file, arcname=Path(dataset['name'], data_file.name))

    # Set the buffer's position to the beginning
    zip_buffer.seek(0)

    return zip_buffer

def test():
    test_mission = models.Missions.objects.first()
    zip_buffer = download_biochem_dataset(test_mission)

    logger.info("Writing zip file")
    with open("test.zip", 'wb') as f:
        f.write(zip_buffer.read())
