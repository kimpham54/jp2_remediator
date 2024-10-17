# jp2_remediator

README for the module to validate jp2images

https://pypi.org/project/jp2_remediator/

## Installation

```bash
pip install jp2_remediator
python3 -m pip install jp2_remediator

pip install jp2_remediator==0.0.2
```

## Usage

## Process one file
`python3 box_reader.py --file tests/test-images/7514499.jp2`

`python3 box_reader.py --file tests/test-images/481014278.jp2`

## Process directory
`python3 box_reader.py --directory tests/test-images/`

## Process Amazon S3 bucket
`python3 box_reader.py --bucket your-bucket-name --prefix optional-prefix`

## Process all .jp2 files in the bucket:
`python3 box_reader.py --bucket remediation-folder`

## Process only files with a specific prefix (folder):
`python3 box_reader.py --bucket remediation-folder --prefix testbatch_20240923`

`python3 box_reader.py --help`

## Run Tests
`python3 test_aws_connection.py`

### Run from src folder
`python3 -m unittest jp2_remediator.tests.test_box_reader`

## Docker environment

Build Docker image
```bash
./bin/docker-build.sh
```

Start Docker container
```bash
./bin/docker-run.sh
```
