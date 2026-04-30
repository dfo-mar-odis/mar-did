import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User, Group, AnonymousUser
from django.test import tag, override_settings, RequestFactory

from core.utils.bulk_upload import build_file_structure, index_files, move_files, get_mission_input_path

from core.tests.core_factory_floor import (MardidTestCase, MissionFactory, MissionLegFactory,
                                           MissionDatasetFactory, DatasetLocationsFactory)

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
        # provided there are datasets and configuration for their datatypes, there should be functionality that will
        # create a file structure where users can place their data files to upload.

        expected_input_path = Path('CTD', 'BTL')
        btl_datatype = models.DataTypes.objects.get_or_create(name="BTL")[0]
        btl_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=btl_datatype)
        dataset_location = DatasetLocationsFactory.create(datatype=btl_datatype, input_dir=expected_input_path)

        build_file_structure(self.mission)

        expected_path = Path(settings.MEDIA_IN, self.mission.mission_path, expected_input_path)
        assert expected_path.exists(), f"Expected file path does not exist: {expected_path}"


@override_settings(MEDIA_IN='media/IN', MEDIA_OUT='media/OUT')
@tag('utils', 'bulk_upload', 'bulk_upload_with_files')
class TestUtilsBulkUploadWithFiles(MardidTestCase):

    def create_files(self, selected_path: Path, files_to_create: list[str]):
        # Create each file in the directory
        for file_name in files_to_create:
            file_path = selected_path / file_name
            file_path.touch()  # This creates an empty file

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.group = Group.objects.get_or_create(name='MarDID Maintainers')[0]
        self.user.groups.add(self.group)

        self.mission = MissionFactory.create()
        MissionLegFactory(mission=self.mission, start_date="2025-09-28", end_date="2025-10-28")

        # This unfortunately requires a lot of setup and configuration.
        self.ctd_files = ['ctd_file_1.xml', 'ctd_file_1.hex', 'ctd_file_1.hdr', 'ctd_file_1.bl']
        self.btl_files = ['ctd_file_1.btl', 'ctd_file_1.ros']
        self.expected_dict = {
            'CTD': self.ctd_files,
            'BTL': self.btl_files
        }

        expected_input_path = Path('CTD', 'BTL')
        self.btl_datatype = models.DataTypes.objects.get_or_create(name="BTL")[0]
        MissionDatasetFactory.create(mission=self.mission, datatype=self.btl_datatype)
        DatasetLocationsFactory.create(datatype=self.btl_datatype, input_dir=expected_input_path, output_dir=expected_input_path)

        expected_input_path = Path('CTD', 'CTD_RAW')
        self.ctd_datatype = models.DataTypes.objects.get_or_create(name="CTD_RAW")[0]
        MissionDatasetFactory.create(mission=self.mission, datatype=self.ctd_datatype)
        DatasetLocationsFactory.create(datatype=self.ctd_datatype, input_dir=expected_input_path, output_dir=expected_input_path)

        build_file_structure(self.mission)

        mission_input_path = get_mission_input_path(self.mission)
        ctd_datatype_path = Path(mission_input_path, self.ctd_datatype.location.input_dir)
        btl_datatype_path = Path(mission_input_path, self.btl_datatype.location.input_dir)

        self.create_files(ctd_datatype_path, files_to_create=self.ctd_files)
        self.create_files(btl_datatype_path, files_to_create=self.btl_files)

    def tearDown(self):
        expected_path = Path(settings.MEDIA_IN)
        if expected_path.exists():
            shutil.rmtree(expected_path)

        expected_path = Path(settings.MEDIA_OUT)
        if expected_path.exists():
            shutil.rmtree(expected_path)

    def test_get_files_in_directories(self):
        # files placed in the bulk input directory should be indexed and a list for each data type returned.
        file_dict = index_files(self.mission)

        assert file_dict is not None, "Expected file dict is None"

        assert 'CTD_RAW' in file_dict, f"Expected data type CTD not found in file dict"
        assert 'BTL' in file_dict, f"Expected data type BTL not found in file dict"

        assert set(self.btl_files) == set(file_dict['BTL']), f"File sets do not match {file_dict['BTL']}"
        assert set(self.ctd_files) == set(file_dict['CTD_RAW']), f"File sets do not match {file_dict['CTD_RAW']}"

    def test_authentication(self):
        # only an authenticated user should be able to log files into the system
        empty_user: User = None

        file_dict = index_files(self.mission)

        with self.assertRaises(PermissionError):
            move_files(empty_user, self.mission, file_dict)

    def test_move_files(self):
        # files placed in the bulk input directory should be indexed and a list for each data type returned.
        # resulting dictionary when fed to the move files function should transfer from the input to output directories.
        file_dict = index_files(self.mission)

        move_files(self.user, self.mission, file_dict)

        output_mission_path = Path(settings.MEDIA_OUT, self.mission.mission_path)
        output_ctd_path = Path(output_mission_path, self.ctd_datatype.location.output_dir)
        output_btl_path = Path(output_mission_path, self.btl_datatype.location.output_dir)

        assert output_ctd_path.exists(), f"Expected file path does not exist: {output_ctd_path}"
        assert output_btl_path.exists(), f"Expected file path does not exist: {output_btl_path}"

        # check that the files are being tracked
        btl_files = models.DataFiles.objects.filter(dataset__datatype__name='BTL')
        assert btl_files.exists(), f"Expected files were not tracked in the database"

        ctd_files = models.DataFiles.objects.filter(dataset__datatype__name='CTD_RAW')
        assert ctd_files.exists(), f"Expected files were not tracked in the database"
