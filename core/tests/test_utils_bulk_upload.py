import shutil
from pathlib import Path

from django.conf import settings
from django.test import tag, override_settings

from core.utils.bulk_upload import build_file_structure
from core.tests.core_factory_floor import MardidTestCase, MissionFactory, MissionLegFactory, MissionDatasetFactory, \
    DatasetLocationsFactory

from core import models

@override_settings(MEDIA_IN='media/IN')
@tag('utils', 'bulk_upload')
class TestUtilsBulkUpload(MardidTestCase):

    def setUp(self):
        self.mission = MissionFactory.create()
        MissionLegFactory(mission=self.mission, start_date="2025-09-28", end_date="2025-10-28")

    def tearDown(self):
        expected_path = Path(settings.MEDIA_IN)
        if expected_path.exists():
            shutil.rmtree(expected_path)

    def test_build_file_structure(self):
        # Provided a mission the bulk upload build file structure function should create the root directory
        # for the mission in the settings.MEDIA_OUT location.

        build_file_structure(self.mission)

        expected_path = Path(settings.MEDIA_IN, self.mission.mission_path)
        assert expected_path.exists(), f"Expected file path does not exist: {expected_path}"

    def test_build_dataset_structure(self):
        expected_input_path = Path('CTD', 'BTL')
        btl_datatype = models.DataTypes.objects.get_or_create(name="BTL")[0]
        btl_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=btl_datatype)
        dataset_location = DatasetLocationsFactory.create(datatype=btl_datatype, input_dir=expected_input_path)

        build_file_structure(self.mission)

        expected_path = Path(settings.MEDIA_IN, self.mission.mission_path, expected_input_path)
        assert expected_path.exists(), f"Expected file path does not exist: {expected_path}"
