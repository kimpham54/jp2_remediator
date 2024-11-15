# jp2_remediator

<a href="https://github.com/harvard-lts/jp2_remediator/actions/workflows/test.yml"><img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/kimpham54/67d4eba1556653d896d2d36fcb3e5c7c/raw/covbadge.json"></a>

<a href="https://github.com/harvard-lts/jp2_remediator/actions/workflows/test.yml"><img src="https://github.com/harvard-lts/jp2_remediator/actions/workflows/test.yml/badge.svg"></a>

README for the module to validate jp2images

https://pypi.org/project/jp2_remediator/

## Installation

```bash
pip install jp2_remediator
python3 -m pip install jp2_remediator

pip install jp2_remediator==0.0.2
```

## Usage

```bash
python3 src/jp2_remediator/main.py  -h

usage: main.py [-h] {file,directory,bucket} ...

JP2 file processor

options:
  -h, --help            show this help message and exit

Input source:
  {file,directory,bucket}
    file                Process a single JP2 file
    directory           Process all JP2 files in a directory
    bucket              Process all JP2 files in an S3 bucket
```

### Process one file
```bash
python3 src/jp2_remediator/main.py file tests/test-images/7514499.jp2

python3 src/jp2_remediator/main.py file tests/test-images/481014278.jp2
```

### Process directory
```bash
python3 src/jp2_remediator/main.py directory tests/test-images/
```

### Process all .jp2 files in an S3 bucket:
```bash
python3 src/jp2_remediator/main.py bucket remediation-folder
```

### Process only files with a specific prefix (folder):
```bash
python3 src/jp2_remediator/main.py bucket remediation-folder --prefix testbatch_20240923`
```

## Run tests

### Run integration tests
```bash
pytest src/jp2_remediator/tests/integration/
```

### Run unit tests
```bash
pytest src/jp2_remediator/tests/unit/
```

## Docker environment

Build Docker image
```bash
./bin/docker-build.sh
```

Start Docker container
```bash
./bin/docker-run.sh
```

## Development environment
```bash
python3 -m venv myenv
source myenv/bin/activate
export PYTHONPATH="${PYTHONPATH}:src"
pip install -r requirements.txt

python src/jp2_remediator/main.py -h
```
