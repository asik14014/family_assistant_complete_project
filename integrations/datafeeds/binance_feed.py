# integrations/datafeeds/binance_feed.py
from __future__ import annotations
import time, requests
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Any

from core.interfaces import AbstractMarketDataFeed

TF_TO_INTERVAL_SEC = {
    "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "1d": 86400,
}

def _to_symbol(pair: str) -> str:
    return pair.replace("/", "").upper()

def _base_url(testnet: bool) -> str:
    return "https://testnet.binance.vision/api" if testnet else "https://api.binance.com/api"

@dataclass
class BinanceMarketDataFeed(AbstractMarketDataFeed):
    pair: str
    timeframe: str
    testnet: bool = True
    _last_stream_open_ms: int = 0

    @property
    def _base(self) -> str:
        return _base_url(self.testnet)

    def _get_klines(self, limit: int) -> List[List[Any]]:
        url = f"{self._base}/v3/klines"
        params = {"symbol": _to_symbol(self.pair), "interval": self.timeframe, "limit": limit}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def history(self, limit: int = 500) -> List[Dict[str, Any]]:
        data = self._get_klines(limit=limit)
        bars = []
        for k in data:
            open_ms = int(k[0])
            bars.append({
                "ts": datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            })
        return bars

    def stream(self) -> Iterable[Dict[str, Any]]:
        poll = max(5, TF_TO_INTERVAL_SEC.get(self.timeframe, 60) // 4)
        while True:
            try:
                last = self._get_klines(limit=1)[0]
                open_ms = int(last[0])
                if open_ms != self._last_stream_open_ms:
                    self._last_stream_open_ms = open_ms
                    yield {
                        "ts": datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc),
                        "open": float(last[1]),
                        "high": float(last[2]),
                        "low": float(last[3]),
                        "close": float(last[4]),
                        "volume": float(last[5]),
                    }
            except Exception as e:
                print(f"[FEED] error: {e}")
            time.sleep(poll)
