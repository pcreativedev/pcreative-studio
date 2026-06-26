#!/usr/bin/env bash
# Wrapper para lanzar Pcreative Studio GUI.
cd "$(dirname "$(readlink -f "$0")")"
exec python3 themeforge.py "$@"
