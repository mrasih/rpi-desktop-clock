#!/usr/bin/env python3
"""
High-Contrast Fullscreen Digital Clock for Raspberry Pi & Windows
Specifically designed for accessibility / visually impaired users:
- Deep black background (#000000)
- High-visibility bright red font (#FF0000) by default with customizable colors
- Auto-scales font size to fill the screen edge-to-edge
- Customizable display: toggle Hours, Minutes, Seconds, and 12h/24h format
- Customizable Time Offsets (hours, minutes, seconds)
- Prevent screen from turning off / sleeping (Stay Awake toggle)
- Persistent JSON configuration
- Accessible Settings UI (Press 'S', Right-Click, or click the gear icon)
"""

import os
import sys
import json
import time
import subprocess
import tkinter as tk
import tkinter.font as tkFont

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "show_hours": True,
    "show_minutes": True,
    "show_seconds": True,
    "use_24hour": True,
    "hour_offset": 0,
    "minute_offset": 0,
    "second_offset": 0,
    "text_color": "#FF0000",
    "bg_color": "#000000",
    "prevent_sleep": True,
    "fullscreen": True,
}

COLOR_PRESETS = [
    ("Bright Red", "#FF0000"),
    ("Amber / Orange", "#FF9900"),
    ("High-Vis Yellow", "#FFFF00"),
    ("Pure White", "#FFFFFF"),
    ("Bright Green", "#00FF66"),
    ("Cyan / Ice Blue", "#00EEFF"),
]


