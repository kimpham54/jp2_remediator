import argparse
from jp2_remediator.box_reader import BoxReader, process_directory, process_s3_bucket


def main():
    parser = argparse.ArgumentParser(description="JP2 file processor")
    parser.add_argument("--file", help="Path to a single JP2 file to process.")
    parser.add_argument(
        "--directory", help="Path to a directory of JP2 files to process."
    )
    parser.add_argument(
        "--bucket", help="Name of the AWS S3 bucket to process JP2 files from."
    )
    parser.add_argument(
        "--prefix", help="Prefix of files in the AWS S3 bucket (optional)."
    )

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


if __name__ == "__main__":
    main()
