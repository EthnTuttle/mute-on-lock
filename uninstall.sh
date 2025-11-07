#!/bin/bash
# Uninstallation script for mute-on-lock

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
    exit 1
fi

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_USER_DIR/mute-on-lock.service"

print_info "Uninstalling mute-on-lock..."
echo

# Check if service exists
if [ ! -f "$SERVICE_FILE" ]; then
    print_warning "Service file not found at $SERVICE_FILE"
    print_info "Nothing to uninstall."
    exit 0
fi

# Stop service
print_info "Stopping service..."
if systemctl --user is-active --quiet mute-on-lock.service; then
    systemctl --user stop mute-on-lock.service
    print_info "Service stopped."
else
    print_info "Service was not running."
fi

# Disable service
print_info "Disabling service..."
if systemctl --user is-enabled --quiet mute-on-lock.service 2>/dev/null; then
    systemctl --user disable mute-on-lock.service
    print_info "Service disabled."
else
    print_info "Service was not enabled."
fi

# Remove service file
print_info "Removing service file..."
rm -f "$SERVICE_FILE"

# Reload systemd
print_info "Reloading systemd daemon..."
systemctl --user daemon-reload

echo
print_info "Uninstallation complete!"
print_warning "Note: The mute-on-lock.py script is still in the original directory."
print_info "You can remove it manually if desired."
