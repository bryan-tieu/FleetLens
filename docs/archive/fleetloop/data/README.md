> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

# Local datasets and working data

Dataset contents and generated outputs stay outside Git. Verify existing .gitignore coverage before introducing a new artifact path.

Historical Windows acquisition used junctions from data/comma2k19, data/nuscenes, data/bdd100k, and data/nhtsa to D:\FleetLoop-data. See [the acquisition record](../docs/data-acquisition.md); its sizes and availability claims are dated observations, not current checks.

M0 needs only a small generated fixture. Do not download the full collection again to start development. Later adapters should support a configured data root with a repo-relative default; that path helper is not implemented yet.

Record source/version, content manifest, permitted use, provenance, and transformation version. Generated records must carry their generated status in-band. Keep telemetry, image/label pairs, and public incident datasets distinct; they do not share a vehicle identity or automatically form one training loop.

Before using real data, verify paths, expected files and label pairing, integrity, and permitted display/redistribution. Read [privacy.md](../docs/privacy.md) before processing real GPS or media. Do not include raw identifying data in logs, reports, fixtures, or commits.
