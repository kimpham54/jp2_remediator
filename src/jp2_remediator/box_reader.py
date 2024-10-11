import sys
import os
import argparse
import boto3
import datetime
from jpylyzer import jpylyzer
from jpylyzer import boxvalidator
from jpylyzer import byteconv

class BoxReader:
    def __init__(self, file_path):
        """Initializes BoxReader with a file path."""
        self.file_path = file_path
        self.file_contents = self.read_file(file_path)
        self.validator = None

    def read_file(self, file_path):
        """Reads the file content from the given path."""
        try:
            with open(file_path, 'rb') as file:
                return file.read()
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def initialize_validator(self):
        """Initializes the jpylyzer BoxValidator for JP2 file validation."""
        options = {'validationFormat': 'jp2', 'verboseFlag': True, 'nullxmlFlag': False, 'packetmarkersFlag': False}
        self.validator = boxvalidator.BoxValidator(options, 'JP2', self.file_contents)
        self.validator.validate()
        return self.validator

    def find_box_position(self, box_hex):
        """Finds the position of the specified box in the file."""
        return self.file_contents.find(box_hex)

    def check_boxes(self):
        """Checks for presence of 'jp2h' and 'colr' boxes in the file contents."""
        jp2h_position = self.find_box_position(b'\x6a\x70\x32\x68')  # search hex for 'jp2h'
        if jp2h_position != -1:
            print(f"'jp2h' found at byte position: {jp2h_position}")
        else:
            print("'jp2h' not found in the file.")

        colr_position = self.find_box_position(b'\x63\x6f\x6c\x72')  # search hex for 'colr'
        if colr_position != -1:
            print(f"'colr' found at byte position: {colr_position}")
        else:
            print("'colr' not found in the file.")

        header_offset_position = self.process_colr_box(colr_position)

        return header_offset_position

    def process_colr_box(self, colr_position):
        """Processes the 'colr' box to determine header offset position."""
        if colr_position != -1:
            print(f"'colr' found at byte position: {colr_position}")
            meth_byte_position = colr_position + 4  # ISO/IEC 15444-1:2019(E) Figure I.10 colr specification box, byte position of METH value after 'colr' 
            meth_value = self.file_contents[meth_byte_position]
            print(f"'meth' value: {meth_value} at byte position: {meth_byte_position}")

            if meth_value == 1:
                header_offset_position = meth_byte_position + 7  # ISO/IEC 15444-1:2019(E) Table I.11 colr specification box, if meth is 1 then color profile starts at byte position 7 after 'colr' 
                print(f"'meth' is 1, setting header_offset_position to: {header_offset_position}")
            elif meth_value == 2:
                header_offset_position = meth_byte_position + 3  # ISO/IEC 15444-1:2019(E) Table I.11 colr specification box, if meth is 2 then color profile (ICC profile) starts at byte position 3 after 'colr' 
                print(f"'meth' is 2, setting header_offset_position to: {header_offset_position} (start of ICC profile)")
            else:
                print(f"'meth' value {meth_value} is not recognized (must be 1 or 2).")
                header_offset_position = None
        else:
            print("'colr' not found in the file.")
            header_offset_position = None

        return header_offset_position

    def process_trc_tag(self, trc_hex, trc_name, new_contents, header_offset_position):
        """Processes the TRC tag and modifies contents if necessary."""
        trc_position = new_contents.find(trc_hex)
        if trc_position == -1:
            print(f"'{trc_name}' not found in the file.")
            return new_contents

        print(f"'{trc_name}' found at byte position: {trc_position}")
        trc_tag_entry = new_contents[trc_position:trc_position + 12]  # 12-byte tag entry length

        if len(trc_tag_entry) != 12:
            print(f"Could not extract the full 12-byte '{trc_name}' tag entry.")
            return new_contents

        trc_tag_signature = trc_tag_entry[0:4]  # ICC.1:2022 Table 24 tag signature, e.g. 'rTRC'
        trc_tag_offset = int.from_bytes(trc_tag_entry[4:8], byteorder='big')  # ICC.1:2022 Table 24 tag offset
        trc_tag_size = int.from_bytes(trc_tag_entry[8:12], byteorder='big')  # ICC.1:2022 Table 24 tag size
        print(f"'{trc_name}' Tag Signature: {trc_tag_signature}")
        print(f"'{trc_name}' Tag Offset: {trc_tag_offset}")
        print(f"'{trc_name}' Tag Size: {trc_tag_size}")

        if header_offset_position is None:
            print(f"Cannot calculate 'curv_{trc_name}_position' due to an unrecognized 'meth' value.")
            return new_contents

        curv_trc_position = trc_tag_offset + header_offset_position  # start of curv profile data
        curv_profile = new_contents[curv_trc_position:curv_trc_position + 12]  # 12-byte curv profile data length

        if len(curv_profile) < 12:
            print(f"Could not read the full 'curv' profile data for {trc_name}.")
            return new_contents

        curv_signature = curv_profile[0:4].decode('utf-8')  # ICC.1:2022 Table 35 tag signature
        curv_reserved = int.from_bytes(curv_profile[4:8], byteorder='big') # ICC.1:2022 Table 35 reserved 0's
        curv_trc_gamma_n = int.from_bytes(curv_profile[8:12], byteorder='big') # # ICC.1:2022 Table 35 n value

        print(f"'curv' Profile Signature for {trc_name}: {curv_signature}")
        print(f"'curv' Reserved Value: {curv_reserved}")
        print(f"'curv_{trc_name}_gamma_n' Value: {curv_trc_gamma_n}")

        curv_trc_field_length = curv_trc_gamma_n * 2 + 12  # ICC.1:2022 Table 35 2n field length
        print(f"'curv_{trc_name}_field_length': {curv_trc_field_length}")

        # Check if curv_trc_gamma_n is not 1 and ask for confirmation to proceed, loops through all TRC tags
        if curv_trc_gamma_n != 1:
            print(f"Warning: 'curv_{trc_name}_gamma_n' value is {curv_trc_gamma_n}, expected 1.")
            proceed = input(f"Do you want to proceed with fixing the file {self.file_path}? (y/n): ").lower()
            if proceed != 'y':
                print(f"Skipping fixing for {self.file_path}")
                return new_contents

        if trc_tag_size != curv_trc_field_length:
            print(f"'{trc_name}' Tag Size ({trc_tag_size}) does not match 'curv_{trc_name}_field_length' ({curv_trc_field_length}). Modifying the size...")
            new_trc_size_bytes = curv_trc_field_length.to_bytes(4, byteorder='big')
            new_contents[trc_position + 8: trc_position + 12] = new_trc_size_bytes

        return new_contents

    def process_all_trc_tags(self, header_offset_position):
        """Function to process 'TRC' tags (rTRC, gTRC, bTRC)."""
        new_file_contents = bytearray(self.file_contents)
        trc_tags = {
            b'\x72\x54\x52\x43': 'rTRC', # search hex for 'rTRC'
            b'\x67\x54\x52\x43': 'gTRC', # search hex for 'gTRC'
            b'\x62\x54\x52\x43': 'bTRC' # search hex for 'bTRC'
        }

        for trc_hex, trc_name in trc_tags.items():
            new_file_contents = self.process_trc_tag(trc_hex, trc_name, new_file_contents, header_offset_position)

        return new_file_contents

    def write_modified_file(self, new_file_contents):
        """Writes the modified file contents to a new file if changes were made."""
        if new_file_contents != self.file_contents:
            timestamp = datetime.datetime.now().strftime("%Y%m%d") # use "%Y%m%d_%H%M%S" for more precision
            new_file_path = self.file_path.replace(".jp2", f"_modified_{timestamp}.jp2")
            with open(new_file_path, 'wb') as new_file:
                new_file.write(new_file_contents)
            print(f"New JP2 file created with modifications: {new_file_path}")
        else:
            print("No modifications were needed. No new file was created.")

    def read_jp2_file(self):
        """Main function to read, validate, and modify JP2 files."""
        if not self.file_contents:
            return

        self.initialize_validator()
        is_valid = self.validator._isValid()
        print("Is file valid?", is_valid)

        header_offset_position = self.check_boxes()
        new_file_contents = self.process_all_trc_tags(header_offset_position)

        self.write_modified_file(new_file_contents)

