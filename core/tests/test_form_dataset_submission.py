import os
import shutil
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import tag, Client
from django.urls import reverse_lazy
from django.test import override_settings

from core.tests import core_factory_floor
from core.tests.core_factory_floor import MardidTestCase
from core.views.forms.form_dataset_submission import get_output_path

# When running unit tests we want to use a separate media output directory to avoid
# accidentally deleting or overwriting real files.
@override_settings(MEDIA_OUT='media/OUT')
class AbstractTestWithUsers(MardidTestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password')
        self.group = Group.objects.get_or_create(name='MarDID Maintainers')[0]
        self.user.groups.add(self.group)

@tag('test_form_dataset_submission')
class TestFormMission(AbstractTestWithUsers):

    def test_dataset_status_update_not_visible_to_anonymous_user(self):
        dataset = core_factory_floor.MissionDatasetFactory()
        core_factory_floor.MissionDataFilesFactory.create_batch(4, dataset=dataset)

        response = self.client.get(reverse_lazy('core:dataset_submission_view', args=[dataset.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        # an anonymous user should not be able to see the file submission form
        file_submission_form = soup.find(id="form_id_dataset_submission")
        self.assertIsNone(file_submission_form)

        # an anonymous user should not be able to see the dataset status form
        dataset_status_form = soup.find(id="form_id_dataset_status")
        self.assertIsNone(dataset_status_form)

        # an anonymous user should be able to see the datasets files tab
        dataset_files_tab = soup.find(id="div_id_dataset_tabs_files")
        self.assertIsNotNone(dataset_files_tab)

        # an anonymous user should be able to see the datasets comment tab
        datasets_comment_tab = soup.find(id="div_id_dataset_tabs_comments")
        self.assertIsNotNone(datasets_comment_tab)

        # an anonymous user should be able to see the datasets archived files tab
        dataset_archive_tab = soup.find(id="div_id_dataset_tabs_archived")
        self.assertIsNotNone(dataset_archive_tab)

        # an anonymous user should not be able to see the datasets comment form
        datasets_comment_form = soup.find(id="form_id_dataset_comments")
        self.assertIsNone(datasets_comment_form)


    def test_dataset_status_update_visible_to_user(self):
        # the purpose of this test is to ensure elements are visible to a user, but also to ensure expected HTML
        # IDs are accounted for if they end up being changed in the future.
        self.client.login(username='testuser', password='password')

        dataset = core_factory_floor.MissionDatasetFactory()
        core_factory_floor.MissionDataFilesFactory.create_batch(4, dataset=dataset)

        response = self.client.get(reverse_lazy('core:dataset_submission_view', args=[dataset.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        # a user should be able to see the file submission form
        file_submission_form = soup.find(id="form_id_dataset_submission")
        self.assertIsNotNone(file_submission_form)

        # a user should be able to see the dataset status form
        dataset_status_form = soup.find(id="form_id_dataset_status")
        self.assertIsNotNone(dataset_status_form)

        # a user should be able to see the datasets files tab
        dataset_files_tab = soup.find(id="div_id_dataset_tabs_files")
        self.assertIsNotNone(dataset_files_tab)

        # a user should be able to see the datasets comment tab
        datasets_comment_tab = soup.find(id="div_id_dataset_tabs_comments")
        self.assertIsNotNone(datasets_comment_tab)

        # a user should be able to see the datasets archived files tab
        dataset_archive_tab = soup.find(id="div_id_dataset_tabs_archived")
        self.assertIsNotNone(dataset_archive_tab)

        # a user should be able to see the datasets comment form
        datasets_comment_form = soup.find(id="form_id_dataset_comments")
        self.assertIsNotNone(datasets_comment_form)

        # a regular user should not be able to see the delete dataset files button
        delete_btn = soup.find("button", attrs={'title': 'Delete Dataset Files'})
        self.assertIsNone(delete_btn)

    def test_superuser_delete_dataset(self):
        # If the user is a superuser, they should have access to the delete data files button.
        self.client.login(username='admin', password='password')

        dataset = core_factory_floor.MissionDatasetFactory()
        core_factory_floor.MissionDataFilesFactory.create_batch(4, dataset=dataset)

        response = self.client.get(reverse_lazy('core:dataset_submission_view', args=[dataset.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        delete_btn = soup.find("button", attrs={'title': 'Delete Dataset Files'})
        self.assertIsNotNone(delete_btn)

@tag('test_form_dataset_submission', 'test_form_dataset_submission_with_files')
class TestFormWithFiles(AbstractTestWithUsers):
    def setUp(self):
        super().setUp()

        self.mission = core_factory_floor.MissionFactory(name='TEST2025001')
        self.leg = core_factory_floor.MissionLegFactory(mission=self.mission,
                                                        start_date=datetime(2025, 1, 1),
                                                        end_date=datetime(2025, 1, 31))
        self.dataset = core_factory_floor.MissionDatasetFactory(mission=self.mission)
        core_factory_floor.DatasetLocationsFactory(datatype=self.dataset.datatype)

    @tag('test_dataset_file_submission_success')
    def test_dataset_file_submission_success(self):
        # If files are successfully submitted, the response should include an HX-Trigger header with the value 'dataset_files_updated'
        # and None is returned because the form should clear itself
        output_path = get_output_path(self.dataset.pk)

        self.client.login(username='testuser', password='password')
        files = ['file1.txt', 'file2.txt', 'file3.txt', 'file4.txt']

        form_data = {
            'files': [SimpleUploadedFile(f, f"File content {n}".encode()) for n,f in enumerate(files)],
            'submitted_by': self.user.id,
        }
        try:
            response = self.client.post(reverse_lazy('core:submit_dataset_files', args=[self.dataset.pk]), data=form_data)
            self.assertIn('HX-Trigger', response.headers)
            self.assertEqual(response.headers['HX-Trigger'], 'dataset_files_updated')
            self.assertEqual(response.content, b'')
        finally:
            if os.path.exists(settings.MEDIA_OUT):
                shutil.rmtree(settings.MEDIA_OUT)

    def test_dataset_file_submission_failure(self):
        # If files are not successfully submitted because they're already being tracked in the database
        # the response should contain a message area to be swapped in where the button exists.
        # this should contain a new form with a text field asking the user to leave a message on why files
        # are being replaced.
        output_path = get_output_path(self.dataset.pk)

        self.client.login(username='testuser', password='password')

        files = core_factory_floor.MissionDataFilesFactory.create_batch(4, dataset=self.dataset)
        # Create mock files

        form_data = {
            'files': [SimpleUploadedFile(f.file_name, f"File content {n}".encode()) for n,f in enumerate(files)],
            'submitted_by': self.user.id,
        }
        try:
            response = self.client.post(reverse_lazy('core:submit_dataset_files', args=[self.dataset.pk]), data=form_data)

            # The response should contain a new form
            soup = BeautifulSoup(response.content, 'html.parser')
            form = soup.find(id="div_id_archive_message_form")
            self.assertIsNotNone(form)
        finally:
            if os.path.exists(settings.MEDIA_OUT):
                shutil.rmtree(settings.MEDIA_OUT)


    @tag('test_dataset_file_submission_success')
    def test_dataset_delete_dataset_files(self):
        # If files are successfully deleted, the response should include an HX-Trigger header with the value 'dataset_files_updated'
        # and None is returned because the form should clear itself
        output_path = get_output_path(self.dataset.pk)

        # must be a superuser to delete files
        self.client.login(username='admin', password='password')

        files = ['file1.txt', 'file2.txt', 'file3.txt', 'file4.txt']

        form_data = {
            'files': [SimpleUploadedFile(f, f"File content {n}".encode()) for n,f in enumerate(files)],
            'submitted_by': self.user.id,
        }

        try:
            response = self.client.post(reverse_lazy('core:submit_dataset_files', args=[self.dataset.pk]), data=form_data)

            for file in files:
                file_path = Path(output_path, file)
                self.assertTrue(file_path.exists())

            response = self.client.post(reverse_lazy('core:delete_dataset_files', args=[self.dataset.pk]), data=form_data)

            for file in files:
                file_path = Path(output_path, file)
                self.assertFalse(file_path.exists())

            self.assertEqual(response.content, b'')
            self.assertIn('HX-Trigger', response.headers)
            self.assertEqual(response.headers['HX-Trigger'], 'dataset_files_updated')
        finally:
            if os.path.exists(settings.MEDIA_OUT):
                shutil.rmtree(settings.MEDIA_OUT)