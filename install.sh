#!/usr/bin/env bash
# Installation script for RPi Desktop Clock on Raspberry Pi OS

set -e

echo "=== Installing RPi Large Accessibility Clock ==="

# 1. Install Python3 and Tkinter if not installed
echo "[1/4] Ensuring Python3 and Tkinter packages are installed..."
sudo apt-get update
sudo apt-get install -y python3 python3-tk fonts-dejavu-core

# 2. Make clock.py executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/clock.py"

# 3. Setup Autostart via ~/.config/autostart
echo "[2/4] Setting up automatic startup on desktop login..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

DESKTOP_FILE="$AUTOSTART_DIR/rpi-clock.desktop"
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=RPi Large Display Clock
Comment=Fullscreen High Contrast Accessibility Clock
Exec=/usr/bin/python3 $SCRIPT_DIR/clock.py
Terminal=false
StartupNotify=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

# 4. Disable screen sleep/blanking (optional but recommended for a wall/desk clock)
echo "[3/4] Configuring screen to prevent blanking/sleeping..."
# For Wayland (Raspberry Pi OS Bookworm):
if [ -d "$HOME/.config/wayfire.ini" ] || command -v wayfire >/dev/null 2>&1; then
    echo "Wayland detected. Please ensure screen sleep is turned off in Raspberry Pi Configuration -> Display."
fi

# For X11 / lightdm:
if [ -f "/etc/lightdm/lightdm.conf" ]; then
    echo "Disabling X11 blanking in lightdm if needed..."
    sudo sed -i 's/^#xserver-command=X/xserver-command=X -s 0 -dpms/' /etc/lightdm/lightdm.conf 2>/dev/null || true
fi

echo "[4/4] Installation complete!"
echo ""
echo "To test immediately, run:"
echo "    python3 $SCRIPT_DIR/clock.py"
echo ""
echo "Press 'q' or 'Esc' to exit the clock."
echo "On next reboot, it will launch automatically in fullscreen."
