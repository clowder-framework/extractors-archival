# Disk Archival Extractor for Clowder

Clowder has the capability of storing file bytes on disk. One simple archiving solution
would be to mount a persistent volume at some pre-specified directory and copy
"archived" resources there when requested.

It is unclear what that appropriate long-term archiving strategy might be, 
or even if one long-term archiving strategy will fit the majority of use cases.
This proof-of-concept will evolve over time as we decide on some of the patterns 
surrounding archival on disk.


## CLI Parameters
| Parameter                   | Default Value                 | Description                                                                        |
| --------------------------- | ----------------------------- | ---------------------------------------------------------------------------------- |
| `--archive-source <value>`  | `/home/clowder/data/uploads/` |  The path on disk where Clowder stores its file bytes                              |
| `--archive-target <value>`  | `/home/clowder/data/archive/` |  The path on disk where file bytes should be archived                              |


## Modes of Operation: Proof-of-Concept

* Submitting a file to the extractor with an extra parameter of `{"operation":"archive"}` will move the file from source to target.
* Simlarly, a parameter of `{"operation":"unarchive"}` will move the file from target back to source.


## TODOs

* Support archiving files from disk/mongo into S3? Vice versa?
* Testing

