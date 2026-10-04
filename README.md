# RPi Large Accessibility Clock

A lightweight, fullscreen, high-contrast digital clock designed for Raspberry Pi. Specifically built for users with impaired vision or elderly individuals who need an ultra-clear, massive display visible from across a room.

## Features
- **Maximum Readability:** Pure pitch-black background (`#000000`) with vibrant, high-contrast red font (`#FF0000`) or customizable color presets (Amber, Yellow, Green, White, Cyan).
- **Edge-to-Edge Auto Scaling:** Calculates screen resolution dynamically and renders text as big as the display allows.
- **Customizable Display Elements:** Toggle **Hours**, **Minutes**, and **Seconds** on/off.
  - *Tip:* Disabling seconds makes the hours & minutes up to **60% larger**, ideal for low-vision readability!
- **12h / 24h Modes:** Toggle between 24-hour (`14:30`) and 12-hour (`02:30 PM`) format.
- **Time Offsets:** Customize and adjust hour, minute, and second offsets (+/-) directly in the UI if needed.
- **Stay Awake / Prevent Screen Sleep:** Built-in toggle to prevent the display from sleeping or blanking.
- **Accessible Settings UI:** Open settings at any time by pressing **`S`**, **right-clicking**, or clicking the **`⚙ Settings`** button.
- **Ultra-lightweight:** Written in pure Python using built-in `Tkinter` (uses negligible CPU and RAM; runs smooth even on a Pi Zero).
- **Auto-starts on Boot:** Runs automatically upon desktop startup.

---

## Quick Installation on Raspberry Pi

1. Clone or copy this repository to your Raspberry Pi (e.g. to `/home/pi/rpi-desktop-clock` or `/home/<user>/rpi-desktop-clock`).
2. Run the installation script:
   ```bash
   cd ~/rpi-desktop-clock
   chmod +x install.sh
   ./install.sh
   ```
3. Test it immediately:
   ```bash
   python3 clock.py
   ```
   - Press <kbd>S</kbd> or right-click to open **Settings**.
   - Press <kbd>q</kbd>, <kbd>Esc</kbd>, or click the **`✕ Exit (Q)`** button at the bottom-right corner to quit.
   - Press <kbd>F11</kbd> to toggle fullscreen.

4. Reboot to test autostart:
   ```bash
   sudo reboot
   ```

---

## Settings UI

You can open the Settings UI at any time:
1. Press <kbd>S</kbd> or <kbd>s</kbd> on the keyboard.
2. **Right-click** anywhere on the clock display.
3. Move the mouse and click the **`⚙ Settings (S)`** button at the bottom-right corner (located right next to the **`✕ Exit (Q)`** button).

### What You Can Customize:
1. **Display Elements:**
   - **Show Hours:** Toggle hours on/off.
   - **Show Minutes:** Toggle minutes on/off.
   - **Show Seconds:** Toggle seconds on/off. *(Disabling seconds expands hours and minutes to fill the entire screen!)*
   - **Format:** Choose between **24-Hour** (e.g. `14:30`) and **12-Hour** (e.g. `02:30 PM`).
2. **Time Offsets:**
   - Adjust Hours (+/- 23)
   - Adjust Minutes (+/- 59)
   - Adjust Seconds (+/- 59)
3. **Display Power & Sleep:**
   - **Prevent screen from turning off / sleeping (Stay Awake):** Keeps your Raspberry Pi monitor continuously illuminated 24/7.
4. **Font Color:**
   - Red (Default `#FF0000`), Amber/Orange, High-Vis Yellow, Pure White, Bright Green, Cyan.

All settings are automatically saved to `config.json` and persist across reboots.
