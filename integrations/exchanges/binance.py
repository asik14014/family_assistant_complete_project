# integrations/exchanges/binance.py
from __future__ import annotations
import os, time, hmac, hashlib, math, requests
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.interfaces import AbstractExchangeAdapter

def _to_symbol(pair: str) -> str:
    return pair.replace("/", "").upper()

def _base_url(testnet: bool) -> str:
    return "https://testnet.binance.vision/api" if testnet else "https://api.binance.com/api"

@dataclass
class BinanceExchangeAdapter(AbstractExchangeAdapter):
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    testnet: bool = (os.getenv("BINANCE_TESTNET", "true").lower() == "true")

    def __post_init__(self):
        if not self.api_key or not self.api_secret:
            raise RuntimeError("BINANCE_API_KEY / BINANCE_API_SECRET are required")
        self._base = _base_url(self.testnet)
        self._exchange_info_cache: Dict[str, Any] = {}

    # ---- helpers ----
    def _headers(self) -> Dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    def _sign(self, qs: str) -> str:
        return hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()

    def _req(self, method: str, path: str, params: Dict[str, Any], signed: bool = False) -> Dict[str, Any]:
        if signed:
            params = {**params, "timestamp": int(time.time() * 1000), "recvWindow": 5000}
            qs = "&".join(f"{k}={params[k]}" for k in sorted(params.keys()) if params[k] is not None)
            sig = self._sign(qs)
            url = f"{self._base}{path}?{qs}&signature={sig}"
            r = requests.request(method, url, headers=self._headers(), timeout=15)
        else:
            url = f"{self._base}{path}"
            r = requests.request(method, url, params=params, headers=self._headers(), timeout=15)
        try:
            r.raise_for_status()
        except Exception:
            raise RuntimeError(f"Binance error [{r.status_code}]: {r.text}")
        return r.json()

    def _exchange_info(self, symbol: str) -> Dict[str, Any]:
        if not self._exchange_info_cache:
            info = self._req("GET", "/v3/exchangeInfo", {}, signed=False)
            for s in info.get("symbols", []):
                self._exchange_info_cache[s["symbol"]] = s
        return self._exchange_info_cache[symbol]

    @staticmethod
    def _round_step(value: float, step: float) -> float:
        if step == 0:
            return value
        return math.floor(value / step) * step

    def _normalize_qty_price(self, symbol: str, qty: float, price: Optional[float] = None) -> Dict[str, float]:
        info = self._exchange_info(symbol)
        qty_step = 0.0
        tick_size = 0.0
        min_notional = 0.0
        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                qty_step = float(f["stepSize"])
            elif f["filterType"] == "PRICE_FILTER":
                tick_size = float(f["tickSize"])
            elif f["filterType"] in ("NOTIONAL", "MIN_NOTIONAL"):
                min_notional = float(f.get("minNotional", f.get("notional", 0)))
        q = self._round_step(qty, qty_step or 1e-6)
        p = price
        if p is not None and tick_size:
            p = self._round_step(p, tick_size)
        if p and q and p * q < (min_notional or 0):
            raise ValueError(f"Order notional too small: {p*q} < {min_notional}")
        return {"qty": q, "price": p}

    # ---- public api ----
    def buy_market(self, pair: str, qty: float, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        symbol = _to_symbol(pair)
        norm = self._normalize_qty_price(symbol, qty)
        params = {
            "symbol": symbol, "side": "BUY", "type": "MARKET",
            "quantity": f"{norm['qty']:.8f}",
            "newClientOrderId": client_order_id or f"BUY:{symbol}:{int(time.time())}"
        }
        return self._req("POST", "/v3/order", params, signed=True)

    def sell_market(self, pair: str, qty: float, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        symbol = _to_symbol(pair)
        norm = self._normalize_qty_price(symbol, qty)
        params = {
            "symbol": symbol, "side": "SELL", "type": "MARKET",
            "quantity": f"{norm['qty']:.8f}",
            "newClientOrderId": client_order_id or f"SELL:{symbol}:{int(time.time())}"
        }
        return self._req("POST", "/v3/order", params, signed=True)

    def cancel_order(self, pair: str, order_id: str) -> Dict[str, Any]:
        symbol = _to_symbol(pair)
        return self._req("DELETE", "/v3/order", {"symbol": symbol, "orderId": order_id}, signed=True)

    def get_order(self, pair: str, order_id: str) -> Dict[str, Any]:
        symbol = _to_symbol(pair)
        return self._req("GET", "/v3/order", {"symbol": symbol, "orderId": order_id}, signed=True)
