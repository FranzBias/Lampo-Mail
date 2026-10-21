#!/usr/bin/env bash
##########################################################
##                Lampo Mail · uninstall                ##
##          Removes the per-user installation           ##
##                   written in Bash                    ##
##                          🇮🇹                          ##
##       by FranzBias 2026 · github.com/FranzBias       ##
##            Licensed under the MIT License            ##
##          See LICENSE file for full license.          ##
##########################################################
# SPDX-License-Identifier: MIT
# Lampo Mail — removal. Your remembered addresses stay in ~/.config/lampo-mail (delete it by hand if you want).
set -euo pipefail
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/lampo-mail"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
rm -f "$APPS/lampo-mail.desktop"
rm -rf "$DEST"
echo "✔ Removed. Your settings remain in ~/.config/lampo-mail: delete that folder by hand if you want."
