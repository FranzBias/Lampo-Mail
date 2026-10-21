#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################
##                      Lampo Mail                      ##
##              An e-mail draft in a flash              ##
##             written in Python 3 · GTK 3              ##
##                          🇮🇹                          ##
##       by FranzBias 2026 · github.com/FranzBias       ##
##            Licensed under the MIT License            ##
##          See LICENSE file for full license.          ##
##########################################################
# SPDX-License-Identifier: MIT
"""
Lampo Mail ⚡ — scrivi un messaggio in un lampo e passalo al tuo programma di posta.

Una finestra sola: Mittente, Destinatari, Oggetto, Testo, Allegati.
Gli indirizzi vengono da due fonti:
  - quelli memorizzati da Lampo Mail (mittenti e destinatari usati);
  - i TUOI indirizzi stanno in Email Picker (emails.json): servono solo come
    Mittente. Col pulsante 💾 se ne aggiunge uno nuovo a una sezione di
    Email Picker (prima viene salvata una copia del file).
Il messaggio non parte da solo: «Prepara» apre la bozza completa nel programma
di posta PREDEFINITO del sistema (quello dei link mailto:) e l'invio resta un tuo
gesto. Con Thunderbird si usa il suo metodo diretto (passa anche mittente e
allegati); con gli altri programmi si usa xdg-email, lo standard di Linux.

Licenza MIT — made with ❤ by Francesco
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio

import json
import os
import shutil
import subprocess
import time
import urllib.parse

APP_NAME = "Lampo Mail"
APP_VERSION = "0.5.2"
HOME = os.path.expanduser("~")
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Lingua: italiano se il sistema è in italiano, altrimenti inglese -------------
# (si può forzare con LAMPO_MAIL_LANG=it / en)
EN = {
    "Mittente": "From", "A": "To", "Cc": "Cc", "Oggetto": "Subject",
    "il tuo indirizzo (ricordato all'invio)": "your address (remembered when sending)",
    "I tuoi indirizzi (Email Picker)": "Your addresses (Email Picker)",
    "Salva questo indirizzo in Email Picker": "Save this address in Email Picker",
    "Togli questo mittente dall'elenco": "Remove this sender from the list",
    "nome@esempio.it — più indirizzi separati da virgola": "name@example.com — separate several addresses with commas",
    "facoltativo": "optional",
    "Allegati: nessuno": "Attachments: none",
    "📎 Allega…": "📎 Attach…", "✕ Togli allegati": "✕ Remove attachments",
    "Svuota": "Clear",
    "⚡ Prepara in {0}": "⚡ Draft in {0}",
    "Apre la bozza nel programma di posta predefinito (Ctrl+Invio)": "Opens the draft in your default mail program (Ctrl+Enter)",
    "programma di posta": "mail program",
    "I tuoi indirizzi (Email Picker): {0} — pulsante 📧": "Your addresses (Email Picker): {0} — 📧 button",
    "Rubrica Email Picker non leggibile": "Email Picker address book not readable",
    "Rubrica Email Picker non trovata": "Email Picker address book not found",
    "📇 Rubrica": "📇 Address book", "Rubrica": "Address book",
    "Cerca nome o email…": "Search name or e-mail…",
    "«A» e «Cc» aggiungono l'indirizzo al campo.\nI tuoi indirizzi stanno in 📧, accanto al Mittente.":
        "«To» and «Cc» add the address to the field.\nYour own addresses are under 📧, next to From.",
    "Destinatari usati": "Used recipients",
    "Nessun destinatario ancora: scrivine uno in «A»,\nverrà ricordato al primo invio.":
        "No recipients yet: type one in «To»,\nit will be remembered on the first send.",
    "Aggiungi a «{0}»": "Add to «{0}»",
    "Togli questo indirizzo dai destinatari usati": "Remove this address from the used recipients",
    "Tolto dai destinatari usati: {0}": "Removed from used recipients: {0}",
    "Aggiunto: {0}": "Added: {0}", "Chiudi": "Close", "Usati di recente": "Recently used",
    "Mittente: {0}": "From: {0}",
    "Cerca tra i tuoi indirizzi…": "Search your addresses…",
    "Email Picker non trovato o vuoto.": "Email Picker not found or empty.",
    "Email Picker aperto.": "Email Picker opened.", "Email Picker non trovato.": "Email Picker not found.",
    "📧 Apri l'app Email Picker": "📧 Open the Email Picker app",
    "⚠️ Scrivi prima un indirizzo valido nel Mittente.": "⚠️ First type a valid address in From.",
    "Email Picker non trovato: salvato solo in Lampo Mail.": "Email Picker not found: saved in Lampo Mail only.",
    "Salva in Email Picker": "Save in Email Picker", "Annulla": "Cancel", "💾 Salva": "💾 Save",
    "Indirizzo": "Address", "Sezione": "Section", "Nome": "Name",
    "facoltativo, es. «Banca» o «Newsletter»": "optional, e.g. «Bank» or «Newsletter»",
    "Mittente tolto dall'elenco.": "Sender removed from the list.",
    "Allega file": "Attach files", "Allega": "Attach",
    "Allegati ({0}): {1}": "Attachments ({0}): {1}",
    "⚠️ Manca il destinatario.": "⚠️ The recipient is missing.",
    "✔ Bozza aperta in {0}.": "✔ Draft opened in {0}.",
    " Il mittente sceglilo lì (questo programma non lo riceve da fuori).":
        " Choose the sender there (this program does not accept it from outside).",
    "⚠️ Non riesco ad aprire il programma di posta: {0}": "⚠️ Cannot open the mail program: {0}",
    "Non riesco a leggere Email Picker: {0}": "Cannot read Email Picker: {0}",
    "È già in Email Picker, sezione «{0}».": "Already in Email Picker, section «{0}».",
    "Sezione di Email Picker non trovata.": "Email Picker section not found.",
    "Copia di sicurezza non riuscita, non scrivo nulla: {0}": "Backup copy failed, nothing written: {0}",
    "Scrittura non riuscita: {0}": "Writing failed: {0}",
    "Salvato in Email Picker, sezione «{0}».": "Saved in Email Picker, section «{0}».",
}


def _detect_lang():
    forced = os.environ.get("LAMPO_MAIL_LANG", "").lower()
    if forced in ("it", "en"):
        return forced
    for var in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        v = os.environ.get(var, "")
        if v:
            return "it" if v.lower().startswith("it") else "en"
    return "en"


LANG = _detect_lang()


def _(text):
    return text if LANG == "it" else EN.get(text, text)


def _data_dir():
    """Dati per macchina fuori dal vault: ~/.0-SYSTEM/Lampo-Mail se esiste ~/.0-SYSTEM,
    altrimenti ~/.config/lampo-mail."""
    if os.environ.get("LAMPO_MAIL_DIR"):
        return os.path.expanduser(os.environ["LAMPO_MAIL_DIR"])
    if os.path.isdir(os.path.join(HOME, ".0-SYSTEM")):
        return os.path.join(HOME, ".0-SYSTEM", "Lampo-Mail")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "lampo-mail")


DATA_DIR = _data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Dove cercare la rubrica di Email Picker (la prima che esiste vince;
# il percorso si può anche impostare in config.json → "email_picker_file")
EMAIL_PICKER_CANDIDATES = [
    os.path.join(HOME, ".0-SYSTEM", "Scripts", "Email-Picker", "emails.json"),
    os.path.join(HOME, ".config", "email-picker", "emails.json"),
]

DEFAULT_CONFIG = {
    "senders": [],            # i tuoi indirizzi, l'ultimo usato in cima
    "recipients": [],         # destinatari usati, l'ultimo in cima
    "email_picker_file": "",  # vuoto = ricerca automatica
    "window": {"w": 1020, "h": 640},
}


# -----------------------------------------------------------------------------
# Dati
# -----------------------------------------------------------------------------
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_FILE)
    except OSError:
        pass


def email_picker_path(cfg):
    custom = (cfg.get("email_picker_file") or "").strip()
    if custom:
        return os.path.expanduser(custom)
    for p in EMAIL_PICKER_CANDIDATES:
        if os.path.isfile(p):
            return p
    return ""


def load_email_picker(cfg):
    """Rubrica di Email Picker: [(scheda, nome, email)]. Solo lettura."""
    path = email_picker_path(cfg)
    out = []
    if not path:
        return out, ""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        tabs = sorted(data.get("tabs", []), key=lambda t: t.get("order", 0))
        for tab in tabs:
            label = tab.get("label", "")
            for e in tab.get("entries", []):
                mail = (e.get("email") or "").strip()
                if mail:
                    out.append((label, (e.get("name") or "").strip(), mail))
    except (OSError, ValueError, AttributeError):
        return [], path
    return out, path


def _dump_email_picker(data):
    """Stesso stile del file di Email Picker: rientro di 2, un indirizzo per riga."""
    lines = ["{", '  "tabs": [']
    tabs = data.get("tabs", [])
    for ti, tab in enumerate(tabs):
        lines.append("    {")
        for k in ("id", "label", "order"):
            if k in tab:
                lines.append(f'      {json.dumps(k)}: {json.dumps(tab[k], ensure_ascii=False)},')
        for k, v in tab.items():
            if k not in ("id", "label", "order", "entries"):
                lines.append(f'      {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},')
        lines.append('      "entries": [')
        ents = tab.get("entries", [])
        for ei, e in enumerate(ents):
            comma = "," if ei < len(ents) - 1 else ""
            lines.append("        " + json.dumps(e, ensure_ascii=False) + comma)
        lines.append("      ]")
        lines.append("    }" + ("," if ti < len(tabs) - 1 else ""))
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def add_to_email_picker(path, tab_id, name, mail):
    """Aggiunge {name, email} alla sezione tab_id di Email Picker.
    Copia di sicurezza prima, scrittura atomica, nessun doppione.
    Restituisce (ok, messaggio)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return False, _("Non riesco a leggere Email Picker: {0}").format(e)
    for tab in data.get("tabs", []):
        for e in tab.get("entries", []):
            if (e.get("email") or "").strip().lower() == mail.lower():
                return False, _("È già in Email Picker, sezione «{0}».").format(tab.get("label", ""))
    target = next((x for x in data.get("tabs", []) if x.get("id") == tab_id), None)
    if target is None:
        return False, _("Sezione di Email Picker non trovata.")
    bdir = os.path.join(DATA_DIR, "backup-email-picker")
    try:
        os.makedirs(bdir, exist_ok=True)
        shutil.copy2(path, os.path.join(bdir, time.strftime("emails-%Y%m%d-%H%M%S.json")))
    except OSError as e:
        return False, _("Copia di sicurezza non riuscita, non scrivo nulla: {0}").format(e)
    target.setdefault("entries", []).append({"name": name, "email": mail})
    tmp = path + ".lampo-tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(_dump_email_picker(data))
        with open(tmp, encoding="utf-8") as f:
            json.load(f)                      # controllo: è JSON valido
        os.replace(tmp, path)
    except (OSError, ValueError) as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False, _("Scrittura non riuscita: {0}").format(e)
    return True, _("Salvato in Email Picker, sezione «{0}».").format(target.get("label", ""))


