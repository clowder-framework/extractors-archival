# S3 Archival Extractor for Clowder

Clowder has the capability of storing file bytes in AWS S3. S3 has the capability of 
switching object storage classes - this could provide a simple interface into archival/unarchival
leveraging our emerging new byte storage strategy.

It is unclear what that appropriate long-term archiving strategy might be, 
or even if one long-term archiving strategy will fit the majority of use cases.
This proof-of-concept will evolve over time as we decide on some of the patterns 
surrounding archival on AWS S3 / Glacier.

For more information, see [Transitioning Objects Using Amazon S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/dev/lifecycle-transition-general-considerations.html)

NOTE: This has not yet been tested with Minio.

## CLI Parameters
| Parameter                     | Default Value | Description                                                                        |
| ----------------------------- | ------------- | ---------------------------------------------------------------------------------- |
| `--service-endpoint <value>`  |       `https://s3.amazonaws.com`      |  AWS S3 Service Endpoint (e.g. "http://localhost:8000" for MinIO)                  |
| `--access-key <value>`        |             |  AWS IAM AccessKey (provided by your AWS admin)                                    |
| `--secret-key <value>`        |             |  AWS IAM SecretKey (provided by your AWS admin)                                    |
| `--region <value>`            |  `us-east-1`  |  AWS Region where bucket can be found (defaults to N. Virginia, ignored for Minio) |
| `--bucket-name <value>`       |             |  AWS S3 bucket used where the file bytes currently live (they will not be moved)   |


## Modes of Operation: Proof-of-Concept

* Submitting a file to the extractor with an extra parameter of `{"operation":"archive"}` will change the storage class of the file in S3 from `STANDARD` to `REDUCED_REDUNDANCY`.
* Simlarly, a parameter of `{"operation":"unarchive"}` will change the storage class of the file in S3 from `REDUCED_REDUNDANCY` back to `STANDARD`.

NOTE: `REDUCED_REDUNDANCY` is a placeholder value for testing - it is not recommended for us by AWS.


## TODOs

* Parameterize archived (or unarchived) storage class(es)?
* Support archiving files from disk/mongo into S3?
* Test other stroage classes - namely STANDARD_IA and/or ONEZONE_IA?
* Test/support the GLACIER or DEEP_ARCHIVE storage classes? Are these costs justified?


## See Also

AWS Documentation
* https://docs.aws.amazon.com/AmazonS3/latest/dev/storage-class-intro.html
* https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#bucket-config-options-intro
* https://docs.aws.amazon.com/AmazonS3/latest/dev/lifecycle-transition-general-considerations.html

boto3 Documentation
* https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#bucket
* https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#object
* https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.copy_object

