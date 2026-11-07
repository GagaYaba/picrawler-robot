#!/usr/bin/env python3
"""Fenêtre de vérification du réseau du robot PiCrawler, avec tutoriel d'ajout d'un réseau.

Lecture seule : la fenêtre compare le WiFi du PC et celui du robot, et affiche la procédure à suivre
à la main si le réseau est inconnu du robot. Elle n'écrit rien sur le Pi et ne demande aucun mot de passe.

Usage : python wifi_widget.py [--host 192.168.1.200] [--user pi]
"""
import argparse
import queue
import threading
import tkinter as tk

import wifi_check as core
import wifi_tutorial

BG, CARD, BTN = "#151515", "#222220", "#2C2C2A"
TXT, MUTED, WARN, OK = "#F2F0E8", "#A8A59B", "#E8A488", "#8FCB9B"
FONT = "Segoe UI"
W, H = 420, 720


class Pill(tk.Canvas):
    """Zone arrondie ; mettre les widgets dans `.inner`."""

    def __init__(self, parent, height=64, r=28):
        super().__init__(parent, width=W - 36, height=height, bg=BG, highlightthickness=0)
        w = W - 36
        pts = [r, 0, w - r, 0, w, 0, w, r, w, height - r, w, height, w - r, height,
               r, height, 0, height, 0, height - r, 0, r, 0, 0]
        self.create_polygon(pts, smooth=True, fill=CARD, outline=CARD)
        self.inner = tk.Frame(self, bg=CARD)
        self.create_window(w // 2, height // 2, window=self.inner, width=w - 40, height=height - 8)


class App(tk.Tk):
    def __init__(self, host, user):
        super().__init__()
        self.host, self.user = host, user
        self.title("Réseau du robot")
        self.geometry(f"{W}x{H}")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.q = queue.Queue()
        self.status = None
        self.main_frame = tk.Frame(self, bg=BG)
        self.tuto_frame = tk.Frame(self, bg=BG)
        self.build_main()
        self.build_tuto()
        self.show(self.main_frame)
        self.after(100, self.poll)
        self.refresh()

    # ---------- utilitaires ----------
    def show(self, frame):
        for f in (self.main_frame, self.tuto_frame):
            f.pack_forget()
        frame.pack(fill="both", expand=True, padx=18, pady=20)

    def header(self, parent, title, left, right=None):
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x")
        for side, (txt, cmd) in (("left", left), ("right", right or ("", None))):
            if txt:
                tk.Button(bar, text=txt, command=cmd, bg=BTN, fg=TXT, bd=0, relief="flat",
                          activebackground="#3A3A37", activeforeground=TXT,
                          font=(FONT, 14), width=3, height=1).pack(side=side)
            else:
                tk.Frame(bar, width=48, bg=BG).pack(side=side)
        tk.Label(bar, text=title, bg=BG, fg=TXT, font=(FONT, 15, "bold")).pack(expand=True)

    def label(self, parent, text, color=MUTED, size=11, **kw):
        return tk.Label(parent, text=text, bg=BG, fg=color, font=(FONT, size), anchor="w", **kw)

    def line(self, parent, text):
        p = Pill(parent, 56)
        lab = tk.Label(p.inner, text=text, bg=CARD, fg=TXT, font=(FONT, 13), anchor="w")
        lab.pack(fill="both", expand=True)
        return p, lab

    # ---------- écran principal ----------
    def build_main(self):
        f = self.main_frame
        self.header(f, "Réseau du robot", ("✕", self.destroy), ("↻", self.refresh))
        self.label(f, "Ton PC").pack(fill="x", padx=8, pady=(18, 4))
        p, self.pc_lab = self.line(f, "…")
        p.pack()
        self.label(f, f"Robot · {self.host}").pack(fill="x", padx=8, pady=(12, 4))
        p, self.robot_lab = self.line(f, "…")
        p.pack()
        self.msg = tk.Label(f, text="", bg=BG, fg=WARN, font=(FONT, 11), anchor="w",
                            justify="left", wraplength=W - 60)
        self.msg.pack(fill="x", padx=8, pady=(6, 0))
        self.label(f, "Réseaux connus du robot").pack(fill="x", padx=8, pady=(12, 4))
        self.known = tk.Label(f, text="", bg=CARD, fg=TXT, font=(FONT, 13), anchor="nw",
                              justify="left", padx=20, pady=14, wraplength=W - 80)
        self.known.pack(fill="x")
        self.tuto_btn = tk.Button(f, text="Tutoriel : ajouter un nouveau réseau",
                                  command=lambda: self.show(self.tuto_frame),
                                  bg=CARD, fg=TXT, bd=0, relief="flat", anchor="w", padx=20,
                                  activebackground="#2C2C2A", activeforeground=TXT,
                                  font=(FONT, 13, "bold"), height=2)
        self.tuto_btn.pack(side="bottom", fill="x")

    def refresh(self):
        self.msg.config(text="Lecture du robot…", fg=MUTED)
        threading.Thread(target=self.read_status, daemon=True).start()

    def read_status(self):
        try:
            st = core.get_status(self.host, self.user)
        except Exception as e:  # ne jamais laisser la fenêtre bloquée sur « Lecture… »
            st = {"pc": None, "robot": None, "known": [], "error": f"erreur interne : {e}"}
        self.q.put(("status", st))

    def apply_status(self, st):
        self.status = st
        mine = st["pc"]
        self.pc_lab.config(text=mine or "inconnu")
        if st["error"]:
            self.robot_lab.config(text="injoignable")
            self.known.config(text="—")
            detail = (st["error"] or "").splitlines()[-1][:120] if st["error"] else ""
            self.msg.config(fg=WARN, text="Le robot ne répond pas en SSH. Vérifie qu'il est allumé et sur le "
                            "même réseau que ton PC (ou isolation entre appareils sur un WiFi public)."
                            + (f"\nDétail : {detail}" if detail else ""))
            return
        self.robot_lab.config(text=st["robot"] or "pas de WiFi actif")
        self.known.config(text="\n".join(st["known"]) or "aucun")
        v = core.verdict(st)
        if v == "ok":
            self.msg.config(fg=OK, text=f"Le robot connaît « {mine} ». Rien à faire.")
        elif v == "different":
            self.msg.config(fg=WARN, text=f"Le robot ne connaît pas « {mine} ». "
                            "Voir le tutoriel pour l'ajouter.")
        else:
            self.msg.config(fg=WARN, text="WiFi du PC inconnu : comparer à la main avec celui du robot.")

    # ---------- écran tutoriel ----------
    def build_tuto(self):
        f = self.tuto_frame
        self.header(f, "Nouveau réseau", ("←", lambda: self.show(self.main_frame)))
        box = tk.Frame(f, bg=BG)
        box.pack(fill="both", expand=True, pady=(12, 0))
        bar = tk.Scrollbar(box)
        bar.pack(side="right", fill="y")
        txt = tk.Text(box, bg=BG, fg=TXT, bd=0, highlightthickness=0, wrap="word", cursor="arrow",
                      font=(FONT, 11), yscrollcommand=bar.set, padx=6)
        txt.pack(side="left", fill="both", expand=True)
        bar.config(command=txt.yview)
        txt.tag_config("title", font=(FONT, 12, "bold"), spacing1=12, spacing3=2)
        txt.tag_config("body", foreground=MUTED, spacing3=4)
        txt.tag_config("cmd", font=("Consolas", 10), background=CARD, lmargin1=8, lmargin2=8,
                       rmargin=8, spacing1=2, spacing3=2)
        for step in wifi_tutorial.STEPS:
            txt.insert("end", step["title"] + "\n", "title")
            txt.insert("end", step["text"] + "\n", "body")
            for cmd in step["commands"]:
                txt.insert("end", cmd + "\n", "cmd")
                btn = tk.Button(txt, text="Copier", command=lambda c=cmd: self.copy(c), bg=BTN, fg=TXT,
                                bd=0, relief="flat", font=(FONT, 9), activebackground="#3A3A37",
                                activeforeground=TXT)
                txt.window_create("end", window=btn)
                txt.insert("end", "\n")
        txt.insert("end", "\n" + wifi_tutorial.LIMITS + "\n", "body")
        txt.config(state="disabled")

    def copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def poll(self):
        try:
            while True:
                _, data = self.q.get_nowait()
                self.apply_status(data)
        except queue.Empty:
            pass
        self.after(100, self.poll)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.1.200")
    ap.add_argument("--user", default="pi")
    a = ap.parse_args()
    App(a.host, a.user).mainloop()