def email_picker_tabs(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [(x.get("id"), x.get("label", "")) for x in
                sorted(data.get("tabs", []), key=lambda x: x.get("order", 0))]
    except (OSError, ValueError):
        return []


def launch_email_picker():
    """Apre l'app Email Picker, se installata (voce di menu o file nelle cartelle note)."""
    for did in ("email-picker.desktop", "miei-script-email-picker.desktop"):
        try:
            info = Gio.DesktopAppInfo.new(did)
        except TypeError:
            info = None
        if info is not None:
            try:
                info.launch([], None)
                return True
            except GLib.Error:
                pass
    for p in (os.path.join(HOME, ".0-SYSTEM", "Scripts", "Email-Picker", "email-picker.py"),
              os.path.join(HOME, ".local", "share", "email-picker", "email-picker.py")):
        if os.path.isfile(p):
            subprocess.Popen(["python3", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            return True
    return False


def default_mail_client():
    """Programma di posta predefinito del sistema (gestore dei link mailto:).
    Restituisce (nome da mostrare, comando per Thunderbird o None)."""
    info = None
    try:
        info = Gio.AppInfo.get_default_for_uri_scheme("mailto")
    except Exception:
        info = None
    if info is None:
        return _("programma di posta"), None
    name = info.get_name() or _("programma di posta")
    ident = (info.get_id() or "").lower()
    exe = (info.get_executable() or "").lower()
    if "thunderbird" in ident or "thunderbird" in exe:
        if "flatpak" in exe or ident.startswith("org.mozilla.thunderbird"):
            return name, ["flatpak", "run", "org.mozilla.Thunderbird"]
        tb = shutil.which("thunderbird") or shutil.which(exe) or "thunderbird"
        return name, [tb]
    return name, None


def remember(cfg, key, addr, limit=40):
    addr = (addr or "").strip()
    if "@" not in addr:
        return
    items = [a for a in cfg.get(key, []) if a and a != addr]
    items.insert(0, addr)
    cfg[key] = items[:limit]


def split_addresses(text):
    parts = [p.strip() for p in text.replace(";", ",").split(",")]
    return [p for p in parts if p]


# -----------------------------------------------------------------------------
# Finestra
# -----------------------------------------------------------------------------
class LampoMail(Gtk.Window):
    def __init__(self):
        super().__init__(title=f"⚡ {APP_NAME}")
        self.cfg = load_config()
        self.book, self.book_path = load_email_picker(self.cfg)
        self.attachments = []

        w = self.cfg.get("window", {})
        # almeno 960 px: a destra c'è la rubrica sempre visibile
        self.set_default_size(max(960, int(w.get("w", 1020))), max(560, int(w.get("h", 640))))
        self.set_border_width(12)
        icon = os.path.join(APP_ROOT, "icon.png")
        if os.path.isfile(icon):
            try:
                self.set_icon_from_file(icon)
            except GLib.Error:
                pass
        else:
            self.set_icon_name("mail-message-new")
        self._css()

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(paned)
        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.set_margin_end(8)
        paned.pack1(grid, resize=True, shrink=False)
        paned.set_position(max(560, int(w.get("w", 1020)) - 380))
        row = 0

        # Mittente
        grid.attach(self._label(_("Mittente")), 0, row, 1, 1)
        self.from_combo = Gtk.ComboBoxText.new_with_entry()
        self.from_combo.set_hexpand(True)
        for s in self.cfg.get("senders", []):
            self.from_combo.append_text(s)
        if self.cfg.get("senders"):
            self.from_combo.set_active(0)
        self.from_combo.get_child().set_placeholder_text(_("il tuo indirizzo (ricordato all'invio)"))
        self._attach_completion(self.from_combo.get_child(), only_book=True)
        grid.attach(self.from_combo, 1, row, 1, 1)
        sender_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        sender_btns.pack_start(self._small_button("📧", _("I tuoi indirizzi (Email Picker)"),
                                                  self.on_pick_sender), False, False, 0)
        sender_btns.pack_start(self._small_button("💾", _("Salva questo indirizzo in Email Picker"),
                                                  self.on_save_sender), False, False, 0)
        sender_btns.pack_start(self._small_button("🗑", _("Togli questo mittente dall'elenco"),
                                                  self.on_forget_sender), False, False, 0)
        grid.attach(sender_btns, 2, row, 1, 1)
        row += 1

        # Destinatari
        grid.attach(self._label(_("A")), 0, row, 1, 1)
        self.to_entry = Gtk.Entry()
        self.to_entry.set_hexpand(True)
        self.to_entry.set_placeholder_text(_("nome@esempio.it — più indirizzi separati da virgola"))
        self._attach_completion(self.to_entry)
        grid.attach(self.to_entry, 1, row, 2, 1)
        row += 1

        grid.attach(self._label(_("Cc")), 0, row, 1, 1)
        self.cc_entry = Gtk.Entry()
        self.cc_entry.set_placeholder_text(_("facoltativo"))
        self._attach_completion(self.cc_entry)
        grid.attach(self.cc_entry, 1, row, 2, 1)
        row += 1

        # Oggetto
        grid.attach(self._label(_("Oggetto")), 0, row, 1, 1)
        self.subject_entry = Gtk.Entry()
        grid.attach(self.subject_entry, 1, row, 2, 1)
        row += 1

        # Testo
        sc = Gtk.ScrolledWindow()
        sc.set_hexpand(True)
        sc.set_vexpand(True)
        sc.set_shadow_type(Gtk.ShadowType.IN)
        self.body_view = Gtk.TextView()
        self.body_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.body_view.set_left_margin(8)
        self.body_view.set_right_margin(8)
        self.body_view.set_top_margin(6)
        self.body_view.get_style_context().add_class("body")
        sc.add(self.body_view)
        grid.attach(sc, 0, row, 3, 1)
        row += 1

        # Allegati
        att_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.att_label = Gtk.Label(label=_("Allegati: nessuno"))
        self.att_label.set_xalign(0.0)
        self.att_label.set_ellipsize(3)
        att_row.pack_start(self.att_label, True, True, 0)
        att_row.pack_start(self._button(_("📎 Allega…"), self.on_attach), False, False, 0)
        att_row.pack_start(self._button(_("✕ Togli allegati"), self.on_clear_attachments), False, False, 0)
        grid.attach(att_row, 0, row, 3, 1)
        row += 1

        # Azioni
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status = Gtk.Label(label=self._book_status())
        self.status.set_xalign(0.0)
        self.status.get_style_context().add_class("status")
        actions.pack_start(self.status, True, True, 0)
        actions.pack_start(self._button(_("Svuota"), self.on_clear), False, False, 0)
        self.mail_client, self.tb_cmd = default_mail_client()
        send = self._button(_("⚡ Prepara in {0}").format(self.mail_client), self.on_send)
        send.set_tooltip_text(_("Apre la bozza nel programma di posta predefinito (Ctrl+Invio)"))
        send.get_style_context().add_class("suggested-action")
        actions.pack_start(send, False, False, 0)
        grid.attach(actions, 0, row, 3, 1)

        paned.pack2(self._build_book_panel(), resize=False, shrink=False)
        self.connect("delete-event", self.on_close)
        self.connect("key-press-event", self.on_key)
        self.show_all()
        (self.to_entry if self.from_combo.get_active() == 0 else self.from_combo.get_child()).grab_focus()

    # --- piccoli aiuti grafici ------------------------------------------------
    def _css(self):
        css = b"""
        .field-label { font-weight: bold; }
        .status { opacity: 0.75; font-size: 9pt; }
        .body { font-size: 11pt; }
        """
        prov = Gtk.CssProvider()
        prov.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    @staticmethod
    def _label(text):
        lb = Gtk.Label(label=text)
        lb.set_xalign(1.0)
        lb.get_style_context().add_class("field-label")
        return lb

    @staticmethod
    def _button(text, cb):
        b = Gtk.Button(label=text)
        b.connect("clicked", cb)
        return b

    @staticmethod
    def _small_button(text, tip, cb):
        b = Gtk.Button(label=text)
        b.set_tooltip_text(tip)
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.connect("clicked", cb)
        return b

    def _book_status(self):
        if self.book:
            return _("I tuoi indirizzi (Email Picker): {0} — pulsante 📧").format(len(self.book))
        if self.book_path:
            return _("Rubrica Email Picker non leggibile")
        return _("Rubrica Email Picker non trovata")

    # --- completamento automatico ---------------------------------------------
    def _all_addresses(self, only_book=False):
        """[(testo mostrato, indirizzo)] senza doppioni."""
        seen, rows = set(), []
        if only_book:   # Mittente: i tuoi indirizzi (salvati + Email Picker)
            sources = [("", "", a) for a in self.cfg.get("senders", [])] + list(self.book)
        else:           # A / Cc: solo destinatari
            sources = [("", "", a) for a in self.cfg.get("recipients", [])]
        for tab, name, mail in sources:
            if mail.lower() in seen:
                continue
            seen.add(mail.lower())
            shown = f"{name} <{mail}>" if name else mail
            if tab:
                shown += f"   · {tab}"
            rows.append((shown, mail))
        return rows

    def _attach_completion(self, entry, only_book=False):
        store = Gtk.ListStore(str, str)
        for shown, mail in self._all_addresses(only_book):
            store.append([shown, mail])
        comp = Gtk.EntryCompletion()
        comp.set_model(store)
        comp.set_text_column(0)
        comp.set_minimum_key_length(1)

        def match(_c, key, it):
            # cerca sull'ultimo indirizzo che si sta scrivendo (dopo l'ultima virgola)
            key = entry.get_text().split(",")[-1].strip().lower()
            return bool(key) and key in store[it][0].lower()

        def selected(_c, model, it):
            parts = split_addresses(entry.get_text())
            parts = parts[:-1] + [model[it][1]]
            entry.set_text(", ".join(parts) + (", " if entry is not self.from_combo.get_child() else ""))
            entry.set_position(-1)
            return True

        comp.set_match_func(match)
        comp.connect("match-selected", selected)
        entry.set_completion(comp)

    # --- rubrica sempre visibile (pannello a destra) --------------------------------
    def _build_book_panel(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(8)
        box.set_size_request(340, -1)
        title = Gtk.Label()
        title.set_markup("<b>" + GLib.markup_escape_text(_("📇 Rubrica")) + "</b>")
        title.set_xalign(0.0)
        box.pack_start(title, False, False, 0)
        self.book_search = Gtk.SearchEntry()
        self.book_search.set_placeholder_text(_("Cerca nome o email…"))
        box.pack_start(self.book_search, False, False, 0)
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_shadow_type(Gtk.ShadowType.IN)
        self.book_list = Gtk.ListBox()
        self.book_list.set_selection_mode(Gtk.SelectionMode.NONE)
        sc.add(self.book_list)
        box.pack_start(sc, True, True, 0)
        hint = Gtk.Label(label=_("«A» e «Cc» aggiungono l'indirizzo al campo.\nI tuoi indirizzi stanno in 📧, accanto al Mittente."))
        hint.set_xalign(0.0)
        hint.get_style_context().add_class("status")
        box.pack_start(hint, False, False, 0)
        self.book_list.set_filter_func(self._book_filter)
        self.book_search.connect("search-changed", lambda _s: self.book_list.invalidate_filter())
        self._fill_book()
        return box

    def _book_filter(self, row):
        q = self.book_search.get_text().strip().lower()
        return not q or (row.search and q in row.search)

    def _fill_book(self):
        for child in self.book_list.get_children():
            self.book_list.remove(child)
        groups = {}
        for addr in self.cfg.get("recipients", []):
            groups.setdefault("Destinatari usati", []).append(("", addr))
        if not groups:
            r = Gtk.ListBoxRow()
            r.search = ""
            empty = Gtk.Label(label=_("Nessun destinatario ancora: scrivine uno in «A»,\nverrà ricordato al primo invio."))
            empty.set_line_wrap(True)
            empty.set_max_width_chars(28)
            empty.set_xalign(0.0)
            r.add(empty)
            self.book_list.add(r)
        for group, items in groups.items():
            head = Gtk.ListBoxRow()
            head.set_activatable(False)
            hl = Gtk.Label()
            hl.set_markup(f"<b>{GLib.markup_escape_text(_(group))}</b>")
            hl.set_xalign(0.0)
            hl.set_margin_top(6)
            head.add(hl)
            head.search = ""
            self.book_list.add(head)
            for name, mail in items:
                r = Gtk.ListBoxRow()
                r.search = f"{name} {mail} {group}".lower()
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                lab = Gtk.Label()
                lab.set_xalign(0.0)
                lab.set_ellipsize(3)
                if name:
                    lab.set_markup(f"{GLib.markup_escape_text(name)}\n"
                                   f"<small>{GLib.markup_escape_text(mail)}</small>")
                else:
                    lab.set_text(mail)
                lab.set_tooltip_text(mail)
                hb.pack_start(lab, True, True, 4)
                for label, entry in (("A", self.to_entry), ("Cc", self.cc_entry)):
                    b = Gtk.Button(label=_(label))
                    b.set_relief(Gtk.ReliefStyle.NONE)
                    b.set_tooltip_text(_("Aggiungi a «{0}»").format(_(label)))
                    b.connect("clicked", lambda _b, m=mail, e=entry: self._add_address(e, m))
                    hb.pack_start(b, False, False, 0)
                if group == "Destinatari usati":
                    d = Gtk.Button(label="🗑")
                    d.set_relief(Gtk.ReliefStyle.NONE)
                    d.set_tooltip_text(_("Togli questo indirizzo dai destinatari usati"))
                    d.connect("clicked", lambda _b, m=mail: self._forget_recipient(m))
                    hb.pack_start(d, False, False, 0)
                r.add(hb)
                self.book_list.add(r)
        self.book_list.show_all()

    def _forget_recipient(self, mail):
        self.cfg["recipients"] = [a for a in self.cfg.get("recipients", []) if a != mail]
        save_config(self.cfg)
        self._fill_book()
        self._attach_completion(self.to_entry)
        self._attach_completion(self.cc_entry)
        self.status.set_text(_("Tolto dai destinatari usati: {0}").format(mail))

    def _add_address(self, entry, mail):
        parts = split_addresses(entry.get_text())
        if mail not in parts:
            parts.append(mail)
        entry.set_text(", ".join(parts))
        self.status.set_text(_("Aggiunto: {0}").format(mail))

    # --- rubrica in finestra (pulsanti 📇) ---------------------------------------
    def open_book(self, target_entry):
        dlg = Gtk.Dialog(title=_("Rubrica"), transient_for=self, flags=0)
        dlg.add_button(_("Chiudi"), Gtk.ResponseType.CLOSE)
        dlg.set_default_size(460, 480)
        box = dlg.get_content_area()
        box.set_spacing(6)
        box.set_border_width(8)
        search = Gtk.SearchEntry()
        search.set_placeholder_text(_("Cerca nome o email…"))
        box.pack_start(search, False, False, 0)
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        lst = Gtk.ListBox()
        sc.add(lst)
        box.pack_start(sc, True, True, 0)

        groups = {}
        for addr in self.cfg.get("recipients", []):
            groups.setdefault(_("Usati di recente"), []).append(("", addr))
        for tab, name, mail in self.book:
            groups.setdefault(tab or "Email Picker", []).append((name, mail))

        for group, items in groups.items():
            head = Gtk.ListBoxRow()
            head.set_activatable(False)
            head.set_selectable(False)
            hl = Gtk.Label()
            hl.set_markup(f"<b>{GLib.markup_escape_text(group)}</b>")
            hl.set_xalign(0.0)
            head.add(hl)
            head.search = ""
            lst.add(head)
            for name, mail in items:
                r = Gtk.ListBoxRow()
                r.mail = mail
                r.search = f"{name} {mail} {group}".lower()
                l = Gtk.Label(label=f"   {name} <{mail}>" if name else f"   {mail}")
                l.set_xalign(0.0)
                r.add(l)
                lst.add(r)

        def flt(row):
            q = search.get_text().strip().lower()
            return not q or (row.search and q in row.search)
        lst.set_filter_func(flt)
        search.connect("search-changed", lambda _s: lst.invalidate_filter())

        def activated(_l, row):
            mail = getattr(row, "mail", None)
            if mail:
                parts = split_addresses(target_entry.get_text())
                if mail not in parts:
                    parts.append(mail)
                target_entry.set_text(", ".join(parts))
                dlg.response(Gtk.ResponseType.CLOSE)
        lst.connect("row-activated", activated)
        dlg.show_all()
        dlg.run()
        dlg.destroy()

    # --- azioni ----------------------------------------------------------------
    def _set_sender(self, mail):
        self.from_combo.get_child().set_text(mail)
        self.status.set_text(_("Mittente: {0}").format(mail))

    def on_pick_sender(self, button):
        """I tuoi indirizzi (Email Picker), divisi per sezione: un clic = Mittente."""
        pop = Gtk.Popover.new(button)
        pop.set_position(Gtk.PositionType.BOTTOM)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(8)
        pop.add(box)
        search = Gtk.SearchEntry()
        search.set_placeholder_text(_("Cerca tra i tuoi indirizzi…"))
        box.pack_start(search, False, False, 0)
        sc = Gtk.ScrolledWindow()
        sc.set_size_request(380, 420)
        lst = Gtk.ListBox()
        sc.add(lst)
        box.pack_start(sc, True, True, 0)
        current = None
        for tab, name, mail in self.book:
            if tab != current:
                current = tab
                head = Gtk.ListBoxRow()
                head.set_activatable(False)
                head.search = ""
                hl = Gtk.Label()
                hl.set_markup(f"<b>{GLib.markup_escape_text(tab or 'Email Picker')}</b>")
                hl.set_xalign(0.0)
                hl.set_margin_top(6)
                head.add(hl)
                lst.add(head)
            r = Gtk.ListBoxRow()
            r.mail = mail
            r.search = f"{name} {mail} {tab}".lower()
            lab = Gtk.Label(label=f"   {name} <{mail}>" if name else f"   {mail}")
            lab.set_xalign(0.0)
            r.add(lab)
            lst.add(r)
        if not self.book:
            r = Gtk.ListBoxRow()
            r.search = ""
            r.add(Gtk.Label(label=_("Email Picker non trovato o vuoto.")))
            lst.add(r)

        def flt(row):
            q = search.get_text().strip().lower()
            return not q or bool(row.search and q in row.search)
        lst.set_filter_func(flt)
        search.connect("search-changed", lambda _s: lst.invalidate_filter())

        def activated(_l, row):
            mail = getattr(row, "mail", None)
            if mail:
                self._set_sender(mail)
                pop.popdown()
        lst.connect("row-activated", activated)

        def open_app(_b):
            self.status.set_text(_("Email Picker aperto.") if launch_email_picker()
                                 else _("Email Picker non trovato."))
            pop.popdown()
        open_btn = Gtk.Button(label=_("📧 Apri l'app Email Picker"))
        open_btn.connect("clicked", open_app)
        box.pack_start(open_btn, False, False, 0)
        box.show_all()
        pop.popup()

    def on_save_sender(self, _b):
        """Salva l'indirizzo del Mittente in una sezione di Email Picker (e in Lampo Mail)."""
        mail = self.from_combo.get_child().get_text().strip()
        if "@" not in mail:
            self.status.set_text(_("⚠️ Scrivi prima un indirizzo valido nel Mittente."))
            return
        path = email_picker_path(self.cfg)
        tabs = email_picker_tabs(path) if path else []
        if not tabs:
            remember(self.cfg, "senders", mail)
            save_config(self.cfg)
            self.status.set_text(_("Email Picker non trovato: salvato solo in Lampo Mail."))
            return
        dlg = Gtk.Dialog(title=_("Salva in Email Picker"), transient_for=self, flags=0)
        dlg.add_button(_("Annulla"), Gtk.ResponseType.CANCEL)
        dlg.add_button(_("💾 Salva"), Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        g = Gtk.Grid(column_spacing=8, row_spacing=8)
        g.set_border_width(12)
        dlg.get_content_area().add(g)
        g.attach(self._label(_("Indirizzo")), 0, 0, 1, 1)
        g.attach(Gtk.Label(label=mail, xalign=0.0), 1, 0, 1, 1)
        g.attach(self._label(_("Sezione")), 0, 1, 1, 1)
        combo = Gtk.ComboBoxText()
        for tid, label in tabs:
            combo.append(tid, label)
        combo.set_active(0)
        g.attach(combo, 1, 1, 1, 1)
        g.attach(self._label(_("Nome")), 0, 2, 1, 1)
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text(_("facoltativo, es. «Banca» o «Newsletter»"))
        name_entry.set_activates_default(True)
        g.attach(name_entry, 1, 2, 1, 1)
        dlg.show_all()
        resp = dlg.run()
        tab_id, name = combo.get_active_id(), name_entry.get_text().strip()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK:
            return
        ok, msg = add_to_email_picker(path, tab_id, name, mail)
        remember(self.cfg, "senders", mail)
        save_config(self.cfg)
        if ok:
            self.book, self.book_path = load_email_picker(self.cfg)
            self._attach_completion(self.from_combo.get_child(), only_book=True)
        self.status.set_text(("✔ " if ok else "⚠️ ") + msg)

    def on_forget_sender(self, _b):
        addr = self.from_combo.get_child().get_text().strip()
        self.cfg["senders"] = [s for s in self.cfg.get("senders", []) if s != addr]
        save_config(self.cfg)
        self.from_combo.remove_all()
        for s in self.cfg["senders"]:
            self.from_combo.append_text(s)
        self.from_combo.get_child().set_text("")
        self.status.set_text(_("Mittente tolto dall'elenco."))

    def on_attach(self, _b):
        dlg = Gtk.FileChooserDialog(title=_("Allega file"), parent=self,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(_("Annulla"), Gtk.ResponseType.CANCEL, _("Allega"), Gtk.ResponseType.OK)
        dlg.set_select_multiple(True)
        if dlg.run() == Gtk.ResponseType.OK:
            for p in dlg.get_filenames():
                if p not in self.attachments:
                    self.attachments.append(p)
        dlg.destroy()
        self._update_att_label()

    def on_clear_attachments(self, _b):
        self.attachments = []
        self._update_att_label()

    def _update_att_label(self):
        if not self.attachments:
            self.att_label.set_text(_("Allegati: nessuno"))
            self.att_label.set_tooltip_text(None)
            return
        names = ", ".join(os.path.basename(p) for p in self.attachments)
        self.att_label.set_text(_("Allegati ({0}): {1}").format(len(self.attachments), names))
        self.att_label.set_tooltip_text("\n".join(self.attachments))

    def on_clear(self, _b):
        self.to_entry.set_text("")
        self.cc_entry.set_text("")
        self.subject_entry.set_text("")
        self.body_view.get_buffer().set_text("")
        self.attachments = []
        self._update_att_label()

    def on_key(self, _w, ev):
        # Ctrl+Invio = prepara la bozza
        if ev.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and ev.state & Gdk.ModifierType.CONTROL_MASK:
            self.on_send(None)
            return True
        return False

    def on_send(self, _b):
        sender = self.from_combo.get_child().get_text().strip()
        to = split_addresses(self.to_entry.get_text())
        cc = split_addresses(self.cc_entry.get_text())
        subject = self.subject_entry.get_text().strip()
        buf = self.body_view.get_buffer()
        body = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

        if not to:
            self.status.set_text(_("⚠️ Manca il destinatario."))
            self.to_entry.grab_focus()
            return

        remember(self.cfg, "senders", sender)
        for a in to + cc:
            remember(self.cfg, "recipients", a)
        save_config(self.cfg)
        self._fill_book()

        # il predefinito si rilegge a ogni invio: se lo cambi, Lampo Mail ti segue
        self.mail_client, self.tb_cmd = default_mail_client()
        try:
            if self.tb_cmd:
                subprocess.Popen(self.tb_cmd + ["-compose", thunderbird_compose_arg(
                    to, cc, subject, body, sender, self.attachments)], start_new_session=True)
                self.status.set_text(_("✔ Bozza aperta in {0}.").format(self.mail_client))
            else:
                cmd = ["xdg-email", "--subject", subject, "--body", body]
                for a in cc:
                    cmd += ["--cc", a]
                for p in self.attachments:
                    cmd += ["--attach", p]
                subprocess.Popen(cmd + to, start_new_session=True)
                msg = _("✔ Bozza aperta in {0}.").format(self.mail_client)
                if sender:
                    msg += _(" Il mittente sceglilo lì (questo programma non lo riceve da fuori).")
                self.status.set_text(msg)
        except OSError as e:
            self.status.set_text(_("⚠️ Non riesco ad aprire il programma di posta: {0}").format(e))

    def on_close(self, *_a):
        w, h = self.get_size()
        self.cfg["window"] = {"w": w, "h": h}
        save_config(self.cfg)
        Gtk.main_quit()
        return False


def thunderbird_compose_arg(to, cc, subject, body, sender, attachments):
    """Costruisce l'argomento di `thunderbird -compose`.
    I valori vanno tra apici singoli; un apice dentro il testo diventa ’ (tipografico)."""
    def q(v):
        return "'" + v.replace("'", "’") + "'"
    parts = [f"to={q(','.join(to))}"]
    if cc:
        parts.append(f"cc={q(','.join(cc))}")
    if subject:
        parts.append(f"subject={q(subject)}")
    if body:
        parts.append(f"body={q(body)}")
    if sender:
        parts.append(f"from={q(sender)}")
    if attachments:
        urls = ",".join("file://" + urllib.parse.quote(os.path.abspath(p)) for p in attachments)
        parts.append(f"attachment={q(urls)}")
    return ",".join(parts)


def main():
    LampoMail()
    Gtk.main()


if __name__ == "__main__":
    main()
