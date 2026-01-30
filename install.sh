#!/bin/bash
#
# KeyLight Installer
# Automatically installs all dependencies and drivers
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="keylight"
CLEVO_REPO="https://github.com/wessel-novacustom/clevo-keyboard.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                    KeyLight Installer                     ║"
    echo "║            Keyboard Backlight Controller                  ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[$1/$TOTAL_STEPS]${NC} $2"
}

print_ok() {
    echo -e "    ${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "    ${YELLOW}!${NC} $1"
}

print_error() {
    echo -e "    ${RED}✗${NC} $1"
}

TOTAL_STEPS=7

print_header

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}Please run without sudo. The script will ask for sudo when needed.${NC}"
    exit 1
fi

# Detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_LIKE=$ID_LIKE
    else
        DISTRO="unknown"
    fi
}

detect_distro
echo -e "Detected: ${GREEN}$DISTRO${NC}"
echo

# Step 1: Install build dependencies
print_step 1 "Installing build dependencies..."

case $DISTRO in
    ubuntu|debian|pop|linuxmint|elementary)
        sudo apt-get update -qq
        sudo apt-get install -y -qq git build-essential linux-headers-$(uname -r) \
            python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
            gir1.2-ayatanaappindicator3-0.1 2>/dev/null || \
        sudo apt-get install -y -qq git build-essential linux-headers-$(uname -r) \
            python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 2>/dev/null
        print_ok "Dependencies installed"
        ;;
    fedora|rhel|centos)
        sudo dnf install -y git kernel-devel kernel-headers \
            python3 python3-gobject gtk3 libappindicator-gtk3
        print_ok "Dependencies installed"
        ;;
    arch|manjaro|endeavouros)
        sudo pacman -S --noconfirm --needed git base-devel linux-headers \
            python python-gobject gtk3 libappindicator-gtk3
        print_ok "Dependencies installed"
        ;;
    opensuse*)
        sudo zypper install -y git kernel-devel \
            python3 python3-gobject gtk3 typelib-1_0-AppIndicator3-0_1
        print_ok "Dependencies installed"
        ;;
    *)
        print_warn "Unknown distro. Please install manually: git, build-essential, linux-headers, python3-gi, gir1.2-gtk-3.0"
        ;;
esac

# Step 2: Check/Install kernel module
print_step 2 "Checking keyboard driver..."

if lsmod | grep -q tuxedo_keyboard; then
    print_ok "tuxedo_keyboard module already loaded"
else
    print_warn "tuxedo_keyboard module not found, installing..."

    # Clone and build the driver
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    echo "    Downloading driver..."
    git clone --depth 1 "$CLEVO_REPO" clevo-keyboard 2>/dev/null

    cd clevo-keyboard
    echo "    Building driver..."
    sudo make -j$(nproc) > /dev/null 2>&1

    echo "    Installing driver..."
    sudo make install > /dev/null 2>&1
    sudo depmod -a

    # Load the module
    sudo modprobe tuxedo_keyboard

    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"

    if lsmod | grep -q tuxedo_keyboard; then
        print_ok "Driver installed and loaded successfully"
    else
        print_error "Failed to load driver"
        exit 1
    fi
fi

# Step 3: Configure module to load on boot
print_step 3 "Configuring driver autoload..."

if [[ ! -f /etc/modules-load.d/tuxedo_keyboard.conf ]]; then
    echo "tuxedo_keyboard" | sudo tee /etc/modules-load.d/tuxedo_keyboard.conf > /dev/null
fi
print_ok "Driver will load automatically on boot"

# Step 4: Set up udev rules for permissions
print_step 4 "Setting up permissions..."

if [[ ! -f /etc/udev/rules.d/99-keylight.rules ]]; then
    sudo tee /etc/udev/rules.d/99-keylight.rules > /dev/null << 'EOF'
