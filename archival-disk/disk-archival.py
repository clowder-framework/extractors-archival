#!/usr/bin/env python

import os
import shutil
import json
import logging
import requests

from pyclowder.extractors import Extractor
import pyclowder.files

class DiskArchiver(Extractor):
    def __init__(self):
        Extractor.__init__(self)

        self.name = 'DiskArchiver'

        # read default parameters values from environment variables
        home_dir = os.getenv('HOME', '/home/clowder')
        default_archive_source = os.getenv('ARCHIVE_SOURCE_DIRECTORY', home_dir + '/clowder/data/uploads/')
        default_archive_target = os.getenv('ARCHIVE_TARGET_DIRECTORY', home_dir + '/clowder/data/archive/')

        # add any additional arguments to parser
        self.parser.add_argument('--archive-source', dest="archive_source",
                                 default=default_archive_source,
                                 help="Directory where Clowder stores active, unarchived files")
        self.parser.add_argument('--archive-target', dest="archive_target",
                                 default=default_archive_target,
                                 help="Directory where extractor should save archived resources")

        # parse command line and setup default logging configuration
        self.setup()
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        self.archive_source = self.args.archive_source
        self.archive_target = self.args.archive_target

        # Ensure archive_source is valid before proceeding
        if self.archive_source == '':
            self.logger.critical('Invalid archive source directory - please provide a path to Clowder\'s disk storage directory using the --archive_source argument or by setting the ARCHIVE_SOURCE_DIRECTORY environment variable.')
            exit(1)
        elif not os.path.isabs(self.archive_source):
            self.logger.critical('Invalid archive source directory - archive target must be an absolute path.')
            exit(2)

        # Ensure archive_target is valid before proceeding
        if self.archive_target == '':
            self.logger.critical('Invalid archive target directory - please provide an archive output directory using the --archive_target argument or by setting the ARCHIVE_TARGET_DIRECTORY environment variable.')
            exit(1)
        elif not os.path.isabs(self.archive_target):
            self.logger.critical('Invalid archive target directory - archive target must be an absolute path.')
            exit(2)
        self.logger.info('ARCHIVE_SOURCE_DIRECTORY: ' + self.archive_source)
        self.logger.info('ARCHIVE_TARGET_DIRECTORY: ' + self.archive_target)

    def archive(self, file):
        path_suffix = file.get('filepath').split(self.archive_source)[1]
        source_path = os.path.abspath(self.archive_source + path_suffix)
        dest_path = os.path.abspath(self.archive_target + path_suffix)
        self.logger.info('Archiving id=%s: %s -> %s' % (file['id'], source_path, dest_path))

        self.moveFile(source_path, dest_path)

        # Call Clowder API endpoint to mark file as "archived"
        resp = requests.post('%sapi/files/%s/archive?key=%s' % (host, resource['id'], secret_key))


    def unarchive(self, file):
        path_suffix = file.get('filepath').split(self.archive_target)
        source_path = os.path.abspath(self.archive_target + path_suffix)
        dest_path = os.path.abspath(self.archive_source + path_suffix)
        self.logger.info('Unarchiving id=%s: %s -> %s' % (file['id'], source_path, dest_path))

        self.moveFile(source_path, dest_path)

        # Call Clowder API endpoint to mark file as "archived"
        resp = requests.post('%sapi/files/%s/unarchive?key=%s' % (host, resource['id'], secret_key))


    def moveFile(self, source, dest):
        # Ensure destination folder exists
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(source, dest)


    def process_message(self, connector, host, secret_key, resource, parameters):
        action = parameters.get('action')
        if action and action != 'manual-submission':
            return

        # Parse user parameters to determine whether we are to archive or unarchive
        userParams = parameters.get('parameters')
        operation = userParams.get('operation')
        self.logger.info('Operation == ' + str(operation))
        if resource['type'] == 'file':
            # If archiving/unarchiving a file, fetch db record from Clowder
            url = '%sapi/files/%s/metadata?key=%s' % (host, resource['id'], secret_key)
            self.logger.debug("sending request for file record: "+url)
            r = requests.get(url)
            if 'json' in r.headers.get('Content-Type'):
                self.logger.debug(r.json())
            else:
                self.logger.error('Response content is not in JSON format.. skipping: ' + str(r.headers.get('Content-Type')))
                return
            file = r.json()

            if operation and operation == 'unarchive':
                # If unarchiving, move the file from target to source
                self.unarchive(file)
            elif operation and operation == 'archive':
                # If archiving, move the file from source to target
                self.archive(file)
            else:
                self.logger.error('Unrecognized operation specified... aborting: ' + str(operation))
                return
        else:
            self.logger.error('Unsupported resource type.. skipping: ' + str(resource['type']))
            return


if __name__ == "__main__":
    extractor = DiskArchiver()
    extractor.start()
