"""Narrow patch-content normalization used by the natural-rate pipeline."""

from __future__ import annotations


def normalize_terminal_lfs(patch: bytes) -> bytes:
    """Remove only terminal LF characters; preserve every other byte-level character."""

    return patch.rstrip(b"\n")


def equivalent_after_terminal_lf_normalization(left: bytes, right: bytes) -> bool:
    """Return whether two patches differ only in their number of terminal LF characters."""

    return normalize_terminal_lfs(left) == normalize_terminal_lfs(right)
