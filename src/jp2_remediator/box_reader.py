# from byteconv_jpylyzer import *
from jpylyzer import jpylyzer
from jpylyzer import boxvalidator
from jpylyzer import byteconv

# from boxvalidator_jpylyzer import *


file_path = "../../tests/test-images/481014278.jp2"

def read_bytes(file_path):
    with open(file_path, "rb") as file:
        first_bytes = file.read(700)
        print(first_bytes)
        # print(byteconv.bytesToHex(first_bytes))

# def validate_jp2(file_path):
#     with open(file_path, "rb") as file:
#         print(validate_colourSpecificationBox(file))






def modify_byte_after_all_curvs(file_path):
    with open(file_path, "rb") as file:
        file_bytes = bytearray(file.read())  # Read the file as a bytearray to allow modifications

    curv_tag = b'curv'
    offset = 0
    modified = False

    while True:
        # Find the position of the next 'curv' tag starting from the current offset
        tag_position = file_bytes.find(curv_tag, offset)

        if tag_position == -1:
            break  # No more 'curv' tags found

        # Position of the 8th byte after the 'curv' tag
        byte_to_modify_position = tag_position + len(curv_tag) + 7

        if byte_to_modify_position < len(file_bytes):
            print(f"Original byte at position {byte_to_modify_position}: {file_bytes[byte_to_modify_position]:#04x}")

            # Check if the byte is 0x01, and change it to 0x02 if it is
            if file_bytes[byte_to_modify_position] == 0x01:
                file_bytes[byte_to_modify_position] = 0x02
                modified = True
                print(f"Byte modified to 0x02 at position {byte_to_modify_position}")
            else:
                print("Byte is not 0x01, no modification made.")
        else:
            print(f"The file is too short to modify the byte at position {byte_to_modify_position}")

        # Update the offset to search for the next 'curv' tag
        offset = tag_position + len(curv_tag)

    if modified:
        # Save the modified bytes back to the file (or a new file)
        with open(file_path + "modified", "wb") as modified_file:
            modified_file.write(file_bytes)
        print(f"File saved as modified_{file_path}")
    else:
        print("No modifications were made.")

# Example usage
# file_path = "../../tests/test-images/481014278.jp2"
# modify_all_curv_bytes(file_path)







def validate_jp2(file_path):
    # validator = BoxValidator()
    # box = jpylyzer.boxvalidator.validate(file_path)
    # print(box)
    # print("hi")
    # box = jpylyzer.checkOneFile(file_path)

    options = {
        'validationFormat': 'JP2',
        'verboseFlag': True,
        'nullxmlFlag': False,
        'packetmarkersFlag': True
    }

    # Define other required parameters
    bType = 'JP2'
    # boxContents = ['item1', 'item2', 'item3']

    # Optionally, define startOffset and components
    # startOffset = 10
    # components = ['componentA', 'componentB']

    with open(file_path, "rb") as file:
        first_bytes = file.read()
        # print(first_bytes)

    # initialize boxvalidator
    validator = boxvalidator.BoxValidator(options, bType, first_bytes)
    colr = validator._getBox(self, 0, )

    print(colr)


# Call the read_bytes function when the script is run
if __name__ == "__main__":
    # read_bytes(file_path)
    # validate_jp2(file_path)
    modify_byte_after_all_curvs(file_path)