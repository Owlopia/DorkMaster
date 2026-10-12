#!/usr/bin/env bash
# Install DorkMaster for the current Linux desktop user without requiring sudo.
set -Eeuo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
# Use SUDO_USER if available (script run with sudo), otherwise current user
INSTALL_USER="${SUDO_USER:-$USER}"
HOME_DIR="/home/${INSTALL_USER}" || HOME_DIR="$HOME"
DATA_HOME="${XDG_DATA_HOME:-$HOME_DIR/.local/share}"
BIN_HOME="${XDG_BIN_HOME:-$HOME_DIR/.local/bin}"
APP_HOME="$DATA_HOME/dorkmaster"
VENV_DIR="$APP_HOME/venv"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME_DIR/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME_DIR/.local/share}/icons/hicolor/128x128/apps"
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

# Create launcher wrapper script
{
    printf '%s\n' '#!/usr/bin/env bash'
    printf 'exec %q "$@"\n' "$VENV_DIR/bin/dorkmaster"
} > "$LAUNCHER"
chmod 755 "$LAUNCHER"

# Generate desktop entry with properly quoted exec path
# Replace Exec=dorkmaster with the full launcher path, preserving quotes
DESKTOP_SOURCE="$REPO_DIR/dorkmaster.desktop"
DESKTOP_TARGET="$DESKTOP_DIR/dorkmaster.desktop"
launcher_escaped=$(printf '%s' "$LAUNCHER" | sed 's/"/\\"/g')
text=$(sed "s|Exec=dorkmaster|Exec=${launcher_escaped}|" "$DESKTOP_SOURCE")
printf '%s\n' "$text" > "$DESKTOP_TARGET"
chmod 644 "$DESKTOP_TARGET"

# Install icon (PNG) - also generate SVG if available
if [ -f "$REPO_DIR/dorkmaster.svg" ]; then
    SVG_DIR="${XDG_DATA_HOME:-$HOME_DIR/.local/share}/icons/hicolor/scalable/apps"
    mkdir -p "$SVG_DIR"
    install -m 644 "$REPO_DIR/dorkmaster.svg" "$SVG_DIR/dorkmaster.svg"
fi
install -m 644 "$REPO_DIR/assets/DorkMaster.png" "$ICON_DIR/dorkmaster.png"

# Update icon cache if tools are available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1 && [ -f "$HOME_DIR/.local/share/icons/hicolor/index.theme" ]; then
    gtk-update-icon-cache -f "$HOME_DIR/.local/share/icons/hicolor" || true
fi

echo "Installed DorkMaster. Find it under Security or Information Gathering in the application menu."
echo "Terminal command: $LAUNCHER"