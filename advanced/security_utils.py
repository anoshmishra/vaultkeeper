"""Best-effort memory hygiene for data Python can safely mutate."""

import ctypes
import sys


class SecurityUtils:
    @staticmethod
    def secure_delete(data):
        """Zero a writable buffer in place and return whether that was possible.

        Python strings and immutable bytes cannot be reliably scrubbed.  Callers
        should keep short-lived sensitive values in ``bytearray`` where practical.
        """
        if isinstance(data, memoryview):
            if data.readonly:
                return False
            data[:] = b"\x00" * len(data)
            return True
        if isinstance(data, bytearray):
            data[:] = b"\x00" * len(data)
            return True
        return False

    @staticmethod
    def lock_memory(data):
        """Try to lock a writable buffer; failure is safe and non-fatal."""
        if not isinstance(data, bytearray) or not data:
            return False
        try:
            libc = ctypes.CDLL(None)
            address = ctypes.addressof(ctypes.c_char.from_buffer(data))
            return libc.mlock(ctypes.c_void_p(address), ctypes.c_size_t(len(data))) == 0
        except (AttributeError, OSError, TypeError):
            return False

    @staticmethod
    def check_debugger():
        return hasattr(sys, "gettrace") and sys.gettrace() is not None
