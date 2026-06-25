from pynput import mouse
import config
import time

_listener  = None
_last_time = None
_accepting = False

def _on_click(x, y, button, pressed):
    global _last_time
    if not _accepting or not pressed:
        return
    now   = time.perf_counter()
    # delay = gap BEFORE this click (how long user waited before clicking)
    delay = (now - _last_time) if _last_time is not None else 0.0
    _last_time = now
    config.click_sequence.append({"x": x, "y": y, "delay": delay})
    print(f"[recorder] {x}, {y}  delay={delay:.3f}s")

def start_recording():
    global _listener, _last_time, _accepting
    _accepting = False
    config.click_sequence.clear()
    stop_recording()
    _listener = mouse.Listener(on_click=_on_click)
    _listener.start()
    time.sleep(0.15)          # ignore mouseUp from the Record button
    _last_time = time.perf_counter()   # start timing FROM HERE, after guard
    _accepting = True

def stop_recording():
    """Stop listener, then strip the last entry (the Stop-button click itself)."""
    global _listener, _accepting
    _accepting = False
    if _listener:
        _listener.stop()
        _listener = None
    if config.click_sequence:
        config.click_sequence.pop()