#!/usr/bin/env python3
"""
Mute audio on screen lock and unmute on unlock.
Monitors systemd-logind and GNOME ScreenSaver for lock/unlock signals.
"""

import subprocess
import sys
import logging
from gi.repository import GLib
from pydbus import SystemBus, SessionBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioMuteManager:
    """Manages audio muting based on screen lock state."""

    def __init__(self):
        self.system_bus = SystemBus()
        self.session_bus = SessionBus()
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

    def on_screensaver_active_changed(self, active):
        """Handle GNOME ScreenSaver ActiveChanged signal."""
        if active:
            logger.info("Screen locked (GNOME ScreenSaver)")
            self.mute_audio()
        else:
            logger.info("Screen unlocked (GNOME ScreenSaver)")
            self.unmute_audio()

    def find_user_session(self, login1):
        """Find the active graphical session for the current user."""
        import os
        uid = os.getuid()

        # List all sessions
        sessions = login1.ListSessions()

        # Find a graphical session for our user
        for session_id, user_id, username, seat, session_path in sessions:
            if user_id == uid:
                session = self.system_bus.get('org.freedesktop.login1', session_path)
                # Check if it's a graphical session
                if hasattr(session, 'Type') and session.Type in ['x11', 'wayland']:
                    logger.info("Found session: %s (type: %s)", session_id, session.Type)
                    return session
                # If no Type property, assume it's the right one if it has a seat
                if seat:
                    logger.info("Found session: %s", session_id)
                    return session

        # If no graphical session found, try the first session for this user
        for session_id, user_id, username, seat, session_path in sessions:
            if user_id == uid:
                logger.info("Using session: %s", session_id)
                return self.system_bus.get('org.freedesktop.login1', session_path)

        raise Exception(f"No session found for UID {uid}")

    def run(self):
        """Start monitoring for lock/unlock events."""
        try:
            # Get the login1 manager
            login1 = self.system_bus.get('org.freedesktop.login1', '/org/freedesktop/login1')

            # Find the user's session
            session = self.find_user_session(login1)

            # Subscribe to Lock/Unlock signals from systemd-logind
            session.onLock = lambda: self.on_lock(True)
            session.onUnlock = lambda: self.on_lock(False)

            # Subscribe to PrepareForSleep signal (suspend/resume)
            login1.onPrepareForSleep = self.on_prepare_for_sleep

            # Try to connect to GNOME ScreenSaver (if available)
            try:
                screensaver = self.session_bus.get(
                    'org.gnome.ScreenSaver',
                    '/org/gnome/ScreenSaver'
                )
                screensaver.onActiveChanged = self.on_screensaver_active_changed
                logger.info("Connected to GNOME ScreenSaver")
            except Exception as e:
                logger.info("GNOME ScreenSaver not available (this is OK on non-GNOME desktops): %s", e)

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
