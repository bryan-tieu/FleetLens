# Local data

Dataset contents, generated outputs, and model artifacts stay outside Git. Only this README is retained under data/ by the initial ignore rules.

No datasets or directory junctions were transferred from FleetLoop. Existing data remains in its original location. M0 uses small synthetic test fixtures and needs no downloads.

A configurable data root is planned; its implementation and exact interface will be documented with the first adapter. Record dataset/version, manifest, permitted use, real/generated provenance, and transformation versions.

Read [the acquisition plan](../docs/data-acquisition.md) and [privacy design](../docs/privacy.md) before processing real data. Do not include identifying traces, restricted images, or credentials in fixtures, reports, or commits.
