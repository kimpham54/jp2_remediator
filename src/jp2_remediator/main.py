import sys
import os


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <folder_path1> <folder_path2>")
        sys.exit(1)

    folder_path1 = sys.argv[1]
    folder_path2 = sys.argv[2]

    if not os.path.isdir(folder_path1):
        print(f"Error: {folder_path1} is not a valid directory.")
        sys.exit(1)

    if not os.path.isdir(folder_path2):
        print(f"Error: {folder_path2} is not a valid directory.")
        sys.exit(1)

    print(f"Folder 1: {folder_path1}")
    print(f"Folder 2: {folder_path2}")


if __name__ == "__main__":
    main()


def hello_world():
    print("Hello, world!")


def add_one(number):
    return number + 1
