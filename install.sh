#!/bin/bash
# MASE v2 compatibility installer. The manifest is the runtime source of truth.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing MASE v2 CLI from $SCRIPT_DIR"
python3 -m pip install "$SCRIPT_DIR"

echo "Installing manifest-declared runtime resources"
mase install --source "$SCRIPT_DIR" "$@"

echo "MASE installation complete"
mase --version
