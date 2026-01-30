# KeyLight

A beautiful GTK3 application for controlling RGB keyboard backlights on Clevo/Gigabyte laptops running Linux.

![KeyLight](assets/keylight.svg)

## Features

- **Color Picker**: Choose any RGB color for your keyboard backlight
- **Preset Colors**: Quick access to 10 pre-configured colors
- **Brightness Control**: Smooth slider to adjust brightness from 0-100%
- **System Tray**: Quick access to controls without opening the main window
- **Keyboard Shortcuts**: Bind keys to cycle colors or toggle backlight
- **Settings Persistence**: Remembers your preferences across reboots
- **CLI Support**: Control via command line for scripting

## Requirements

- Linux with GTK 3.0+
- Python 3.8+
- Clevo/Gigabyte laptop with RGB keyboard
- `tuxedo_keyboard` kernel module

## Installation

### Quick Install

```bash
./install.sh
```

This will:
1. Check/load the tuxedo_keyboard module
2. Set up permissions for LED control
3. Install desktop entry
4. Create CLI shortcuts

### Manual Installation

1. **Install the kernel module:**
   ```bash
   cd /tmp
   git clone https://github.com/wessel-novacustom/clevo-keyboard.git
   cd clevo-keyboard
   sudo make && sudo make install
   sudo depmod -a
   sudo modprobe tuxedo_keyboard
   ```

2. **Make it load on boot:**
   ```bash
   echo "tuxedo_keyboard" | sudo tee /etc/modules-load.d/tuxedo_keyboard.conf
   ```

3. **Run KeyLight:**
   ```bash
   python3 keylight.py
   ```

## Usage

### GUI Application

Launch from application menu or run:
```bash
python3 keylight.py
```

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

After installation, set up shortcuts in your desktop environment:

**GNOME/Ubuntu:**
1. Settings → Keyboard → Keyboard Shortcuts
2. Add Custom Shortcut
3. Command: `~/.local/bin/keylight-cycle`
4. Set key combination (e.g., Super+Space)

**KDE:**
1. System Settings → Shortcuts → Custom Shortcuts
2. Add new Global Shortcut
3. Command: `~/.local/bin/keylight-cycle`

## Configuration

Configuration is stored in `~/.config/keylight/config.json`:

```json
{
  "brightness": 255,
  "current_color": "#FFFFFF",
  "favorite_colors": ["#FFFFFF", "#FF0000", ...],
  "cycle_colors": ["#FFFFFF", "#FF0000", "#00FF00", "#0000FF"],
  "restore_on_startup": true
}
```

## File Structure

```
KEYLIGHT/
├── keylight.py          # Main entry point
├── keylight/
│   ├── __init__.py
│   ├── controller.py    # Hardware interface
│   ├── config.py        # Settings management
│   ├── gui.py           # GTK3 user interface
│   ├── tray.py          # System tray icon
│   └── shortcuts.py     # Keyboard shortcut handling
├── assets/
│   └── keylight.svg     # Application icon
├── keylight.desktop     # Desktop entry
├── install.sh           # Installer script
└── README.md
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

## License

MIT License

## Credits

- [clevo-keyboard](https://github.com/wessel-novacustom/clevo-keyboard) - Kernel module for Clevo laptops
- GTK3 - User interface toolkit
