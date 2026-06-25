"""
clicker.py — high-performance click engine
Uses pynput (preferred) → pyautogui fallback.
Eliminates pyautogui's hidden 0.1 s pause and uses
drift-corrected, hybrid busy-wait timing for accurate CPS.
"""

import time
import config

# ── backend selection ─────────────────────────────────────────────────────────
try:
    from pynput.mouse import Controller as _MC, Button as _Btn
    _mouse = _MC()
    _BTN_MAP = {"left": _Btn.left, "right": _Btn.right, "middle": _Btn.middle}

    def _down(btn="left"):  _mouse.press(_BTN_MAP.get(btn, _Btn.left))
    def _up(btn="left"):    _mouse.release(_BTN_MAP.get(btn, _Btn.left))
    def _move(x, y):        _mouse.position = (x, y)

    BACKEND = "pynput"

except ImportError:
    import pyautogui as _pg
    _pg.PAUSE     = 0
    _pg.FAILSAFE  = True

    def _down(btn="left"):  _pg.mouseDown(button=btn)
    def _up(btn="left"):    _pg.mouseUp(button=btn)
    def _move(x, y):        _pg.moveTo(x, y, duration=0)

    BACKEND = "pyautogui"

print(f"[clicker] backend: {BACKEND}")

# ── precision sleep (OS sleep + busy-spin last 1 ms) ─────────────────────────
def _sleep(secs: float) -> None:
    if secs <= 0:
        return
    deadline = time.perf_counter() + secs
    if secs > 0.001:
        time.sleep(secs - 0.001)
    while time.perf_counter() < deadline:
        pass

# ── click primitives ──────────────────────────────────────────────────────────
_HOLD = 0.004   # 4 ms — enough for any game/app to register

def _click(btn: str) -> None:
    _down(btn)
    _sleep(_HOLD)
    _up(btn)

def _double_click(btn: str) -> None:
    _click(btn)
    _sleep(0.03)
    _click(btn)

# ── public loops ──────────────────────────────────────────────────────────────
def click_loop() -> None:
    while config.running:
        interval = 1.0 / max(config.cps, 0.1)

        if config.mode == "single":
            _do_single(interval)
        else:
            _do_sequence()

def _do_single(interval: float) -> None:
    btn   = config.mouse_button
    start = time.perf_counter()

    if config.click_type == "Single":
        _click(btn)
    else:
        _double_click(btn)

    # drift-corrected: sleep only the time remaining in the interval
    elapsed = time.perf_counter() - start
    _sleep(interval - elapsed)

def _do_sequence() -> None:
    while config.running:
        for action in config.click_sequence:
            if not config.running:
                break
            _sleep(action["delay"])
            if not config.running:
                break
            _move(action["x"], action["y"])
            _click(config.mouse_button)