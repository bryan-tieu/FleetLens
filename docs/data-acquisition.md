# Data acquisition

No data acquisition is required for M0 or the first synthetic demo.

The FleetLoop history records existing downloads for comma2k19, nuScenes mini, BDD100K images, and NHTSA/FHWA data on the Windows machine. Detection-label readiness and current file availability need verification. Existing data was not copied or moved during migration.

Before a later real-data milestone:
1. Inspect the existing dataset location instead of redownloading automatically.
2. Verify source/version, integrity, expected file counts and label pairing.
3. Check permitted processing, display, and redistribution.
4. Record the source manifest, observed date, and actual configured path.
5. Apply the relevant [privacy design](privacy.md).

Keep telemetry, image/label data, and incident-report data separate. They have different populations and do not automatically share identity or exposure. See the [archived acquisition record](archive/fleetloop/docs/data-acquisition.md) for historical download details, not live endpoint guarantees.
