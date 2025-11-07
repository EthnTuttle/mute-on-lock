#!/bin/bash
# Installation script for mute-on-lock

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored message
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if script is run as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root or with sudo."
    print_info "This script installs to your user systemd directory."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_info "Installing mute-on-lock from $SCRIPT_DIR"
echo

# Check for required commands
print_info "Checking for required commands..."
if ! command -v pactl &> /dev/null; then
    print_error "pactl not found. Please install PulseAudio or PipeWire."
    exit 1
fi

if ! command -v systemctl &> /dev/null; then
    print_error "systemctl not found. This system does not appear to use systemd."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "python3 not found. Please install Python 3."
    exit 1
fi

print_info "All required commands found."
echo

# Check for Python dependencies
print_info "Checking Python dependencies..."
MISSING_DEPS=()

if ! python3 -c "import pydbus" 2>/dev/null; then
    MISSING_DEPS+=("pydbus")
fi

if ! python3 -c "from gi.repository import GLib" 2>/dev/null; then
    MISSING_DEPS+=("PyGObject")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    print_warning "Missing Python dependencies: ${MISSING_DEPS[*]}"
    echo
    print_info "Install them with:"

    # Detect package manager
    if command -v apt &> /dev/null; then
        echo "  sudo apt install python3-pydbus python3-gi"
    elif command -v dnf &> /dev/null; then
        echo "  sudo dnf install python3-pydbus python3-gobject"
    elif command -v pacman &> /dev/null; then
        echo "  sudo pacman -S python-pydbus python-gobject"
    else
        echo "  Install python3-pydbus and python3-gi using your package manager"
    fi
    echo

    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled."
        exit 1
    fi
else
    print_info "All Python dependencies found."
fi

echo

# Create systemd user directory if it doesn't exist
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
print_info "Creating systemd user directory..."
mkdir -p "$SYSTEMD_USER_DIR"

# Copy files
print_info "Copying files..."
cp "$SCRIPT_DIR/mute-on-lock.service" "$SYSTEMD_USER_DIR/"
chmod +x "$SCRIPT_DIR/mute-on-lock.py"

print_info "Files installed:"
print_info "  Script: $SCRIPT_DIR/mute-on-lock.py"
print_info "  Service: $SYSTEMD_USER_DIR/mute-on-lock.service"
echo

# Reload systemd
print_info "Reloading systemd daemon..."
systemctl --user daemon-reload

# Enable and start service
print_info "Enabling and starting service..."
systemctl --user enable mute-on-lock.service
systemctl --user start mute-on-lock.service

echo
# Check status
if systemctl --user is-active --quiet mute-on-lock.service; then
    print_info "Service is running successfully!"
    echo
    print_info "View logs with:"
    echo "  journalctl --user -u mute-on-lock.service -f"
    echo
    print_info "Check status with:"
    echo "  systemctl --user status mute-on-lock.service"
else
    print_error "Service failed to start. Check logs with:"
    echo "  journalctl --user -u mute-on-lock.service -n 50"
    exit 1
fi

echo
print_info "Installation complete! Your audio will now mute when you lock your screen."
