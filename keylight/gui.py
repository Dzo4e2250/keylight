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

    def __init__(self, color: str, size: int = 36):
        super().__init__()
        self.color = color
        self.set_size_request(size, size)
        self.set_tooltip_text(color)
        self._update_style()

    def _update_style(self):
        """Update button appearance."""
        css = f"""
        button {{
            background: {self.color};
            border-radius: 6px;
            border: 2px solid rgba(255,255,255,0.2);
            min-width: 36px;
            min-height: 36px;
            padding: 0;
        }}
        button:hover {{
            border: 2px solid white;
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        self.get_style_context().add_provider(
            provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class KeyLightWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, app):
        super().__init__(application=app, title="KeyLight")
        self.app = app
        self.controller = KeyboardBacklightController()
        self.config = Config()
        self.effects = EffectEngine(self.controller)
        self.effects.set_callback(self._on_effect_color_change)

        # Window settings
        self.set_default_size(380, 480)
        self.set_size_request(320, 400)  # Minimum size
        self.set_position(Gtk.WindowPosition.CENTER)

        # Restore window size from config
        saved_width = self.config.get("window_width", 380)
        saved_height = self.config.get("window_height", 480)
        self.set_default_size(saved_width, saved_height)

        # Save size on resize
        self.connect("configure-event", self._on_window_resize)

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
            background: #1a1a2e;
        }
        .main-container {
            padding: 16px;
        }
        .title-label {
            font-size: 20px;
            font-weight: bold;
            color: white;
        }
        .subtitle-label {
            font-size: 11px;
            color: #888;
        }
        .section-label {
            font-size: 12px;
            font-weight: bold;
            color: #666;
            margin-top: 8px;
        }
        .color-preview {
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.15);
        }
        scale {
            padding: 0;
        }
        scale trough {
            background: #333;
            border-radius: 4px;
            min-height: 6px;
        }
        scale highlight {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        scale slider {
            background: white;
            border-radius: 50%;
            min-width: 16px;
            min-height: 16px;
        }
        button.toggle-btn {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 20px;
            padding: 10px 24px;
            font-size: 13px;
            font-weight: bold;
            color: white;
        }
        button.toggle-btn:hover {
            background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
        }
        button.toggle-btn.off {
            background: #333;
        }
        combobox button {
            background: #2a2a3e;
            border: 1px solid #444;
            border-radius: 6px;
            color: white;
            padding: 6px 12px;
        }
        combobox button:hover {
            border-color: #667eea;
        }
        .info-label {
            color: #555;
            font-size: 10px;
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
        # Scrolled window for responsiveness
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled)

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.get_style_context().add_class("main-container")
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        scrolled.add(main_box)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="KeyLight")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("title-label")
        title_box.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Keyboard Backlight Controller")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.get_style_context().add_class("subtitle-label")
        title_box.pack_start(subtitle, False, False, 0)

        header_box.pack_start(title_box, True, True, 0)

        # Toggle button in header
        self.toggle_btn = Gtk.Button(label="ON")
        self.toggle_btn.set_size_request(60, 36)
        self.toggle_btn.get_style_context().add_class("toggle-btn")
        self.toggle_btn.connect("clicked", self._on_toggle_clicked)
        header_box.pack_end(self.toggle_btn, False, False, 0)

        main_box.pack_start(header_box, False, False, 0)

        # Color preview
        self.color_preview = Gtk.DrawingArea()
        self.color_preview.set_size_request(-1, 60)
        self.color_preview.get_style_context().add_class("color-preview")
        self.color_preview.connect("draw", self._draw_color_preview)
        main_box.pack_start(self.color_preview, False, False, 8)

        # Brightness section
        brightness_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        brightness_label = Gtk.Label(label="Brightness")
        brightness_label.set_halign(Gtk.Align.START)
        brightness_label.get_style_context().add_class("section-label")
        brightness_box.pack_start(brightness_label, False, False, 0)

        self.brightness_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 255, 1
        )
        self.brightness_scale.set_value(self.controller.brightness)
        self.brightness_scale.set_draw_value(False)
        self.brightness_scale.set_hexpand(True)
        self.brightness_scale.connect("value-changed", self._on_brightness_changed)
        brightness_box.pack_start(self.brightness_scale, True, True, 0)

        self.brightness_label = Gtk.Label(label="100%")
        self.brightness_label.set_size_request(45, -1)
        brightness_box.pack_end(self.brightness_label, False, False, 0)

        main_box.pack_start(brightness_box, False, False, 0)

        # Colors section
        colors_label = Gtk.Label(label="Colors")
        colors_label.set_halign(Gtk.Align.START)
        colors_label.get_style_context().add_class("section-label")
        main_box.pack_start(colors_label, False, False, 4)

        # Color grid - 2 rows
        color_grid = Gtk.Grid()
        color_grid.set_row_spacing(8)
        color_grid.set_column_spacing(8)
        color_grid.set_halign(Gtk.Align.CENTER)

        colors = self.config.favorite_colors[:10]  # Max 10 colors
        for i, color in enumerate(colors):
            btn = ColorButton(color)
            btn.connect("clicked", self._on_color_clicked, color)
            color_grid.attach(btn, i % 5, i // 5, 1, 1)

        main_box.pack_start(color_grid, False, False, 4)

        # Custom color row
        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.color_button = Gtk.ColorButton()
        current_color = Gdk.RGBA()
        current_color.parse(self.controller.get_color_hex())
        self.color_button.set_rgba(current_color)
        self.color_button.set_use_alpha(False)
        self.color_button.set_title("Choose Color")
        self.color_button.connect("color-set", self._on_custom_color_set)
        self.color_button.set_size_request(100, 36)
        custom_box.pack_start(self.color_button, False, False, 0)

        custom_label = Gtk.Label(label="Custom color")
        custom_label.get_style_context().add_class("section-label")
        custom_box.pack_start(custom_label, False, False, 0)

        main_box.pack_start(custom_box, False, False, 4)

        # Effects section
        effects_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        effects_label = Gtk.Label(label="Effect")
        effects_label.get_style_context().add_class("section-label")
        effects_box.pack_start(effects_label, False, False, 0)

        # Effect dropdown
        self.effect_combo = Gtk.ComboBoxText()
        effects_list = [
            ("static", "Static"),
            ("rainbow", "Rainbow"),
            ("breathing", "Breathing"),
            ("wave", "Color Wave"),
            ("strobe", "Strobe"),
            ("candle", "Candle"),
            ("police", "Police"),
        ]
        for effect_id, effect_name in effects_list:
            self.effect_combo.append(effect_id, effect_name)
        self.effect_combo.set_active_id("static")
        self.effect_combo.connect("changed", self._on_effect_changed)
        self.effect_combo.set_hexpand(True)
        effects_box.pack_start(self.effect_combo, True, True, 0)

        main_box.pack_start(effects_box, False, False, 4)

        # Speed slider (only visible for effects)
        self.speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        speed_label = Gtk.Label(label="Speed")
        speed_label.get_style_context().add_class("section-label")
        self.speed_box.pack_start(speed_label, False, False, 0)

        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        self.speed_scale.set_value(50)
        self.speed_scale.set_draw_value(False)
        self.speed_scale.set_hexpand(True)
        self.speed_scale.connect("value-changed", self._on_speed_changed)
        self.speed_box.pack_start(self.speed_scale, True, True, 0)

        self.speed_label = Gtk.Label(label="50%")
        self.speed_label.set_size_request(45, -1)
        self.speed_box.pack_end(self.speed_label, False, False, 0)

        main_box.pack_start(self.speed_box, False, False, 0)

        # Hide speed initially (static mode)
        self.speed_box.set_visible(False)
        self.speed_box.set_no_show_all(True)

        # Spacer
        main_box.pack_start(Gtk.Box(), True, True, 0)

        # Shortcut info
        shortcut_info = Gtk.Label()
        shortcut_info.set_markup('<span color="#555" size="small">Tip: Add keyboard shortcut for keylight-cycle</span>')
        shortcut_info.get_style_context().add_class("info-label")
        main_box.pack_end(shortcut_info, False, False, 8)

        self._update_toggle_button()
        self._update_brightness_label()

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

        # Draw rounded rectangle
        radius = 10
        cr.new_path()
        cr.arc(width - radius, radius, radius, -1.5708, 0)
        cr.arc(width - radius, height - radius, radius, 0, 1.5708)
        cr.arc(radius, height - radius, radius, 1.5708, 3.1416)
        cr.arc(radius, radius, radius, 3.1416, 4.7124)
        cr.close_path()

        # Fill with color
        cr.set_source_rgb(r, g, b)
        cr.fill_preserve()

        # Draw border
        cr.set_source_rgba(1, 1, 1, 0.15)
        cr.set_line_width(2)
        cr.stroke()

    def _on_window_resize(self, widget, event):
        """Save window size on resize."""
        width, height = self.get_size()
        self.config.set("window_width", width)
        self.config.set("window_height", height)

    def _update_brightness_label(self):
        """Update the brightness percentage label."""
        brightness = int(self.brightness_scale.get_value())
        percentage = int((brightness / 255) * 100)
        self.brightness_label.set_text(f"{percentage}%")

    def _update_toggle_button(self):
        """Update toggle button state."""
        is_on = self.controller.brightness > 0
        self.toggle_btn.set_label("ON" if is_on else "OFF")
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
        self._stop_effect_and_set_static()

        self.controller.set_color_hex(color)
        self.config.current_color = color
        self.color_preview.queue_draw()

        rgba = Gdk.RGBA()
        rgba.parse(color)
        self.color_button.set_rgba(rgba)

        if self.controller.brightness == 0:
            self.brightness_scale.set_value(self.config.brightness or 255)

    def _on_custom_color_set(self, button):
        """Handle custom color selection."""
        self._stop_effect_and_set_static()

        rgba = button.get_rgba()
        r = int(rgba.red * 255)
        g = int(rgba.green * 255)
        b = int(rgba.blue * 255)
        color = f"#{r:02X}{g:02X}{b:02X}"

        self.controller.set_color_hex(color)
        self.config.current_color = color
        self.color_preview.queue_draw()

        if self.controller.brightness == 0:
            self.brightness_scale.set_value(self.config.brightness or 255)

    def _stop_effect_and_set_static(self):
        """Stop effect and set combo to static."""
        self.effects.stop()
        self.effect_combo.set_active_id("static")
        self.speed_box.set_visible(False)

    def _on_effect_changed(self, combo):
        """Handle effect dropdown change."""
        effect_id = combo.get_active_id()

        self.effects.stop()

        # Show/hide speed control
        show_speed = effect_id != "static"
        self.speed_box.set_visible(show_speed)
        self.speed_box.set_no_show_all(not show_speed)
        if show_speed:
            self.speed_box.show_all()

        # Start effect
        if effect_id == "rainbow":
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

        if self.controller.brightness == 0:
            self.brightness_scale.set_value(self.config.brightness or 255)

    def _on_speed_changed(self, scale):
        """Handle speed slider change."""
        value = int(scale.get_value())
        self.effects.speed = value
        self.speed_label.set_text(f"{value}%")

    def _on_effect_color_change(self, r, g, b):
        """Called by effect engine when color changes."""
        GLib.idle_add(self._update_preview_color)

    def _update_preview_color(self):
        """Update the color preview."""
        self.color_preview.queue_draw()
        return False

    def _on_toggle_clicked(self, button):
        """Toggle backlight on/off."""
        if self.controller.brightness > 0:
            self.brightness_scale.set_value(0)
        else:
            self.brightness_scale.set_value(self.config.brightness or 255)
        self._update_toggle_button()
        self.color_preview.queue_draw()

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
            self._update_brightness_label()


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
