def _safe_str(value, default="-"):
    """Helper function to safely convert value to string, handling encoding errors."""
    if value is None:
        return default
    try:
        return str(value)
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            # Try to decode as latin-1 if utf-8 fails
            if isinstance(value, bytes):
                return value.decode("latin-1", errors="replace")
            return str(value).encode("latin-1", errors="replace").decode("utf-8", errors="replace")
        except Exception:
            return default