def process_directory(directory_path):
    """Process all JP2 files in a given directory."""
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.jp2'):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                reader = BoxReader(file_path)
                reader.read_jp2_file()

def process_s3_bucket(bucket_name, prefix=''):
    """Process all JP2 files in a given S3 bucket."""
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    if 'Contents' in response:
        for obj in response['Contents']:
            if obj['Key'].lower().endswith('.jp2'):
                file_path = obj['Key']
                print(f"Processing file: {file_path} from bucket {bucket_name}")
                download_path = f"/tmp/{os.path.basename(file_path)}"
                s3.download_file(bucket_name, file_path, download_path)
                reader = BoxReader(download_path)
                reader.read_jp2_file()
                # Optionally, upload modified file back to S3
                timestamp = datetime.datetime.now().strftime("%Y%m%d") # use "%Y%m%d_%H%M%S" for more precision
                s3.upload_file(download_path.replace(".jp2", f"_modified_{timestamp}.jp2"), bucket_name, file_path.replace(".jp2", f"_modified_{timestamp}.jp2"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JP2 file processor")
    parser.add_argument("--file", help="Path to a single JP2 file to process.")
    parser.add_argument("--directory", help="Path to a directory of JP2 files to process.")
    parser.add_argument("--bucket", help="Name of the AWS S3 bucket to process JP2 files from.")
    parser.add_argument("--prefix", help="Prefix of files in the AWS S3 bucket (optional).")

    args = parser.parse_args()

    if args.file:
        reader = BoxReader(args.file)
        reader.read_jp2_file()
    elif args.directory:
        process_directory(args.directory)
    elif args.bucket:
        process_s3_bucket(args.bucket, args.prefix)
    else:
        print("Please specify either --file, --directory, or --bucket.")