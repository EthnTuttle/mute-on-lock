# Mute on Lock

A systemd service that automatically mutes audio when you lock your screen and unmutes it when you unlock it.

## Features

- Automatically mutes audio on screen lock
- Unmutes audio on screen unlock
- Respects previous mute state (won't unmute if already muted)
- Also handles suspend/resume events
- Runs as a systemd user service
- Lightweight and uses native D-Bus signals
- Works with GNOME, KDE, and other desktop environments

## Requirements

- Linux with systemd
- PulseAudio or PipeWire (with pipewire-pulse)
- Python 3
- Python packages: `pydbus`, `PyGObject`

## Installation

### Quick Install (Recommended)

1. Install Python dependencies:
   ```bash
   sudo apt install python3-pydbus python3-gi  # Ubuntu/Debian
   # or
   sudo dnf install python3-pydbus python3-gobject  # Fedora
   # or
   sudo pacman -S python-pydbus python-gobject  # Arch
   ```

2. Run the install script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

The script will automatically:
- Check for required dependencies
- Copy files to the correct locations
- Enable and start the systemd service
- Verify the installation

### Manual Installation

If you prefer to install manually:

1. Install Python dependencies (see above)

2. Copy the service file to systemd user directory:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp mute-on-lock.service ~/.config/systemd/user/
   ```

3. Make the script executable:
   ```bash
   chmod +x mute-on-lock.py
   ```

4. Enable and start the service:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable mute-on-lock.service
   systemctl --user start mute-on-lock.service
   ```

## Usage

Once installed, the service runs automatically in the background. It will:

- Mute audio when you lock your screen (Ctrl+Alt+L or similar)
- Mute audio when your system suspends
- Unmute audio when you unlock or resume (only if it wasn't already muted)

## Checking Status

```bash
# Check if service is running
systemctl --user status mute-on-lock.service

# View logs
journalctl --user -u mute-on-lock.service -f
```

## Troubleshooting

### Service fails to start

Check the logs:
```bash
journalctl --user -u mute-on-lock.service -n 50
```

### Audio doesn't mute/unmute

Make sure PulseAudio is running:
```bash
pactl info
```

Test manual muting:
```bash
pactl set-sink-mute @DEFAULT_SINK@ 1  # mute
pactl set-sink-mute @DEFAULT_SINK@ 0  # unmute
```

## Uninstallation

### Quick Uninstall

```bash
chmod +x uninstall.sh
./uninstall.sh
```

### Manual Uninstall

```bash
systemctl --user stop mute-on-lock.service
systemctl --user disable mute-on-lock.service
rm ~/.config/systemd/user/mute-on-lock.service
systemctl --user daemon-reload
```

## How It Works

The service monitors multiple D-Bus interfaces to catch lock/unlock events:

1. **systemd-logind** - Monitors `Lock`/`Unlock` signals from your session and `PrepareForSleep` signals for suspend/resume
2. **GNOME ScreenSaver** - For GNOME desktop environments, monitors the `ActiveChanged` signal
3. **Other desktop environments** - Falls back to systemd-logind signals for KDE, XFCE, etc.

When a lock or suspend event is detected, it uses `pactl` to mute the default audio sink. When unlocking or resuming, it unmutes only if the audio wasn't already muted before locking.

## License

MIT
