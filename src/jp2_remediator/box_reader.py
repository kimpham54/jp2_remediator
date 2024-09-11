import sys
import os
import argparse
import boto3
from jpylyzer import jpylyzer
from jpylyzer import boxvalidator
from jpylyzer import byteconv

def read_file(file_path):
    """Reads the file content from the given path."""
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def initialize_validator(file_contents):
    """Initializes the jpylyzer BoxValidator for JP2 file validation."""
    options = {'validationFormat': 'jp2', 'verboseFlag': True, 'nullxmlFlag': False, 'packetmarkersFlag': False}
    validator = boxvalidator.BoxValidator(options, 'JP2', file_contents)
    validator.validate()
    return validator

def find_box_position(file_contents, box_hex):
    """Finds the position of the specified box in the file."""
    return file_contents.find(box_hex)

def check_boxes(file_contents):
    """Checks for 'jp2h' and 'colr' boxes in the file contents."""
    jp2h_position = find_box_position(file_contents, b'\x6a\x70\x32\x68')
    if jp2h_position != -1:
        print(f"'jp2h' found at byte position: {jp2h_position}")
    else:
        print("'jp2h' not found in the file.")
    
    colr_position = find_box_position(file_contents, b'\x63\x6f\x6c\x72')
    if colr_position != -1:
        print(f"'colr' found at byte position: {colr_position}")
    else:
        print("'colr' not found in the file.")

    header_offset_position = process_colr_box(file_contents, colr_position)
    
    return header_offset_position

def process_colr_box(file_contents, colr_position):
    """Processes the 'colr' box to determine header offset position."""
    if colr_position != -1:
        print(f"'colr' found at byte position: {colr_position}")
        meth_byte_position = colr_position + 4
        meth_value = file_contents[meth_byte_position]
        print(f"'meth' value: {meth_value} at byte position: {meth_byte_position}")
        
        if meth_value == 1:
            header_offset_position = meth_byte_position + 7
            print(f"'meth' is 1, setting header_offset_position to: {header_offset_position}")
        elif meth_value == 2:
            header_offset_position = meth_byte_position + 3
            print(f"'meth' is 2, setting header_offset_position to: {header_offset_position}")
        else:
            print(f"'meth' value {meth_value} is not recognized (must be 1 or 2).")
            header_offset_position = None
    else:
        print("'colr' not found in the file.")
        header_offset_position = None

    return header_offset_position

def process_trc_tag(trc_hex, trc_name, new_contents, header_offset_position):
    """Processes the TRC tag and modifies contents if necessary."""
    trc_position = new_contents.find(trc_hex)
    if trc_position == -1:
        print(f"'{trc_name}' not found in the file.")
        return new_contents

    print(f"'{trc_name}' found at byte position: {trc_position}")
    trc_tag_entry = new_contents[trc_position:trc_position + 12]

    if len(trc_tag_entry) != 12:
        print(f"Could not extract the full 12-byte '{trc_name}' tag entry.")
        return new_contents

    trc_tag_signature = trc_tag_entry[0:4]
    trc_tag_offset = int.from_bytes(trc_tag_entry[4:8], byteorder='big')
    trc_tag_size = int.from_bytes(trc_tag_entry[8:12], byteorder='big')
    print(f"'{trc_name}' Tag Signature: {trc_tag_signature}")
    print(f"'{trc_name}' Tag Offset: {trc_tag_offset}")
    print(f"'{trc_name}' Tag Size: {trc_tag_size}")

    if header_offset_position is None:
        print(f"Cannot calculate 'curv_{trc_name}_position' due to an unrecognized 'meth' value.")
        return new_contents

    curv_trc_position = trc_tag_offset + header_offset_position
    curv_profile = new_contents[curv_trc_position:curv_trc_position + 12]

    if len(curv_profile) < 12:
        print(f"Could not read the full 'curv' profile data for {trc_name}.")
        return new_contents

    curv_signature = curv_profile[0:4].decode('utf-8')
    curv_reserved = int.from_bytes(curv_profile[4:8], byteorder='big')
    curv_trc_gamma_n = int.from_bytes(curv_profile[8:12], byteorder='big')

    print(f"'curv' Profile Signature for {trc_name}: {curv_signature}")
    print(f"'curv' Reserved Value: {curv_reserved}")
    print(f"'curv_{trc_name}_gamma_n' Value: {curv_trc_gamma_n}")

    curv_trc_field_length = curv_trc_gamma_n * 2 + 12
    print(f"'curv_{trc_name}_field_length': {curv_trc_field_length}")

    if trc_tag_size != curv_trc_field_length:
        print(f"'{trc_name}' Tag Size ({trc_tag_size}) does not match 'curv_{trc_name}_field_length' ({curv_trc_field_length}). Modifying the size...")
        new_trc_size_bytes = curv_trc_field_length.to_bytes(4, byteorder='big')
        new_contents[trc_position + 8: trc_position + 12] = new_trc_size_bytes

    return new_contents

def process_all_trc_tags(file_contents, header_offset_position):
    """Function to process 'TRC' tags (rTRC, gTRC, bTRC)."""
    new_file_contents = bytearray(file_contents)
    trc_tags = {
        b'\x72\x54\x52\x43': 'rTRC',
        b'\x67\x54\x52\x43': 'gTRC',
        b'\x62\x54\x52\x43': 'bTRC'
    }

    for trc_hex, trc_name in trc_tags.items():
        new_file_contents = process_trc_tag(trc_hex, trc_name, new_file_contents, header_offset_position)

    return new_file_contents

def write_modified_file(file_path, new_file_contents, original_file_contents):
    """Writes the modified file contents to a new file if changes were made."""
    if new_file_contents != original_file_contents:
        new_file_path = file_path.replace(".jp2", "_modified2.jp2")
        with open(new_file_path, 'wb') as new_file:
            new_file.write(new_file_contents)
        print(f"New JP2 file created with modifications: {new_file_path}")
    else:
        print("No modifications were needed. No new file was created.")

def read_jp2_file(file_path):
    """Main function to read, validate, and modify JP2 files."""
    file_contents = read_file(file_path)
    if not file_contents:
        return

    validator = initialize_validator(file_contents)
    is_valid = validator._isValid()
    print("Is file valid?", is_valid)

    header_offset_position = check_boxes(file_contents)
    new_file_contents = process_all_trc_tags(file_contents, header_offset_position)

    write_modified_file(file_path, new_file_contents, file_contents)

def process_directory(directory_path):
    """Process all JP2 files in a given directory."""
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.jp2'):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                read_jp2_file(file_path)

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
                read_jp2_file(download_path)
                # Optionally, upload modified file back to S3
                s3.upload_file(download_path.replace(".jp2", "_modified2.jp2"), bucket_name, file_path.replace(".jp2", "_modified2.jp2"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JP2 file processor")
    parser.add_argument("--file", help="Path to a single JP2 file to process.")
    parser.add_argument("--directory", help="Path to a directory of JP2 files to process.")
    parser.add_argument("--bucket", help="Name of the AWS S3 bucket to process JP2 files from.")
    parser.add_argument("--prefix", help="Prefix of files in the AWS S3 bucket (optional).")

    args = parser.parse_args()

    if args.file:
        read_jp2_file(args.file)
    elif args.directory:
        process_directory(args.directory)
    elif args.bucket:
        process_s3_bucket(args.bucket, args.prefix)
    else:
        print("Please specify either --file, --directory, or --bucket.")