#!/usr/bin/env bash
set -euo pipefail

# Build a single-file executable using pyinstaller.
# Usage: ./build_standalone.sh [--onefile|--onedir] [--windowed]

MODE="--onefile"
WINDOWED="--windowed"

if [[ ${1:-} == "--onedir" ]]; then
  MODE="--onedir"
  shift
fi

if [[ ${1:-} == "--console" ]]; then
  WINDOWED=""
  shift
fi

python3 -m pip install --upgrade pip setuptools pyinstaller

# Ensure resources are copy-friendly
SCRIPT_PATH="src/main.py"

pyinstaller $MODE $WINDOWED \
  --name "discord-auto-messenger" \
  --add-data "src/config_template.json:." \
  --add-data "src/messages_template.txt:." \
  --add-data "src/auto_messenger/gui:gui" \
  --add-data "src/auto_messenger/core:core" \
  --add-data "src/auto_messenger/utils:utils" \
  --distpath dist \
  --workpath build \
  --clean \
  $SCRIPT_PATH

echo "Standalone build complete. Output: dist/discord-auto-messenger"