"""Inactivity and macOS session-event vault locking."""

import time


class AutoLockMonitor:
    def __init__(self, root, lock_callback, timeout_seconds=900):
        self.root = root
        self.lock_callback = lock_callback
        self.timeout_seconds = timeout_seconds
        self.last_activity = time.monotonic()
        self.enabled = False
        self._after_id = None
        self._observer = None

    def start(self):
        self.enabled = True
        self.record_activity()
        for event in ("<KeyPress>", "<ButtonPress>", "<Motion>", "<FocusIn>"):
            self.root.bind_all(event, self.record_activity, add="+")
        self._watch_macos_session_events()
        self._schedule_check()

    def stop(self):
        self.enabled = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def record_activity(self, _event=None):
        self.last_activity = time.monotonic()

    def _schedule_check(self):
        if self.enabled:
            self._after_id = self.root.after(1000, self._check)

    def _check(self):
        if self.enabled and time.monotonic() - self.last_activity >= self.timeout_seconds:
            self.enabled = False
            self.lock_callback(reason="inactivity")
            return
        self._schedule_check()

    def _watch_macos_session_events(self):
        """Use NSWorkspace notifications when PyObjC is installed on macOS."""
        try:
            from AppKit import NSWorkspace
            from Foundation import NSObject

            callback = self.lock_callback

            class WorkspaceObserver(NSObject):
                def workspaceSessionChanged_(self, _notification):
                    callback(reason="screen lock or sleep")

            self._observer = WorkspaceObserver.alloc().init()
            center = NSWorkspace.sharedWorkspace().notificationCenter()
            for name in ("NSWorkspaceScreensDidSleepNotification", "NSWorkspaceSessionDidResignActiveNotification"):
                center.addObserver_selector_name_object_(
                    self._observer, "workspaceSessionChanged:", name, None
                )
        except (ImportError, AttributeError):
            # Inactivity lock remains available where the optional macOS bridge
            # is not installed.
            self._observer = None
