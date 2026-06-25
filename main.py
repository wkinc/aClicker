import tkinter as tk
from tkinter import font as tkfont
import threading
import keyboard
import time

import sys
import os

import config
from clicker import BACKEND, _click, _double_click, _move, _sleep
import recorder
import tray

def resource_path(name: str) -> str:
    """Return correct path for a bundled file whether frozen or running from source."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

# ── palette ───────────────────────────────────────────────────────────────────
BG       = "#0d0d1a"
PANEL    = "#16162a"
CARD     = "#1e1e36"
BORDER   = "#2a2a48"
ACCENT   = "#7c6fff"
TEXT     = "#e8e8f4"
SUBTEXT  = "#7070a0"
GREEN    = "#3ddc84"
RED      = "#ff5f7e"
ENTRY_BG = "#0a0a18"
TITLEBAR = "#0a0a14"

def _blend(c1: str, c2: str, t: float) -> str:
    """Blend hex c1→c2 by t (0=c1, 1=c2)."""
    r = lambda s, i: int(s[i:i+2], 16)
    nr = int(r(c1,1) + (r(c2,1)-r(c1,1))*t)
    ng = int(r(c1,3) + (r(c2,3)-r(c1,3))*t)
    nb = int(r(c1,5) + (r(c2,5)-r(c1,5))*t)
    return f"#{nr:02x}{ng:02x}{nb:02x}"

def _dim(color: str, pct: float) -> str:
    return _blend(BG, color, pct)


class AutoClickerApp:
    def __init__(self, root: tk.Tk):
        self.root          = root
        self._drag_x       = 0
        self._drag_y       = 0
        self._hotkey_ref   = None
        self._click_count  = 0
        self._cps_ts       = time.perf_counter()
        self._live_cps     = 0.0
        self._recording    = False

        self._setup_window()
        self._build_ui()
        self._apply_hotkey()
        self._tick()

    # ── borderless window ─────────────────────────────────────────────────────
    def _setup_window(self):
        r = self.root
        r.overrideredirect(True)          # remove OS title bar
        r.configure(bg=BG)
        r.geometry("420x600")
        r.resizable(False, False)
        # center on screen
        r.update_idletasks()
        sw = r.winfo_screenwidth()
        sh = r.winfo_screenheight()
        x  = (sw - 420) // 2
        y  = (sh - 600) // 2
        r.geometry(f"420x600+{x}+{y}")
        # keep on top optional — comment out if unwanted
        r.attributes("-topmost", True)
        # set window/taskbar icon
        try:
            r.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        try:
            _img = tk.PhotoImage(file=resource_path("icon.png"))
            r.iconphoto(True, _img)
        except Exception:
            pass

    # ── fonts ─────────────────────────────────────────────────────────────────
    def _f(self, size, weight="normal", fam="Segoe UI"):
        return tkfont.Font(family=fam, size=size, weight=weight)

    # ── drag support ──────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag_move(self, e):
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        x  = self.root.winfo_x() + dx
        y  = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # ── full UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        r = self.root

        # ── custom title bar
        tbar = tk.Frame(r, bg=TITLEBAR, height=40)
        tbar.pack(fill="x")
        tbar.pack_propagate(False)
        tbar.bind("<ButtonPress-1>",   self._drag_start)
        tbar.bind("<B1-Motion>",       self._drag_move)

        tk.Label(tbar, text="⚡", bg=TITLEBAR, fg=ACCENT,
                 font=self._f(13)).pack(side="left", padx=(14,4), pady=8)
        tk.Label(tbar, text="AutoClicker", bg=TITLEBAR, fg=TEXT,
                 font=self._f(11, "bold")).pack(side="left", pady=8)
        tk.Label(tbar, text=f"· {BACKEND}", bg=TITLEBAR, fg=SUBTEXT,
                 font=self._f(8)).pack(side="left", pady=8, padx=4)

        # window controls — ✕ rightmost, then ─
        def _close():
            config.running = False
            r.destroy()
        def _minimize():
            self._show_toast("Minimized to system tray", "Click the tray icon to restore")
            r.after(600, lambda: tray.hide_to_tray(r))

        for sym, cmd, col in [("✕", _close, RED), ("─", _minimize, SUBTEXT)]:
            b = tk.Label(tbar, text=sym, bg=TITLEBAR, fg=col,
                         font=self._f(11), cursor="hand2", padx=10)
            b.pack(side="right")
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>",    lambda e, w=b, c=col: w.config(bg=_dim(c, 0.25)))
            b.bind("<Leave>",    lambda e, w=b: w.config(bg=TITLEBAR))

        # thin accent line under title bar
        tk.Frame(r, bg=ACCENT, height=2).pack(fill="x")

        # ── scrollable body
        body = tk.Frame(r, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=12)

        # ── live CPS card
        self._build_cps_card(body)

        # ── speed section
        self._build_speed_section(body)

        # ── options row
        self._build_options_section(body)

        # ── hotkey section
        self._build_hotkey_section(body)

        # ── recording section
        self._build_record_section(body)

        # ── main toggle button
        self._toggle_btn = tk.Button(
            body, text="▶   Start Clicking",
            bg=ACCENT, fg="#ffffff",
            relief="flat", font=self._f(12, "bold"),
            cursor="hand2", bd=0, pady=13,
            activebackground=_dim(ACCENT, 0.75),
            activeforeground="#fff",
            command=self.toggle
        )
        self._toggle_btn.pack(fill="x", pady=(14, 0))

        # ── bottom bar
        bot = tk.Frame(body, bg=BG)
        bot.pack(fill="x", pady=(6, 0))
        self._status = tk.Label(bot, text="Idle", bg=BG, fg=SUBTEXT,
                                font=self._f(8))
        self._status.pack(side="left")
        tk.Label(bot, text="·", bg=BG, fg=BORDER,
                 font=self._f(8)).pack(side="left", padx=4)
        def _hide():
            self._show_toast("Minimized to system tray", "Click the tray icon to restore")
            r.after(600, lambda: tray.hide_to_tray(r))
        tk.Button(bot, text="Hide to tray", bg=BG, fg=SUBTEXT,
                  relief="flat", font=self._f(8), cursor="hand2",
                  activebackground=BG, activeforeground=TEXT, bd=0,
                  command=_hide).pack(side="left")

    # ── toast notification ───────────────────────────────────────────────────
    def _show_toast(self, title: str, body: str, duration: int = 2500):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 280, 64
        x = sw - w - 20
        y = sh - h - 48

        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.geometry(f"{w}x{h}+{x}+{y}")
        toast.configure(bg=CARD)

        # border frame
        border = tk.Frame(toast, bg=ACCENT, padx=1, pady=1)
        border.pack(fill="both", expand=True)
        inner = tk.Frame(border, bg=CARD)
        inner.pack(fill="both", expand=True)

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="both", expand=True, padx=12, pady=8)

        tk.Label(row, text="⚡", bg=CARD, fg=ACCENT,
                 font=self._f(14)).pack(side="left", padx=(0, 8))

        text_col = tk.Frame(row, bg=CARD)
        text_col.pack(side="left", fill="both")
        tk.Label(text_col, text=title, bg=CARD, fg=TEXT,
                 font=self._f(9, "bold"), anchor="w").pack(anchor="w")
        tk.Label(text_col, text=body, bg=CARD, fg=SUBTEXT,
                 font=self._f(8), anchor="w").pack(anchor="w")

        def _fade(alpha=1.0):
            if alpha <= 0:
                toast.destroy()
                return
            try:
                toast.attributes("-alpha", alpha)
                toast.after(30, lambda: _fade(alpha - 0.05))
            except Exception:
                pass

        toast.after(duration, lambda: _fade(1.0))

    # ── section builders ──────────────────────────────────────────────────────
    def _card(self, parent, pady=(0, 10)) -> tk.Frame:
        f = tk.Frame(parent, bg=CARD,
                     highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill="x", pady=pady)
        return f

    def _label(self, parent, text, size=9, fg=None, weight="normal", **kw):
        return tk.Label(parent, text=text, bg=parent["bg"],
                        fg=fg or SUBTEXT, font=self._f(size, weight), **kw)

    def _build_cps_card(self, body):
        card = self._card(body, pady=(0, 12))
        inner = tk.Frame(card, bg=CARD)
        inner.pack(pady=14)
        self._cps_big = tk.Label(inner, text="0.0", bg=CARD, fg=ACCENT,
                                 font=self._f(40, "bold", "Consolas"))
        self._cps_big.pack()
        self._label(inner, "clicks / second", size=8).pack()

    def _build_speed_section(self, body):
        self._label(body, "SPEED", size=7, weight="bold").pack(anchor="w", pady=(0,3))
        card = self._card(body)
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=12, pady=10)

        self._label(inner, "Target CPS", size=8).pack(anchor="w")

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x", pady=(4, 0))

        self._cps_var = tk.StringVar(value="10")
        tk.Entry(row, textvariable=self._cps_var,
                 bg=ENTRY_BG, fg=TEXT, insertbackground=ACCENT,
                 relief="flat", font=self._f(14, "bold", "Consolas"),
                 width=5, justify="center",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT).pack(side="left")

        pf = tk.Frame(row, bg=CARD)
        pf.pack(side="left", padx=(10,0))
        for lbl, val in [("1",1),("10",10),("20",20),("50",50),("MAX",100)]:
            self._pill_btn(pf, lbl, lambda v=val: self._cps_var.set(str(v))
                          ).pack(side="left", padx=2)

    def _build_options_section(self, body):
        self._label(body, "OPTIONS", size=7, weight="bold").pack(anchor="w", pady=(0,3))
        card = self._card(body)
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=12, pady=10)

        self._click_type_var   = tk.StringVar(value="Single")
        self._mouse_button_var = tk.StringVar(value="left")
        self._mode_var         = tk.StringVar(value="single")

        self._dropdown(row, "Click Type",  self._click_type_var,
                       ["Single","Double"]).pack(side="left", padx=(0,16))
        self._dropdown(row, "Button",      self._mouse_button_var,
                       ["left","right","middle"]).pack(side="left", padx=(0,16))
        self._dropdown(row, "Mode",        self._mode_var,
                       ["single","sequence"]).pack(side="left")

    def _build_hotkey_section(self, body):
        self._label(body, "HOTKEY", size=7, weight="bold").pack(anchor="w", pady=(0,3))
        card = self._card(body)
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=12, pady=10)

        self._label(row, "Toggle key", size=8).pack(side="left")

        self._hotkey_var = tk.StringVar(value="f6")
        tk.Entry(row, textvariable=self._hotkey_var,
                 bg=ENTRY_BG, fg=ACCENT, insertbackground=ACCENT,
                 relief="flat", font=self._f(10, "bold", "Consolas"),
                 width=7, justify="center",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT).pack(side="left", padx=8)

        self._pill_btn(row, "Apply", self._apply_hotkey,
                       color=ACCENT).pack(side="left")

    def _build_record_section(self, body):
        self._label(body, "SEQUENCE RECORDING", size=7, weight="bold").pack(anchor="w", pady=(0,3))
        card = self._card(body)
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=12, pady=10)

        self._rec_btn = tk.Button(
            row, text="● Record",
            bg=_dim(RED, 0.2), fg=RED,
            relief="flat", font=self._f(9, "bold"),
            cursor="hand2", bd=0, padx=12, pady=5,
            activebackground=_dim(RED, 0.35), activeforeground=RED,
            command=self._start_record
        )
        self._rec_btn.pack(side="left", padx=(0,6))

        self._stop_rec_btn = tk.Button(
            row, text="■ Stop",
            bg=_dim(SUBTEXT, 0.15), fg=SUBTEXT,
            relief="flat", font=self._f(9),
            cursor="hand2", bd=0, padx=12, pady=5,
            activebackground=_dim(SUBTEXT, 0.25), activeforeground=TEXT,
            command=self._stop_record
        )
        self._stop_rec_btn.pack(side="left", padx=(0,8))

        self._seq_lbl = self._label(row, "0 steps", size=8)
        self._seq_lbl.pack(side="left")

    # ── widget helpers ────────────────────────────────────────────────────────
    def _pill_btn(self, parent, text, cmd, color=ACCENT) -> tk.Button:
        return tk.Button(parent, text=text,
                         bg=_dim(color, 0.2), fg=color,
                         relief="flat", font=self._f(8), cursor="hand2",
                         activebackground=_dim(color, 0.35), activeforeground=color,
                         bd=0, padx=7, pady=3, command=cmd)

    def _dropdown(self, parent, label, var, values) -> tk.Frame:
        f = tk.Frame(parent, bg=CARD)
        self._label(f, label, size=7).pack(anchor="w")
        m = tk.OptionMenu(f, var, *values)
        m.config(bg=ENTRY_BG, fg=TEXT, relief="flat",
                 font=self._f(9), highlightthickness=0,
                 activebackground=_dim(ACCENT, 0.3), activeforeground=TEXT,
                 indicatoron=True, bd=0, padx=6, pady=3, cursor="hand2")
        m["menu"].config(bg=ENTRY_BG, fg=TEXT, activebackground=ACCENT,
                         activeforeground="#fff", relief="flat", bd=0)
        m.pack(anchor="w")
        return f

    # ── logic ─────────────────────────────────────────────────────────────────
    def _read_settings(self):
        try:    config.cps = float(self._cps_var.get())
        except: config.cps = 10.0
        config.click_type   = self._click_type_var.get()
        config.mouse_button = self._mouse_button_var.get()
        config.mode         = self._mode_var.get()

    def toggle(self):
        (self._stop if config.running else self._start)()

    def _start(self):
        self._read_settings()
        config.running    = True
        self._click_count = 0
        self._cps_ts      = time.perf_counter()
        threading.Thread(target=self._click_thread, daemon=True).start()
        self._toggle_btn.config(text="■   Stop Clicking", bg=RED,
                                activebackground=_dim(RED, 0.75))
        self._status.config(text="Running", fg=GREEN)

    def _stop(self):
        config.running = False
        self._toggle_btn.config(text="▶   Start Clicking", bg=ACCENT,
                                activebackground=_dim(ACCENT, 0.75))
        self._status.config(text="Idle", fg=SUBTEXT)
        self._cps_big.config(text="0.0")

    def _click_thread(self):
        while config.running:
            interval = 1.0 / max(config.cps, 0.1)

            if config.mode == "single":
                start = time.perf_counter()
                btn   = config.mouse_button
                if config.click_type == "Single":
                    _click(btn)
                else:
                    _double_click(btn)
                self._click_count += 1
                _sleep(interval - (time.perf_counter() - start))

            else:
                if not config.click_sequence:
                    time.sleep(0.1)
                    continue
                while config.running:
                    for action in config.click_sequence:
                        if not config.running:
                            break
                        _sleep(action["delay"])
                        if not config.running:
                            break
                        _move(action["x"], action["y"])
                        _click(config.mouse_button)
                        self._click_count += 1

    def _tick(self):
        if config.running and self._click_count > 0:
            now     = time.perf_counter()
            elapsed = now - self._cps_ts
            if elapsed >= 0.2:
                self._live_cps    = self._click_count / elapsed
                self._click_count = 0
                self._cps_ts      = now
            self._cps_big.config(text=f"{self._live_cps:.1f}")
        elif not config.running:
            self._cps_big.config(text="0.0")

        # update seq label while recording
        if self._recording:
            self._seq_lbl.config(text=f"{len(config.click_sequence)} steps")

        self.root.after(200, self._tick)

    def _apply_hotkey(self):
        key = self._hotkey_var.get().strip().lower()
        if not key:
            return
        if self._hotkey_ref:
            try: keyboard.remove_hotkey(self._hotkey_ref)
            except: pass
        self._hotkey_ref = keyboard.add_hotkey(key, self.toggle)
        config.hotkey    = key
        self._status.config(text=f"Hotkey: {key}", fg=ACCENT)
        self.root.after(2000, lambda: self._status.config(
            text="Running" if config.running else "Idle",
            fg=GREEN if config.running else SUBTEXT))

    def _start_record(self):
        self._recording = True
        # run in thread so the 0.15 s guard sleep doesn't freeze the UI
        threading.Thread(target=recorder.start_recording, daemon=True).start()
        self._rec_btn.config(bg=RED, fg="#ffffff")
        self._status.config(text="Recording…", fg=RED)
        self._seq_lbl.config(text="0 steps")

    def _stop_record(self):
        self._recording = False
        recorder.stop_recording()
        self._rec_btn.config(bg=_dim(RED, 0.2), fg=RED)
        n = len(config.click_sequence)
        self._seq_lbl.config(text=f"{n} steps")
        self._status.config(text=f"Recorded {n} steps", fg=GREEN)


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()