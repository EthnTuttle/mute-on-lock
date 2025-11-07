#!/usr/bin/env python3
"""
Mute audio on screen lock and unmute on unlock.
Monitors systemd-logind for lock/unlock signals.
"""

import subprocess
import sys
import logging
from gi.repository import GLib
from pydbus import SystemBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioMuteManager:
    """Manages audio muting based on screen lock state."""

    def __init__(self):
        self.bus = SystemBus()
        self.was_muted = False

    def mute_audio(self):
        """Mute all audio sinks."""
        try:
            # Get current mute state before muting
            result = subprocess.run(
                ['pactl', 'get-sink-mute', '@DEFAULT_SINK@'],
                capture_output=True,
                text=True,
                check=True
            )
            self.was_muted = 'yes' in result.stdout.lower()

            # Mute the default sink
            subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '1'], check=True)
            logger.info("Audio muted (was previously muted: %s)", self.was_muted)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to mute audio: %s", e)

    def unmute_audio(self):
        """Unmute audio only if it wasn't already muted before locking."""
        try:
            # Only unmute if we muted it (it wasn't already muted)
            if not self.was_muted:
                subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '0'], check=True)
                logger.info("Audio unmuted")
            else:
                logger.info("Audio kept muted (was muted before lock)")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to unmute audio: %s", e)

    def on_lock(self, locked):
        """Handle lock/unlock signal."""
        if locked:
            logger.info("Screen locked")
            self.mute_audio()
        else:
            logger.info("Screen unlocked")
            self.unmute_audio()

    def on_prepare_for_sleep(self, sleeping):
        """Handle suspend/resume signal."""
        if sleeping:
            logger.info("System suspending")
            self.mute_audio()
        else:
            logger.info("System resuming")
            self.unmute_audio()

    def run(self):
        """Start monitoring for lock/unlock events."""
        try:
            # Get the login1 manager
            login1 = self.bus.get('org.freedesktop.login1', '/org/freedesktop/login1')

            # Get current session
            session_path = login1.GetSessionByPID(0)
            session = self.bus.get('org.freedesktop.login1', session_path)

            # Subscribe to Lock/Unlock signals
            session.onLock = lambda: self.on_lock(True)
            session.onUnlock = lambda: self.on_lock(False)

            # Subscribe to PrepareForSleep signal (suspend/resume)
            login1.onPrepareForSleep = self.on_prepare_for_sleep

            logger.info("Monitoring started. Press Ctrl+C to stop.")

            # Start the main loop
            loop = GLib.MainLoop()
            loop.run()

        except KeyboardInterrupt:
            logger.info("Stopping monitor...")
            sys.exit(0)
        except Exception as e:
            logger.error("Error: %s", e)
            sys.exit(1)


if __name__ == '__main__':
    manager = AudioMuteManager()
    manager.run()
