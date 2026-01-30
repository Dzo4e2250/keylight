"""
Keyboard backlight effects and animations.
"""

import threading
import time
import math
from typing import Callable, List, Optional
from .controller import KeyboardBacklightController


class EffectEngine:
    """Manages keyboard backlight effects and animations."""

    def __init__(self, controller: KeyboardBacklightController):
        self.controller = controller
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_effect = "static"
        self._speed = 50  # 0-100
        self._colors: List[str] = []
        self._on_color_change: Optional[Callable] = None

    def set_callback(self, callback: Callable):
        """Set callback for color changes (for UI updates)."""
        self._on_color_change = callback

    def _notify_color_change(self, r: int, g: int, b: int):
        """Notify UI of color change."""
        if self._on_color_change:
            try:
                self._on_color_change(r, g, b)
            except:
                pass

    @property
    def speed(self) -> int:
        return self._speed

    @speed.setter
    def speed(self, value: int):
        self._speed = max(1, min(100, value))

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_effect(self) -> str:
        return self._current_effect

    def stop(self):
        """Stop any running effect."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._current_effect = "static"

    def _get_delay(self) -> float:
        """Calculate delay based on speed setting."""
        # Speed 1 = 0.2s delay, Speed 100 = 0.01s delay
        return 0.2 - (self._speed / 100) * 0.19

    def start_rainbow(self):
        """Start rainbow color cycling effect."""
        self.stop()
        self._current_effect = "rainbow"
        self._running = True
        self._thread = threading.Thread(target=self._rainbow_loop, daemon=True)
        self._thread.start()

    def _rainbow_loop(self):
        """Rainbow effect loop - cycles through HSV hue."""
        hue = 0
        while self._running:
            # Convert HSV to RGB (S=1, V=1)
            r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
            self.controller.color = (r, g, b)
            self._notify_color_change(r, g, b)

            hue = (hue + 2) % 360  # Increment hue
            time.sleep(self._get_delay())

    def start_breathing(self, color: str = None):
        """Start breathing effect (fade in/out)."""
        self.stop()
        self._current_effect = "breathing"
        self._running = True

        if color:
            self._colors = [color]
        elif not self._colors:
            self._colors = [self.controller.get_color_hex()]

        self._thread = threading.Thread(target=self._breathing_loop, daemon=True)
        self._thread.start()

    def _breathing_loop(self):
        """Breathing effect loop."""
        base_color = self._colors[0] if self._colors else "#FFFFFF"
        r, g, b = self._hex_to_rgb(base_color)

        phase = 0
        while self._running:
            # Sine wave for smooth breathing (0 to 1)
            brightness = (math.sin(phase) + 1) / 2

            # Apply brightness to color
            cr = int(r * brightness)
            cg = int(g * brightness)
            cb = int(b * brightness)

            self.controller.color = (cr, cg, cb)
            self._notify_color_change(cr, cg, cb)

            phase += 0.1
            if phase > 2 * math.pi:
                phase = 0

            time.sleep(self._get_delay())

    def start_color_wave(self, colors: List[str] = None):
        """Start color wave effect - cycles through multiple colors."""
        self.stop()
        self._current_effect = "wave"
        self._running = True

        if colors:
            self._colors = colors
        elif not self._colors:
            self._colors = ["#FF0000", "#FF8000", "#FFFF00", "#00FF00",
                           "#00FFFF", "#0000FF", "#8000FF", "#FF00FF"]

        self._thread = threading.Thread(target=self._wave_loop, daemon=True)
        self._thread.start()

    def _wave_loop(self):
        """Color wave effect loop with smooth transitions."""
        colors = [self._hex_to_rgb(c) for c in self._colors]
        if not colors:
            return

        color_idx = 0
        transition_progress = 0.0

        while self._running:
            # Get current and next color
            current = colors[color_idx]
            next_color = colors[(color_idx + 1) % len(colors)]

            # Interpolate between colors
            r = int(current[0] + (next_color[0] - current[0]) * transition_progress)
            g = int(current[1] + (next_color[1] - current[1]) * transition_progress)
            b = int(current[2] + (next_color[2] - current[2]) * transition_progress)

            self.controller.color = (r, g, b)
            self._notify_color_change(r, g, b)

            transition_progress += 0.02
            if transition_progress >= 1.0:
                transition_progress = 0.0
                color_idx = (color_idx + 1) % len(colors)

            time.sleep(self._get_delay())

    def start_strobe(self, color: str = None):
        """Start strobe/flash effect."""
        self.stop()
        self._current_effect = "strobe"
        self._running = True

        if color:
            self._colors = [color]
        elif not self._colors:
            self._colors = [self.controller.get_color_hex()]

        self._thread = threading.Thread(target=self._strobe_loop, daemon=True)
        self._thread.start()

    def _strobe_loop(self):
        """Strobe effect loop."""
        base_color = self._colors[0] if self._colors else "#FFFFFF"
        r, g, b = self._hex_to_rgb(base_color)
        on = True

        while self._running:
            if on:
                self.controller.color = (r, g, b)
                self._notify_color_change(r, g, b)
            else:
                self.controller.color = (0, 0, 0)
                self._notify_color_change(0, 0, 0)

            on = not on
            time.sleep(self._get_delay() * 2)

    def start_candle(self):
        """Start candle flicker effect."""
        self.stop()
        self._current_effect = "candle"
        self._running = True
        self._thread = threading.Thread(target=self._candle_loop, daemon=True)
        self._thread.start()

    def _candle_loop(self):
        """Candle flicker effect - warm orange with random flicker."""
        import random

        while self._running:
            # Base warm color (orange/yellow)
            base_r, base_g, base_b = 255, 147, 41

            # Random flicker intensity
            flicker = random.uniform(0.7, 1.0)

            r = int(base_r * flicker)
            g = int(base_g * flicker)
            b = int(base_b * flicker * 0.5)

            self.controller.color = (r, g, b)
            self._notify_color_change(r, g, b)

            # Random delay for natural flicker
            time.sleep(random.uniform(0.05, 0.15))

    def start_police(self):
        """Start police lights effect (red/blue flash)."""
        self.stop()
        self._current_effect = "police"
        self._running = True
        self._thread = threading.Thread(target=self._police_loop, daemon=True)
        self._thread.start()

    def _police_loop(self):
        """Police lights effect loop."""
        colors = [(255, 0, 0), (0, 0, 255)]
        idx = 0
        flash_count = 0

        while self._running:
            r, g, b = colors[idx]
            self.controller.color = (r, g, b)
            self._notify_color_change(r, g, b)
            time.sleep(0.1)

            self.controller.color = (0, 0, 0)
            self._notify_color_change(0, 0, 0)
            time.sleep(0.05)

            flash_count += 1
            if flash_count >= 3:
                flash_count = 0
                idx = (idx + 1) % 2
                time.sleep(0.1)

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> tuple:
        """Convert HSV to RGB (h: 0-360, s: 0-1, v: 0-1)."""
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