class ScreenManager:
    """Controls screen sleep/blanking prevention across Linux/Raspberry Pi and Windows."""
    def __init__(self, prevent_sleep=True):
        self.prevent_sleep = prevent_sleep
        self.apply(prevent_sleep)

    def apply(self, prevent: bool):
        self.prevent_sleep = prevent
        if sys.platform.startswith("linux"):
            try:
                if prevent:
                    subprocess.run(["xset", "s", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                    subprocess.run(["xset", "-dpms"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                    subprocess.run(["xset", "s", "noblank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                else:
                    subprocess.run(["xset", "s", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                    subprocess.run(["xset", "+dpms"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
        elif sys.platform == "win32":
            try:
                import ctypes
                ES_CONTINUOUS = 0x80000000
                ES_SYSTEM_REQUIRED = 0x00000001
                ES_DISPLAY_REQUIRED = 0x00000002
                if prevent:
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
                else:
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            except Exception:
                pass

    def heartbeat(self):
        """Periodic heartbeat to keep screen awake on Linux X11 systems."""
        if self.prevent_sleep and sys.platform.startswith("linux"):
            try:
                subprocess.run(["xset", "s", "reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass


class LargeDisplayClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessibility Clock")
        
        # 1. Initialize state variables first
        self.settings_window = None
        self.cursor_timer = None
        self.cursor_hidden = False
        self.last_font_size = 100
        
        # 2. Load configuration
        self.config = self.load_config()
        self.screen_manager = ScreenManager(self.config.get("prevent_sleep", True))
        
        # 3. Configure root window
        self.root.configure(bg=self.config["bg_color"])
        self.is_fullscreen = self.config.get("fullscreen", True)
        self.root.attributes("-fullscreen", self.is_fullscreen)
        
        # 4. Bind keyboard and mouse events
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("q", lambda e: self.root.destroy())
        self.root.bind("Q", lambda e: self.root.destroy())
        self.root.bind("s", lambda e: self.open_settings())
        self.root.bind("S", lambda e: self.open_settings())
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Button-3>", lambda e: self.open_settings())  # Right-click
        self.root.bind("<Motion>", self.on_mouse_move)
        
        # 5. Build widgets
        self.main_frame = tk.Frame(self.root, bg=self.config["bg_color"])
        self.main_frame.pack(expand=True, fill="both")
        
        self.time_label = tk.Label(
            self.main_frame,
            text="",
            fg=self.config["text_color"],
            bg=self.config["bg_color"],
            font=("DejaVu Sans", 100, "bold")
        )
        self.time_label.pack(expand=True, fill="both")
        self.time_label.bind("<Button-3>", lambda e: self.open_settings())
        
        # Discreet Settings button in bottom-right corner
        self.gear_btn = tk.Button(
            self.root,
            text="⚙ Settings (S)",
            fg="#777777",
            bg=self.config["bg_color"],
            activeforeground="#FFFFFF",
            activebackground="#222222",
            font=("DejaVu Sans", 11, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.open_settings
        )
        self.gear_btn.place(relx=0.99, rely=0.98, anchor="se")
        self.gear_btn.bind("<Enter>", lambda e: self.gear_btn.configure(fg="#FF4444"))
        self.gear_btn.bind("<Leave>", lambda e: self.gear_btn.configure(fg="#777777"))

        # 6. Apply initial cursor state
        if self.is_fullscreen:
            self.hide_cursor()

        # 7. Start update loops
        self.root.update_idletasks()
        self.resize_font()
        self.update_time()
        self.screen_heartbeat_loop()

    def load_config(self):
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    config.update(saved)
            except Exception as e:
                print(f"Notice: using default settings ({e})")
        return config

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def on_mouse_move(self, event=None):
        """Show cursor on movement, auto-hide in fullscreen after 2.5s of stillness."""
        if self.cursor_hidden:
            try:
                self.root.config(cursor="")
            except Exception:
                pass
            self.cursor_hidden = False
            
        if self.cursor_timer is not None:
            self.root.after_cancel(self.cursor_timer)
            self.cursor_timer = None
            
        if self.is_fullscreen and (self.settings_window is None or not self.settings_window.winfo_exists()):
            self.cursor_timer = self.root.after(2500, self.hide_cursor)

    def hide_cursor(self):
        if self.is_fullscreen and (self.settings_window is None or not self.settings_window.winfo_exists()):
            try:
                self.root.config(cursor="none")
            except Exception:
                pass
            self.cursor_hidden = True

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        self.config["fullscreen"] = self.is_fullscreen
        self.save_config()
        if not self.is_fullscreen:
            try:
                self.root.config(cursor="")
            except Exception:
                pass
            self.cursor_hidden = False
        else:
            self.hide_cursor()
        self.root.after(100, self.resize_font)

    def on_resize(self, event=None):
        self.resize_font()

    def get_template_text(self):
        """Generate representative text pattern to calculate max font size."""
        parts = []
        if self.config["show_hours"]:
            parts.append("00")
        if self.config["show_minutes"]:
            parts.append("00")
        if self.config["show_seconds"]:
            parts.append("00")
            
        if not parts:
            return "--:--"
            
        base = ":".join(parts)
        if not self.config["use_24hour"] and self.config["show_hours"]:
            base += " PM"
        return base

    def resize_font(self):
        """Dynamically compute the maximum fitting font size for current window size."""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        if width <= 10 or height <= 10:
            return

        test_text = self.get_template_text()
        max_w = width * 0.94
        max_h = height * 0.88
        
        available_fonts = tkFont.families()
        font_family = "DejaVu Sans"
        if "DejaVu Sans" not in available_fonts:
            if "FreeSans" in available_fonts:
                font_family = "FreeSans"
            elif "Arial" in available_fonts:
                font_family = "Arial"
            else:
                font_family = "Helvetica"
                
        low = 16
        high = max(50, height)
        best_size = low
        
        while low <= high:
            mid = (low + high) // 2
            test_font = tkFont.Font(family=font_family, size=mid, weight="bold")
            text_w = test_font.measure(test_text)
            text_h = test_font.metrics("linespace")
            
            if text_w <= max_w and text_h <= max_h:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1
                
        self.last_font_size = best_size
        self.time_label.configure(font=(font_family, best_size, "bold"))

    def get_current_time_str(self):
        """Build formatted time string considering offsets and format toggles."""
        offset_seconds = (
            self.config.get("hour_offset", 0) * 3600
            + self.config.get("minute_offset", 0) * 60
            + self.config.get("second_offset", 0)
        )
        curr_epoch = time.time() + offset_seconds
        t = time.localtime(curr_epoch)
        
        parts = []
        if self.config["show_hours"]:
            if self.config["use_24hour"]:
                parts.append(time.strftime("%H", t))
            else:
                parts.append(time.strftime("%I", t))
                
        if self.config["show_minutes"]:
            parts.append(time.strftime("%M", t))
            
        if self.config["show_seconds"]:
            parts.append(time.strftime("%S", t))
            
        if not parts:
            return "--:--"
            
        time_str = ":".join(parts)
        if not self.config["use_24hour"] and self.config["show_hours"]:
            time_str += " " + time.strftime("%p", t)
            
        return time_str

    def update_time(self):
        """Update clock label and schedule next refresh."""
        self.time_label.configure(text=self.get_current_time_str())
        self.root.after(150, self.update_time)

    def screen_heartbeat_loop(self):
        """Periodically refresh screen sleep prevention."""
        self.screen_manager.heartbeat()
        self.root.after(60000, self.screen_heartbeat_loop)

    def apply_settings(self, new_config):
        """Apply changes from settings dialog live."""
        self.config = new_config
        self.save_config()
        
        # Apply visual styles
        self.root.configure(bg=self.config["bg_color"])
        self.main_frame.configure(bg=self.config["bg_color"])
        self.time_label.configure(
            fg=self.config["text_color"],
            bg=self.config["bg_color"]
        )
        self.gear_btn.configure(bg=self.config["bg_color"])
        
        # Apply screen sleep prevention
        self.screen_manager.apply(self.config.get("prevent_sleep", True))
        
        # Recompute font for new text layout
        self.resize_font()

    def open_settings(self):
        """Launch the accessible settings dialog."""
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
            
        try:
            self.root.config(cursor="")
        except Exception:
            pass
        self.cursor_hidden = False
        
        self.settings_window = SettingsDialog(self.root, self.config, self.apply_settings)


class SettingsDialog(tk.Toplevel):
    """Large, high-contrast, accessible Settings window."""
    def __init__(self, parent, current_config, on_save_callback):
        super().__init__(parent)
        self.title("Clock Settings")
        self.on_save = on_save_callback
        self.config = current_config.copy()
        
        # High contrast dialog styling
        self.bg = "#1A1A1A"
        self.fg = "#FFFFFF"
        self.accent = "#FF3333"
        self.card_bg = "#262626"
        
        self.configure(bg=self.bg)
        self.geometry("620x720")
        self.minsize(560, 640)
        self.transient(parent)
        self.grab_set()  # Modal
        
        # Center the dialog on parent screen
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 620
        h = 720
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        # Variables
        self.var_show_hours = tk.BooleanVar(value=self.config["show_hours"])
        self.var_show_minutes = tk.BooleanVar(value=self.config["show_minutes"])
        self.var_show_seconds = tk.BooleanVar(value=self.config["show_seconds"])
        self.var_use_24hour = tk.BooleanVar(value=self.config["use_24hour"])
        
        self.var_hour_offset = tk.IntVar(value=self.config.get("hour_offset", 0))
        self.var_min_offset = tk.IntVar(value=self.config.get("minute_offset", 0))
        self.var_sec_offset = tk.IntVar(value=self.config.get("second_offset", 0))
        
        self.var_prevent_sleep = tk.BooleanVar(value=self.config.get("prevent_sleep", True))
        self.var_color = tk.StringVar(value=self.config.get("text_color", "#FF0000"))
        
        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Label(
            self,
            text="⚙ Clock Settings",
            font=("DejaVu Sans", 18, "bold"),
            fg=self.accent,
            bg=self.bg
        )
        header.pack(pady=(16, 12))
        
        container = tk.Frame(self, bg=self.bg)
        container.pack(fill="both", expand=True, padx=24)
        
        # --- Section 1: Display Elements (Hours, Minutes, Seconds) ---
        f_elements = tk.LabelFrame(
            container,
            text=" Display Elements (Size & Visibility) ",
            font=("DejaVu Sans", 12, "bold"),
            fg="#FF8888",
            bg=self.card_bg,
            padx=16,
            pady=12,
            bd=2
        )
        f_elements.pack(fill="x", pady=6)
        
        tk.Checkbutton(
            f_elements,
            text="Show Hours",
            variable=self.var_show_hours,
            font=("DejaVu Sans", 13, "bold"),
            fg=self.fg,
            bg=self.card_bg,
            selectcolor="#333333",
            activebackground=self.card_bg,
            activeforeground=self.fg
        ).pack(anchor="w", pady=3)
        
        tk.Checkbutton(
            f_elements,
            text="Show Minutes",
            variable=self.var_show_minutes,
            font=("DejaVu Sans", 13, "bold"),
            fg=self.fg,
            bg=self.card_bg,
            selectcolor="#333333",
            activebackground=self.card_bg,
            activeforeground=self.fg
        ).pack(anchor="w", pady=3)
        
        cb_sec = tk.Checkbutton(
            f_elements,
            text="Show Seconds  (Uncheck for 60% bigger digits)",
            variable=self.var_show_seconds,
            font=("DejaVu Sans", 13, "bold"),
            fg=self.fg,
            bg=self.card_bg,
            selectcolor="#333333",
            activebackground=self.card_bg,
            activeforeground=self.fg
        )
        cb_sec.pack(anchor="w", pady=3)
        
        # Format: 24h vs 12h
        f_format = tk.Frame(f_elements, bg=self.card_bg)
        f_format.pack(anchor="w", pady=(8, 2))
        
        tk.Label(
            f_format,
            text="Format: ",
            font=("DejaVu Sans", 12, "bold"),
            fg="#CCCCCC",
            bg=self.card_bg
        ).pack(side="left")
        
        tk.Radiobutton(
            f_format,
            text="24-Hour (14:30)",
            variable=self.var_use_24hour,
            value=True,
            font=("DejaVu Sans", 12),
            fg=self.fg,
            bg=self.card_bg,
            selectcolor="#333333",
            activebackground=self.card_bg,
            activeforeground=self.fg
        ).pack(side="left", padx=10)
        
        tk.Radiobutton(
            f_format,
            text="12-Hour (02:30 PM)",
            variable=self.var_use_24hour,
            value=False,
            font=("DejaVu Sans", 12),
            fg=self.fg,
            bg=self.card_bg,
            selectcolor="#333333",
            activebackground=self.card_bg,
            activeforeground=self.fg
        ).pack(side="left")

        # --- Section 2: Time Customization / Offsets ---
        f_offset = tk.LabelFrame(
            container,
            text=" Customize Time Offsets (Adjust +/-) ",
            font=("DejaVu Sans", 12, "bold"),
            fg="#FF8888",
            bg=self.card_bg,
            padx=16,
            pady=10,
            bd=2
        )
        f_offset.pack(fill="x", pady=6)
        
        self.create_offset_row(f_offset, "Hours Offset:", self.var_hour_offset, -23, 23)
        self.create_offset_row(f_offset, "Minutes Offset:", self.var_min_offset, -59, 59)
        self.create_offset_row(f_offset, "Seconds Offset:", self.var_sec_offset, -59, 59)

        # --- Section 3: Screen Sleep / Power Management ---
        f_sleep = tk.LabelFrame(
            container,
            text=" Display Power & Sleep ",
            font=("DejaVu Sans", 12, "bold"),
            fg="#FF8888",
            bg=self.card_bg,
            padx=16,
            pady=12,
            bd=2
        )
        f_sleep.pack(fill="x", pady=6)
        
        tk.Checkbutton(
            f_sleep,
            text="Prevent screen from turning off / sleeping (Stay Awake)",
            variable=self.var_prevent_sleep,
            font=("DejaVu Sans", 12, "bold"),
            fg="#00FF66",
            bg=self.card_bg,
            selectcolor="#333333",
            activebackground=self.card_bg,
            activeforeground="#00FF66"
        ).pack(anchor="w")
        
        tk.Label(
            f_sleep,
            text="Keeps display continuously on for 24/7 visibility.",
            font=("DejaVu Sans", 9, "italic"),
            fg="#AAAAAA",
            bg=self.card_bg
        ).pack(anchor="w", padx=24, pady=(2, 0))

        # --- Section 4: Font Color Selection ---
        f_color = tk.LabelFrame(
            container,
            text=" Clock Font Color ",
            font=("DejaVu Sans", 12, "bold"),
            fg="#FF8888",
            bg=self.card_bg,
            padx=16,
            pady=10,
            bd=2
        )
        f_color.pack(fill="x", pady=6)
        
        color_btn_frame = tk.Frame(f_color, bg=self.card_bg)
        color_btn_frame.pack(fill="x")
        
        for name, hex_code in COLOR_PRESETS:
            btn = tk.Radiobutton(
                color_btn_frame,
                text=name,
                value=hex_code,
                variable=self.var_color,
                font=("DejaVu Sans", 10, "bold"),
                fg=hex_code,
                bg=self.card_bg,
                selectcolor="#222222",
                activebackground=self.card_bg,
                activeforeground=hex_code
            )
            btn.pack(side="left", padx=4, expand=True)

        # --- Section 5: Action Buttons ---
        btn_box = tk.Frame(self, bg=self.bg)
        btn_box.pack(fill="x", padx=24, pady=16)
        
        save_btn = tk.Button(
            btn_box,
            text="✔ Save & Apply",
            font=("DejaVu Sans", 12, "bold"),
            fg="#FFFFFF",
            bg="#CC0000",
            activeforeground="#FFFFFF",
            activebackground="#FF2222",
            padx=20,
            pady=8,
            relief="raised",
            cursor="hand2",
            command=self.save_and_close
        )
        save_btn.pack(side="right", padx=6)
        
        cancel_btn = tk.Button(
            btn_box,
            text="Cancel",
            font=("DejaVu Sans", 12),
            fg="#DDDDDD",
            bg="#333333",
            activeforeground="#FFFFFF",
            activebackground="#444444",
            padx=16,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=6)
        
        reset_btn = tk.Button(
            btn_box,
            text="↺ Reset Defaults",
            font=("DejaVu Sans", 11),
            fg="#AAAAAA",
            bg="#222222",
            activeforeground="#FFFFFF",
            activebackground="#333333",
            padx=12,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self.reset_defaults
        )
        reset_btn.pack(side="left")

    def create_offset_row(self, parent, label_text, var, min_v, max_v):
        row = tk.Frame(parent, bg=self.card_bg)
        row.pack(fill="x", pady=2)
        
        tk.Label(
            row,
            text=label_text,
            width=16,
            anchor="w",
            font=("DejaVu Sans", 11, "bold"),
            fg=self.fg,
            bg=self.card_bg
        ).pack(side="left")
        
        def dec():
            if var.get() > min_v:
                var.set(var.get() - 1)
        tk.Button(
            row, text=" - ", font=("DejaVu Sans", 10, "bold"),
            bg="#444444", fg="#FFFFFF", width=3, relief="flat", command=dec
        ).pack(side="left", padx=4)
        
        val_lbl = tk.Label(
            row,
            textvariable=var,
            width=5,
            font=("DejaVu Sans", 11, "bold"),
            fg=self.accent,
            bg="#111111",
            relief="sunken"
        )
        val_lbl.pack(side="left", padx=2)
        
        def inc():
            if var.get() < max_v:
                var.set(var.get() + 1)
        tk.Button(
            row, text=" + ", font=("DejaVu Sans", 10, "bold"),
            bg="#444444", fg="#FFFFFF", width=3, relief="flat", command=inc
        ).pack(side="left", padx=4)
        
        def reset():
            var.set(0)
        tk.Button(
            row, text="Reset", font=("DejaVu Sans", 9),
            bg="#262626", fg="#888888", relief="flat", command=reset
        ).pack(side="left", padx=8)

    def reset_defaults(self):
        self.var_show_hours.set(DEFAULT_CONFIG["show_hours"])
        self.var_show_minutes.set(DEFAULT_CONFIG["show_minutes"])
        self.var_show_seconds.set(DEFAULT_CONFIG["show_seconds"])
        self.var_use_24hour.set(DEFAULT_CONFIG["use_24hour"])
        self.var_hour_offset.set(DEFAULT_CONFIG["hour_offset"])
        self.var_min_offset.set(DEFAULT_CONFIG["minute_offset"])
        self.var_sec_offset.set(DEFAULT_CONFIG["second_offset"])
        self.var_prevent_sleep.set(DEFAULT_CONFIG["prevent_sleep"])
        self.var_color.set(DEFAULT_CONFIG["text_color"])

    def save_and_close(self):
        if not (self.var_show_hours.get() or self.var_show_minutes.get() or self.var_show_seconds.get()):
            self.var_show_hours.set(True)
            self.var_show_minutes.set(True)
            
        new_config = {
            "show_hours": self.var_show_hours.get(),
            "show_minutes": self.var_show_minutes.get(),
            "show_seconds": self.var_show_seconds.get(),
            "use_24hour": self.var_use_24hour.get(),
            "hour_offset": self.var_hour_offset.get(),
            "minute_offset": self.var_min_offset.get(),
            "second_offset": self.var_sec_offset.get(),
            "prevent_sleep": self.var_prevent_sleep.get(),
            "text_color": self.var_color.get(),
            "bg_color": self.config.get("bg_color", "#000000"),
            "fullscreen": self.config.get("fullscreen", True)
        }
        
        self.on_save(new_config)
        self.destroy()


def main():
    root = tk.Tk()
    app = LargeDisplayClock(root)
    root.mainloop()


if __name__ == "__main__":
    main()
