from __future__ import annotations
from datetime import datetime
from database.db import SessionLocal
from database import crud
from database.models import PositionStatus
from services.trading_service import TradingService

# Инициализируй глобально/через DI
svc = None  # присвоишь в apps/api.py после инициализации TradingService

def route_signal(*, symbol: str, timeframe: str, signal: str, price: float, bar_ts: datetime, source: str, meta: dict):
    """
    Минимальный роутер:
    - логируем сигнал
    - отдаём его в TradingService, который уже проверит риск/стейт
    """
    with SessionLocal() as db:
        crud.log_signal(
            db,
            symbol=symbol, timeframe=timeframe, bar_ts=bar_ts,
            strategy="trend_ema_rsi", strategy_version="v1",
            ema_fast=None, ema_slow=None, rsi=None, atr=None,
            entry_signal=(signal == "BUY"), exit_signal=(signal == "SELL"),
            decided_action="FORWARDED", notes=f"source={source}"
        )
        db.commit()

    # Передаём «намерение»: BUY/SELL. Торговые решения остаются за сервисом.
    if signal == "BUY":
        svc.force_buy_intent(symbol=symbol, ref_price=price, bar_ts=bar_ts, source=source)
    elif signal == "SELL":
        svc.force_sell_intent(symbol=symbol, ref_price=price, bar_ts=bar_ts, source=source)
