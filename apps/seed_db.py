from __future__ import annotations
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
import random

# Попытка импортировать готовые engine/Session из твоего модуля БД
# Если у тебя они в другом месте (например, database.session), просто поправь импорт ниже.
try:
    from database.db import Base, SessionLocal, engine
except Exception:
    # Fallback: создадим engine/session из переменной окружения DB_URL (или SQLite по умолчанию)
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base as _Base  # чтобы точно получить Base
    DB_URL = os.getenv("DB_URL", "sqlite:///./tradingbot_mvp.db")
    engine = create_engine(DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base = _Base

from database.models import (
    Position, Order, Trade, SignalLog, DailyPnL,
    PositionStatus, Side, OrderType, OrderStatus
)

UTC = timezone.utc

def d(val: float) -> Decimal:
    # округлим до 10 знаков после запятой под Numeric(28,10)
    return Decimal(str(round(val, 10)))

def seed_positions_orders_trades(session):
    now = datetime.now(UTC)

    # ===== Позиция 1: LONG (OPEN) по BTC/USDT =====
    p1 = Position(
        symbol="BTC/USDT",
        exchange="binance",
        strategy="trend_ema_rsi",
        strategy_version="v1",
        status=PositionStatus.OPEN,
        side=Side.LONG,
        qty=d(0.0123),
        entry_price=d(65250.0),
        stop_price=d(64200.0),
        tp1_price=d(66600.0),
        opened_at=now - timedelta(hours=6),
        realized_pnl=None,
        fees_paid=None,
        notes="seed: open long"
    )
    session.add(p1); session.flush()

    # Ордер входа (filled)
    o1 = Order(
        position_id=p1.id,
        client_order_id=f"seed-enter-btc-{random.randint(1000,9999)}",
        exchange_order_id=None,
        symbol=p1.symbol,
        side=p1.side,
        type=OrderType.MARKET,
        status=OrderStatus.FILLED,
        price=None,
        stop_price=None,
        qty=p1.qty,
        filled_qty=p1.qty,
        avg_fill_price=p1.entry_price,
        is_protective=False,
        created_at=p1.opened_at,
        updated_at=p1.opened_at
    )
    session.add(o1); session.flush()

    # Трейд (fill) по входу
    t1 = Trade(
        order_id=o1.id,
        exchange_trade_id=f"tr-{random.randint(10_000,99_999)}",
        price=p1.entry_price,
        qty=p1.qty,
        fee=d(0.2),         # условно 0.2 USDT
        fee_asset="USDT",
        ts=p1.opened_at
    )
    session.add(t1)

    # Защитный стоп (активный, пока не сработал)
    o1s = Order(
        position_id=p1.id,
        client_order_id=f"seed-sl-btc-{random.randint(1000,9999)}",
        exchange_order_id=None,
        symbol=p1.symbol,
        side=Side.SHORT,  # закрывает long
        type=OrderType.STOP_MARKET,
        status=OrderStatus.NEW,
        price=None,
        stop_price=p1.stop_price,
        qty=p1.qty,
        filled_qty=d(0),
        avg_fill_price=None,
        is_protective=True,
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=6)
    )
    session.add(o1s)

    # ===== Позиция 2: SHORT (OPEN) по ETH/USDT =====
    p2 = Position(
        symbol="ETH/USDT",
        exchange="binance",
        strategy="trend_ema_rsi",
        strategy_version="v1",
        status=PositionStatus.OPEN,
        side=Side.SHORT,
        qty=d(0.85),
        entry_price=d(3450.0),
        stop_price=d(3525.0),
        tp1_price=d(3350.0),
        opened_at=now - timedelta(hours=2),
        realized_pnl=None,
        fees_paid=None,
        notes="seed: open short"
    )
    session.add(p2); session.flush()

    o2 = Order(
        position_id=p2.id,
        client_order_id=f"seed-enter-eth-{random.randint(1000,9999)}",
        exchange_order_id=None,
        symbol=p2.symbol,
        side=p2.side,
        type=OrderType.MARKET,
        status=OrderStatus.FILLED,
        price=None,
        stop_price=None,
        qty=p2.qty,
        filled_qty=p2.qty,
        avg_fill_price=p2.entry_price,
        is_protective=False,
        created_at=p2.opened_at,
        updated_at=p2.opened_at
    )
    session.add(o2); session.flush()

    t2 = Trade(
        order_id=o2.id,
        exchange_trade_id=f"tr-{random.randint(10_000,99_999)}",
        price=p2.entry_price,
        qty=p2.qty,
        fee=d(0.12),
        fee_asset="USDT",
        ts=p2.opened_at
    )
    session.add(t2)

    o2s = Order(
        position_id=p2.id,
        client_order_id=f"seed-sl-eth-{random.randint(1000,9999)}",
        exchange_order_id=None,
        symbol=p2.symbol,
        side=Side.LONG,  # закрывает short
        type=OrderType.STOP_MARKET,
        status=OrderStatus.NEW,
        price=None,
        stop_price=p2.stop_price,
        qty=p2.qty,
        filled_qty=d(0),
        avg_fill_price=None,
        is_protective=True,
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2)
    )
    session.add(o2s)

    # ===== Позиция 3: LONG (CLOSED) по BTC/USDT — уже закрыта, чтобы были realized_pnl =====
    entry_price = 64000.0
    exit_price  = 64880.0
    qty3 = 0.015
    realized = (exit_price - entry_price) * qty3  # грубая оценка PnL
    p3 = Position(
        symbol="BTC/USDT",
        exchange="binance",
        strategy="trend_ema_rsi",
        strategy_version="v1",
        status=PositionStatus.CLOSED,
        side=Side.LONG,
        qty=d(qty3),
        entry_price=d(entry_price),
        stop_price=d(63200.0),
        tp1_price=d(65000.0),
        opened_at=now - timedelta(days=1, hours=5),
        closed_at=now - timedelta(days=1, hours=3),
        realized_pnl=d(realized),
        fees_paid=d(0.22),
        notes="seed: closed long"
    )
    session.add(p3); session.flush()

    o3_in = Order(
        position_id=p3.id,
        client_order_id=f"seed-enter-btc2-{random.randint(1000,9999)}",
        exchange_order_id=None,
        symbol=p3.symbol,
        side=p3.side,
        type=OrderType.MARKET,
        status=OrderStatus.FILLED,
        qty=d(qty3),
        filled_qty=d(qty3),
        avg_fill_price=d(entry_price),
        is_protective=False,
        created_at=p3.opened_at,
        updated_at=p3.opened_at
    )
    session.add(o3_in); session.flush()

    t3_in = Trade(
        order_id=o3_in.id,
        exchange_trade_id=f"tr-{random.randint(10_000,99_999)}",
        price=d(entry_price),
        qty=d(qty3),
        fee=d(0.11),
        fee_asset="USDT",
        ts=p3.opened_at
    )
    session.add(t3_in)

    o3_out = Order(
        position_id=p3.id,
        client_order_id=f"seed-exit-btc2-{random.randint(1000,9999)}",
        exchange_order_id=None,
        symbol=p3.symbol,
        side=Side.SHORT,  # закрытие long
        type=OrderType.MARKET,
        status=OrderStatus.FILLED,
        qty=d(qty3),
        filled_qty=d(qty3),
        avg_fill_price=d(exit_price),
        is_protective=False,
        created_at=p3.closed_at,
        updated_at=p3.closed_at
    )
    session.add(o3_out); session.flush()

    t3_out = Trade(
        order_id=o3_out.id,
        exchange_trade_id=f"tr-{random.randint(10_000,99_999)}",
        price=d(exit_price),
        qty=d(qty3),
        fee=d(0.11),
        fee_asset="USDT",
        ts=p3.closed_at
    )
    session.add(t3_out)


