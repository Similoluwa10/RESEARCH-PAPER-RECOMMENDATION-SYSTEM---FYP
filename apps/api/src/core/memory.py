"""
memory.py - Process memory helpers

Used after large one-off allocations (model loading, TF-IDF fitting) so the
process stays within small memory limits (e.g. Render's 512 MB free tier).
"""

import ctypes
import gc
import logging
import sys

logger = logging.getLogger(__name__)


def release_memory() -> None:
    """Run the garbage collector and return freed heap pages to the OS.

    On Linux/glibc, freed memory normally stays reserved by the process, so a
    temporary spike keeps counting against the container limit. malloc_trim
    hands it back. On other platforms only the garbage collector runs.
    """
    gc.collect()
    if sys.platform.startswith("linux"):
        try:
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception as e:  # non-glibc (e.g. musl/Alpine)
            logger.debug(f"malloc_trim unavailable: {e}")
