# Mouse Recorder & Player (Mac Quartz Edition)

This application uses low-level **Quartz** events to control the mouse on macOS, which is much more reliable than standard cross-platform libraries like `pyautogui` or `pynput` for automation on Mac.

## Features
- **Record**: Captures movements, clicks, and scrolling.
- **Playback**: Accurate replay using native macOS Quartz events.
- **Global Hotkey**: **Cmd+Option+T** (Default) to stop any operation instantly, even if the app is in the background. You can customize this hotkey.
- **Robust**: Bypasses many common "silent failure" issues with Python automation on Mac.

## Prerequisites
- macOS
- Python 3

## Installation

1. **Activate Virtual Environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   (Note: `pyobjc-framework-Quartz` is the key dependency here, included via pynput/pyautogui dependencies)

## Usage

1. **Run the App**:
   ```bash
   python3 app.py
   ```

2. **Test Mouse Control**:
   - Click the **"Test Mouse (Quartz)"** button.
   - If the mouse moves to (200, 200) and then (300, 300), permissions are working!
   - If it **does not move**, see the Troubleshooting section below.

3. **Recording & Playback**:
   - Click **Start Recording**, perform actions.
   - Press **Cmd+Option+T** (or your custom hotkey) to STOP recording.
   - Set repetitions and click **Play**.
   - Press **Cmd+Option+T** to STOP playback immediately.

## ⚠️ Troubleshooting Permissions (READ ME)

If the mouse does not move or recording captures 0 events, you have a **macOS Accessibility Permission** issue. Even if it looks "On", it might be broken.

**FIX STEPS:**
1. Go to **System Settings** > **Privacy & Security** > **Accessibility**.
2. Find **Terminal** (or `iTerm`, `VS Code`, `Python`, `Trae`).
3. **⛔️ IMPORTANT**: Do not just toggle it off/on. **Select it and click the minus (-) button to DELETE it.**
4. Run the app again (`python3 app.py`).
5. macOS will prompt you to grant permission. Click **Open System Settings** and toggle it **ON**.
6. Restart the Terminal/App and try again.
