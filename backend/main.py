import sys

# Windows terminals (cmd.exe, some PowerShell/shell configurations, or anything that redirects
# stdout without an explicit UTF-8 codepage) default stdout/stderr to cp1252, which cannot encode
# the emoji used throughout this app's log messages. Without this, the very first emoji print()
# during startup raises UnicodeEncodeError and crashes the whole app ("Application startup failed.
# Exiting.") before it ever starts serving requests. Must run before anything else prints.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from app.main import app

# Export FastAPI app for Uvicorn runner
__all__ = ["app"]
