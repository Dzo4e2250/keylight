#!/usr/bin/env python3
"""
KeyLight - Keyboard Backlight Controller
Main entry point for the application.
"""

import sys
import os

# Add the application directory to path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib

from keylight.controller import KeyboardBacklightController
from keylight.config import Config
from keylight.gui import KeyLightWindow
from keylight.tray import TrayIcon, HAS_INDICATOR
from keylight.shortcuts import create_shortcut_script, create_toggle_script


class KeyLightApplication(Gtk.Application):
    """Main KeyLight application."""

    def __init__(self):
        super().__init__(
            application_id="com.keylight.app",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        self.tray = None
        self.controller = KeyboardBacklightController()
        self.config = Config()

    def do_startup(self):
        """Handle application startup."""
        Gtk.Application.do_startup(self)

        # Create shortcut scripts
        create_shortcut_script(self.config)
        create_toggle_script(self.config)

        # Add application actions
        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

    def do_activate(self):
        """Handle application activation."""
        if not self.window:
            self.window = KeyLightWindow(self)
            self.window.connect("delete-event", self.on_window_delete)

            # Create tray icon if available
            if HAS_INDICATOR:
                self.tray = TrayIcon(self, self.controller, self.config)

        self.window.present()

    def on_window_delete(self, window, event):
        """Handle window close - minimize to tray if available."""
        if HAS_INDICATOR and self.tray:
            window.hide()
            return True  # Prevent destruction
        return False

    def on_quit(self, action, param):
        """Quit the application."""
        self.quit()

    def on_about(self, action, param):
        """Show about dialog."""
        about = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about.set_program_name("KeyLight")
        about.set_version("1.0.0")
        about.set_comments("Keyboard Backlight Controller for Linux")
        about.set_license_type(Gtk.License.MIT_X11)
        about.set_website("https://github.com/keylight")
        about.run()
        about.destroy()


def check_requirements():
    """Check if the system meets requirements."""
    controller = KeyboardBacklightController()

    if not controller.available:
        print("ERROR: Keyboard backlight not detected!")
        print()
        print("Make sure the tuxedo_keyboard module is loaded:")
        print("  sudo modprobe tuxedo_keyboard")
        print()
        print("To make it persistent:")
        print("  echo 'tuxedo_keyboard' | sudo tee /etc/modules-load.d/tuxedo_keyboard.conf")
        return False

    return True


def main():
    """Main entry point."""
    # Check for --help or --version
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print("KeyLight - Keyboard Backlight Controller")
            print()
            print("Usage: keylight [OPTIONS]")
            print()
            print("Options:")
            print("  -h, --help     Show this help message")
            print("  -v, --version  Show version")
            print("  --cycle        Cycle to next color (for shortcuts)")
            print("  --toggle       Toggle backlight on/off")
            print("  --set COLOR    Set color (hex, e.g., #FF0000)")
            print("  --brightness N Set brightness (0-255)")
            return 0

        if sys.argv[1] in ("-v", "--version"):
            print("KeyLight 1.0.0")
            return 0

        # CLI commands
        controller = KeyboardBacklightController()
        config = Config()

        if not controller.available:
            print("Keyboard backlight not available")
            return 1

        if sys.argv[1] == "--cycle":
            colors = config.cycle_colors
            idx = controller.cycle_color(colors)
            print(f"Color: {colors[idx]}")
            return 0

        if sys.argv[1] == "--toggle":
            is_on = controller.toggle()
            if is_on:
                controller.brightness = config.brightness or 255
            print("ON" if is_on else "OFF")
            return 0

        if sys.argv[1] == "--set" and len(sys.argv) > 2:
            color = sys.argv[2]
            controller.set_color_hex(color)
            config.current_color = color
            if controller.brightness == 0:
                controller.brightness = config.brightness or 255
            print(f"Color set to {color}")
            return 0

        if sys.argv[1] == "--brightness" and len(sys.argv) > 2:
            try:
                brightness = int(sys.argv[2])
                controller.brightness = brightness
                config.brightness = brightness
                print(f"Brightness set to {brightness}")
                return 0
            except ValueError:
                print("Invalid brightness value")
                return 1

    # Check requirements
    if not check_requirements():
        return 1

    # Run GUI application
    app = KeyLightApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
