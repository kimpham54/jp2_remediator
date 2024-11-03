import datetime
import os
import boto3


class Processor:
    """Class to process JP2 files."""

    def __init__(self, factory):
        """Initialize the Processor with a BoxReader factory."""
        self.box_reader_factory = factory

    def process_file(self, file_path):
        """Process a single JP2 file."""
        print(f"Processing file: {file_path}")
        reader = self.box_reader_factory.get_reader(file_path)
        reader.read_jp2_file()

    def process_directory(self, directory_path):
        """Process all JP2 files in a given directory."""
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(".jp2"):
                    file_path = os.path.join(root, file)
                    print(f"Processing file: {file_path}")
                    reader = self.box_reader_factory.get_reader(file_path)
                    reader.read_jp2_file()

    def process_s3_bucket(self, bucket_name, prefix=""):
        """Process all JP2 files in a given S3 bucket."""
        s3 = boto3.client("s3")
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if "Contents" in response:
            for obj in response["Contents"]:
                if obj["Key"].lower().endswith(".jp2"):
                    file_path = obj["Key"]
                    print(f"""Processing file: {file_path} from bucket {
                        bucket_name
                        }""")
                    download_path = f"/tmp/{os.path.basename(file_path)}"
                    s3.download_file(bucket_name, file_path, download_path)
                    reader = self.box_reader_factory.get_reader(download_path)
                    reader.read_jp2_file()
                    # Optionally, upload modified file back to S3
                    timestamp = datetime.datetime.now().strftime(
                        "%Y%m%d"
                    )  # use "%Y%m%d_%H%M%S" for more precision
                    s3.upload_file(
                        download_path.replace(
                            ".jp2", f"_modified_{timestamp}.jp2"
                            ),
                        bucket_name,
                        file_path.replace(".jp2", f"_modified_{timestamp}.jp2")
                    )