def seed_signal_logs(session):
    """Сгенерируем сигналы за ~48 часов по BTC/USDT и ETH/USDT, TF=15m."""
    now = datetime.now(UTC)
    for sym in ("BTC/USDT", "ETH/USDT"):
        ts = now - timedelta(hours=48)
        while ts <= now:
            # «технические» показатели — правдоподобные значения
            ema_fast = 0.0
            ema_slow = 0.0
            rsi = random.uniform(35.0, 70.0)
            atr = random.uniform(30.0, 150.0) if sym.startswith("BTC") else random.uniform(1.5, 15.0)

            # раз в 10 баров — вход, раз в 25 — выход
            idx = int((now - ts).total_seconds() // (15 * 60))
            entry = (idx % 10 == 0)
            exit_ = (idx % 25 == 0)

            log = SignalLog(
                symbol=sym,
                timeframe="15m",
                bar_ts=ts,
                strategy="trend_ema_rsi",
                strategy_version="v1",
                ema_fast=d(ema_fast),
                ema_slow=d(ema_slow),
                rsi=d(rsi),
                atr=d(atr),
                entry_signal=entry,
                exit_signal=exit_,
                decided_action=("BUY" if entry else ("SELL" if exit_ else "HOLD")),
                notes=None
            )
            session.add(log)
            ts += timedelta(minutes=15)


def seed_daily_pnl(session, days: int = 30, start_equity: float = 10000.0):
    """30 дней PnL + equity (кумулятивная)."""
    today = date.today()
    equity = start_equity
    for i in range(days, 0, -1):
        day = today - timedelta(days=i)
        # правдоподобный дневной результат
        pnl_realized = random.uniform(-180.0, 260.0)
        pnl_unreal = random.uniform(-60.0, 60.0)
        equity += pnl_realized + pnl_unreal * 0.2  # часть нереализ. учитываем «визуально»

        dp = DailyPnL(
            day=day,
            realized_pnl=d(pnl_realized),
            unrealized_pnl=d(pnl_unreal),
            equity=d(equity),
            updated_at=datetime.now(UTC)
        )
        session.add(dp)


def main():
    # Создаём схему, если ещё нет
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        seed_positions_orders_trades(session)
        seed_signal_logs(session)
        seed_daily_pnl(session, days=30, start_equity=10000.0)
        session.commit()

    print("✅ Dummy data inserted: positions, orders, trades, signal_logs, daily_pnl")


if __name__ == "__main__":
    main()
