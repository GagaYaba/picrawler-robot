#!/usr/bin/env python3
"""Vérifie (en LECTURE SEULE) si le PC et le robot PiCrawler sont sur le même WiFi.

Ne modifie rien sur le Pi : seules des commandes `nmcli ... show` / `list` sont lancées.
Aucun mot de passe WiFi n'est lu, affiché ni stocké.

Usage :
    python wifi_check.py                       # pi@192.168.1.200 par défaut
    python wifi_check.py --host 192.168.1.200 --user pi
    python wifi_check.py --tutorial            # affiche la procédure pour ajouter un nouveau réseau
"""
import argparse
import platform
import shlex
import subprocess
import sys

import wifi_tutorial


def decode(raw, windows_console=False):
    """Décode une sortie de commande sans jamais planter (accents, console Windows)."""
    if windows_console and platform.system() == "Windows":
        try:
            return raw.decode("oem")  # console Windows (cp850 en français)
        except (LookupError, UnicodeDecodeError):
            pass
    return raw.decode("utf-8", errors="replace")


def run(cmd, timeout=15, windows_console=False):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    out = decode(r.stdout if r.returncode == 0 else r.stderr, windows_console).strip()
    return r.returncode, out


def parse_netsh(text):
    """SSID courant depuis `netsh wlan show interfaces` (ignore la ligne BSSID)."""
    for line in text.splitlines():
        key, _, val = line.partition(":")
        if key.strip().lower() == "ssid" and val.strip():
            return val.strip()
    return None


def parse_nmcli_terse(text):
    """Lignes `nmcli -t` -> listes de champs (gère les ':' échappés par '\\:')."""
    rows = []
    for line in text.splitlines():
        fields, cur, esc = [], "", False
        for ch in line:
            if esc:
                cur += ch
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == ":":
                fields.append(cur)
                cur = ""
            else:
                cur += ch
        fields.append(cur)
        rows.append(fields)
    return rows


def pc_ssid():
    system = platform.system()
    if system == "Windows":
        code, out = run(["netsh", "wlan", "show", "interfaces"], windows_console=True)
        return parse_netsh(out) if code == 0 else None
    if system == "Linux":
        code, out = run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
        if code == 0:
            for active, *ssid in parse_nmcli_terse(out):
                if active == "yes":
                    return ":".join(ssid)
    return None


def ssh_read(host, user, remote_cmd):
    return run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
                f"{user}@{host}", remote_cmd])


# Lecture seule côté Pi : renvoie les SSID (pas les noms de profil, qui peuvent différer,
# par ex. « netplan-wlan0-Bbox-10A57558 » pour le WiFi « Bbox-10A57558 »).
REMOTE_LIST = (
    "list() { nmcli -t -f NAME,TYPE connection show $1 | grep ':802-11-wireless$' "
    "| sed 's/:802-11-wireless$//; s/\\\\:/:/g'; }; "
    "list --active | while IFS= read -r n; do "
    "echo \"ACTIVE:$(nmcli -g 802-11-wireless.ssid connection show \"$n\")\"; done; "
    "list | while IFS= read -r n; do "
    "echo \"KNOWN:$(nmcli -g 802-11-wireless.ssid connection show \"$n\")\"; done"
)


def parse_remote_list(text):
    """Texte ACTIVE:/KNOWN: -> (ssid actif ou None, liste des ssid connus sans doublon)."""
    active, known = None, []
    for line in text.splitlines():
        kind, _, ssid = line.partition(":")
        if not ssid:
            continue
        if kind == "ACTIVE" and active is None:
            active = ssid
        elif kind == "KNOWN" and ssid not in known:
            known.append(ssid)
    return active, known


def get_status(host, user):
    """Retourne {pc, robot, known, error}. Lecture seule."""
    st = {"pc": pc_ssid(), "robot": None, "known": [], "error": None}
    code, out = ssh_read(host, user, "bash -c " + shlex.quote(REMOTE_LIST))
    if code != 0:
        st["error"] = out or "pas de réponse"
        return st
    st["robot"], st["known"] = parse_remote_list(out)
    return st


def verdict(st):
    """Résumé de get_status : unreachable, pc_unknown, ok ou different."""
    if st["error"]:
        return "unreachable"
    if not st["pc"]:
        return "pc_unknown"
    return "ok" if st["pc"] in st["known"] else "different"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="192.168.1.200")
    ap.add_argument("--user", default="pi")
    ap.add_argument("--tutorial", action="store_true",
                    help="affiche la procédure pour ajouter un nouveau réseau (n'exécute rien)")
    args = ap.parse_args()

    if args.tutorial:
        print(wifi_tutorial.as_text())
        return 0

    st = get_status(args.host, args.user)
    mine, known = st["pc"], st["known"]
    print(f"WiFi du PC     : {mine or 'inconnu / non connecté en WiFi'}")
    if st["error"]:
        print(f"Robot ({args.user}@{args.host}) : injoignable en SSH -> {st['error']}")
        print("\nCauses probables : PC et robot pas sur le même réseau, IP différente, "
              "ou isolation entre appareils (réseau public/hôtel/école).")
        return 2
    print(f"WiFi du robot  : {st['robot'] or 'pas de WiFi actif (câble ?)'}")
    print(f"Réseaux connus du robot : {', '.join(known) or 'aucun'}")

    if mine and mine in known:
        print(f"\nOK : le robot connaît « {mine} ». Il s'y connectera tout seul s'il est à portée.")
        return 0
    if mine:
        print(f"\nATTENTION : le robot ne connaît PAS « {mine} ». Procédure d'ajout :")
        print("  python wifi_check.py --tutorial")
        return 1
    print("\nImpossible de connaître le WiFi du PC, compare à la main.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
