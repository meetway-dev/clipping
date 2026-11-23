"""
ClipForge AI - Core Package
100% Free Local Podcast & Video Clipping Engine
"""
# Compatibility Patch for PyAV 19+ with faster-whisper:
# PyAV 19+ removed the deprecated 'metadata_errors' parameter from av.open()
try:
    import av
    _orig_av_open = av.open
    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _safe_av_open
except Exception:
    pass

__version__ = "1.1.0"
