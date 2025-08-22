import os

from django.test import tag, TestCase
from unittest.mock import patch, MagicMock, mock_open

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from core.views.forms import form_data_submission
from core import models


@tag('data_submission', 'data_submission_functions')
class TestDataSubmissionFunctions(TestCase):

    def setUp(self):
        pass

    @patch('core.views.forms.form_data_submission.os.makedirs')
    @patch('core.views.forms.form_data_submission.open', new_callable=mock_open)
    @patch('core.views.forms.form_data_submission.models.DataFiles.objects.create')
    def test_save_files(self, mock_create, mock_open, mock_makedirs):
        # Mock user and data objects
        user = MagicMock()
        data = MagicMock()
        data.cruise.start_date.strftime.return_value = '2023'
        data.cruise.name = 'TestCruise'
        data.data_type.name = 'TestDataType'
        data.data_files.filter.return_value.exists.return_value = False

        # Mock file input
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile('test_file.txt', file_content)

        # Call the function
        form_data_submission.save_files(user, data, [uploaded_file])

        expected_path = os.path.join(settings.MEDIA_ROOT, '2023', 'TestCruise', 'TestDataType')
        # Assertions
        mock_makedirs.assert_called_once_with(
            expected_path,
            exist_ok=True
        )
        mock_open.assert_called_once_with(
            os.path.join(expected_path, 'test_file.txt'),
            'wb+'
        )
        mock_create.assert_called_once_with(
            data=data,
            file=os.path.join(expected_path, 'test_file.txt'),
            file_name='test_file.txt',
            submitted_by=user
        )

    @patch('core.views.forms.form_data_submission.os.makedirs')
    def test_save_files_raises_file_exists_error(self, mock_makedirs):
        # Mock user and data objects
        user = MagicMock()
        data = MagicMock()
        data.cruise.start_date.strftime.return_value = '2023'
        data.cruise.name = 'TestCruise'
        data.data_type.name = 'TestDataType'
        data.data_files.filter.return_value.exists.return_value = True  # Simulate file already exists

        # Mock file input
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile('test_file.txt', file_content)

        # Assert that FileExistsError is raised
        with self.assertRaises(FileExistsError):
            form_data_submission.save_files(user, data, [uploaded_file])


    @patch('core.views.forms.form_data_submission.os.makedirs')
    @patch('core.views.forms.form_data_submission.open', new_callable=mock_open)
    @patch('core.views.forms.form_data_submission.models.DataFiles.objects.filter')
    def test_save_files_with_override(self, mock_filter, mock_open, mock_makedirs):
        expected_file_name = 'test_file.txt'

        # Mock existing file
        existing_file = MagicMock()
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.first.return_value = existing_file

        # Mock user and data objects
        user = MagicMock()
        data = MagicMock()
        data.cruise.start_date.strftime.return_value = '2023'
        data.cruise.name = 'TestCruise'
        data.data_type.name = 'TestDataType'
        data.data_files.filter = mock_filter

        # Mock file input
        file_content = b'Updated file content'
        uploaded_file = SimpleUploadedFile(expected_file_name, file_content)

        # Call the function with override=True
        form_data_submission.save_files(user, data, [uploaded_file], override=True)

        expected_path = os.path.join(settings.MEDIA_ROOT, '2023', 'TestCruise', 'TestDataType')
        # Assertions
        mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)
        mock_open.assert_called_once_with(
            os.path.join(expected_path, expected_file_name),
            'wb+'
        )

        # the file_name should not have been changed
        existing_file.file_name.assert_not_called()

        # Check that the existing_file mock retains changes
        self.assertEqual(existing_file.file, os.path.join(expected_path, expected_file_name))
        self.assertEqual(existing_file.submitted_by, user)
        existing_file.save.assert_called_once()