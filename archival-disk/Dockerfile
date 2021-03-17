FROM python:3.9

LABEL maintainer="Mike Lambert <lambert8@illinois.edu>"

ARG VERSION="unknown"
ARG BUILDNUMBER="unknown"
ARG GITSHA1="unknown"

# environemnt variables
ENV VERSION=${VERSION} \
    BUILDNUMBER=${BUILDNUMBER} \
    GITSHA1=${GITSHA1} \
    RABBITMQ_QUEUE="ncsa.archival.disk" \
    ARCHIVE_SOURCE_DIRECTORY="/home/clowder/clowder/data/uploads/" \
    ARCHIVE_TARGET_DIRECTORY="/home/clowder/clowder/data/archive/" \
    MOUNTED_PATHS='{}'
    

WORKDIR /extractor
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY disk-archival.py extractor_info.json ./
CMD python disk-archival.py
