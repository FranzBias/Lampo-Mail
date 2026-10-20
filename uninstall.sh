#!/usr/bin/env bash
# Lampo Mail — removal. Your remembered addresses stay in ~/.config/lampo-mail (delete it by hand if you want).
set -euo pipefail
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/lampo-mail"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
rm -f "$APPS/lampo-mail.desktop"
rm -rf "$DEST"
echo "✔ Removed. Your settings remain in ~/.config/lampo-mail: delete that folder by hand if you want."
