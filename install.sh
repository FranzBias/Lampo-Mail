#!/usr/bin/env bash
# Lampo Mail — installation for the current user only (no sudo).
# Copies the app to ~/.local/share/lampo-mail and adds the menu entry.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/lampo-mail"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DEST" "$APPS"
cp -r "$SRC/src/." "$DEST/"
sed -e "s|@APPDIR@|$DEST|g" "$SRC/lampo-mail.desktop.in" > "$APPS/lampo-mail.desktop"
chmod +x "$DEST/Lampo-Mail.py"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" 2>/dev/null || true
echo "✔ Installed in $DEST"
echo "  Look for «Lampo Mail» in the menu, or run: python3 \"$DEST/Lampo-Mail.py\""
