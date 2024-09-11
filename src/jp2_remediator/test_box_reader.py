import unittest
import os
from unittest.mock import patch, mock_open
from box_reader import (
    read_file,
    initialize_validator,
    find_box_position,
    check_boxes,
    process_colr_box,
    process_trc_tag,
    process_all_trc_tags,
    write_modified_file
)
from jpylyzer import jpylyzer
from jpylyzer import boxvalidator
from jpylyzer import byteconv

# Define the path to the test data file
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'tests', 'sample.jp2')

class TestJP2ProcessingWithFile(unittest.TestCase):

    def test_read_file_with_valid_path(self):
        # Test reading a valid test file
        result = read_file(TEST_DATA_PATH)
        self.assertIsNotNone(result)  # Ensure file content is not None
        self.assertIsInstance(result, bytes)  # Ensure file content is in bytes

    def test_initialize_validator_with_file_content(self):
        # Read file content
        file_contents = read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Initialize validator and check the type
        validator = initialize_validator(file_contents)
        self.assertIsInstance(validator, boxvalidator.BoxValidator)

    def test_find_box_position_in_file(self):
        # Read file content
        file_contents = read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        # Find a known box position in the sample file (you should know the expected values)
        position = find_box_position(file_contents, b'\x6a\x70\x32\x68')
        self.assertNotEqual(position, -1)  # Ensure that the box is found

    def test_check_boxes_in_file(self):
        # Read file content
        file_contents = read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")
        
        header_offset_position = check_boxes(file_contents)
        self.assertIsNotNone(header_offset_position)

    def test_process_colr_box_in_file(self):
        # Read file content
        file_contents = read_file(TEST_DATA_PATH)
        if file_contents is None:
            self.fail("Test file could not be read.")

        colr_position = find_box_position(file_contents, b'\x63\x6f\x6c\x72')
        if colr_position == -1:
            self.fail("'colr' box not found in the test file.")
        
        header_offset_position = process_colr_box(file_contents, colr_position)
        self.assertIsNotNone(header_offset_position)

@patch('builtins.open', new_callable=mock_open)
def test_write_modified_file_with_changes(self, mock_file):
    # Read file content
    file_contents = read_file(TEST_DATA_PATH)
    if file_contents is None:
        self.fail("Test file could not be read.")

    # Modify the file contents slightly using bytes
    new_file_contents = file_contents + b' modified'  # Append in bytes, not string
    
    # Test writing the modified file
    write_modified_file(TEST_DATA_PATH, new_file_contents, file_contents)
    mock_file.assert_called_once_with(TEST_DATA_PATH.replace('.jp2', '_modified2.jp2'), 'wb')

if __name__ == '__main__':
    unittest.main()