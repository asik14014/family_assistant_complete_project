from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
from datetime import datetime

class Side(str, Enum):
    LONG = "LONG"
    FLAT = "FLAT"

@dataclass
class Bar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class Position:
    side: Side = Side.FLAT
    qty: float = 0.0
    entry: Optional[float] = None
    stop: Optional[float] = None
    tp1: Optional[float] = None
    meta: Dict = None
