import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
from jp2_remediator.box_reader import BoxReader, process_directory
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

    def test_read_file_with_valid_path(self):
        # Test reading a valid test file
        result = self.reader.read_file(TEST_DATA_PATH)
        self.assertIsNotNone(result)  # Ensure file content is not None
        self.assertIsInstance(result, bytes)  # Ensure file content is in bytes

    def test_initialize_validator_with_file_content(self):
        # Read file content
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Initialize validator and check the type
        self.reader.file_contents = file_contents
        validator = self.reader.initialize_validator()
        self.assertIsInstance(validator, boxvalidator.BoxValidator)

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

    @patch("builtins.open", new_callable=mock_open)
    def test_read_file_with_io_error(self, mock_open_func):
        # Mock open and read a file and get an error
        mock_open_func.side_effect = IOError("Unable to read file")
        result = self.reader.read_file("nonexistent.jp2")
        self.assertIsNone(result)
        self.reader.logger.error.assert_called_once_with(
            "Error reading file nonexistent.jp2: Unable to read file"
        )

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


if __name__ == "__main__":
    unittest.main()
