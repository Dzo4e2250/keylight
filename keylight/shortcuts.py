"""
Global keyboard shortcut handler for KeyLight.
Uses D-Bus to register global shortcuts.
"""

import ast
import subprocess
from typing import Optional
from pathlib import Path

from .controller import KeyboardBacklightController
from .config import Config


class ShortcutManager:
    """Manages keyboard shortcuts for color cycling."""

    def __init__(self, controller: KeyboardBacklightController, config: Config):
        self.controller = controller
        self.config = config
        self.current_color_index = 0

    def cycle_colors(self):
        """Cycle through configured colors."""
        colors = self.config.cycle_colors
        if not colors:
            return

        self.current_color_index = (self.current_color_index + 1) % len(colors)
        color = colors[self.current_color_index]
        self.controller.set_color_hex(color)
        self.config.current_color = color

        # Turn on if off
        if self.controller.brightness == 0:
            self.controller.brightness = self.config.brightness or 255

    def toggle_backlight(self):
        """Toggle backlight on/off."""
        self.controller.toggle()


def create_shortcut_script(config: Config) -> Path:
    """Create a script that can be bound to a keyboard shortcut."""
    script_path = Path.home() / ".local" / "bin" / "keylight-cycle"
    script_path.parent.mkdir(parents=True, exist_ok=True)

    script_content = '''#!/usr/bin/env python3
"""KeyLight color cycle script - bind this to a keyboard shortcut."""

import sys
sys.path.insert(0, "{app_path}")

from keylight.controller import KeyboardBacklightController
from keylight.config import Config

def main():
    controller = KeyboardBacklightController()
    config = Config()

    if not controller.available:
        print("Keyboard backlight not available")
        return 1

    # Get cycle colors
    colors = config.cycle_colors
    current = controller.get_color_hex().upper()

    # Find current color index
    colors_upper = [c.upper().lstrip('#') for c in colors]
    current_clean = current.lstrip('#')

    try:
        idx = colors_upper.index(current_clean)
        next_idx = (idx + 1) % len(colors)
    except ValueError:
        next_idx = 0

    # Set new color
    new_color = colors[next_idx]
    controller.set_color_hex(new_color)
    config.current_color = new_color

    # Turn on if off
    if controller.brightness == 0:
        controller.brightness = config.brightness or 255

    print(f"Color: {{new_color}}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''.format(app_path=str(Path(__file__).parent.parent.absolute()))

    script_path.write_text(script_content)
    script_path.chmod(0o755)
    return script_path


def create_toggle_script(config: Config) -> Path:
    """Create a script to toggle backlight on/off."""
    script_path = Path.home() / ".local" / "bin" / "keylight-toggle"
    script_path.parent.mkdir(parents=True, exist_ok=True)

    script_content = '''#!/usr/bin/env python3
"""KeyLight toggle script - bind this to a keyboard shortcut."""

import sys
sys.path.insert(0, "{app_path}")

from keylight.controller import KeyboardBacklightController
from keylight.config import Config

def main():
    controller = KeyboardBacklightController()
    config = Config()

    if not controller.available:
        print("Keyboard backlight not available")
        return 1

    if controller.brightness > 0:
        controller.brightness = 0
        print("Backlight OFF")
    else:
        controller.brightness = config.brightness or 255
        print("Backlight ON")

    return 0

if __name__ == "__main__":
    sys.exit(main())
'''.format(app_path=str(Path(__file__).parent.parent.absolute()))

    script_path.write_text(script_content)
    script_path.chmod(0o755)
    return script_path


def setup_gnome_shortcut(script_path: Path, shortcut: str = "<Super>space"):
    """
    Set up a GNOME keyboard shortcut.
    Note: This creates a custom shortcut in GNOME settings.
    """
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            capture_output=True, text=True
        )
        current = result.stdout.strip()

        # Create new keybinding path
        binding_path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/keylight-cycle/"

        # Set the binding properties
        base = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
        schema_path = f"{base}:{binding_path}"

        subprocess.run(["gsettings", "set", schema_path, "name", "KeyLight Cycle Colors"], check=True)
        subprocess.run(["gsettings", "set", schema_path, "command", str(script_path)], check=True)
        subprocess.run(["gsettings", "set", schema_path, "binding", shortcut], check=True)

        # Add to list of custom keybindings if not present
        if binding_path not in current:
            if current == "@as []" or current == "[]":
                new_bindings = f"['{binding_path}']"
            else:
                # Parse existing using ast.literal_eval (safe for literals)
                try:
                    bindings = ast.literal_eval(current) if current.startswith('[') else []
                except (ValueError, SyntaxError):
                    bindings = []
                if binding_path not in bindings:
                    bindings.append(binding_path)
                new_bindings = str(bindings)

            subprocess.run([
                "gsettings", "set",
                "org.gnome.settings-daemon.plugins.media-keys",
                "custom-keybindings", new_bindings
            ], check=True)

        return True
    except Exception as e:
        print(f"Failed to set GNOME shortcut: {e}")
        return False


def get_shortcut_instructions() -> str:
    """Return instructions for setting up keyboard shortcuts."""
    return """
To set up keyboard shortcuts for KeyLight:

GNOME/Ubuntu:
1. Open Settings > Keyboard > Keyboard Shortcuts
2. Scroll down and click "Custom Shortcuts"
3. Click "+" to add a new shortcut
4. Name: "KeyLight Cycle Colors"
5. Command: ~/.local/bin/keylight-cycle
6. Set your preferred shortcut (e.g., Super+Space)

KDE Plasma:
1. Open System Settings > Shortcuts > Custom Shortcuts
2. Click "Edit" > "New" > "Global Shortcut" > "Command/URL"
3. Name it "KeyLight Cycle"
4. Set Trigger to your preferred key combo
5. Set Action to: ~/.local/bin/keylight-cycle

XFCE:
1. Open Settings > Keyboard > Application Shortcuts
2. Click "Add"
3. Command: ~/.local/bin/keylight-cycle
4. Press your preferred shortcut

Alternative - using xbindkeys:
1. Install xbindkeys: sudo apt install xbindkeys
2. Create ~/.xbindkeysrc with:
   "~/.local/bin/keylight-cycle"
     Mod4 + space
3. Run: xbindkeys

The scripts are located at:
- ~/.local/bin/keylight-cycle  (cycle through colors)
- ~/.local/bin/keylight-toggle (toggle on/off)
"""
