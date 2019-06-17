#!/usr/bin/env python

import os
import json
import logging
import boto3
import requests

from botocore.exceptions import ClientError

from pyclowder.extractors import Extractor
import pyclowder.files

class S3Archiver(Extractor):
    def __init__(self):
        Extractor.__init__(self)

        self.name = 'S3Archiver'

        # read default parameters values from environment variables
        default_access_key = os.getenv('AWS_ACCESS_KEY', '')
        default_secret_key = os.getenv('AWS_SECRET_KEY', '')
        default_bucket_name = os.getenv('AWS_BUCKET_NAME', 's3-clowder-test')
        default_aws_region = os.getenv('AWS_REGION', 'us-east-1')

        # add any additional arguments to parser
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

        # parse command line and setup default logging configuration
        self.setup()
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        self.access_key = self.args.access_key
        self.secret_key = self.args.secret_key
        self.bucket_name = self.args.bucket_name
        self.aws_region = self.args.aws_region

        # Set AWS AccessKey / SecretKey / BucketName / Region
        if self.access_key == '':
            self.logger.critical('Invalid access key - please provide an access key using the --access-key argument or by setting the AWS_ACCESS_KEY environment variable.')
            exit(1)

        if self.secret_key == '':
            self.logger.critical('Invalid secret key - please provide a secret key using the --secret-key argument or by setting the AWS_SECRET_KEY environment variable.')
            exit(1)

        if self.bucket_name == '':
            self.logger.critical('Invalid bucket name - please provide a bucket name using the --bucket-name argument or by setting the AWS_BUCKET_NAME environment variable.')
            exit(1)


        self.session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self.s3 = self.session.resource('s3', self.aws_region)

        # TODO: Call wait_until_exists on startup? Create bucket on startup?
        # this would also verify credentials/permissions for access


    def get_object(self, object_key):
       try:
           # S3 Object (bucket_name and key are identifiers)
           obj = self.s3.Object(bucket_name=self.bucket_name, key=object_key)
           self.logger.info('Bucket Name: ' + str(obj.bucket_name))
           self.logger.info('Object Key: ' + str(obj.key))
           return obj
       except ClientError as e:
           self.logger.error(e)
           
    def test_upload(self, obj):
       try:
           response = obj.put(Body=b'example bytes')
           return response
       except ClientError as e:
           self.logger.error(e)

    def change_storage_class(self, obj, storage_class='STANDARD'):
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
           print('Copied successfully!')
       except ClientError as e:
           self.logger.error(e)


    def process_message(self, connector, host, secret_key, resource, parameters):
        action = parameters.get('action')
        if action and action != 'manual-submission':
            return

        # Parse user parameters to determine whether we are to archive or unarchive
        userParams = parameters.get('parameters')
        operation = userParams.get('operation')
        if operation and operation == 'unarchive': 
            # If unarchiving, change storage class back to STANDARD
            # TODO: Needs testing with other storage classes
            self.logger.info('Unarchive: Changing S3 Storage Class back from RR to Default')
            url = '%sapi/files/%s/metadata?key=%s' % (host, resource['id'], secret_key)
            self.logger.debug("sending request for file record: "+url)
            r = requests.get(url)
            object_key = r.json().get('object-key')
            obj = self.get_object(object_key)
            self.change_storage_class(obj, 'STANDARD')

            # Call Clowder API endpoint to mark file as "unarchived"
#            url = '%sapi/files/%s/archive?key=%s' % (host, resource['id'], secret_key)
#            self.logger.debug("sending request for file record: "+url)
#            r = requests.post('%sapi/files/%s/unarchive?key=%s' % (host, resource['id'], secret_key))
            return
        elif operation and operation == 'archive':
            if resource['type'] == 'file':
                # If archiving a file, fetch db record from Clowder
                url = '%sapi/files/%s/metadata?key=%s' % (host, resource['id'], secret_key)

                self.logger.debug("sending request for file record: "+url)
                r = requests.get(url)

                # TODO: Check if object is already exists in dest storage
                # TODO: If not exists, upload a copy with IT storage class
                # If exists, change storage class on existing object
                if 'json' in r.headers.get('Content-Type'):
                    self.logger.debug(r.json())
                    object_key = r.json().get('object-key')
                    self.logger.info('Archive: Changing S3 Storage Class from Default to RR')
                    obj = self.get_object(object_key)
                    self.change_storage_class(obj, 'REDUCED_REDUNDANCY')

                    # TODO: if source != dest, delete original file in favor of archived copy?
                    # Call Clowder API endpoint to mark file as "archived"
#                    url = '%sapi/files/%s/archive?key=%s' % (host, resource['id'], secret_key)
#                    self.logger.debug("sending request for file record: "+url)
#                    r = requests.post('%sapi/files/%s/archive?key=%s' % (host, resource['id'], secret_key))
                else:
                    self.logger.error('Response content is not in JSON format.. skipping: ' + str(r.headers.get('Content-Type')))
                    return
            else:
                self.logger.error('Unsupported resource type.. skipping: ' + str(resource['type']))
                return
        else:
            self.logger.error('Invalid operation specified.. aborting: ' + str(operation))
            return

    def list_contains_key(self, list, keyFieldName, keyValue):
        """
        returns true iff the given key already exists in the list
        :return:
        """
        for item in list:
            if item[keyFieldName] == keyValue:
                return True

        return False

if __name__ == "__main__":
    extractor = S3Archiver()
    extractor.start()
