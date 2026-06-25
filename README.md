# ⚡ AutoClicker

A lightweight, high-performance auto clicker for Windows with a sleek dark UI, sequence recording, and hotkey support.

---

## Features

- **Single & Double click** modes with drift-corrected timing
- **Clicks per second (CPS)** control from 1 to 100+
- **Sequence recording** — record a series of clicks with positions and delays, then replay them in a loop
- **Left / Right / Middle** mouse button support
- **Customizable hotkey** to toggle clicking on/off without touching the window
- **System tray** support — minimize to tray and restore anytime
- **Borderless dark UI** that stays on top

---

## Requirements

- **Windows** (tested on Windows 10/11)
- **Python 3.8+** — [Download here](https://www.python.org/downloads/)

---

## Quick Start

### Option 1 — Run with the batch file (easiest)

1. Clone or download this repository.
2. Double-click `run.bat`.

That's it. The script will check for Python, install all dependencies automatically, and launch the app.

### Option 2 — Run manually

1. **Clone the repository**

   ```bash
   git clone https://github.com/wkinc/aClicker.git
   cd "WHERE YOU CLONE"
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the app**

   ```bash
   python main.py
   ```

### Option 3 — Build a standalone executable with PyInstaller

This packages the app into a single `.exe` that runs without Python installed — useful for sharing with others.

1. **Install PyInstaller**

   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**

   ```bash
   pyinstaller --onefile --noconsole --hidden-import=keyboard --hidden-import=pynput --hidden-import=pystray --hidden-import=pystray._win32 --hidden-import=PIL main.py
   ```

   | Flag | Purpose |
   |------|---------|
   | `--onefile` | Bundles everything into a single `.exe` |
   | `--noconsole` | Hides the console window when running |
   | `--hidden-import=keyboard` | Ensures the `keyboard` module is included |
   | `--hidden-import=pynput` | Ensures the `pynput` module is included |
   | `--hidden-import=pystray` | Ensures the `pystray` module is included |
   | `--hidden-import=pystray._win32` | Includes the Windows-specific pystray backend |
   | `--hidden-import=PIL` | Ensures Pillow is included for the tray icon |

3. **Find and run the output**

   The compiled executable will be at:

   ```
   dist/main.exe
   ```

   You can rename it and distribute it freely — no Python installation required on the target machine.

> **Note:** Windows Defender or other antivirus software may flag PyInstaller-built executables as suspicious. This is a common false positive with packaged Python apps. If needed, add an exclusion for the `dist/` folder or submit the file to your antivirus vendor for whitelisting. 
>
> This is also the bash line i used to create the exe file. If you are not confident in this bash/pwsh command, you can use your own or the other option.

---

## Dependencies

All dependencies are listed in `requirements.txt` and installed automatically:

| Package     | Purpose                              |
|-------------|--------------------------------------|
| `pyautogui` | Fallback mouse control backend       |
| `pynput`    | Primary mouse control & recording    |
| `pystray`   | System tray icon support             |
| `pillow`    | Image handling for tray icon         |
| `keyboard`  | Global hotkey registration           |

---

## How to Use

### Basic clicking

1. Set your desired **CPS** (clicks per second) using the input field or the preset buttons (1, 10, 20, 50, MAX).
2. Choose your **Click Type** (Single or Double), **Mouse Button** (left, right, middle), and **Mode** (single or sequence).
3. Press **▶ Start Clicking** or use your hotkey (default: `F6`) to toggle clicking on/off.

### Sequence mode

1. Set **Mode** to `sequence` in the Options section.
2. Click **● Record** and perform the clicks you want to record anywhere on screen.
3. Click **■ Stop** when done — the number of recorded steps will be shown.
4. Start the clicker as normal; it will replay your recorded sequence in a loop.

### Hotkey

- The default toggle hotkey is `F6`.
- To change it, type a new key in the **Hotkey** field and click **Apply**.
- Supported key names: `f1`–`f12`, `ctrl+k`, `alt+x`, etc.

### System tray

- Click **─** (the minimize button) or **Hide to tray** at the bottom to send the window to the system tray.
- Double-click or right-click the tray icon and select **Show** to restore the window.
- Select **Quit** from the tray menu to fully exit.

---

## File Structure

```
├── main.py           # UI and application entry point
├── clicker.py        # High-performance click engine
├── recorder.py       # Mouse sequence recorder
├── tray.py           # System tray integration
├── config.py         # Shared runtime state
├── icon.ico          # App icon
├── requirements.txt  # Python dependencies
└── run.bat           # One-click launcher for Windows
```

---

## Notes

- The app uses `pynput` as the primary mouse backend for best performance and falls back to `pyautogui` if it's unavailable.
- Some games or applications running as Administrator may require you to also run this script as Administrator for clicks to register.
- Antivirus software may flag auto clickers — this is a false positive. You can review all source code in this repository.

---

## License

This project is open source. Feel free to use, modify, and distribute it.