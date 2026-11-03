#!/bin/sh
# Run a whisperlite command in the Docker image with the project's data/ and
# results/ mounted, a model cache volume, and this PC's name recorded.
# usage: scripts/docker-run.sh bench --manifest data/pilot/manifest.csv
ROOT=$(cd "$(dirname "$0")/.." && pwd)
exec docker run --rm \
    -e WHISPERLITE_HOST="$(hostname -s)" \
    -v "$ROOT/data:/app/data" \
    -v "$ROOT/results:/app/results" \
    -v whisperlite-cache:/cache \
    whisperlite "$@"
