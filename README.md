# Archiving Files

The archival process in Clowder is an optional addon to the already optional RabbitMQ extractor framework.

The definition of "archiving" is left to the implementation of each archival extractor, and "unarchiving" is the exact inverse of that process.

Two archival extractor implementations exist that currently depend on which ByteStorageDriver you are using:

- [**ncsa.archival.disk**](archival-disk) **:** Moves the file from one specially-designated folder on disk to another **(requires write access to Clowder's data directory)**
- [**ncsa.archival.s3**](archival-s3) **:** Changes the Storage Class of an object stored in S3 **(requires write access to Clowder's bucket in S3)**

The two options cannot currently be mixed, meaning that if Clowder uses DiskByteStorage then you must use the Disk archiver.

If neither of these two extractors fit your use case, pyclowder can be used to quickly create a new archival extractor that fits your needs.

- [Process Overview](#ArchivingFiles-ProcessOverview)
  - [On Archive](#ArchivingFiles-OnArchive)
  - [On Unarchive](#ArchivingFiles-OnUnarchive)
  - [Automatic File Archival](#ArchivingFiles-AutomaticFileArchival)
- [Configuration Options / Defaults for Clowder](#ArchivingFiles-ConfigurationOptions/Def)
  - [ncsa.archival.disk](#ArchivingFiles-ncsa.archival.disk)
    - [Configuration Options](#ArchivingFiles-ConfigurationOptions)
    - [Example Configuration: Archive to another folder](#ArchivingFiles-ExampleConfiguration:Arc)
  - [ncsa.archival.s3](#ArchivingFiles-ncsa.archival.s3)
    - [Configuration Options](#ArchivingFiles-ConfigurationOptions.1)
    - [Example Configuration: S3 on AWS in us-east-2 Region](#ArchivingFiles-ExampleConfiguration:S3o)
    - [Example Configuration: MinIO](#ArchivingFiles-ExampleConfiguration:Min)
- [Common Pitfalls](#ArchivingFiles-CommonPitfalls)
  - [Gotcha: attempting to download an ARCHIVED File via the Clowder API's /api/files/:id  endpoint will result in a 404](#ArchivingFiles-Gotcha:attemptingtodownl)
  - [Gotcha: communication issues between containers](#ArchivingFiles-Gotcha:communicationissu)
  - [Gotcha: extractor complains about Python's built-in Thread.isAlive(), and dies quickly after starting](#ArchivingFiles-Gotcha:extractorcomplain)

## Process Overview

When a file is first uploaded, it is placed into a temp folder and created in the DB with the state CREATED.

At this point, users can start associating metadata with the new file, even though the actual file bytes are not yet available through Clowder's API.

Clowder then begins transferring the file bytes to the configured ByteStorage driver.

Once the bytes are completely uploaded into Clowder and done transferring to the data store, the file is marked as PROCESSED.

At this point users can access the file bytes via the Clowder API and UI, and are able download the file as normal.

If the admin has configured the archival feature (see below), then the user is also offered a button to Archive the file.

### On Archive

If a user chooses to Archive the file, then it is sent to the configured archival extractor with a parameter of _**operation=archive**_.

The extractor performs whatever operation it deems as "archiving" - for example, copying to a network file system.

The page will refresh automatically after a few seconds - for most cases, this hard-coded delay is enough to pick up the new File status of ARCHIVED on refresh.

Finally the file is marked as ARCHIVED, and (if configured) the user is given the option to Unarchive the file.

If the user attempts to download an ARCHIVED file, then they should be presented with a prompt to notify the admin for a request to unarchive.

### On Unarchive

If a user chooses to Unarchive a file, then it is sent to the configured archival extractor with a parameter of **_operation=unarchive_**.

The extractor performs the inverse of whatever operation that it previously defined as "archiving", bringing the file bytes back to where Clowder can access them for download.

NOTE: The page will refresh automatically after a few seconds - for most cases, this hard-coded delay is enough to pick up the new File status of PROCESSED on refresh.

Finally the file is marked as PROCESSED, and the user should be once again given the option to Archive the file and requests to download the file bytes should succeed.

### Automatic File Archival

If configured (see below), Clowder can automatically archive files of sufficient size after a predetermined period of inactivity.

By default, files that are over 1MB and have not been downloaded in that last 90 days will be automatically archived.

Both the file size and the inactivity period can be configured according to your preferences.

## Configuration Options / Defaults for Clowder

To use the archival feature, the RabbitMQ plugin must be enabled and properly configured.

With the RabbitMQ plugin enabled, the following defaults are configured in application.conf, but can be overridden by using a custom.conf file:

| **Configuration Path** | **Default** | **Description** |
| --- | --- | --- |
| archiveEnabled | false | If true, Clowder should perform a lookup once per day to see if any files uploaded the past hour are candidates for archival. |
| archiveDebug | false | If true, Clowder should temporarily use "5 minutes" as the archive check interval (instead of once per day). In addition, it only considers candidate files that were uploaded in the past hour. |
| archiveExtractorId | "ncsa.archival.disk" | The id of the Extractor to use for archival |
| archiveAllowUnarchive | false | If true, the UI should offer a way to Unarchive a file that is ARCHIVED |
| archiveAutoAfterDaysInactive | 90 | The number of days that an item can go without being downloaded before it is automatically archived. |
| archiveMinimumStorageSize | 1000000 | The minimum number of bytes for a file to be considered as a candidate for automatic archival. |

### ncsa.archival.disk

To build the Disk archival extractor's Docker image, execute the following commands:

git clone https://opensource.ncsa.illinois.edu/bitbucket/scm/cats/extractors-archival-disk.git

cd extractors-archival-disk/

docker build -t clowder/extractors-archival-disk .

#### Configuration Options

The following configuration options must match your configuration of the DiskByteStorageDriver:

| **Environment Variable** | **Command-Line Flag** | **Default Value** | **Description** |
| --- | --- | --- | --- |
| ARCHIVE\_SOURCE\_DIRECTORY | --archive-source | $HOME/clowder/data/uploads/ | The current directory where Clowder stores it's uploaded files |
| ARCHIVE\_TARGET\_DIRECTORY | --archive-target | $HOME/clowder/data/archive/ | The target directory where the archival extractor should store the files that it archives. Note that this path can be on a network or other persistent storage. |

#### Example Configuration: Archive to another folder

In Clowder, configure the following:

```
# storage driver
service.byteStorage=services.filesystem.DiskByteStorageService

# disk storage path
#clowder.diskStorage.path="/Users/bob/clowder/data" # MacOSX
clowder.diskStorage.path="/home/clowder/clowder/data" # Linux

# disk archival settings
archiveEnabled=true
archiveDebug=false
archiveExtractorId="ncsa.archival.disk"
archiveAutoAfterDaysInactive=90
archiveMinimumStorageSize=1000000
archiveAllowUnarchive=true
```

To run the Disk archival extractor with this configuration:

docker run --net=host -itd -e MOUNTED\_PATHS='{ "/Users/lambert8/clowder/data":"/home/clowder/clowder/data" }' -v /Users/lambert8/clowder/data/:/home/clowder/clowder/data -e ARCHIVE\_SOURCE\_DIRECTORY="/home/clowder/clowder/data/uploads/" -e ARCHIVE\_TARGET\_DIRECTORY="/home/clowder/clowder/data/archive/" clowder/extractors-archival-disk

NOTE 1: MOUNTED\_PATHS configuration is currently required without modifications to the Python code, since we require direct write access to the data directory. This prevents us from needing to download the file to archive or unarchive it.

NOTE 2: on MacOSX, you may need to run the extractor with the --net=host option to connect to RabbitMQ.

### ncsa.archival.s3

To build the S3 archival extractor's Docker image, execute the following commands:

git clone https://opensource.ncsa.illinois.edu/bitbucket/scm/cats/extractors-archival-s3.git

cd extractors-archival-s3/

docker build -t clowder/extractors-archival-s3 .

#### Configuration Options

The following configuration options must match your configuration of the S3ByteStorageDriver:

| **Environment Variable** | **Command-Line Flag** | **Default Value** | **Description** |
| --- | --- | --- | --- |
| AWS\_S3\_SERVICE\_ENDPOINT | --service-endpoint \<value\> | [https://s3.amazonaws.com](https://s3.amazonaws.com/) | Which AWS Service Endpoint to use to connect to S3. Note that this may depend on the region used, but can also be used to point at a running MinIO instance. |
| AWS\_ACCESS\_KEY | --access-key \<value\> | "" | The AccessKey that should be used to authorize with AWS or MinIO |
| AWS\_SECRET\_KEY | --secret-key \<value\> | "" | The SecretKey that should be used to authorize with AWS or MinIO |
| AWS\_BUCKET\_NAME | --bucket-name \<value\> | clowder-archive | The name of the bucket where the files are stored in Clowder. |
| AWS\_REGION | --region \<value\> | us-east-1 | **AWS only** : the region where the S3 bucket exists |

#### Example Configuration: S3 on AWS in us-east-2 Region

In Clowder, configure the following:

```
# storage driver
service.byteStorage=services.s3.S3ByteStorageService

# AWS S3
clowder.s3.serviceEndpoint="https://s3-us-east-2.amazonaws.com"
clowder.s3.accessKey="AWSACCESSKEYKASOKD"
clowder.s3.secretKey="aWSseCretKey+asAfasf90asdASDADAOaisdoas"
clowder.s3.bucketName="bucket-on-aws"
clowder.s3.region="us-east-2"

# disk archival settings
archiveEnabled=true
archiveDebug=false
archiveExtractorId="ncsa.archival.s3"
archiveAutoAfterDaysInactive=90
archiveMinimumStorageSize=1000000
archiveAllowUnarchive=true
```

NOTE: Changing the Region typically requires changing the S3 Service Endpoint.

To run the S3 archival extractor with this configuration:

docker run --net=host -itd -e AWS\_S3\_SERVICE\_ENDPOINT='https://s3-us-east-2.amazonaws.com' -e AWS\_ACCESS\_KEY='AWSACCESSKEYKASOKD' -e AWS\_SECRET\_KEY='aWSseCretKey+asAfasf90asdASDADAOaisdoas' -e AWS\_BUCKET\_NAME='bucket-on-aws' -e AWS\_REGION='us-east-2' clowder/extractors-archival-s3

NOTE: on MacOSX, you may need to run the extractor with the --net=host option to connect to RabbitMQ.

#### Example Configuration: MinIO

In Clowder, configure the following to point the S3ByteStorageDriver and the archival extractor at your running MinIO instance:

```
# storage driver
service.byteStorage=services.s3.S3ByteStorageService

# Minio S3
clowder.s3.serviceEndpoint="http://localhost:8000"
clowder.s3.accessKey="AMINIOACCESSKEYKASOKD"
clowder.s3.secretKey="aMinIOseCretKey+asAfasf90asdASDADAOaisdoas"
clowder.s3.bucketName="bucket-on-minio"

# S3 archival settings
archiveEnabled=true
archiveDebug=false
archiveExtractorId="ncsa.archival.s3"
archiveAutoAfterDaysInactive=90
archiveMinimumStorageSize=1000000
archiveAllowUnarchive=true
```

NOTE: MinIO ignores the value for "Region", if one is specified.

To run the S3 archival extractor with this configuration:

docker run --net=host -itd -e AWS\_S3\_SERVICE\_ENDPOINT='http://localhost:8000' -e AWS\_ACCESS\_KEY='AMINIOACCESSKEYKASOKD' -e AWS\_SECRET\_KEY='aMinIOseCretKey+asAfasf90asdASDADAOaisdoas' -e AWS\_BUCKET\_NAME='bucket-on-minio' clowder/extractors-archival-s3

NOTE: on MacOSX, you may need to run the extractor with the --net=host option to connect to RabbitMQ.

## Common Pitfalls

### Gotcha: attempting to download an ARCHIVED File via the Clowder API's /api/files/:id  endpoint will result in a 404

This is important for debugging, as it was a little confusing until I realized what was going on.

Perhaps 404 is the wrong error code here, or maybe it just needs a better error message for this edge case.

There may be an implication that there is no model found with that ID, when really the problem is that it's internal state simply prevents it from being downloaded.

My vote is for [418 I'm a teapot](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/418), but something like **409 Conflict** or **410 Gone** would likely get the point across.

**412 Precondition Failed** and **417 Expectation Failed** also look promising, but I'm not sure if these have other underlying implications for the browser.

### Gotcha: communication issues between containers

NOTE: This issue can be tricky to workaround, as it is typically very environment-specific or setup-specific.

For example, this can happen if you're running RabbitMQ and the Extractor in separate containers, where the RabbitMQ container was created with --net=host and your Extractor was not.

As another example, this can happen on MacOSX if Clowder is running in IntelliJ on the host, with RabbitMQ and the extractor running in Docker containers (without --net=host).

Since one container is on the host network and the other is on the Docker bridge network, the two containers cannot communicate with each other.

The following configuration snippet can be added to Clowder's custom.conf to override the hostnames where both expect to find each other:

clowder.rabbitmq.uri="amqp://guest:guest@\<PRIVATE IP\>:5672/%2F"

clowder.rabbitmq.exchange="clowder"

clowder.rabbitmq.clowderurl="http://\<PRIVATE IP\>:9000"

### Gotcha: extractor complains about Python's built-in Thread.isAlive(), and dies quickly after starting

pyclowder has an open issue [here](https://github.com/clowder-framework/pyclowder/issues/25) regarding a minor incompatibility with Python 3.9

If you encounter this problem, simply change the Docker base image to build FROM python:3.8
