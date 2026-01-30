#!/bin/bash
#
# Build KeyLight .deb package
#

set -e

VERSION="1.0.0"
PACKAGE_NAME="keylight"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building KeyLight $VERSION .deb package..."

# Create build directory
BUILD_DIR=$(mktemp -d)
PKG_DIR="$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_all"

# Create directory structure
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/share/keylight"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$PKG_DIR/usr/bin"

# Copy application files
cp -r "$SCRIPT_DIR/keylight" "$PKG_DIR/usr/share/keylight/"
cp "$SCRIPT_DIR/keylight.py" "$PKG_DIR/usr/share/keylight/"

# Copy icon
cp "$SCRIPT_DIR/assets/keylight.svg" "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/"

# Create desktop entry
cat > "$PKG_DIR/usr/share/applications/keylight.desktop" << 'EOF'
[Desktop Entry]
Name=KeyLight
Comment=Keyboard Backlight Controller
GenericName=Keyboard Backlight
Exec=/usr/bin/keylight
Icon=keylight
Terminal=false
Type=Application
Categories=Utility;Settings;HardwareSettings;
Keywords=keyboard;backlight;rgb;led;color;
StartupNotify=true
StartupWMClass=keylight
EOF

# Create launcher scripts
cat > "$PKG_DIR/usr/bin/keylight" << 'EOF'
#!/bin/bash
python3 /usr/share/keylight/keylight.py "$@"
EOF
chmod +x "$PKG_DIR/usr/bin/keylight"

cat > "$PKG_DIR/usr/bin/keylight-cycle" << 'EOF'
#!/bin/bash
python3 /usr/share/keylight/keylight.py --cycle
EOF
chmod +x "$PKG_DIR/usr/bin/keylight-cycle"

cat > "$PKG_DIR/usr/bin/keylight-toggle" << 'EOF'
#!/bin/bash
python3 /usr/share/keylight/keylight.py --toggle
EOF
chmod +x "$PKG_DIR/usr/bin/keylight-toggle"

# Create DEBIAN/control
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: keylight
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, python3-gi-cairo, gir1.2-gtk-3.0
Recommends: gir1.2-ayatanaappindicator3-0.1
Maintainer: KeyLight <keylight@example.com>
Description: Keyboard Backlight Controller for Linux
 KeyLight is a GTK3 application for controlling RGB keyboard
 backlights on Clevo/Gigabyte laptops.
 .
 Features include color picker, brightness control, system tray,
 keyboard shortcuts, and CLI interface.
EOF

# Create postinst script
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# Setup udev rules if not exists
if [[ ! -f /etc/udev/rules.d/99-keylight.rules ]]; then
    cat > /etc/udev/rules.d/99-keylight.rules << 'RULES'
# KeyLight - Allow users in video group to control keyboard backlight
SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", ACTION=="add", RUN+="/bin/chgrp video /sys%p/brightness /sys%p/multi_intensity"
SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", ACTION=="add", RUN+="/bin/chmod g+w /sys%p/brightness /sys%p/multi_intensity"
RULES
    udevadm control --reload-rules 2>/dev/null || true
fi

echo ""
echo "KeyLight installed successfully!"
echo ""
echo "NOTE: Make sure the tuxedo_keyboard module is installed."
echo "If keyboard backlight doesn't work, run:"
echo "  sudo modprobe tuxedo_keyboard"
echo ""
EOF
chmod +x "$PKG_DIR/DEBIAN/postinst"

# Create postrm script
cat > "$PKG_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

if [ "$1" = "purge" ]; then
    rm -f /etc/udev/rules.d/99-keylight.rules 2>/dev/null || true
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
EOF
chmod +x "$PKG_DIR/DEBIAN/postrm"

# Build the package
dpkg-deb --build "$PKG_DIR"

# Move to script directory
mv "$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_all.deb" "$SCRIPT_DIR/"

# Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "Package built: ${PACKAGE_NAME}_${VERSION}_all.deb"
echo ""
echo "Install with:"
echo "  sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_all.deb"
echo "  sudo apt-get install -f  # to install dependencies"
