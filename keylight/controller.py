"""
Keyboard backlight hardware controller.
Interfaces with /sys/class/leds/rgb:kbd_backlight
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional


class KeyboardBacklightController:
    """Controls the keyboard backlight via sysfs interface."""

    LED_PATH = Path("/sys/class/leds/rgb:kbd_backlight")

    def __init__(self):
        self._check_available()

    def _check_available(self) -> bool:
        """Check if keyboard backlight is available."""
        self.available = self.LED_PATH.exists()
        return self.available

    def _read_file(self, filename: str) -> Optional[str]:
        """Read a sysfs file."""
        try:
            return (self.LED_PATH / filename).read_text().strip()
        except (PermissionError, FileNotFoundError, IOError):
            return None

    def _write_file(self, filename: str, value: str) -> bool:
        """Write to a sysfs file."""
        filepath = self.LED_PATH / filename
        try:
            filepath.write_text(value)
            return True
        except (PermissionError, IOError):
            # Try with pkexec for permission elevation
            try:
                subprocess.run(
                    ["pkexec", "tee", str(filepath)],
                    input=value.encode(),
                    capture_output=True,
                    check=True
                )
                return True
            except subprocess.CalledProcessError:
                return False

    @property
    def max_brightness(self) -> int:
        """Get maximum brightness value."""
        val = self._read_file("max_brightness")
        return int(val) if val else 255

    @property
    def brightness(self) -> int:
        """Get current brightness."""
        val = self._read_file("brightness")
        return int(val) if val else 0

    @brightness.setter
    def brightness(self, value: int):
        """Set brightness (0-255)."""
        value = max(0, min(self.max_brightness, value))
        self._write_file("brightness", str(value))

    @property
    def color(self) -> Tuple[int, int, int]:
        """Get current RGB color."""
        val = self._read_file("multi_intensity")
        if val:
            parts = val.split()
            if len(parts) >= 3:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
        return (255, 255, 255)

    @color.setter
    def color(self, rgb: Tuple[int, int, int]):
        """Set RGB color."""
        r, g, b = rgb
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self._write_file("multi_intensity", f"{r} {g} {b}")

    def set_color_hex(self, hex_color: str):
        """Set color from hex string (e.g., '#FF0000' or 'FF0000')."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            self.color = (r, g, b)

    def get_color_hex(self) -> str:
        """Get current color as hex string."""
        r, g, b = self.color
        return f"#{r:02X}{g:02X}{b:02X}"

    def turn_on(self, brightness: int = 255):
        """Turn on the backlight."""
        self.brightness = brightness

    def turn_off(self):
        """Turn off the backlight."""
        self.brightness = 0

    def toggle(self) -> bool:
        """Toggle backlight on/off. Returns new state (True=on)."""
        if self.brightness > 0:
            self.turn_off()
            return False
        else:
            self.turn_on()
            return True

    def cycle_color(self, colors: list) -> int:
        """Cycle through a list of colors. Returns new color index."""
        current = self.get_color_hex().upper()
        colors_upper = [c.upper().lstrip('#') for c in colors]
        current_clean = current.lstrip('#')

        try:
            idx = colors_upper.index(current_clean)
            next_idx = (idx + 1) % len(colors)
        except ValueError:
            next_idx = 0

        self.set_color_hex(colors[next_idx])
        return next_idx
