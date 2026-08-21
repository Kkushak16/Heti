import sys
import io
import os

class SafeStream(io.TextIOBase):
    """Fallback stream for GUI execution environments (like pythonw) where stdout/stderr are None."""
    def write(self, s):
        return len(s) if s else 0

    def flush(self):
        pass

def setup_safe_io():
    """Configures stdout/stderr to be safe against NoneType (pythonw) and UnicodeEncodeError (cp1252 Windows console)."""
    if sys.stdout is None:
        sys.stdout = SafeStream()
    else:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if sys.stderr is None:
        sys.stderr = SafeStream()
    else:
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

def safe_print(*args, **kwargs):
    """Encoding-safe print function that prevents UnicodeEncodeError on Windows."""
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            sep = kwargs.get("sep", " ")
            end = kwargs.get("end", "\n")
            text = sep.join(str(a) for a in args) + end
            encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
            safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
            sys.stdout.write(safe_text)
            sys.stdout.flush()
        except Exception:
            pass
