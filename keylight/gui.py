"""
GTK3 GUI for KeyLight application.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
import cairo

from .controller import KeyboardBacklightController
from .config import Config
from .effects import EffectEngine


class ColorButton(Gtk.Button):
    """A button that displays and sets a color."""

    def __init__(self, color: str, size: int = 40):
        super().__init__()
        self.color = color
        self.set_size_request(size, size)
        self._update_style()

    def _update_style(self):
        """Update button appearance."""
        css = f"""
        button {{
            background: {self.color};
            border-radius: 8px;
            border: 2px solid rgba(255,255,255,0.3);
            min-width: 40px;
            min-height: 40px;
        }}
        button:hover {{
            border: 2px solid white;
            box-shadow: 0 0 10px {self.color};
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        self.get_style_context().add_provider(
            provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def set_color(self, color: str):
        """Update the button color."""
        self.color = color
        self._update_style()


class KeyLightWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, app):
        super().__init__(application=app, title="KeyLight")
        self.app = app
        self.controller = KeyboardBacklightController()
        self.config = Config()
        self.effects = EffectEngine(self.controller)
        self.effects.set_callback(self._on_effect_color_change)

        self.set_default_size(420, 700)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Apply dark theme
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        # Apply custom CSS
        self._apply_css()

        # Build UI
        self._build_ui()

        # Load saved state
        self._restore_state()

        # Show all widgets
        self.show_all()

    def _apply_css(self):
        """Apply custom CSS styling."""
        css = """
        window {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        }
        .title-label {
            font-size: 24px;
            font-weight: bold;
            color: white;
        }
        .section-label {
            font-size: 14px;
            font-weight: bold;
            color: #888;
            margin-top: 10px;
        }
        .color-preview {
            border-radius: 12px;
            border: 3px solid rgba(255,255,255,0.2);
        }
        scale {
            margin: 10px 0;
        }
        scale trough {
            background: #333;
            border-radius: 5px;
        }
        scale highlight {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
        }
        button.toggle-btn {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-size: 14px;
            font-weight: bold;
            color: white;
        }
        button.toggle-btn:hover {
            background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
        }
        button.off {
            background: linear-gradient(180deg, #434343 0%, #000000 100%);
        }
        .info-label {
            color: #666;
            font-size: 11px;
        }
        button.effect-btn {
            background: #2a2a3e;
            border: 1px solid #444;
            border-radius: 8px;
            color: #aaa;
            font-size: 12px;
        }
        button.effect-btn:hover {
            background: #3a3a4e;
            border-color: #667eea;
            color: white;
        }
        button.effect-active {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
            color: white;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(25)
        main_box.set_margin_end(25)
        self.add(main_box)

        # Title
        title = Gtk.Label(label="KeyLight")
        title.get_style_context().add_class("title-label")
        main_box.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Keyboard Backlight Controller")
        subtitle.set_markup('<span color="#888">Keyboard Backlight Controller</span>')
        main_box.pack_start(subtitle, False, False, 0)

        # Color preview
        self.color_preview = Gtk.DrawingArea()
        self.color_preview.set_size_request(350, 80)
        self.color_preview.get_style_context().add_class("color-preview")
        self.color_preview.connect("draw", self._draw_color_preview)
        main_box.pack_start(self.color_preview, False, False, 10)

        # Brightness section
        brightness_label = Gtk.Label(label="BRIGHTNESS")
        brightness_label.set_halign(Gtk.Align.START)
        brightness_label.get_style_context().add_class("section-label")
        main_box.pack_start(brightness_label, False, False, 0)

        # Brightness slider
        self.brightness_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 255, 1
        )
        self.brightness_scale.set_value(self.controller.brightness)
        self.brightness_scale.set_draw_value(False)
        self.brightness_scale.connect("value-changed", self._on_brightness_changed)
        main_box.pack_start(self.brightness_scale, False, False, 0)

        # Brightness percentage label
        self.brightness_label = Gtk.Label()
        self.brightness_label.set_halign(Gtk.Align.END)
        self._update_brightness_label()
        main_box.pack_start(self.brightness_label, False, False, 0)

        # Colors section
        colors_label = Gtk.Label(label="PRESET COLORS")
        colors_label.set_halign(Gtk.Align.START)
        colors_label.get_style_context().add_class("section-label")
        main_box.pack_start(colors_label, False, False, 5)

        # Color grid
        color_grid = Gtk.FlowBox()
        color_grid.set_max_children_per_line(5)
        color_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        color_grid.set_homogeneous(True)
        color_grid.set_row_spacing(10)
        color_grid.set_column_spacing(10)

        for color in self.config.favorite_colors:
            btn = ColorButton(color)
            btn.connect("clicked", self._on_color_clicked, color)
            color_grid.add(btn)

        main_box.pack_start(color_grid, False, False, 5)

        # Custom color section
        custom_label = Gtk.Label(label="CUSTOM COLOR")
        custom_label.set_halign(Gtk.Align.START)
        custom_label.get_style_context().add_class("section-label")
        main_box.pack_start(custom_label, False, False, 5)

        # Color chooser button
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.color_button = Gtk.ColorButton()
        current_color = Gdk.RGBA()
        current_color.parse(self.controller.get_color_hex())
        self.color_button.set_rgba(current_color)
        self.color_button.set_use_alpha(False)
        self.color_button.connect("color-set", self._on_custom_color_set)
        self.color_button.set_size_request(200, 40)
        color_box.pack_start(self.color_button, True, True, 0)

        # Add to favorites button
        add_fav_btn = Gtk.Button(label="+ Add to Favorites")
        add_fav_btn.connect("clicked", self._on_add_favorite)
        color_box.pack_start(add_fav_btn, False, False, 0)

        main_box.pack_start(color_box, False, False, 5)

        # Effects section
        effects_label = Gtk.Label(label="EFFECTS")
        effects_label.set_halign(Gtk.Align.START)
        effects_label.get_style_context().add_class("section-label")
        main_box.pack_start(effects_label, False, False, 5)

        # Effect buttons grid
        effects_grid = Gtk.Grid()
        effects_grid.set_row_spacing(8)
        effects_grid.set_column_spacing(8)

        effect_buttons = [
            ("Static", "static", 0, 0),
            ("Rainbow", "rainbow", 1, 0),
            ("Breathing", "breathing", 2, 0),
            ("Wave", "wave", 0, 1),
            ("Strobe", "strobe", 1, 1),
            ("Candle", "candle", 2, 1),
            ("Police", "police", 0, 2),
        ]

        self.effect_buttons = {}
        for label, effect_id, col, row in effect_buttons:
            btn = Gtk.Button(label=label)
            btn.set_size_request(90, 35)
            btn.connect("clicked", self._on_effect_clicked, effect_id)
            btn.get_style_context().add_class("effect-btn")
            effects_grid.attach(btn, col, row, 1, 1)
            self.effect_buttons[effect_id] = btn

        # Highlight static as default
        self.effect_buttons["static"].get_style_context().add_class("effect-active")

        main_box.pack_start(effects_grid, False, False, 5)

        # Speed slider for effects
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        speed_label = Gtk.Label(label="Speed:")
        speed_label.set_markup('<span color="#888">Speed:</span>')
        speed_box.pack_start(speed_label, False, False, 0)

        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        self.speed_scale.set_value(50)
        self.speed_scale.set_draw_value(False)
        self.speed_scale.set_hexpand(True)
        self.speed_scale.connect("value-changed", self._on_speed_changed)
        speed_box.pack_start(self.speed_scale, True, True, 0)

        self.speed_value_label = Gtk.Label(label="50%")
        self.speed_value_label.set_markup('<span color="#888">50%</span>')
        speed_box.pack_start(self.speed_value_label, False, False, 0)

        main_box.pack_start(speed_box, False, False, 5)

        # Toggle button
        self.toggle_btn = Gtk.Button(label="Turn Off")
        self.toggle_btn.get_style_context().add_class("toggle-btn")
        self.toggle_btn.connect("clicked", self._on_toggle_clicked)
        self._update_toggle_button()
        main_box.pack_start(self.toggle_btn, False, False, 15)

        # Shortcut info
        shortcut_info = Gtk.Label()
        shortcut_info.set_markup(
            '<span color="#666" size="small">Tip: Use Fn+Space to cycle colors (after setup)</span>'
        )
        shortcut_info.get_style_context().add_class("info-label")
        main_box.pack_start(shortcut_info, False, False, 5)

    def _draw_color_preview(self, widget, cr):
        """Draw the color preview area."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        # Get current color
        r, g, b = self.controller.color
        brightness = self.controller.brightness / 255.0

        # Apply brightness to color
        r = int(r * brightness) / 255.0
        g = int(g * brightness) / 255.0
        b = int(b * brightness) / 255.0

        # Draw rounded rectangle with gradient
        radius = 12
        cr.new_path()
        cr.arc(width - radius, radius, radius, -1.5708, 0)
        cr.arc(width - radius, height - radius, radius, 0, 1.5708)
        cr.arc(radius, height - radius, radius, 1.5708, 3.1416)
        cr.arc(radius, radius, radius, 3.1416, 4.7124)
        cr.close_path()

        # Create gradient
        pattern = cairo.LinearGradient(0, 0, width, height)
        pattern.add_color_stop_rgb(0, r, g, b)
        pattern.add_color_stop_rgb(1, r * 0.7, g * 0.7, b * 0.7)

        cr.set_source(pattern)
        cr.fill_preserve()

        # Draw border
        cr.set_source_rgba(1, 1, 1, 0.2)
        cr.set_line_width(2)
        cr.stroke()

        # Draw "glow" effect
        if brightness > 0:
            cr.set_source_rgba(r, g, b, 0.3)
            cr.rectangle(0, 0, width, height)
            cr.fill()

    def _update_brightness_label(self):
        """Update the brightness percentage label."""
        brightness = int(self.brightness_scale.get_value())
        percentage = int((brightness / 255) * 100)
        self.brightness_label.set_markup(
            f'<span color="#888">{percentage}%</span>'
        )

    def _update_toggle_button(self):
        """Update toggle button state."""
        is_on = self.controller.brightness > 0
        self.toggle_btn.set_label("Turn Off" if is_on else "Turn On")
        ctx = self.toggle_btn.get_style_context()
        if is_on:
            ctx.remove_class("off")
        else:
            ctx.add_class("off")

    def _on_brightness_changed(self, scale):
        """Handle brightness slider change."""
        value = int(scale.get_value())
        self.controller.brightness = value
        self.config.brightness = value
        self._update_brightness_label()
        self._update_toggle_button()
        self.color_preview.queue_draw()

    def _on_color_clicked(self, button, color):
        """Handle preset color button click."""
        # Stop any running effect and set to static
        self.effects.stop()
        self._set_effect_button_active("static")

        self.controller.set_color_hex(color)
        self.config.current_color = color
        self.color_preview.queue_draw()

        # Update color button
        rgba = Gdk.RGBA()
        rgba.parse(color)
        self.color_button.set_rgba(rgba)

        # Make sure backlight is on
        if self.controller.brightness == 0:
            self.brightness_scale.set_value(self.config.brightness or 255)

    def _set_effect_button_active(self, effect_id):
        """Set which effect button appears active."""
        for eid, btn in self.effect_buttons.items():
            ctx = btn.get_style_context()
            if eid == effect_id:
                ctx.add_class("effect-active")
            else:
                ctx.remove_class("effect-active")

    def _on_custom_color_set(self, button):
        """Handle custom color selection."""
        # Stop any running effect
        self.effects.stop()
        self._set_effect_button_active("static")

        rgba = button.get_rgba()
        r = int(rgba.red * 255)
        g = int(rgba.green * 255)
        b = int(rgba.blue * 255)
        color = f"#{r:02X}{g:02X}{b:02X}"

        self.controller.set_color_hex(color)
        self.config.current_color = color
        self.color_preview.queue_draw()

        # Make sure backlight is on
        if self.controller.brightness == 0:
            self.brightness_scale.set_value(self.config.brightness or 255)

    def _on_add_favorite(self, button):
        """Add current color to favorites."""
        color = self.controller.get_color_hex()
        self.config.add_favorite_color(color)
        # Show notification
        self._show_notification(f"Added {color} to favorites")

    def _on_toggle_clicked(self, button):
        """Toggle backlight on/off."""
        is_on = self.controller.toggle()
        if is_on:
            self.brightness_scale.set_value(self.config.brightness or 255)
        else:
            self.brightness_scale.set_value(0)
        self._update_toggle_button()
        self.color_preview.queue_draw()

    def _on_effect_clicked(self, button, effect_id):
        """Handle effect button click."""
        # Stop any running effect first
        self.effects.stop()

        # Update button styles
        for eid, btn in self.effect_buttons.items():
            ctx = btn.get_style_context()
            if eid == effect_id:
                ctx.add_class("effect-active")
            else:
                ctx.remove_class("effect-active")

        # Start the selected effect
        if effect_id == "static":
            pass  # Just stop, use current color
        elif effect_id == "rainbow":
            self.effects.start_rainbow()
        elif effect_id == "breathing":
            self.effects.start_breathing()
        elif effect_id == "wave":
            self.effects.start_color_wave()
        elif effect_id == "strobe":
            self.effects.start_strobe()
        elif effect_id == "candle":
            self.effects.start_candle()
        elif effect_id == "police":
            self.effects.start_police()

        # Make sure backlight is on
        if self.controller.brightness == 0:
            self.brightness_scale.set_value(self.config.brightness or 255)

    def _on_speed_changed(self, scale):
        """Handle speed slider change."""
        value = int(scale.get_value())
        self.effects.speed = value
        self.speed_value_label.set_markup(f'<span color="#888">{value}%</span>')

    def _on_effect_color_change(self, r, g, b):
        """Called by effect engine when color changes (for UI update)."""
        # Update UI from main thread
        GLib.idle_add(self._update_preview_color, r, g, b)

    def _update_preview_color(self, r, g, b):
        """Update the color preview (called from main thread)."""
        self.color_preview.queue_draw()
        return False  # Don't repeat

    def _restore_state(self):
        """Restore saved state."""
        if self.config.get("restore_on_startup", True):
            color = self.config.current_color
            brightness = self.config.brightness

            self.controller.set_color_hex(color)
            self.controller.brightness = brightness

            self.brightness_scale.set_value(brightness)

            rgba = Gdk.RGBA()
            rgba.parse(color)
            self.color_button.set_rgba(rgba)

            self.color_preview.queue_draw()
            self._update_toggle_button()

    def _show_notification(self, message: str):
        """Show a notification."""
        if self.config.get("show_notifications", True):
            try:
                notification = Gio.Notification.new("KeyLight")
                notification.set_body(message)
                self.app.send_notification(None, notification)
            except:
                pass


class KeyLightApp(Gtk.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id="com.keylight.app",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None

    def do_activate(self):
        """Handle application activation."""
        if not self.window:
            self.window = KeyLightWindow(self)
        self.window.present()

    def do_startup(self):
        """Handle application startup."""
        Gtk.Application.do_startup(self)
