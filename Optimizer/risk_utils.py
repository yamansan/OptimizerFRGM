from __future__ import annotations

"""trading.utils

Low-level helpers shared by the back-testing and live-trading scripts.

This file is deliberately dependency-light (only the standard library and
NumPy) so that it can be reused in environments where Pandas is not
available.
"""

from typing import List
import re
import numpy as np

# ---------------------------------------------------------------------------
# Constants / technical levels
# ---------------------------------------------------------------------------

_TICK32: float = 1.0 / 32.0       # one 32nd = 0.03125
_HALF32: float = 1.0 / 64.0       # "+"  = half-tick = 0.015625

# CBOT 10-year T-Note technical levels that we want the strategy to respect.
# Feel free to load this list from an external source (database, CSV, etc.).
TECHNICAL_LEVELS: list[str] = [
    "108'15", "108'23", "108'29",
    "109'02", "109'07", "109'11", "109'19", "109'21", "109'28",
    "110'02", "110'06", "110'09", "110'15", "110'20", "110'24", "110'31",
    "111'01", "111'05", "111'08", "111'14", "111'18", "111'26", "112'00",
    "112'07", "112'11", "112'16", "112'19", "112'26",
    "113'01", "113'08", "113'11", "113'18", "113'25", "113'31",
    "114'06", "114'12", "114'18", "114'23", "114'30",
]

# Pre-compute the decimal representations once at import-time so that every
# consumer of this module shares the same NumPy array instance (cheap).

def _init_levels() -> None:
    """Populate the global TECH_LEVELS_DEC array lazily."""
    global TECH_LEVELS_DEC
    if TECH_LEVELS_DEC[0] is None:  # un-initialised sentinel
        TECH_LEVELS_DEC = np.array([zn_to_decimal(s) for s in TECHNICAL_LEVELS], dtype=float)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def zn_to_decimal(s: str) -> float:
    """Convert CBOT price strings (e.g. "111-04+" or "110'18+") to decimals."""
    m = re.fullmatch(r"\s*(\d+)[\-\' ]?(\d{2})(\+?)\s*", s)
    if not m:
        raise ValueError(f"Can't parse ZN price '{s}'")
    pts = int(m.group(1))           # whole points
    frac = int(m.group(2))          # 0–31 (32nds)
    half = 1 if m.group(3) else 0   # "+": adds one half-tick
    return pts + frac * _TICK32 + half * _HALF32

TECH_LEVELS_DEC: np.ndarray = np.array([zn_to_decimal(s) for s in TECHNICAL_LEVELS], dtype=float)


def decimal_to_zn(x: float) -> str:
    """Convert decimal prices back to the CBOT 32nds string format."""
    pts = int(x)
    # Multiply by 32 **before** taking int to avoid FP rounding surprises
    remainder = round((x - pts) * 32, 3)  # keep three decimals, good enough
    frac = int(remainder)
    half = 1 if (remainder - frac) >= 0.5 else 0
    return f"{pts}'{frac:02d}{'+' if half else ''}"


def levels_crossed(p0: float, p1: float, levels: np.ndarray | List[float]) -> List[float]:
    """Return the technical levels *strictly* between p0 and p1, inclusive.

    The order of the returned list reflects the direction of travel: if p1 > p0
    the list is ascending, otherwise descending.  This is useful when you want
    to replay the path chronologically.
    """
    lvls = np.asarray(levels)
    lo, hi = sorted((p0, p1))
    crossed = lvls[(lvls >= lo) & (lvls <= hi)]
    return crossed.tolist() if p1 > p0 else crossed[::-1].tolist()

# Ensure TECH_LEVELS_DEC is available as soon as the module is imported
_init_levels() 
