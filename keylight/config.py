"""
Configuration management for KeyLight.
Stores user preferences and custom colors.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = {
        "brightness": 255,
        "current_color": "#FFFFFF",
        "favorite_colors": [
            "#FFFFFF",  # White
            "#FF0000",  # Red
            "#00FF00",  # Green
            "#0000FF",  # Blue
            "#FFFF00",  # Yellow
            "#FF00FF",  # Magenta
            "#00FFFF",  # Cyan
            "#FF8000",  # Orange
            "#8000FF",  # Purple
            "#00FF80",  # Mint
        ],
        "cycle_colors": [
            "#FFFFFF",
            "#FF0000",
            "#00FF00",
            "#0000FF",
            "#FFFF00",
            "#FF00FF",
            "#00FFFF",
        ],
        "shortcut_enabled": True,
        "shortcut_action": "cycle",  # "cycle" or "toggle"
        "start_minimized": False,
        "restore_on_startup": True,
        "show_notifications": True,
    }

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "keylight"
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                self.config = json.loads(self.config_file.read_text())
            else:
                self.config = self.DEFAULT_CONFIG.copy()
                self._save()
        except (json.JSONDecodeError, IOError):
            self.config = self.DEFAULT_CONFIG.copy()

    def _save(self):
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file.write_text(json.dumps(self.config, indent=2))
        except IOError:
            pass

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, self.DEFAULT_CONFIG.get(key, default))

    def set(self, key: str, value):
        """Set a configuration value."""
        self.config[key] = value
        self._save()

    @property
    def brightness(self) -> int:
        return self.get("brightness", 255)

    @brightness.setter
    def brightness(self, value: int):
        self.set("brightness", value)

    @property
    def current_color(self) -> str:
        return self.get("current_color", "#FFFFFF")

    @current_color.setter
    def current_color(self, value: str):
        self.set("current_color", value)

    @property
    def favorite_colors(self) -> List[str]:
        return self.get("favorite_colors", self.DEFAULT_CONFIG["favorite_colors"])

    @favorite_colors.setter
    def favorite_colors(self, colors: List[str]):
        self.set("favorite_colors", colors)

    @property
    def cycle_colors(self) -> List[str]:
        return self.get("cycle_colors", self.DEFAULT_CONFIG["cycle_colors"])

    @cycle_colors.setter
    def cycle_colors(self, colors: List[str]):
        self.set("cycle_colors", colors)

    def add_favorite_color(self, color: str):
        """Add a color to favorites."""
        colors = self.favorite_colors
        if color not in colors:
            colors.append(color)
            self.favorite_colors = colors

    def remove_favorite_color(self, color: str):
        """Remove a color from favorites."""
        colors = self.favorite_colors
        if color in colors:
            colors.remove(color)
            self.favorite_colors = colors
