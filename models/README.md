# Frozen route neural weights

These are the selected V27 phase route and V26 interval route float32 weights, exported for the C++17 `PhaseRouteModel` reader. They contain fitted parameters, development-only normalization and architecture-only graph embeddings. They do not contain validation answers.

The export manifest is `reports/Neural-route-export.json`; architecture, measurements and command line are in `reports/V20-V35-architecture-research.md`. Regenerate from the selected local training checkpoints with `out/research-env/bin/python scripts/export_route_neural_models.py`.

The binary format currently uses little-endian IEEE float32 and uint32, with a double teacher blend weight. It is exercised on this Mac; a Linux competition build is not yet validated. Total weight size is 2,055,836 bytes. This figure excludes all existing path assets and source files.
