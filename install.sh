#!/usr/bin/env bash
# Install DorkMaster for the current Linux desktop user without requiring sudo.
set -Eeuo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="${XDG_BIN_HOME:-$HOME/.local/bin}"
APP_HOME="$DATA_HOME/dorkmaster"
VENV_DIR="$APP_HOME/venv"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/128x128/apps"
LAUNCHER="$BIN_HOME/dorkmaster"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
    echo "Python 3 is required. Install python3 and python3-venv, then retry." >&2
    exit 1
}

echo "Creating isolated DorkMaster environment..."
mkdir -p "$APP_HOME"
"$PYTHON_BIN" -m venv "$VENV_DIR" || {
    echo "Unable to create a virtual environment. Install python3-venv and retry." >&2
    exit 1
}
"$VENV_DIR/bin/python" -m pip install --upgrade "$REPO_DIR"

mkdir -p "$BIN_HOME" "$DESKTOP_DIR" "$ICON_DIR"
{
    printf '%s\n' '#!/usr/bin/env bash'
    printf 'exec %q "$@"\n' "$VENV_DIR/bin/dorkmaster"
} > "$LAUNCHER"
chmod 755 "$LAUNCHER"

DESKTOP_LAUNCHER="$LAUNCHER" DESKTOP_SOURCE="$REPO_DIR/dorkmaster.desktop" DESKTOP_TARGET="$DESKTOP_DIR/dorkmaster.desktop" \
    "$VENV_DIR/bin/python" -c 'import os; from pathlib import Path; launcher = os.environ["DESKTOP_LAUNCHER"].replace("\\", "\\\\").replace(" ", "\\s"); text = Path(os.environ["DESKTOP_SOURCE"]).read_text(encoding="utf-8").replace("Exec=dorkmaster", "Exec=" + launcher); Path(os.environ["DESKTOP_TARGET"]).write_text(text, encoding="utf-8")'
install -m 644 "$REPO_DIR/assets/DorkMaster.png" "$ICON_DIR/dorkmaster.png"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" || true

echo "Installed DorkMaster. Find it under Security or Information Gathering in the application menu."
echo "Terminal command: $LAUNCHER"
