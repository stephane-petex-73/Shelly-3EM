#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests pyinstaller

pyinstaller --noconsole --onefile --name Shelly3EMViewer_V3_Linux shelly_3em_reader_v3.py

echo "Executable Linux créé dans : $ROOT_DIR/dist/Shelly3EMViewer_V3_Linux"
