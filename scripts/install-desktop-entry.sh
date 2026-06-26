#!/usr/bin/env bash
# Installs a user-local .desktop launcher for Pcreative Studio so it shows up
# in your DE's app menu / dock. Idempotent — re-run to refresh.
#
# Usage: bash scripts/install-desktop-entry.sh
#
# Removes: bash scripts/install-desktop-entry.sh --uninstall

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/themeforge.desktop"

if [[ "${1:-}" == "--uninstall" ]]; then
    rm -fv "$DESKTOP_FILE"
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    echo "✓ removed"
    exit 0
fi

if [[ ! -f "$REPO_DIR/assets/themeforge.desktop.template" ]]; then
    echo "✗ template not found at $REPO_DIR/assets/themeforge.desktop.template" >&2
    exit 1
fi
if [[ ! -f "$REPO_DIR/assets/themeforge.png" ]]; then
    echo "✗ icon not found at $REPO_DIR/assets/themeforge.png" >&2
    exit 1
fi

mkdir -p "$DESKTOP_DIR"
sed "s|__INSTALL_PATH__|$REPO_DIR|g" \
    "$REPO_DIR/assets/themeforge.desktop.template" \
    > "$DESKTOP_FILE"

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "✓ installed → $DESKTOP_FILE"
echo "  Open your app menu and search for 'Pcreative Studio'."
