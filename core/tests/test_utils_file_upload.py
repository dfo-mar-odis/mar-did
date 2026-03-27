import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User, Group
from django.test import tag, RequestFactory, override_settings

from core import models
from core.tests import core_factory_floor
from core.tests.core_factory_floor import MardidTestCase

from core.utils import file_upload


# When running unit tests we want to use a separate media output directory to avoid
# accidentally deleting or overwriting real files.
@override_settings(MEDIA_OUT='media/OUT')
@tag("file_upload")
class TestFileUpload(MardidTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password')
        self.group = Group.objects.get_or_create(name='MarDID Maintainers')[0]
        self.user.groups.add(self.group)

    def test_authentication_fails(self):
        try:
            file_upload.save_files(user=None, dataset=None, files=[], output_path="")
        except PermissionError as ex:
            assert str(ex) == "Only authenticated users can upload files."
        else:
            assert False, "Expected PermissionError was not raised."

    def test_returns_without_files(self):
        try:
            file_upload.save_files(user=self.user, dataset=None, files=[], output_path="")
        except Exception as ex:
            assert False, f"Unexpected exception was raised: {ex}"

    def tests_os_path_created_called(self):
        dataset = core_factory_floor.MissionDatasetFactory(datatype=models.DataTypes.objects.get(pk=1))
        core_factory_floor.DatasetLocationsFactory(datatype=dataset.datatype)

        output_path = Path(settings.BASE_DIR, 'core', 'tests', 'data', dataset.datatype.locations.first().output_dir)

        mock_files = [
            SimpleUploadedFile("file1.txt", b"Content of file 1"),
            SimpleUploadedFile("file2.txt", b"Content of file 2"),
            SimpleUploadedFile("file3.txt", b"Content of file 3"),
        ]
        try:
            file_upload.save_files(user=self.user, dataset=dataset, files=mock_files, output_path=output_path)
            assert os.path.exists(output_path), "Output path was not created."
        except Exception as ex:
            assert False, f"Unexpected exception was raised: {ex}"
        finally:
            if os.path.exists(output_path):
                shutil.rmtree(output_path)

    def test_file_validation(self):
        dataset = core_factory_floor.MissionDatasetFactory(datatype=models.DataTypes.objects.get(pk=1))
        models.DatasetLocations.objects.create(datatype=dataset.datatype, output_dir="test_output")

        mock_files = [
            SimpleUploadedFile("file1.txt", b"Content of file 1"),
            SimpleUploadedFile("file2.txt", b"Content of file 2"),
            SimpleUploadedFile("file3.txt", b"Content of file 3"),
        ]

        # First upload should succeed
        existing_files = file_upload.validate_files(user=self.user, dataset=dataset, files=mock_files)
        self.assertIsNone(existing_files, "Expected no existing files on first validation.")

        # Simulate saving the files to the dataset
        for file in mock_files:
            models.DataFiles.objects.create(dataset=dataset, file_name=file.name,
                                            file_type=models.FileTypes.objects.first(), submitted_by=self.user,
                                            is_archived=False)

        # Second upload with the same files should fail
        existing_files = file_upload.validate_files(user=self.user, dataset=dataset, files=mock_files)
        self.assertIsNotNone(existing_files, "Expected existing files on second validation.")

    @tag('test_file_validation_should_not_return_archived_files')
    def test_file_validation_should_not_return_archived_files(self):
        dataset = core_factory_floor.MissionDatasetFactory(datatype=models.DataTypes.objects.get(pk=1))
        models.DatasetLocations.objects.create(datatype=dataset.datatype, output_dir="test_output")

        mock_file = SimpleUploadedFile("file1.txt", b"Content of file 1")

        # Simulate saving the file to the dataset
        data_file = models.DataFiles.objects.create(dataset=dataset, file_name=mock_file.name,
                                            file_type=models.FileTypes.objects.first(), submitted_by=self.user,
                                            is_archived=False)

        # Validate the file exists
        existing_files = file_upload.validate_files(user=self.user, dataset=dataset, files=[mock_file])
        self.assertIsNotNone(existing_files, "Expected existing files on validation.")

        # Mark the file as archived
        data_file.is_archived = True
        data_file.save()

        # Validate the file is no longer returned by validation
        existing_files = file_upload.validate_files(user=self.user, dataset=dataset, files=[mock_file])
        self.assertIsNone(existing_files, "Expected no existing files after archiving.")

    def test_archive_files_success(self):
        dataset = core_factory_floor.MissionDatasetFactory(datatype=models.DataTypes.objects.get(pk=1))
        models.DatasetLocations.objects.create(datatype=dataset.datatype, output_dir="test_output")

        output_path = Path(settings.BASE_DIR, 'core', 'tests', 'data', 'test_output',
                           dataset.datatype.locations.first().output_dir)
        archive_path = Path(settings.BASE_DIR, 'core', 'tests', 'data', 'test_output', 'archive',
                            dataset.datatype.locations.first().output_dir)

        try:
            mock_files = [
                SimpleUploadedFile("file1.txt", b"Content of file 1"),
                SimpleUploadedFile("file2.txt", b"Content of file 2"),
                SimpleUploadedFile("file3.txt", b"Content of file 3"),
            ]

            file_upload.save_files(user=self.user, dataset=dataset, files=mock_files, output_path=output_path)
            assert os.path.exists(output_path), "Output path was not created."

            new_mock_files = [
                SimpleUploadedFile("file1.txt", b"Content of new file 1"),
            ]

            file_upload.archive_files(user=self.user, dataset=dataset,
                                      file_names=[file.name for file in new_mock_files],
                                      output_path=output_path, archive_path=archive_path,
                                      message="Archiving for test")
            archived_file = dataset.files.filter(is_archived=True)
            assert archived_file.exists(), "Expected file to be archived."

            file_upload.save_files(user=self.user, dataset=dataset, files=new_mock_files, output_path=output_path)
        except Exception as ex:
            assert False, f"Unexpected exception was raised: {ex}"
        finally:
            if os.path.exists(output_path):
                shutil.rmtree(output_path)
