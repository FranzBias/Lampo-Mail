# Changelog

## 0.5.2 — 2026-10-20 — first public release

- One window: From, To, Cc, Subject, text and attachments.
- The draft opens in your **default mail program** (the one that handles `mailto:` links):
  with Thunderbird the sender and the attachments are passed too; with any other program
  the standard `xdg-email` is used. Nothing is ever sent automatically — you press *Send*.
- Remembers the senders and recipients you use; a 🗑 removes an address from the list.
- Address book panel on the right with search, «To» and «Cc» buttons.
- Optional **Email Picker** integration: your own addresses can be picked as sender (📧) and
  a new sender can be saved into an Email Picker section (💾, with a backup copy first).
- Italian and English interface (follows the system language; `LAMPO_MAIL_LANG=it|en`).
- `install.sh` / `uninstall.sh` for a per-user installation.
