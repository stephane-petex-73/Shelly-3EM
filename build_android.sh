#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR/android_app"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install buildozer cython virtualenv

# Build the Android APK on a Linux/macOS host with Android SDK/NDK installed.
# The build is not executed here because this environment is not configured for Android packaging.
buildozer android debug

echo "APK Android généré dans le dossier bin/ de buildozer"
