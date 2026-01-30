"""
System tray icon for KeyLight.
Allows quick access to color controls without opening the main window.
"""

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
    HAS_INDICATOR = True
except:
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
        HAS_INDICATOR = True
    except:
        HAS_INDICATOR = False

from gi.repository import Gtk, GLib

from .controller import KeyboardBacklightController
from .config import Config


class TrayIcon:
    """System tray icon with quick controls."""

    def __init__(self, app, controller: KeyboardBacklightController, config: Config):
        self.app = app
        self.controller = controller
        self.config = config
        self.indicator = None

        if HAS_INDICATOR:
            self._create_indicator()

    def _create_indicator(self):
        """Create the app indicator."""
        self.indicator = AppIndicator.Indicator.new(
            "keylight",
            "keyboard-brightness-symbolic",
            AppIndicator.IndicatorCategory.HARDWARE
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title("KeyLight")

        # Create menu
        menu = self._create_menu()
        self.indicator.set_menu(menu)

    def _create_menu(self) -> Gtk.Menu:
        """Create the tray menu."""
        menu = Gtk.Menu()

        # Show window
        item_show = Gtk.MenuItem(label="Open KeyLight")
        item_show.connect("activate", self._on_show)
        menu.append(item_show)

        menu.append(Gtk.SeparatorMenuItem())

        # Quick colors submenu
        item_colors = Gtk.MenuItem(label="Quick Colors")
        colors_menu = Gtk.Menu()

        preset_colors = [
            ("White", "#FFFFFF"),
            ("Red", "#FF0000"),
            ("Green", "#00FF00"),
            ("Blue", "#0000FF"),
            ("Yellow", "#FFFF00"),
            ("Cyan", "#00FFFF"),
            ("Magenta", "#FF00FF"),
            ("Orange", "#FF8000"),
        ]

        for name, color in preset_colors:
            item = Gtk.MenuItem(label=name)
            item.connect("activate", self._on_color_select, color)
            colors_menu.append(item)

        item_colors.set_submenu(colors_menu)
        menu.append(item_colors)

        # Brightness submenu
        item_brightness = Gtk.MenuItem(label="Brightness")
        brightness_menu = Gtk.Menu()

        for level in [100, 75, 50, 25, 10]:
            item = Gtk.MenuItem(label=f"{level}%")
            item.connect("activate", self._on_brightness_select, int(level * 2.55))
            brightness_menu.append(item)

        item_brightness.set_submenu(brightness_menu)
        menu.append(item_brightness)

        menu.append(Gtk.SeparatorMenuItem())

        # Toggle on/off
        self.toggle_item = Gtk.MenuItem(label="Turn Off")
        self.toggle_item.connect("activate", self._on_toggle)
        menu.append(self.toggle_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Quit
        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", self._on_quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def _on_show(self, item):
        """Show the main window."""
        if self.app.window:
            self.app.window.present()

    def _on_color_select(self, item, color: str):
        """Handle color selection from tray."""
        self.controller.set_color_hex(color)
        self.config.current_color = color
        if self.controller.brightness == 0:
            self.controller.brightness = self.config.brightness or 255
        self._update_toggle_label()

    def _on_brightness_select(self, item, brightness: int):
        """Handle brightness selection from tray."""
        self.controller.brightness = brightness
        self.config.brightness = brightness
        self._update_toggle_label()

    def _on_toggle(self, item):
        """Toggle backlight on/off."""
        is_on = self.controller.toggle()
        if is_on:
            self.controller.brightness = self.config.brightness or 255
        self._update_toggle_label()

    def _update_toggle_label(self):
        """Update toggle menu item label."""
        is_on = self.controller.brightness > 0
        self.toggle_item.set_label("Turn Off" if is_on else "Turn On")

    def _on_quit(self, item):
        """Quit the application."""
        self.app.quit()
