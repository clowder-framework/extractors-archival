#!/usr/bin/env python

import os
import json
import logging
import requests

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from pyclowder.extractors import Extractor
import pyclowder.files
from pyclowder.utils import CheckMessage

class S3Archiver(Extractor):
    def __init__(self):
        Extractor.__init__(self)

        self.name = 'S3Archiver'

        # read default parameters values from environment variables
        default_service_endpoint= os.getenv('AWS_S3_SERVICE_ENDPOINT', 'https://s3.amazonaws.com')
        default_access_key = os.getenv('AWS_ACCESS_KEY', '')
        default_secret_key = os.getenv('AWS_SECRET_KEY', '')
        default_bucket_name = os.getenv('AWS_BUCKET_NAME', 'clowder-archive')
        default_aws_region = os.getenv('AWS_REGION', 'us-east-1')
        default_unarchived_storage_class = os.getenv('AWS_UNARCHIVED_STORAGE_CLASS', 'STANDARD')
        default_archived_storage_class = os.getenv('AWS_ARCHIVED_STORAGE_CLASS', 'INTELLIGENT_TIERING')

        # add any additional arguments to parser
        self.parser.add_argument('--service-endpoint', dest="service_endpoint",
                                 default=default_service_endpoint,
                                 help="AWS S3 Service Endpoint")
        self.parser.add_argument('--access-key', dest="access_key",
                                 default=default_access_key,
                                 help="AWS AccessKey")
        self.parser.add_argument('--secret-key', dest="secret_key",
                                 default=default_secret_key,
                                 help="AWS SecretKey")
        self.parser.add_argument('--bucket-name', dest="bucket_name",
                                 default=default_bucket_name,
                                 help="AWS S3 bucket name")
        self.parser.add_argument('--region', dest="aws_region",
                                 default=default_aws_region,
                                 help="AWS Region")
        self.parser.add_argument('--unarchived-storage-class', dest="aws_unarchived_storage_class",
                                 default=default_unarchived_storage_class,
                                 help="AWS StorageClass for unarchived files")
        self.parser.add_argument('--archived-storage-class', dest="aws_archived_storage_class",
                                 default=default_archived_storage_class,
                                 help="AWS StorageClass for archived files")

        # parse command line and setup default logging configuration
        self.setup()
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        self.service_endpoint = self.args.service_endpoint
        self.access_key = self.args.access_key
        self.secret_key = self.args.secret_key
        self.bucket_name = self.args.bucket_name
        self.aws_region = self.args.aws_region
        self.archived_storage_class = self.args.aws_archived_storage_class
        self.unarchived_storage_class = self.args.aws_unarchived_storage_class

        # Set AWS ServiceEndpoint / AccessKey / SecretKey / BucketName / Region
        if self.service_endpoint == '':
            self.logger.critical('Invalid service endpoint - please provide an endpoint using the --service-endpoint argument or by setting the AWS_S3_SERVICE_ENDPOINT environment variable. An example value might be "http://localhost:8000" to point at a MinIO server running locally.')
            exit(1)

        if self.access_key == '':
            self.logger.critical('Invalid access key - please provide an access key using the --access-key argument or by setting the AWS_ACCESS_KEY environment variable.')
            exit(1)

        if self.secret_key == '':
            self.logger.critical('Invalid secret key - please provide a secret key using the --secret-key argument or by setting the AWS_SECRET_KEY environment variable.')
            exit(1)

        if self.bucket_name == '':
            self.logger.critical('Invalid bucket name - please provide a bucket name using the --bucket-name argument or by setting the AWS_BUCKET_NAME environment variable. Note that bucket names should be DNS-compliant, if possible.')
            exit(1)

        if self.archived_storage_class == '':
            self.logger.critical('Invalid StorageClass specified for archived file - please provide a StorageClass for archived files by settings the --archived-storage-class argument or by setting the AWS_ARCHIVED_STORAGE_CLASS environment variable.')
            exit(1)

        if self.unarchived_storage_class == '':
            self.logger.critical('Invalid StorageClass specified for unarchived file - please provide a StorageClass for unarchived files by settings the --unarchived-storage-class argument or by setting the AWS_UNARCHIVED_STORAGE_CLASS environment variable.')
            exit(1)

        self.session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self.s3 = self.session.resource('s3',
                                endpoint_url=self.service_endpoint,
                                config=Config(signature_version='s3v4'),
                                region_name=self.aws_region)

        # TODO: Call wait_until_exists on startup? Create bucket on startup?
        # this would also verify credentials/permissions for access


    def get_object(self, object_key):
       try:
           # S3 Object (bucket_name and key are identifiers)
           obj = self.s3.Object(bucket_name=self.bucket_name, key=object_key)
           return obj
       except ClientError as e:
           self.logger.error('Get object failed:')
           self.logger.error(e)
           
    def change_storage_class(self, obj, storage_class):
       copy_source = {
           'Bucket': obj.bucket_name,
           'Key': obj.key
       }

       try:
           # S3 Object (bucket_name and key are identifiers)
           obj.copy(
             copy_source,
             ExtraArgs = {
               'StorageClass': storage_class,
               'MetadataDirective': 'COPY'
             }
           )
           self.logger.debug('S3 object copied successfully')
       except ClientError as e:
           # Propagate error up to the caller
           raise ClientError(e)

    def archive(self, host, secret_key, file):
        if file['status'] == 'ARCHIVED':
            self.logger.warn('File already archived: ' + file['id'] + '... Skipping.')
            return

        self.logger.info('Archive: Changing S3 StorageClass to ' + self.archived_storage_class)
        object_key = file.get('object-key')
        obj = self.get_object(object_key)
        try:
            self.change_storage_class(obj, self.archived_storage_class)

            # Call Clowder API endpoint to mark file as "archived"
            # NOTE: this won't be called if a ClientError is encountered changing the storage class
            resp = requests.post('%sapi/files/%s/archive?key=%s' % (host, file['id'], secret_key))
        except ClientError as e:
            # Catch the propagated error here
            self.logger.error(e)

    def unarchive(self, host, connector, secret_key, file):
        if file['status'] == 'PROCESSED':
            self.logger.warn('File already unarchived: ' + file['id'] + '... Skipping.')
            return

        self.logger.info('Unarchive: Changing S3 StorageClass to ' + self.unarchived_storage_class)
        object_key = file.get('object-key')
        obj = self.get_object(object_key)
        try:
            self.change_storage_class(obj, self.unarchived_storage_class)

            # Call Clowder API endpoint to mark file as "unarchived"
            # NOTE: this won't be called if a ClientError is encountered changing the storage class
            resp = requests.post('%sapi/files/%s/unarchive?key=%s' % (host, file['id'], secret_key))
        except ClientError as e:
            # Catch the propagated error here
            self.logger.error(e)

    # No need to download the file bytes, we're just working with S3
    def check_message(self, connector, host, secret_key, resource, parameters):
        return CheckMessage.bypass

    def process_message(self, connector, host, secret_key, resource, parameters):
        action = parameters.get('action')
        if action and action != 'manual-submission':
            return

        # Parse user parameters to determine whether we are to archive or unarchive
        userParams = parameters.get('parameters')
        operation = userParams.get('operation')
        if resource['type'] == 'file':
            # If archiving/unarchiving a file, fetch db record from Clowder
            url = '%sapi/files/%s/metadata?key=%s' % (host, resource['id'], secret_key)
            r = requests.get(url)
            if 'json' in r.headers.get('Content-Type'):
                self.logger.debug(r.json())
            else:
                self.logger.error('Response content is not in JSON format.. skipping: ' + str(r.headers.get('Content-Type')))
                return
            file = r.json()

            if operation and operation == 'unarchive': 
                # If unarchiving, change storage class back to STANDARD
                self.unarchive(host, connector, secret_key, file)
            elif operation and operation == 'archive':
                # If archiving, change storage class from STANDARD to target
                self.archive(host, secret_key, file)
            else:
                self.logger.error('Unrecognized operation specified... aborting: ' + str(operation))
                return
        else:
            self.logger.error('Unsupported resource type.. skipping: ' + str(resource['type']))
            return


if __name__ == "__main__":
    extractor = S3Archiver()
    extractor.start()
