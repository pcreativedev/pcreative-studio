#!/usr/bin/env bash
# Local macOS .app build. Mirrors .github/workflows/build-macos.yml so
# Mac developers can reproduce the CI build on their machine without
# pushing to GitHub.
#
# Requirements:
#   - macOS 13+
#   - Python 3.11+
#   - Xcode Command Line Tools (for iconutil)
#
# Usage:
#   bash scripts/build-macos.sh
#
# Output:
#   dist/Pcreative Studio.app
#   dist/Pcreative Studio-macOS.zip

set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
    echo "✗ this script must run on macOS (this is $(uname))" >&2
    exit 1
fi

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "▶ installing Python deps…"
python3 -m pip install --upgrade pip
python3 -m pip install pyqt6 pyqt6-webengine pyqt6-charts pyinstaller

echo "▶ generating .icns from PNG sources…"
rm -rf icon.iconset
mkdir -p icon.iconset
cp assets/themeforge-16.png  icon.iconset/icon_16x16.png
cp assets/themeforge-32.png  icon.iconset/icon_16x16@2x.png
cp assets/themeforge-32.png  icon.iconset/icon_32x32.png
cp assets/themeforge-64.png  icon.iconset/icon_32x32@2x.png
cp assets/themeforge-128.png icon.iconset/icon_128x128.png
cp assets/themeforge-256.png icon.iconset/icon_128x128@2x.png
cp assets/themeforge-256.png icon.iconset/icon_256x256.png
cp assets/themeforge.png     icon.iconset/icon_256x256@2x.png
cp assets/themeforge.png     icon.iconset/icon_512x512.png
cp assets/themeforge.png     icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset -o assets/themeforge.icns
echo "✓ assets/themeforge.icns"

echo "▶ building .app with PyInstaller…"
rm -rf build dist
pyinstaller --noconfirm --clean \
    --windowed \
    --name Pcreative Studio \
    --icon assets/themeforge.icns \
    --osx-bundle-identifier dev.pcreative.themeforge \
    --add-data "assets:assets" \
    --add-data "context:context" \
    --collect-submodules PyQt6 \
    themeforge.py

echo "▶ zipping for distribution…"
( cd dist && zip -r --symlinks Pcreative Studio-macOS.zip Pcreative Studio.app )

echo
echo "✓ done."
echo "  → dist/Pcreative Studio.app"
echo "  → dist/Pcreative Studio-macOS.zip"
echo
echo "Smoke test:"
echo "  open dist/Pcreative Studio.app"
