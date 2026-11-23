import shutil
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import override_settings, tag
from django.urls import reverse_lazy

from core.tests.core_factory_floor import (MardidTestCase, MissionFactory, MissionLegFactory, MissionDatasetFactory,
                                           MissionDataFilesFactory)
from core import models


@override_settings(MEDIA_IN='media/IN', MEDIA_OUT='media/OUT')
@tag("test_mission_dataset_form")
class TestFormMissionDatasets(MardidTestCase):

    def create_files(self, selected_path: Path, files_to_create: list[str]):
        # Create each file in the directory
        for file_name in files_to_create:
            file_path = selected_path / file_name
            file_path.touch()  # This creates an empty file

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

        expected_input_path = Path('CTD', 'CTD_RAW')
        self.ctd_datatype = models.DataTypes.objects.get_or_create(name="CTD_RAW")[0]
        self.ctd_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=self.ctd_datatype)

        self.salinity_datatype = models.DataTypes.objects.get_or_create(name="SALINITY")[0]
        self.salinity_dataset = MissionDatasetFactory.create(mission=self.mission, datatype=self.salinity_datatype)

    def tearDown(self):
        expected_path = Path(settings.MEDIA_IN)
        if expected_path.exists():
            shutil.rmtree(expected_path)

    @tag("test_non_superuser_delete_dataset_without_files")
    def test_non_superuser_delete_dataset_without_files(self):
        # When a non-superuser is logged in they should be able to delete datasets from a mission if the dataset
        # has no files.
        self.client.login(username='testuser', password='password')

        # ensure the btl_dataset has files attached.
        MissionDataFilesFactory.create(dataset=self.btl_dataset, filename="test_file.btl")

        url = reverse_lazy('core:list_mission_datasets', args=[self.mission.pk])
        response = self.client.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        delete_btl_btn = soup.find(id=f"button_id_delete_dataset_{self.btl_dataset.pk}")
        assert delete_btl_btn is None, "Anonymous user should not see the dataset delete button for BTL dataset, which has files"

        delete_salinity_btn = soup.find(id=f"button_id_delete_dataset_{self.salinity_dataset.pk}")
        assert delete_salinity_btn is None, "Anonymous user should not see the dataset delete button for Salinity dataset, which doesn't have files"

    def test_delete_dataset_with_files_fails(self):
        # Datasets should not be able to be removed from a mission when they have files. A user at the superuser level
        # is required to log in and remove both current and archive files from the dataset views page before the dataset
        # can be removed from a mission.
        self.client.login(username='admin', password='password')

        # ensure the btl_dataset has files attached.
        MissionDataFilesFactory.create(dataset=self.btl_dataset, filename="test_file.btl")

        url = reverse_lazy('core:delete_mission_dataset', args=[self.mission.pk, self.btl_dataset.pk])
        response = self.client.get(url)

        assert response.status_code == 403, "Even a superuser should not be able to delete a dataset with files attached"