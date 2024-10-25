import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
from jp2_remediator.box_reader import BoxReader, process_directory, process_s3_bucket
from jpylyzer import boxvalidator
from project_paths import paths
import datetime

# Define the path to the test data file
TEST_DATA_PATH = os.path.join(paths.dir_unit_resources, "sample.jp2")


class TestJP2ProcessingWithFile(unittest.TestCase):

    def setUp(self):
        """Set up a BoxReader instance for each test."""
        self.reader = BoxReader(TEST_DATA_PATH)
        self.reader.logger = MagicMock()  # Mock logger directly

    # Test for read_file method
    def test_read_file_with_valid_path(self):
        # Test reading a valid test file
        result = self.reader.read_file(TEST_DATA_PATH)
        self.assertIsNotNone(result)  # Ensure file content is not None
        self.assertIsInstance(result, bytes)  # Ensure file content is in bytes

    # Test for initialize_validator method
    def test_initialize_validator_with_file_content(self):
        # Read file content
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Initialize validator and check the type
        self.reader.file_contents = file_contents
        validator = self.reader.initialize_validator()
        self.assertIsInstance(validator, boxvalidator.BoxValidator)

    # Test for find_box_position method
    def test_find_box_position_in_file(self):
        # Read file content
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Set the file contents for the reader instance
        self.reader.file_contents = file_contents

        # Find a known box position in the sample file
        position = self.reader.find_box_position(b"\x6a\x70\x32\x68")
        self.assertNotEqual(position, -1)  # Ensure that the box is found

    # Test for check_boxes method
    def test_check_boxes_in_file(self):
        # Read file content
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Set the file contents for the reader instance
        self.reader.file_contents = file_contents

        # Call check_boxes
        header_offset_position = self.reader.check_boxes()
        self.assertIsNotNone(header_offset_position)

    # Test for process_colr_box method
    def test_process_colr_box_in_file(self):
        # Read file content
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Set the file contents for the reader instance
        self.reader.file_contents = file_contents

        # Find the colr box position
        colr_position = self.reader.find_box_position(b"\x63\x6f\x6c\x72")
        if colr_position == -1:
            self.fail("'colr' box not found in the test file.")

        # Process the colr box
        header_offset_position = self.reader.process_colr_box(colr_position)
        self.assertIsNotNone(header_offset_position)

    # Test for write_modified_file method
    @patch(
            "builtins.open",
            new_callable=mock_open,
            read_data=b"sample content"
            )
    def test_write_modified_file_with_changes(self, mock_file):
        # Read file content (from mock)
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Modify the file contents slightly using bytes
        new_file_contents = file_contents + b" modified"
        # Append in bytes, not string

        # Test writing the modified file
        self.reader.write_modified_file(new_file_contents)
        timestamp = datetime.datetime.now().strftime(
            "%Y%m%d"
        )  # use "%Y%m%d_%H%M%S" for more precision
        expected_filename = TEST_DATA_PATH.replace(
            ".jp2", f"_modified_{timestamp}.jp2")

        # Ensure the file was written to the correct file path
        mock_file.assert_any_call(expected_filename, "wb")

        # Ensure the contents were written correctly
        mock_file().write.assert_called_once_with(b"sample content modified")

    # Test for read_file method with IOError
    @patch("builtins.open", new_callable=mock_open)
    def test_read_file_with_io_error(self, mock_open_func):
        # Mock open and read a file and get an error
        mock_open_func.side_effect = IOError("Unable to read file")
        result = self.reader.read_file("nonexistent.jp2")
        self.assertIsNone(result)
        self.reader.logger.error.assert_called_once_with(
            "Error reading file nonexistent.jp2: Unable to read file"
        )

    # Test for process_all_trc_tags method
    def test_process_all_trc_tags(self):
        # Create TRC tags to process
        trc_tags = (b"\x72\x54\x52\x43" + b"\x67\x54\x52\x43" +
                    b"\x62\x54\x52\x43")
        self.reader.file_contents = bytearray(b"\x00" * 50 + trc_tags
                                              + b"\x00" * 50)
        header_offset_position = 50
        modified_contents = self.reader.process_all_trc_tags(
            header_offset_position
        )
        self.assertEqual(modified_contents, self.reader.file_contents)

    # Test for process_directory function
    @patch("jp2_remediator.box_reader.BoxReader")
    @patch("os.walk", return_value=[("root", [], ["file1.jp2", "file2.jp2"])])
    @patch("builtins.print")
    def test_process_directory_with_multiple_files(
        self, mock_print, mock_os_walk, mock_box_reader
    ):
        # Process a dir with multiple jp2 files
        # Mock the logger for each BoxReader instance created
        mock_box_reader.return_value.logger = MagicMock()

        # Call process_directory with a dummy path
        process_directory("dummy_path")

        # Check that each JP2 file in the directory was processed
        mock_print.assert_any_call("Processing file: root/file1.jp2")
        mock_print.assert_any_call("Processing file: root/file2.jp2")

        # Ensure each BoxReader instance had its read_jp2_file method called
        self.assertEqual(
            mock_box_reader.return_value.read_jp2_file.call_count, 2
            )

    # Test for check_boxes method logging when 'jp2h' not found
    def test_jp2h_not_found_logging(self):
        # Set up file_contents to simulate a missing 'jp2h' box
        self.reader.file_contents = b"\x00" * 100
        # Arbitrary content without 'jp2h'
        # Call the method that should log the debug message
        self.reader.check_boxes()
        # Check that the specific debug message was logged
        self.reader.logger.debug.assert_any_call(
            "'jp2h' not found in the file."
            )

    # Test for write_modified_file method when no changes
    @patch("builtins.open", new_callable=mock_open)
    def test_write_modified_file_no_changes(self, mock_file):
        # Set the file contents to simulate a situation with no modifications
        original_content = b"original content"
        self.reader.file_contents = original_content

        # Call write_modified_file with identical content
        self.reader.write_modified_file(original_content)

        # Ensure that no file was written because there were no modifications
        mock_file.assert_not_called()

        # Check that the specific debug message was logged
        self.reader.logger.debug.assert_called_once_with(
            "No modifications needed. No new file created."
            )

    # Test for process_colr_box method when meth_value == 1
    def test_process_colr_box_meth_value_1(self):
        # Create file contents with exactly positioned 'colr' box and meth_value = 1
        # Ensure 'colr' starts at 100, followed by 4 bytes, and then meth_value at 1
        self.reader.file_contents = (
            b"\x00" * 100 +  # Padding before 'colr' box
            b"\x63\x6f\x6c\x72" +  # 'colr' box
            # b"\x00\x00\x00\x00" +  # Four placeholder bytes - kim why issue
            b"\x01"  # meth_value set to 1
        )
        colr_position = 100
        header_offset_position = self.reader.process_colr_box(colr_position)
        expected_position = colr_position + 4 + 7
        # Assert the expected header offset position
        self.assertEqual(header_offset_position, expected_position)
        self.reader.logger.debug.assert_any_call(
            f"'meth' is 1, setting header_offset_position to: {expected_position}"
        )

    # Test for process_colr_box method with unrecognized meth_value
    def test_process_colr_box_unrecognized_meth_value(self):
        self.reader.file_contents = (
            b"\x00" * 100 +  # Padding before 'colr' box
            b"\x63\x6f\x6c\x72" +  # 'colr' box
            # b"\x00\x00\x00\x00" +  # Four placeholder bytes - kim why issue
            b"\x03"  # meth_value set to 3
        )
        colr_position = 100
        # print("File Contents:", self.reader.file_contents)  # Debug print
        header_offset_position = self.reader.process_colr_box(colr_position)
        self.assertIsNone(header_offset_position)
        self.reader.logger.debug.assert_any_call(
            "'meth' value 3 is not recognized (must be 1 or 2)."
        )

    # Test for process_colr_box method when 'colr' box is missing
    def test_process_colr_box_missing(self):
        self.reader.file_contents = b"\x00" * 100
        colr_position = -1
        header_offset_position = self.reader.process_colr_box(colr_position)
        self.assertIsNone(header_offset_position)
        self.reader.logger.debug.assert_any_call("'colr' not found in the file.")

    # Test for process_trc_tag method with incomplete trc_tag_entry
    def test_process_trc_tag_incomplete_entry(self):
        self.reader.file_contents = b"\x00" * 100 + b"\x72\x54\x52\x43" + b"\x00" * 6
        trc_hex = b"\x72\x54\x52\x43"
        header_offset_position = 50
        new_contents = self.reader.process_trc_tag(trc_hex, "rTRC", bytearray(self.reader.file_contents), header_offset_position)
        self.reader.logger.debug.assert_any_call("Could not extract the full 12-byte 'rTRC' tag entry.")

    # Test for process_trc_tag: trc_hex not found in new_contents
    def test_process_trc_tag_trc_hex_not_found(self):
        # Prepare the test data for when trc_hex is not found
        trc_hex = b"\x72\x54\x52\x43"  # Hex value not present in new_contents
        trc_name = "rTRC"
        new_contents = bytearray(b"\x00" * 100)  # Sample contents without trc_hex
        header_offset_position = 50

        # Call process_trc_tag and expect no modifications to new_contents
        result = self.reader.process_trc_tag(trc_hex, trc_name, new_contents, header_offset_position)

        # Check that the function returned the original new_contents
        self.assertEqual(result, new_contents)

        # Verify that the correct debug message was logged
        self.reader.logger.debug.assert_any_call(f"'{trc_name}' not found in the file.")

    # Test for process_trc_tag: header_offset_position is None
    def test_process_trc_tag_header_offset_none(self):
        # Prepare the test data where header_offset_position is None
        trc_hex = b"\x72\x54\x52\x43"  # Hex value found in new_contents
        trc_name = "rTRC"
        new_contents = bytearray(b"\x00" * 50 + trc_hex + b"\x00" * 50)
        header_offset_position = None  # Simulate unrecognized meth value

        # Call process_trc_tag and expect no modifications to new_contents
        result = self.reader.process_trc_tag(trc_hex, trc_name, new_contents, header_offset_position)

        # Check that the function returned the original new_contents
        self.assertEqual(result, new_contents)

        # Verify that the correct debug message was logged
        self.reader.logger.debug.assert_any_call(
            f"Cannot calculate 'curv_{trc_name}_position' due to an unrecognized 'meth' value."
        )

    # Test for read_jp2_file method when file_contents is valid
    def test_read_jp2_file(self):
        # Prepare the test data with valid file contents
        self.reader.file_contents = b"Valid JP2 content"

        # Mock dependent methods and attributes
        with patch.object(self.reader, 'initialize_validator') as mock_initialize_validator, \
            patch.object(self.reader, 'validator') as mock_validator, \
            patch.object(self.reader, 'check_boxes') as mock_check_boxes, \
            patch.object(self.reader, 'process_all_trc_tags') as mock_process_all_trc_tags, \
            patch.object(self.reader, 'write_modified_file') as mock_write_modified_file:

            # Set up the mock for validator._isValid()
            mock_validator._isValid.return_value = True

            # Set up return values for other methods
            mock_check_boxes.return_value = 100  # Example header_offset_position
            mock_process_all_trc_tags.return_value = b"Modified JP2 content"

            # Call the method under test
            self.reader.read_jp2_file()

            # Assert that initialize_validator was called once
            mock_initialize_validator.assert_called_once()

            # Assert that validator._isValid() was called once
            mock_validator._isValid.assert_called_once()

            # Assert that logger.info was called with correct parameters
            self.reader.logger.info.assert_called_with("Is file valid?", True)

            # Assert that check_boxes was called once
            mock_check_boxes.assert_called_once()

            # Assert that process_all_trc_tags was called with the correct header_offset_position
            mock_process_all_trc_tags.assert_called_once_with(100)

            # Assert that write_modified_file was called with the modified contents
            mock_write_modified_file.assert_called_once_with(b"Modified JP2 content")

    # Test for read_jp2_file method when file_contents is valid
    def test_read_jp2_file(self):
        # Prepare the test data with valid file contents
        self.reader.file_contents = b"Valid JP2 content"

        # Mock dependent methods and attributes
        with patch.object(self.reader, 'initialize_validator') as mock_initialize_validator, \
            patch.object(self.reader, 'validator') as mock_validator, \
            patch.object(self.reader, 'check_boxes') as mock_check_boxes, \
            patch.object(self.reader, 'process_all_trc_tags') as mock_process_all_trc_tags, \
            patch.object(self.reader, 'write_modified_file') as mock_write_modified_file:

            # Set up the mock for validator._isValid()
            mock_validator._isValid.return_value = True

            # Set up return values for other methods
            mock_check_boxes.return_value = 100  # Example header_offset_position
            mock_process_all_trc_tags.return_value = b"Modified JP2 content"

            # Call the method under test
            self.reader.read_jp2_file()

            # Assert that initialize_validator was called once
            mock_initialize_validator.assert_called_once()

            # Assert that validator._isValid() was called once
            mock_validator._isValid.assert_called_once()

            # Assert that logger.info was called with correct parameters
            self.reader.logger.info.assert_called_with("Is file valid?", True)

            # Assert that check_boxes was called once
            mock_check_boxes.assert_called_once()

            # Assert that process_all_trc_tags was called with the correct header_offset_position
            mock_process_all_trc_tags.assert_called_once_with(100)

            # Assert that write_modified_file was called with the modified contents
            mock_write_modified_file.assert_called_once_with(b"Modified JP2 content")

    # Test for read_jp2_file method when file_contents is valid
    def test_read_jp2_file(self):
        # Prepare the test data with valid file contents
        self.reader.file_contents = b"Valid JP2 content"

        # Mock dependent methods and attributes
        with patch.object(self.reader, 'initialize_validator') as mock_initialize_validator, \
            patch.object(self.reader, 'validator') as mock_validator, \
            patch.object(self.reader, 'check_boxes') as mock_check_boxes, \
            patch.object(self.reader, 'process_all_trc_tags') as mock_process_all_trc_tags, \
            patch.object(self.reader, 'write_modified_file') as mock_write_modified_file:

            # Set up the mock for validator._isValid()
            mock_validator._isValid.return_value = True

            # Set up return values for other methods
            mock_check_boxes.return_value = 100  # Example header_offset_position
            mock_process_all_trc_tags.return_value = b"Modified JP2 content"

            # Call the method under test
            self.reader.read_jp2_file()

            # Assert that initialize_validator was called once
            mock_initialize_validator.assert_called_once()

            # Assert that validator._isValid() was called once
            mock_validator._isValid.assert_called_once()

            # Assert that logger.info was called with correct parameters
            self.reader.logger.info.assert_called_with("Is file valid?", True)

            # Assert that check_boxes was called once
            mock_check_boxes.assert_called_once()

            # Assert that process_all_trc_tags was called with the correct header_offset_position
            mock_process_all_trc_tags.assert_called_once_with(100)

            # Assert that write_modified_file was called with the modified contents
            mock_write_modified_file.assert_called_once_with(b"Modified JP2 content")

    # Test for read_jp2_file method when file_contents is None or empty
    def test_read_jp2_file_no_file_contents(self):
        # Set file_contents to None to simulate missing content
        self.reader.file_contents = None

        # Mock dependent methods to ensure they are not called
        with patch.object(self.reader, 'initialize_validator') as mock_initialize_validator, \
            patch.object(self.reader, 'check_boxes') as mock_check_boxes, \
            patch.object(self.reader, 'process_all_trc_tags') as mock_process_all_trc_tags, \
            patch.object(self.reader, 'write_modified_file') as mock_write_modified_file:

            # Call the method under test
            self.reader.read_jp2_file()

            # Assert that the method returns early and dependent methods are not called
            mock_initialize_validator.assert_not_called()
            mock_check_boxes.assert_not_called()
            mock_process_all_trc_tags.assert_not_called()
            mock_write_modified_file.assert_not_called()

    # Test for process_s3_bucket function
    @patch("jp2_remediator.box_reader.boto3.client")
    @patch("jp2_remediator.box_reader.BoxReader")
    @patch("builtins.print")
    def test_process_s3_bucket(self, mock_print, mock_box_reader, mock_boto3_client):
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

        # Mock BoxReader instance and its read_jp2_file method
        mock_reader_instance = MagicMock()
        mock_box_reader.return_value = mock_reader_instance

        # Call the method under test
        process_s3_bucket(bucket_name, prefix)

        # Verify that list_objects_v2 was called with the correct parameters
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket=bucket_name, Prefix=prefix)

        # Verify that download_file was called for each .jp2 file
        expected_download_calls = [
            unittest.mock.call(bucket_name, "file1.jp2", "/tmp/file1.jp2"),
            unittest.mock.call(bucket_name, "file2.jp2", "/tmp/file2.jp2"),
        ]
        self.assertEqual(mock_s3_client.download_file.call_args_list, expected_download_calls)

        # Verify that BoxReader was instantiated with the correct download paths
        expected_boxreader_calls = [
            unittest.mock.call("/tmp/file1.jp2"),
            unittest.mock.call("/tmp/file2.jp2"),
        ]
        self.assertEqual(mock_box_reader.call_args_list, expected_boxreader_calls)

        # Verify that read_jp2_file was called for each .jp2 file
        self.assertEqual(mock_reader_instance.read_jp2_file.call_count, 2)

        # Verify that upload_file was called for each .jp2 file
        upload_calls = mock_s3_client.upload_file.call_args_list
        self.assertEqual(len(upload_calls), 2)
        for call in upload_calls:
            args, _ = call
            local_file_path = args[0]
            upload_bucket = args[1]
            upload_key = args[2]
            # Check that the local file path includes '_modified_' and ends with '.jp2'
            self.assertIn("_modified_", local_file_path)
            self.assertTrue(local_file_path.endswith(".jp2"))
            # Check that the upload is to the correct bucket and key
            self.assertEqual(upload_bucket, bucket_name)
            self.assertIn("_modified_", upload_key)
            self.assertTrue(upload_key.endswith(".jp2"))

        # Verify that print was called correctly
        expected_print_calls = [
            unittest.mock.call(f"Processing file: file1.jp2 from bucket {bucket_name}"),
            unittest.mock.call(f"Processing file: file2.jp2 from bucket {bucket_name}"),
        ]
        mock_print.assert_has_calls(expected_print_calls, any_order=True)

    # Test for process_trc_tag: when trc_tag_size != curv_trc_field_length
    def test_process_trc_tag_size_mismatch(self):
        # Prepare test data where trc_tag_size does not match curv_trc_field_length
        trc_hex = b'\x72\x54\x52\x43'  # Hex for 'rTRC'
        trc_name = 'rTRC'
        trc_position = 10  # Arbitrary position where trc_hex is found in new_contents

        # Set trc_tag_offset and trc_tag_size with values that will cause a mismatch
        trc_tag_offset = 50  # Arbitrary offset value
        trc_tag_size = 20    # Set intentionally different from curv_trc_field_length

        # Build the trc_tag_entry (12 bytes): signature + offset + size
        trc_tag_entry = trc_hex + trc_tag_offset.to_bytes(4, 'big') + trc_tag_size.to_bytes(4, 'big')

        # Prepare new_contents with the trc_tag_entry at trc_position
        new_contents = bytearray(b'\x00' * trc_position + trc_tag_entry + b'\x00' * 200)

        # Set header_offset_position to a valid integer
        header_offset_position = 5  # Arbitrary valid value

        # Prepare curv_profile data with curv_trc_gamma_n such that curv_trc_field_length != trc_tag_size
        curv_trc_gamma_n = 1  # Set gamma_n to 2
        curv_trc_field_length = curv_trc_gamma_n * 2 + 12  # Calculates to 16

        # Build curv_profile (12 bytes): signature + reserved + gamma_n
        curv_signature = b'curv'  # Signature 'curv'
        curv_reserved = (0).to_bytes(4, 'big')  # Reserved bytes set to zero
        curv_trc_gamma_n_bytes = curv_trc_gamma_n.to_bytes(4, 'big')
        curv_profile = curv_signature + curv_reserved + curv_trc_gamma_n_bytes

        # Calculate curv_trc_position based on trc_tag_offset and header_offset_position
        curv_trc_position = trc_tag_offset + header_offset_position

        # Ensure new_contents is large enough to hold the curv_profile at the calculated position
        required_length = curv_trc_position + len(curv_profile)
        if len(new_contents) < required_length:
            new_contents.extend(b'\x00' * (required_length - len(new_contents)))

        # Insert curv_profile into new_contents at curv_trc_position
        new_contents[curv_trc_position:curv_trc_position + len(curv_profile)] = curv_profile

        # Mock the logger to capture warnings
        self.reader.logger = MagicMock()

        # Call the method under test
        result_contents = self.reader.process_trc_tag(trc_hex, trc_name, new_contents, header_offset_position)

        # Verify that the trc_tag_size in new_contents was updated to curv_trc_field_length
        updated_trc_tag_size_bytes = result_contents[trc_position + 8: trc_position + 12]
        updated_trc_tag_size = int.from_bytes(updated_trc_tag_size_bytes, 'big')
        self.assertEqual(updated_trc_tag_size, curv_trc_field_length)

        # Verify that the appropriate warning was logged
        expected_warning = f"'{trc_name}' Tag Size ({trc_tag_size}) does not match 'curv_{trc_name}_field_length' ({curv_trc_field_length}). Modifying the size..."
        self.reader.logger.warning.assert_any_call(expected_warning)

if __name__ == "__main__":
    unittest.main()