import pytest
from unittest.mock import patch, MagicMock
from jp2_remediator.processor import Processor


class TestProcessor:

    @pytest.fixture
    def mock_box_reader_factory(self):
        return MagicMock()

    @pytest.fixture
    def processor(self, mock_box_reader_factory):
        return Processor(mock_box_reader_factory)

    @patch("builtins.print")
    def test_process_file(self, mock_print, processor, mock_box_reader_factory):
        file_path = "test_file.jp2"
        processor.process_file(file_path)
        mock_print.assert_called_once_with(f"Processing file: {file_path}")
        mock_box_reader_factory.get_reader.assert_called_once_with(file_path)
        mock_box_reader_factory.get_reader.return_value.read_jp2_file.assert_called_once()

    @patch("os.walk", return_value=[("root", [], ["file1.jp2", "file2.jp2"])])
    @patch("builtins.print")
    def test_process_directory_with_multiple_files(self, mock_print, mock_os_walk, processor, mock_box_reader_factory):
        processor.process_directory("dummy_path")
        mock_print.assert_any_call("Processing file: root/file1.jp2")
        mock_print.assert_any_call("Processing file: root/file2.jp2")
        assert mock_box_reader_factory.get_reader.call_count == 2
        assert mock_box_reader_factory.get_reader.return_value.read_jp2_file.call_count == 2

    @patch("jp2_remediator.processor.os.path.exists", return_value=True)
    @patch("jp2_remediator.processor.boto3.client", autospec=True)
    @patch("builtins.print", autospec=True)
    def test_process_s3_file_without_output_key_or_prefix(
        self, mock_print, mock_boto3_client, mock_os_path_exists, processor, mock_box_reader_factory
    ):
        # No explicit output_key or prefix given, output_prefix is empty string
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        input_bucket = "test-bucket"
        input_key = "some_folder/my_image.jp2"
        mock_s3_client.download_file.return_value = None
        mock_s3_client.upload_file.return_value = None

        processor.process_s3_file(
            input_bucket=input_bucket,
            input_key=input_key,
            output_bucket=input_bucket,
            output_prefix=""  # Ensures dynamic output_key creation without None issues
        )

        mock_s3_client.download_file.assert_called_once()
        mock_box_reader_factory.get_reader.assert_called_once()
        mock_box_reader_factory.get_reader.return_value.read_jp2_file.assert_called_once()
        assert any("Uploading modified file to bucket:" in c.args[0] for c in mock_print.call_args_list)

    @patch("jp2_remediator.processor.os.path.exists", return_value=True)
    @patch("jp2_remediator.processor.boto3.client", autospec=True)
    @patch("builtins.print", autospec=True)
    def test_process_s3_bucket_with_jp2_files(
        self, mock_print, mock_boto3_client, mock_os_path_exists, processor, mock_box_reader_factory
    ):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        input_bucket = "test-input-bucket"
        input_prefix = "some-prefix/"
        output_bucket = "test-output-bucket"
        output_prefix = "processed/"
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "some-prefix/image1.jp2"},
                {"Key": "some-prefix/image2.jp2"}
            ]
        }
        mock_s3_client.download_file.return_value = None
        mock_s3_client.upload_file.return_value = None

        processor.process_s3_bucket(input_bucket, input_prefix, output_bucket, output_prefix)

        mock_s3_client.list_objects_v2.assert_called_once()
        mock_print.assert_any_call(f"Processing file: some-prefix/image1.jp2 from bucket: {input_bucket}")
        mock_print.assert_any_call(f"Processing file: some-prefix/image2.jp2 from bucket: {input_bucket}")
        assert mock_box_reader_factory.get_reader.call_count == 2
        assert mock_box_reader_factory.get_reader.return_value.read_jp2_file.call_count == 2

    @patch("jp2_remediator.processor.boto3.client", autospec=True)
    @patch("builtins.print", autospec=True)
    def test_process_s3_bucket_empty_response(self, mock_print, mock_boto3_client, processor):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        mock_s3_client.list_objects_v2.return_value = {}
        processor.process_s3_bucket("test-bucket", "test-prefix/", "output-bucket", "output-prefix/")
        mock_print.assert_not_called()
        mock_s3_client.upload_file.assert_not_called()

    @patch("jp2_remediator.processor.os.path.exists", return_value=True)
    @patch("jp2_remediator.processor.boto3.client", autospec=True)
    @patch("builtins.print", autospec=True)
    def test_process_s3_bucket_skip_non_jp2_files(
        self, mock_print, mock_boto3_client, mock_os_path_exists, processor
    ):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "test-prefix/file1.jp2"},
                {"Key": "test-prefix/file2.txt"},
                {"Key": "test-prefix/file3.jpg"},
            ]
        }
        processor.process_s3_bucket("test-bucket", "test-prefix/", "output-bucket", "output-prefix/")
        mock_print.assert_any_call("Processing file: test-prefix/file1.jp2 from bucket: test-bucket")
        mock_s3_client.upload_file.assert_called_once()

    @patch("jp2_remediator.processor.os.path.exists", side_effect=[True, False])
    @patch("jp2_remediator.processor.boto3.client", autospec=True)
    @patch("builtins.print", autospec=True)
    def test_process_s3_file_upload_logic(
        self, mock_print, mock_boto3_client, mock_os_path_exists, processor, mock_box_reader_factory
    ):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        input_bucket = "test-bucket"
        input_key = "test-folder/file.jp2"
        output_bucket = "output-bucket"
        output_key = "output-folder/file_modified.jp2"
        mock_s3_client.download_file.return_value = None
        mock_s3_client.upload_file.return_value = None

        # First call (file exists)
        processor.process_s3_file(input_bucket, input_key, output_bucket, output_key=output_key)
        # Second call (file does not exist after modification)
        processor.process_s3_file(input_bucket, input_key, output_bucket, output_key=output_key)

        mock_print.assert_any_call(f"Uploading modified file to bucket: {output_bucket}, key: {output_key}")
        all_prints = [c.args[0] for c in mock_print.call_args_list]
        assert any("does not exist, skipping upload." in p for p in all_prints)
