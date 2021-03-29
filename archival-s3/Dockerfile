FROM python:3.9

LABEL maintainer="Mike Lambert <lambert8@illinois.edu>"

ARG VERSION="unknown"
ARG BUILDNUMBER="unknown"
ARG GITSHA1="unknown"

# environemnt variables
ENV VERSION=${VERSION} \
    BUILDNUMBER=${BUILDNUMBER} \
    GITSHA1=${GITSHA1} \
    RABBITMQ_QUEUE="ncsa.archival.s3" \
    AWS_REGION="us-east-1" \
    AWS_SERVICE_ENDPOINT="https://s3.amazonaws.com" \
    AWS_ARCHIVED_STORAGE_CLASS="INTELLIGENT_TIERING" \
    AWS_UNARCHIVED_STORAGE_CLASS="STANDARD" \
    AWS_ACCESS_KEY="" \
    AWS_SECRET_KEY="" \
    AWS_BUCKET_NAME=""
    

WORKDIR /extractor
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY s3-archival.py extractor_info.json ./
CMD python s3-archival.py
