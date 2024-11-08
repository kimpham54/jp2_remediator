import argparse
from jp2_remediator.box_reader_factory import BoxReaderFactory
from jp2_remediator.processor import Processor


def main():
    """Main entry point for the JP2 file processor."""
    processor = Processor(BoxReaderFactory())

    parser = argparse.ArgumentParser(description="JP2 file processor")

    # Create mutually exclusive subparsers for specifying input source
    subparsers = parser.add_subparsers(
        title="Input source", dest="input_source"
    )

    # Subparser for processing a single JP2 file
    file_parser = subparsers.add_parser(
        "file", help="Process a single JP2 file"
    )
    file_parser.add_argument(
        "file", help="Path to a single JP2 file to process"
    )
    file_parser.set_defaults(
        func=lambda args: processor.process_file(args.file)
    )

    # Subparser for processing all JP2 files in a directory
    directory_parser = subparsers.add_parser(
        "directory", help="Process all JP2 files in a directory"
    )
    directory_parser.add_argument(
        "directory", help="Path to a directory of JP2 files to process"
    )
    directory_parser.set_defaults(
        func=lambda args: processor.process_directory(args.directory)
    )

    # Subparser for processing all JP2 files in an S3 bucket
    bucket_parser = subparsers.add_parser(
        "bucket", help="Process all JP2 files in an S3 bucket"
    )
    bucket_parser.add_argument(
        "bucket", help="Name of the AWS S3 bucket to process JP2 files from"
    )
    bucket_parser.add_argument(
        "--prefix", help="Prefix of files in the AWS S3 bucket (optional)",
        default=""
    )
    bucket_parser.set_defaults(
        func=lambda args: processor.process_s3_bucket(args.bucket, args.prefix)
    )

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
