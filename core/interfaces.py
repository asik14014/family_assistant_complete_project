# core/interfaces.py
from typing import Dict, Any, Iterable
from datetime import datetime

class AbstractExchangeAdapter:
    def buy_market(self, pair: str, qty: float, client_order_id: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def sell_market(self, pair: str, qty: float, client_order_id: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def cancel_order(self, pair: str, order_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_order(self, pair: str, order_id: str) -> Dict[str, Any]:
        raise NotImplementedError


class AbstractMarketDataFeed:
    def history(self, limit: int = 500) -> list[Dict[str, Any]]:
        """История баров"""
        raise NotImplementedError

    def stream(self) -> Iterable[Dict[str, Any]]:
        """Итератор закрытых баров"""
        raise NotImplementedError
