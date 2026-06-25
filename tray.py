import sys
import os
import threading
import pystray
from PIL import Image, ImageDraw

def _resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def _create_icon():
    # try loading the user's icon first
    for name in ("icon.png", "icon.ico"):
        try:
            img = Image.open(_resource_path(name)).convert("RGBA").resize((64, 64))
            return img
        except Exception:
            pass
    # fallback: draw a simple icon
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill="#7c6fff")
    draw.ellipse((18, 18, 46, 46), fill="#0d0d1a")
    return img

def hide_to_tray(root):
    """Withdraw the window and show a tray icon to restore it."""
    root.withdraw()

    _icon_holder = [None]

    def _show(icon, _):
        icon.stop()
        # Must schedule back onto the Tk main thread
        root.after(0, _restore)

    def _restore():
        root.overrideredirect(True)   # re-apply after any OS interactions
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)

    def _quit(icon, _):
        icon.stop()
        root.after(0, root.destroy)

    icon = pystray.Icon(
        "AutoClicker",
        _create_icon(),
        "AutoClicker",
        menu=pystray.Menu(
            pystray.MenuItem("Show", _show, default=True),
            pystray.MenuItem("Quit", _quit),
        ),
    )
    _icon_holder[0] = icon
    threading.Thread(target=icon.run, daemon=True).start()