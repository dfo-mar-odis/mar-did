import shutil
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import override_settings, tag
from django.urls import reverse_lazy

from core.tests.core_factory_floor import MardidTestCase, MissionFactory, MissionLegFactory, MissionDatasetFactory, \
    DatasetLocationsFactory, MissionDataFilesFactory
from core.utils.bulk_upload import build_file_structure, get_mission_input_path
from core import models


@override_settings(MEDIA_IN='media/IN', MEDIA_OUT='media/OUT')
@tag("test_mission_dataset_form")
class TestFormMissionDatasets(MardidTestCase):

    def create_files(self, selected_path: Path, files_to_create: list[str]):
        # Create each file in the directory
        for file_name in files_to_create:
            file_path = selected_path / file_name
            file_path.touch()  # This creates an empty file

    def populate_input_directories(self):
        # provided a mission the bulk input function should scan the input directories, move files to the
        # expected output directory and log the new files in the database. This is going to get complicated...
        build_file_structure(self.mission)
        mission_input_path = get_mission_input_path(self.mission)
        ctd_datatype_path = Path(mission_input_path, self.ctd_datatype.location.input_dir)
        btl_datatype_path = Path(mission_input_path, self.btl_datatype.location.input_dir)

        self.create_files(ctd_datatype_path, files_to_create=self.ctd_files)
        self.create_files(btl_datatype_path, files_to_create=self.btl_files)

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password')
        self.group = Group.objects.get_or_create(name='MarDID Maintainers')[0]
        self.user.groups.add(self.group)

        self.mission = MissionFactory.create()
        MissionLegFactory(mission=self.mission, start_date="2025-09-28", end_date="2025-10-28")

        # This unfortunately requires a lot of setup and configuration.
        self.ctd_files = ['ctd_file_1.xml', 'ctd_file_1.hex', 'ctd_file_1.hdr', 'ctd_file_1.bl']
        self.btl_files = ['ctd_file_1.btl', 'ctd_file_1.ros']
        self.expected_dict = {
            'CTD': self.ctd_files,
            'BTL': self.btl_files,
        }

        expected_input_path = Path('CTD', 'BTL')
        self.btl_datatype = models.DataTypes.objects.get_or_create(name="BTL")[0]
        self.btl_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=self.btl_datatype)
        DatasetLocationsFactory.create(datatype=self.btl_datatype, input_dir=expected_input_path, output_dir=expected_input_path)

        expected_input_path = Path('CTD', 'CTD_RAW')
        self.ctd_datatype = models.DataTypes.objects.get_or_create(name="CTD_RAW")[0]
        self.ctd_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=self.ctd_datatype)
        DatasetLocationsFactory.create(datatype=self.ctd_datatype, input_dir=expected_input_path, output_dir=expected_input_path)

        self.salinity_datatype = models.DataTypes.objects.get_or_create(name="SALINITY")[0]
        self.salinity_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=self.salinity_datatype)

    def tearDown(self):
        expected_path = Path(settings.MEDIA_IN)
        if expected_path.exists():
            shutil.rmtree(expected_path)

    def test_anonymous_user_build_bulk_btn(self):
        # an anonymous user should not be able to access the build input button
        url = reverse_lazy('core:list_mission_datasets', args=[self.mission.pk])
        response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        bulk_input_btn = soup.find(id="button_id_build_bulk_input")
        assert bulk_input_btn is None, "Anonymous user should not see the build bulk input button"

    def test_anonymous_user_build_bulk_update_denied(self):
        # an anonymous user should not be able to call the build bulk input function
        url = reverse_lazy('core:build_bulk_input_directories', args=[self.mission.pk])
        response = self.client.get(url)

        assert response.status_code == 302, "Anonymous user should not beable to access the bulk input function"

    def test_authenticated_user_build_bulk_btn(self):
        self.client.login(username='testuser', password='password')

        # an authenticated user should be able to access the build input button
        url = reverse_lazy('core:update_mission_view', args=[self.mission.pk])
        response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        bulk_input_btn = soup.find(id="button_id_build_bulk_input")
        assert bulk_input_btn is not None, "Authenticated user should see the build bulk input button"

    def test_build_bulk_input_dir(self):
        self.client.login(username='testuser', password='password')

        # provided a mission the bulk input function should create an input directory structer for the mission
        url = reverse_lazy('core:build_bulk_input_directories', args=[self.mission.pk])
        response = self.client.get(url)

        expected_path = Path(settings.MEDIA_IN, self.mission.mission_path)
        assert expected_path.exists(), f"Expected file path does not exist: {expected_path}"

    def test_anonymous_user_upload_bulk_btn(self):
        # an anonymous user should not be able to access the upload input button
        url = reverse_lazy('core:list_mission_datasets', args=[self.mission.pk])
        response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        bulk_input_btn = soup.find(id="button_id_upload_bulk_input")
        assert bulk_input_btn is None, "Anonymous user should not see the build bulk input button"

    def test_anonymous_user_upload_bulk_update_denied(self):
        # an anonymous user should not be able to call the build bulk input function
        url = reverse_lazy('core:upload_bulk_input_directories', args=[self.mission.pk])
        response = self.client.get(url)

        assert response.status_code == 302, "Anonymous user should not beable to access the bulk input function"

    def test_authenticated_user_upload_bulk_btn(self):
        self.client.login(username='testuser', password='password')

        # an authenticated user should be able to access the bulk upload button
        url = reverse_lazy('core:update_mission_view', args=[self.mission.pk])
        response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        bulk_input_btn = soup.find(id="button_id_upload_bulk_input")
        assert bulk_input_btn is not None, "Authenticated user should see the upload bulk input button"

    def test_upload_bulk_input_dir(self):
        self.client.login(username='testuser', password='password')
        self.populate_input_directories()

        url = reverse_lazy('core:upload_bulk_input_directories', args=[self.mission.pk])
        response = self.client.get(url)

        expected_path = Path(settings.MEDIA_OUT, self.mission.mission_path)
        assert expected_path.exists(), f"Expected file path does not exist: {expected_path}"

        ctd_src_datatype_path = Path(expected_path, self.ctd_datatype.location.input_dir)
        assert ctd_src_datatype_path.exists(), f"Expected file path does not exist: {ctd_src_datatype_path}"

        btl_src_datatype_path = Path(expected_path, self.btl_datatype.location.input_dir)
        assert btl_src_datatype_path.exists(), f"Expected file path does not exist: {btl_src_datatype_path}"

    @tag("test_upload_bulk_update_file_exists")
    def test_upload_bulk_update_file_exists(self):
        # if uploading a bath of files that already exists the bulk upload function should return a dialog to the
        # user indicating that the files already exist and ask if they want to upload the file anyway. This dialog
        # should have a button to confirm the upload and a button to cancel the upload.
        self.client.login(username='testuser', password='password')

        url = reverse_lazy('core:upload_bulk_input_directories', args=[self.mission.pk])

        with patch('core.utils.bulk_upload.move_files', side_effect=FileExistsError("One or more files already exist")):
            response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        assert soup.find("button", id="button_id_upload_bulk_confirm")

    @tag("test_non_superuser_delete_dataset_without_files")
    def test_non_superuser_delete_dataset_without_files(self):
        # When a non-superuser is logged in they should be able to delete datasets from a mission if the dataset
        # has no files.
        self.client.login(username='testuser', password='password')

        # ensure the btl_dataset has files attached.
        MissionDataFilesFactory.create(dataset=self.btl_dataset, file_name="test_file.btl")

        url = reverse_lazy('core:list_mission_datasets', args=[self.mission.pk])
        response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        delete_btl_btn = soup.find(id=f"button_id_delete_dataset_{self.btl_dataset.pk}")
        assert delete_btl_btn is not None, "Anonymous user should see the dataset delete button for BTL dataset, which has files"
        assert 'disabled' in delete_btl_btn.attrs, "The delete button should be disabled if a dataset has files attached to it"


        delete_salinity_btn = soup.find(id=f"button_id_delete_dataset_{self.salinity_dataset.pk}")
        assert delete_salinity_btn is not None, "Anonymous user should see the dataset delete button for Salinity dataset, which doesn't have files"

    def test_delete_dataset_with_files_fails(self):
        # Datasets should not be able to be removed from a mission when they have files. A user at the superuser level
        # is required to log in and remove both current and archive files from the dataset views page before the dataset
        # can be removed from a mission.
        self.client.login(username='admin', password='password')

        # ensure the btl_dataset has files attached.
        MissionDataFilesFactory.create(dataset=self.btl_dataset, file_name="test_file.btl")

        url = reverse_lazy('core:delete_mission_dataset', args=[self.mission.pk, self.btl_dataset.pk])
        response = self.client.get(url)

        assert response.status_code == 403, "Even a superuser should not be able to delete a dataset with files attached"