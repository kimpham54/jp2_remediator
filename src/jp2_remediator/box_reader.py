from byteconv_jpylyzer import bytesToHex

file_path = "../../tests/test-images/481014278.jp2"

with open(file_path, "rb") as file:
    first_500_bytes = file.read(500)
    # print(first_500_bytes)
    print(bytesToHex(first_500_bytes))