# KeyLight - Allow users in video group to control keyboard backlight
SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", ACTION=="add", RUN+="/bin/chgrp video /sys%p/brightness /sys%p/multi_intensity"
SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", ACTION=="add", RUN+="/bin/chmod g+w /sys%p/brightness /sys%p/multi_intensity"
EOF
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

# Add user to video group if needed
if ! groups | grep -q video; then
    sudo usermod -aG video "$USER"
    print_warn "Added $USER to video group (re-login for full effect)"
else
    print_ok "User already in video group"
fi

# Apply permissions now
sudo chgrp video /sys/class/leds/rgb:kbd_backlight/brightness 2>/dev/null || true
sudo chmod g+w /sys/class/leds/rgb:kbd_backlight/brightness 2>/dev/null || true
sudo chgrp video /sys/class/leds/rgb:kbd_backlight/multi_intensity 2>/dev/null || true
sudo chmod g+w /sys/class/leds/rgb:kbd_backlight/multi_intensity 2>/dev/null || true
print_ok "Permissions configured"

# Step 5: Install desktop entry
print_step 5 "Installing application..."

mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/scalable/apps

# Update desktop file with correct path
sed "s|Exec=.*|Exec=python3 $SCRIPT_DIR/keylight.py|g; s|Icon=.*|Icon=keylight|g" \
    "$SCRIPT_DIR/keylight.desktop" > ~/.local/share/applications/keylight.desktop
chmod +x ~/.local/share/applications/keylight.desktop

# Install icon
cp "$SCRIPT_DIR/assets/keylight.svg" ~/.local/share/icons/hicolor/scalable/apps/keylight.svg

update-desktop-database ~/.local/share/applications 2>/dev/null || true
gtk-update-icon-cache ~/.local/share/icons/hicolor 2>/dev/null || true

print_ok "Desktop entry installed"

# Step 6: Create CLI commands
print_step 6 "Creating CLI commands..."

mkdir -p ~/.local/bin

# Main launcher
cat > ~/.local/bin/keylight << EOF
#!/bin/bash
python3 "$SCRIPT_DIR/keylight.py" "\$@"
EOF
chmod +x ~/.local/bin/keylight

# Cycle colors command
cat > ~/.local/bin/keylight-cycle << EOF
#!/bin/bash
python3 "$SCRIPT_DIR/keylight.py" --cycle
EOF
chmod +x ~/.local/bin/keylight-cycle

# Toggle command
cat > ~/.local/bin/keylight-toggle << EOF
#!/bin/bash
python3 "$SCRIPT_DIR/keylight.py" --toggle
EOF
chmod +x ~/.local/bin/keylight-toggle

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    print_warn "Add ~/.local/bin to PATH in your .bashrc or .zshrc"
fi

print_ok "CLI commands created"

# Step 7: Verify installation
print_step 7 "Verifying installation..."

if [[ -f /sys/class/leds/rgb:kbd_backlight/brightness ]]; then
    CURRENT_BRIGHTNESS=$(cat /sys/class/leds/rgb:kbd_backlight/brightness)
    CURRENT_COLOR=$(cat /sys/class/leds/rgb:kbd_backlight/multi_intensity)
    print_ok "Keyboard backlight detected (brightness: $CURRENT_BRIGHTNESS)"
else
    print_error "Keyboard backlight not found"
    exit 1
fi

# Done!
echo
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              Installation Complete!                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo
echo "Launch KeyLight:"
echo "  • From application menu (search 'KeyLight')"
echo "  • Terminal: keylight"
echo
echo "CLI commands:"
echo "  • keylight --cycle     Cycle through colors"
echo "  • keylight --toggle    Toggle on/off"
echo "  • keylight --set '#FF0000'  Set color"
echo
echo "Keyboard shortcuts:"
echo "  Settings → Keyboard → Shortcuts → Add custom:"
echo "    Command: keylight-cycle"
echo "    Key: Super+Space (or your preference)"
echo
if ! groups | grep -q video; then
    echo -e "${YELLOW}NOTE: Please log out and back in for permissions to take effect.${NC}"
fi
