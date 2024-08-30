import sys
from jpylyzer import jpylyzer
from jpylyzer import boxvalidator
from jpylyzer import byteconv

def read_jp2_file(file_path):
    """Reads a JP2 file and checks for jp2h and colr boxes."""
    try:
        with open(file_path, 'rb') as file:
            file_contents = file.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return

    # Options for BoxValidator (dummy options here; customize as needed)
    options = {'validationFormat': 'jp2', 'verboseFlag': True, 'nullxmlFlag': False, 'packetmarkersFlag': False}

    # Initialize the validator for the entire file
    validator = boxvalidator.BoxValidator(options, 'JP2', file_contents)
    validator.validate()

    # Example usage of boxvalidator's _isValid() method
    is_valid = validator._isValid()
    print("Is file valid?", is_valid)

    # Check for JP2 Header Box (jp2h)
    jp2h_hex = b'\x6a\x70\x32\x68'  # Hexadecimal sequence for 'jp2h'
    jp2h_position = file_contents.find(jp2h_hex)

    if jp2h_position != -1:
        print(f"'jp2h' found at byte position: {jp2h_position}")
    else:
        print("'jp2h' not found in the file.")

    # Check for the presence of 'colr' box
    colr_hex = b'\x63\x6f\x6c\x72'  # Hexadecimal sequence for 'colr'
    colr_position = file_contents.find(colr_hex)

    if colr_position != -1:
        print(f"'colr' found at byte position: {colr_position}")

        # Find the 'meth' value, which is the byte immediately after 'colr'
        meth_byte_position = colr_position + 4  # 'meth' is the byte after the 4-byte 'colr' identifier
        meth_value = file_contents[meth_byte_position]

        print(f"'meth' value: {meth_value} at byte position: {meth_byte_position}")

        # Determine header_offset_position based on the value of 'meth'
        if meth_value == 1:
            header_offset_position = meth_byte_position + 7
            print(f"'meth' is 1, setting header_offset_position to: {header_offset_position}")
        elif meth_value == 2:
            header_offset_position = meth_byte_position + 3
            print(f"'meth' is 2, setting header_offset_position to: {header_offset_position}")
        else:
            print(f"'meth' value {meth_value} is not recognized (must be 1 or 2).")
            header_offset_position = None  # Set to None if meth is not recognized
    else:
        print("'colr' not found in the file.")
        header_offset_position = None

    # Convert the original file contents to a mutable bytearray
    new_file_contents = bytearray(file_contents)

    # Function to process 'TRC' tags (rTRC, gTRC, bTRC)
    def process_trc_tag(trc_hex, trc_name, new_contents):
        trc_position = new_contents.find(trc_hex)
        if trc_position != -1:
            print(f"'{trc_name}' found at byte position: {trc_position}")

            # Extract the 12-byte tag entry starting from the TRC position
            trc_tag_entry = new_contents[trc_position:trc_position + 12]
            if len(trc_tag_entry) == 12:
                trc_tag_signature = trc_tag_entry[0:4]
                trc_tag_offset = int.from_bytes(trc_tag_entry[4:8], byteorder='big')
                trc_tag_size = int.from_bytes(trc_tag_entry[8:12], byteorder='big')

                print(f"'{trc_name}' Tag Signature: {trc_tag_signature}")
                print(f"'{trc_name}' Tag Offset: {trc_tag_offset}")
                print(f"'{trc_name}' Tag Size: {trc_tag_size}")

                # Calculate the curv_trc_position
                if header_offset_position is not None:
                    curv_trc_position = trc_tag_offset + header_offset_position
                    print(f"'curv_{trc_name}_position' is at byte: {curv_trc_position}")

                    # Read the 'curv' profile data from 'curv_trc_position'
                    curv_profile = new_contents[curv_trc_position:curv_trc_position + 12]
                    if len(curv_profile) >= 12:
                        curv_signature = curv_profile[0:4].decode('utf-8')
                        curv_reserved = int.from_bytes(curv_profile[4:8], byteorder='big')
                        curv_trc_gamma_n = int.from_bytes(curv_profile[8:12], byteorder='big')

                        print(f"'curv' Profile Signature for {trc_name}: {curv_signature}")
                        print(f"'curv' Reserved Value: {curv_reserved}")
                        print(f"'curv_{trc_name}_gamma_n' Value: {curv_trc_gamma_n}")

                        # Calculate the curv_trc_field_length
                        curv_trc_field_length = curv_trc_gamma_n * 2 + 12
                        print(f"'curv_{trc_name}_field_length': {curv_trc_field_length}")

                        # Check if trc_tag_size and curv_trc_field_length are equal
                        if trc_tag_size != curv_trc_field_length:
                            print(f"'{trc_name}' Tag Size ({trc_tag_size}) does not match 'curv_{trc_name}_field_length' ({curv_trc_field_length}).")
                            print(f"Modifying the '{trc_name}' Tag Size...")

                            # Modify the JP2 file with the updated trc_tag_size
                            new_trc_size_bytes = curv_trc_field_length.to_bytes(4, byteorder='big')
                            new_contents[trc_position + 8: trc_position + 12] = new_trc_size_bytes

                        else:
                            print(f"'{trc_name}' Tag Size matches 'curv_{trc_name}_field_length'. No modification needed.")
                    else:
                        print(f"Could not read the full 'curv' profile data for {trc_name}.")
                else:
                    print(f"Cannot calculate 'curv_{trc_name}_position' due to an unrecognized 'meth' value.")
            else:
                print(f"Could not extract the full 12-byte '{trc_name}' tag entry.")
        else:
            print(f"'{trc_name}' not found in the file.")
        return new_contents

    # Process all TRC tags and update contents as necessary
    new_file_contents = process_trc_tag(b'\x72\x54\x52\x43', 'rTRC', new_file_contents)  # Process 'rTRC'
    new_file_contents = process_trc_tag(b'\x67\x54\x52\x43', 'gTRC', new_file_contents)  # Process 'gTRC'
    new_file_contents = process_trc_tag(b'\x62\x54\x52\x43', 'bTRC', new_file_contents)  # Process 'bTRC'

    # Check if any changes were made and write to a new file if needed
    if new_file_contents != file_contents:
        new_file_path = file_path.replace(".jp2", "_modified.jp2")
        with open(new_file_path, 'wb') as new_file:
            new_file.write(new_file_contents)
        print(f"New JP2 file created with modifications: {new_file_path}")
    else:
        print("No modifications were needed. No new file was created.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python box_reader.py <JP2 file path>")
        sys.exit(1)

    jp2_file_path = sys.argv[1]
    read_jp2_file(jp2_file_path)