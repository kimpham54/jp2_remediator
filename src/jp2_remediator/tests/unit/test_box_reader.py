import unittest
import os
from unittest.mock import patch, mock_open
from jp2_remediator.box_reader import BoxReader
from jpylyzer import boxvalidator
from project_paths import paths
import datetime

# Define the path to the test data file
TEST_DATA_PATH = os.path.join(paths.dir_unit_resources, 'sample.jp2')

class TestJP2ProcessingWithFile(unittest.TestCase):

    def setUp(self):
        """Set up a BoxReader instance for each test."""
        self.reader = BoxReader(TEST_DATA_PATH)

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

        # Find a known box position in the sample file (you should know the expected values)
        position = self.reader.find_box_position(b'\x6a\x70\x32\x68')
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
        colr_position = self.reader.find_box_position(b'\x63\x6f\x6c\x72')
        if colr_position == -1:
            self.fail("'colr' box not found in the test file.")
        
        # Process the colr box
        header_offset_position = self.reader.process_colr_box(colr_position)
        self.assertIsNotNone(header_offset_position)

    @patch('builtins.open', new_callable=mock_open, read_data=b'sample content')
    def test_write_modified_file_with_changes(self, mock_file):
        # Read file content (from mock)
        file_contents = self.reader.read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Modify the file contents slightly using bytes
        new_file_contents = file_contents + b' modified'  # Append in bytes, not string

        # Test writing the modified file
        self.reader.write_modified_file(new_file_contents)
        timestamp = datetime.datetime.now().strftime("%Y%m%d") # use "%Y%m%d_%H%M%S" for more precision
        expected_filename = TEST_DATA_PATH.replace('.jp2', f'_modified_{timestamp}.jp2')
        
        # Ensure the file was written to the correct file path
        mock_file.assert_any_call(expected_filename, 'wb')
        
        # Ensure the contents were written correctly
        mock_file().write.assert_called_once_with(b'sample content modified')

if __name__ == '__main__':
    unittest.main()