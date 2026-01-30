# KeyLight

A beautiful GTK3 application for controlling RGB keyboard backlights on Clevo/Gigabyte laptops running Linux.

![KeyLight](assets/keylight.svg)

## Why I Built This

I own a Gigabyte G5 GD laptop and wanted to control my RGB keyboard backlight on Linux. I searched everywhere - forums, GitHub, Reddit - but couldn't find a single working solution for my laptop. Every tool I tried either didn't support my hardware or required Windows-only software like Gigabyte Control Center.

After hours of frustration, I decided to build my own application from scratch. I reverse-engineered how the keyboard backlight works, found the right kernel drivers, and created a simple GUI that just works.

**I'm sharing this so others don't have to waste hours like I did.** The installer automatically downloads and sets up all the required drivers - just run it and you're done.

## Supported Hardware

- **Gigabyte**: G5, G7, Aero series
- **Clevo**: Most models with RGB keyboards
- **Tongfang**: Various rebranded laptops
- Other laptops using the `tuxedo_keyboard` driver

## Features

- **Color Picker**: Choose any RGB color for your keyboard backlight
- **Preset Colors**: Quick access to 10 pre-configured colors
- **Brightness Control**: Smooth slider to adjust brightness from 0-100%
- **Animated Effects**: Rainbow, Breathing, Wave, Strobe, Candle, Police lights
- **Speed Control**: Adjust animation speed
- **System Tray**: Quick access to controls without opening the main window
- **Keyboard Shortcuts**: Bind keys to cycle colors or toggle backlight
- **Settings Persistence**: Remembers your preferences across reboots
- **CLI Support**: Control via command line for scripting
- **Auto Driver Install**: The installer handles everything automatically

## Installation

### One-Line Install (Recommended)

Copy and paste this into your terminal:

```bash
git clone https://github.com/Dzo4e2250/keylight.git ~/.local/share/keylight && ~/.local/share/keylight/install.sh
```

That's it! After installation:
- **KeyLight** appears in your application menu - just click to launch
- Run `keylight` from any terminal
- No need to navigate to folders or run python commands

### What the installer does

1. Installs all required dependencies (GTK3, Python packages)
2. Downloads and builds the kernel driver automatically
3. Sets up permissions (no root password needed after install)
4. Adds KeyLight to your application menu with icon
5. Creates CLI commands: `keylight`, `keylight-cycle`, `keylight-toggle`
6. Configures everything to persist after reboot

### Alternative: Install from .deb (Debian/Ubuntu)

```bash
git clone https://github.com/Dzo4e2250/keylight.git
cd keylight
./build-deb.sh
sudo dpkg -i keylight_1.0.0_all.deb
sudo apt-get install -f
```

### Uninstall

```bash
~/.local/share/keylight/uninstall.sh
```

## Usage

### GUI Application

Launch from your application menu (search for "KeyLight") or run:
```bash
python3 keylight.py
```

### Effects

KeyLight includes animated lighting effects:

| Effect | Description |
|--------|-------------|
| Static | Solid color (no animation) |
| Rainbow | Cycles through all colors |
| Breathing | Fades in and out |
| Wave | Smooth transitions between colors |
| Strobe | Fast flashing |
| Candle | Warm flickering effect |
| Police | Red/blue emergency lights |

### Command Line

```bash
# Cycle through colors
keylight --cycle

# Toggle on/off
keylight --toggle

# Set specific color
keylight --set "#FF0000"

# Set brightness (0-255)
keylight --brightness 128
```

### Keyboard Shortcuts

Set up a shortcut to cycle colors with a key combo:

**GNOME/Ubuntu:**
1. Settings → Keyboard → Keyboard Shortcuts
2. Add Custom Shortcut
3. Command: `keylight-cycle`
4. Set key combination (e.g., Super+Space)

**KDE:**
1. System Settings → Shortcuts → Custom Shortcuts
2. Add new Global Shortcut
3. Command: `keylight-cycle`

## Configuration

Configuration is stored in `~/.config/keylight/config.json`:

```json
{
  "brightness": 255,
  "current_color": "#FFFFFF",
  "favorite_colors": ["#FFFFFF", "#FF0000", "#00FF00", ...],
  "cycle_colors": ["#FFFFFF", "#FF0000", "#00FF00", "#0000FF"],
  "restore_on_startup": true
}
```

## Troubleshooting

### "Keyboard backlight not available"

Make sure the kernel module is loaded:
```bash
sudo modprobe tuxedo_keyboard
lsmod | grep tuxedo
```

Check if the LED interface exists:
```bash
ls /sys/class/leds/rgb:kbd_backlight/
```

### Permission denied

Run the installer to set up udev rules, or manually:
```bash
sudo chgrp video /sys/class/leds/rgb:kbd_backlight/brightness
sudo chmod g+w /sys/class/leds/rgb:kbd_backlight/brightness
sudo usermod -aG video $USER
# Log out and back in
```

### Colors not changing

Some laptops only support certain colors. Try the preset colors first.

## File Structure

```
keylight/
├── keylight.py          # Main entry point
├── keylight/
│   ├── controller.py    # Hardware interface
│   ├── config.py        # Settings management
│   ├── effects.py       # Animated lighting effects
│   ├── gui.py           # GTK3 user interface
│   ├── tray.py          # System tray icon
│   └── shortcuts.py     # Keyboard shortcut handling
├── assets/
│   └── keylight.svg     # Application icon
├── install.sh           # Auto-installer with driver setup
├── build-deb.sh         # Debian package builder
└── snap/                # Snap package files
```

## Contributing

Found a bug or want to add support for more hardware? Pull requests are welcome!

## License

MIT License

## Credits

- [clevo-keyboard](https://github.com/wessel-novacustom/clevo-keyboard) - Kernel module for Clevo laptops
- GTK3 - User interface toolkit

---

*If this helped you, consider giving it a ⭐ on GitHub!*
