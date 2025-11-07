# Mute on Lock

A systemd service that automatically mutes audio when you lock your screen and unmutes it when you unlock it.

## Features

- Automatically mutes audio on screen lock
- Unmutes audio on screen unlock
- Respects previous mute state (won't unmute if already muted)
- Also handles suspend/resume events
- Runs as a systemd user service
- Lightweight and uses native systemd signals

## Requirements

- Linux with systemd
- PulseAudio or PipeWire (with pipewire-pulse)
- Python 3
- Python packages: `pydbus`, `PyGObject`

## Installation

1. Install Python dependencies:
   ```bash
   sudo apt install python3-pydbus python3-gi  # Ubuntu/Debian
   # or
   sudo dnf install python3-pydbus python3-gobject  # Fedora
   # or
   sudo pacman -S python-pydbus python-gobject  # Arch
   ```

2. Copy the service file to systemd user directory:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp mute-on-lock.service ~/.config/systemd/user/
   ```

3. Enable and start the service:
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

```bash
systemctl --user stop mute-on-lock.service
systemctl --user disable mute-on-lock.service
rm ~/.config/systemd/user/mute-on-lock.service
systemctl --user daemon-reload
```

## How It Works

The service uses the systemd-logind D-Bus API to monitor for:
- `Lock`/`Unlock` signals from your session
- `PrepareForSleep` signals for suspend/resume

When a lock or suspend event is detected, it uses `pactl` to mute the default audio sink. When unlocking or resuming, it unmutes only if the audio wasn't already muted before locking.

## License

MIT
