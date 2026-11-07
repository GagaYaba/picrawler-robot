#!/usr/bin/env python3
"""Lance la connexion SSH au robot ; signale d'abord si le robot ne connaît pas le WiFi du PC.

Usage : python picrawler_ssh.py [--host 192.168.1.200] [--user pi]
"""
import argparse
import os

import wifi_check as core

ap = argparse.ArgumentParser()
ap.add_argument("--host", default="192.168.1.200")
ap.add_argument("--user", default="pi")
a = ap.parse_args()

st = core.get_status(a.host, a.user)
if not st["error"] and st["pc"] and st["pc"] not in st["known"]:
    print(f"Le robot ne connaît pas « {st['pc']} ». Procédure d'ajout : python wifi_check.py --tutorial")
os.execvp("ssh", ["ssh", f"{a.user}@{a.host}"])
