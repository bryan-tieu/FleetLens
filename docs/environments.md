# Development environments

FleetLens has no verified Python environment yet. Start in C:\Users\Bryan\Downloads\FleetLens. M0 establishes and documents the supported interpreter, installation, and check commands.

Windows is the intended canonical benchmark host; macOS may be used for development. Record hardware and software with each measurement and keep comparison conditions controlled. Historical versions, disk readings, paths, and CUDA claims from FleetLoop require fresh verification.

Use repo-relative paths and portable Python helpers where practical. Dataset access will use a configurable root, proposed as FLEETLENS_DATA_DIR with a local data/ default. No path helper, junction, or dataset adapter exists yet.

Do not copy a .venv, recreate dataset junctions, launch archived Compose commands, or install the entire future stack to start M0. The [migration archive](migration.md) retains the older environment record for troubleshooting context.
