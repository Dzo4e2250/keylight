#!/bin/bash
#
# KeyLight Uninstaller
#

echo "Uninstalling KeyLight..."

# Remove desktop entry
rm -f ~/.local/share/applications/keylight.desktop

# Remove icon
rm -f ~/.local/share/icons/hicolor/scalable/apps/keylight.svg

# Remove CLI commands
rm -f ~/.local/bin/keylight
rm -f ~/.local/bin/keylight-cycle
rm -f ~/.local/bin/keylight-toggle

# Update caches
update-desktop-database ~/.local/share/applications 2>/dev/null
gtk-update-icon-cache ~/.local/share/icons/hicolor 2>/dev/null

echo ""
echo "KeyLight has been uninstalled."
echo ""
echo "Note: The application files are still in ~/.local/share/keylight"
echo "To completely remove, run: rm -rf ~/.local/share/keylight"
echo ""
echo "The kernel driver (tuxedo_keyboard) was not removed."
echo "To remove it: sudo modprobe -r tuxedo_keyboard"
