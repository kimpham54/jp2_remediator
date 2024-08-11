#!/bin/bash

## bash entrypoint
docker run --rm --mount type=bind,source=${PWD},target=/app -it --entrypoint /bin/bash artifactory.huit.harvard.edu/lts/jp2_remediator $@

## Executable Docker image
#docker run --rm --mount type=bind,source=${PWD},target=/app -it artifactory.huit.harvard.edu/lts/jp2_remediator $@
