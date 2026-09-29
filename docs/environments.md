# Development environments

Supported interpreter: Python 3.11 (verified locally on Windows with 3.11.9; hosted CI passes on windows-latest and ubuntu-latest). Repository: C:\Users\Bryan\Downloads\FleetLens. Setup and check commands are in the [README](../README.md); a local .venv exists and is git-ignored.

Windows is the intended canonical benchmark host; macOS may be used for development. Record hardware and software with each measurement and keep comparison conditions controlled. Historical versions, disk readings, paths, and CUDA claims from FleetLoop require fresh verification.

Use repo-relative paths and portable Python helpers where practical. Dataset access will use a configurable root, proposed as FLEETLENS_DATA_DIR with a local data/ default. No path helper, junction, or dataset adapter exists yet.

Do not copy a .venv, recreate dataset junctions, launch archived Compose commands, or install the entire future stack to start M0. The [migration archive](migration.md) retains the older environment record for troubleshooting context.
