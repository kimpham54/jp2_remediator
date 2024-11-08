import unittest
import pytest
from unittest.mock import call, patch, MagicMock
from jp2_remediator.processor import Processor


class TestProcessor:

    @pytest.fixture
    def mock_box_reader_factory(self):
        return MagicMock()

    @pytest.fixture
    def processor(self, mock_box_reader_factory):
        return Processor(mock_box_reader_factory)

    # Test for process_file function
    @patch("builtins.print")
    def test_process_file(self, mock_print, processor, mock_box_reader_factory):
        # Define the file path
        file_path = "test_file.jp2"

        # Call process_file with the test file path
        processor.process_file(file_path)

        # Check that the file was processed
        mock_print.assert_called_once_with(f"Processing file: {file_path}")

        # Ensure the BoxReader instance had its read_jp2_file method called
        mock_box_reader_factory.get_reader.assert_called_once_with(file_path)
        mock_box_reader_factory.get_reader.return_value.read_jp2_file.assert_called_once()

    # Test for process_directory function
    @patch("os.walk", return_value=[("root", [], ["file1.jp2", "file2.jp2"])])
    @patch("builtins.print")
    def test_process_directory_with_multiple_files(
        self, mock_print, mock_os_walk, processor, mock_box_reader_factory
    ):
        # Call process_directory with a dummy path
        processor.process_directory("dummy_path")

        # Check that each JP2 file in the directory was processed
        mock_print.assert_any_call("Processing file: root/file1.jp2")
        mock_print.assert_any_call("Processing file: root/file2.jp2")

        # Ensure each BoxReader instance had its read_jp2_file method called
        assert mock_box_reader_factory.get_reader.call_count == 2

        # Ensure each BoxReader instance was created with the correct file path
        assert mock_box_reader_factory.get_reader.call_args_list == [
            call("root/file1.jp2"),
            call("root/file2.jp2"),
        ]
        assert mock_box_reader_factory.get_reader.return_value.read_jp2_file.call_count == 2

    # Test for process_s3_bucket function
    @patch("jp2_remediator.processor.boto3.client")
    @patch("builtins.print")
    def test_process_s3_bucket(self, mock_print, mock_boto3_client, processor, mock_box_reader_factory):
        # Set up the mock S3 client
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        # Define the bucket name and prefix
        bucket_name = "test-bucket"
        prefix = "test-prefix"

        # Prepare a fake response for list_objects_v2
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "file1.jp2"},
                {"Key": "file2.jp2"},
                {"Key": "file3.txt"},  # Non-JP2 file to test filtering
            ]
        }

        # Mock download_file and upload_file methods
        mock_s3_client.download_file.return_value = None
        mock_s3_client.upload_file.return_value = None

        # Call the method under test
        processor.process_s3_bucket(bucket_name, prefix)

        # Verify that list_objects_v2 was called with the correct parameters
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket=bucket_name, Prefix=prefix)

        # Verify that download_file was called for each .jp2 file
        expected_download_calls = [
            unittest.mock.call(bucket_name, "file1.jp2", "/tmp/file1.jp2"),
            unittest.mock.call(bucket_name, "file2.jp2", "/tmp/file2.jp2"),
        ]
        assert mock_s3_client.download_file.call_args_list == expected_download_calls

        # Verify that BoxReader was instantiated with the correct download paths
        expected_boxreader_calls = [
            unittest.mock.call("/tmp/file1.jp2"),
            unittest.mock.call("/tmp/file2.jp2"),
        ]
        assert mock_box_reader_factory.get_reader.call_args_list == expected_boxreader_calls

        # Verify that read_jp2_file was called for each .jp2 file
        assert mock_box_reader_factory.get_reader.return_value.read_jp2_file.call_count == 2

        # Verify that upload_file was called for each .jp2 file
        upload_calls = mock_s3_client.upload_file.call_args_list
        assert len(upload_calls) == 2
        for c in upload_calls:
            args, _ = c
            local_file_path = args[0]
            upload_bucket = args[1]
            upload_key = args[2]
            # Check that the local file path includes '_modified_' and ends with '.jp2'
            assert "_modified_" in local_file_path, "'_modified_' should be in local_file_path"
            assert local_file_path.endswith(".jp2")
            # Check that the upload is to the correct bucket and key
            assert upload_bucket == bucket_name
            assert "_modified_" in upload_key
            assert upload_key.endswith(".jp2")

        # Verify that print was called correctly
        expected_print_calls = [
            unittest.mock.call(f"Processing file: file1.jp2 from bucket {bucket_name}"),
            unittest.mock.call(f"Processing file: file2.jp2 from bucket {bucket_name}"),
        ]
        mock_print.assert_has_calls(expected_print_calls, any_order=True)
