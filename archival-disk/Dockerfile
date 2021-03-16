FROM python:3.7-alpine

LABEL maintainer="Mike Lambert <lambert8@illinois.edu>"

ARG VERSION="unknown"
ARG BUILDNUMBER="unknown"
ARG GITSHA1="unknown"

# environemnt variables
ENV VERSION=${VERSION} \
    BUILDNUMBER=${BUILDNUMBER} \
    GITSHA1=${GITSHA1} \
    RABBITMQ_QUEUE="ncsa.file.digest" \
    EXTRACTOR_HASHLIST="md5","sha1","sha224","sha256","sha384","sha512"

WORKDIR /extractor
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY disk-archival.py extractor_info.json ./
CMD python disk-archival.py
