# database/trade_service.py
from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from . import crud
from .models import Side, OrderType, OrderStatus, Position
from .schemas import PositionCreate

# ---- утилиты ----
def d(x: float | Decimal | None) -> Decimal:
    return Decimal(str(x or 0))

def calc_realized_pnl_long(entry: Decimal, exit: Decimal, qty: Decimal, total_fees: Decimal = Decimal("0")) -> Decimal:
    """
    PnL для LONG: (exit - entry) * qty - fees
    """
    return (d(exit) - d(entry)) * d(qty) - d(total_fees)

def make_client_order_id(prefix: str, symbol: str, ts: datetime) -> str:
    # простой детерминированный cid
    return f"{prefix}:{symbol}:{ts.strftime('%Y%m%d%H%M%S')}"


# ---- 1) Открытие позиции и создание входного ордера ----
def open_long_with_entry_order(
    db: Session,
    *,
    symbol: str,
    entry_price: float,
    stop_price: Optional[float],
    qty: float,
    strategy: str = "trend_ema_rsi",
    strategy_version: str = "v1",
    tp1_price: Optional[float] = None,
    client_ts: Optional[datetime] = None,
) -> Tuple[Position, int]:
    """
    Создаёт Position(OPEN) и entry-ордер (MARKET по умолчанию).
    Возвращает (позиция, order_id).
    """
    pos = crud.open_position(
        db,
        symbol=symbol,
        side=Side.LONG,
        qty=qty,
        entry_price=entry_price,      # предварительное — будет уточнено после fill
        stop_price=stop_price,
        tp1_price=tp1_price,
        strategy=strategy,
        strategy_version=strategy_version,
        exchange="binance",
    )
    cid = make_client_order_id("ENTRY", symbol, client_ts or datetime.utcnow())
    entry_order = crud.create_order(
        db,
        position_id=pos.id,
        client_order_id=cid,
        symbol=symbol,
        side=Side.LONG,
        type=OrderType.MARKET,
        qty=qty,
        is_protective=False,
    )
    db.commit()
    db.refresh(pos)
    return pos, entry_order.id


# ---- 2) Обработка исполнения входного ордера ----
def on_entry_fill(
    db: Session,
    *,
    order_id: int,
    filled_qty: float,
    avg_price: float,
    exchange_order_id: Optional[str] = None,
    fee: float = 0.0,
    fee_asset: Optional[str] = None,
) -> None:
    """
    Фиксируем fill, обновляем позицию фактической ценой входа.
    """
    order = db.get(crud.Order, order_id)
    if not order:
        raise ValueError("Order not found")

    crud.set_order_exchange_ids_and_status(db, order, exchange_order_id=exchange_order_id, status=OrderStatus.PARTIALLY_FILLED)
    crud.update_order_fill(db, order, filled_qty=filled_qty, avg_price=avg_price, status=OrderStatus.FILLED)
    crud.add_trade_fill(db, order_id=order.id, price=avg_price, qty=filled_qty, fee=fee, fee_asset=fee_asset)

    pos = db.get(crud.Position, order.position_id)
    # Обновляем позицию «фактическим» входом и количеством
    pos.entry_price = Decimal(str(avg_price))
    pos.qty = Decimal(str(filled_qty))
    db.add(pos)

    db.commit()


# ---- 3) Установка защитных ордеров ----
def place_protective_orders_after_entry(
    db: Session,
    *,
    position_id: int,
    stop_price: Optional[float],
    tp1_price: Optional[float] = None,
) -> Tuple[Optional[int], Optional[int]]:
    """
    Создаём стоп и (опц.) тейк как отдельные ордера (если нет поддержки OCO).
    Возвращает (stop_order_id, tp1_order_id).
    """
    pos = db.get(crud.Position, position_id)
    if not pos:
        raise ValueError("Position not found")

    stop_order_id = None
    tp1_order_id = None

    if stop_price:
        stop_order = crud.create_order(
            db,
            position_id=pos.id,
            client_order_id=make_client_order_id("STOP", pos.symbol, datetime.utcnow()),
            symbol=pos.symbol,
            side=Side.SHORT,  # закрывает LONG
            type=OrderType.STOP_MARKET,
            qty=float(pos.qty),
            stop_price=stop_price,
            is_protective=True,
        )
        stop_order_id = stop_order.id

    if tp1_price:
        tp_order = crud.create_order(
            db,
            position_id=pos.id,
            client_order_id=make_client_order_id("TP1", pos.symbol, datetime.utcnow()),
            symbol=pos.symbol,
            side=Side.SHORT,
            type=OrderType.LIMIT,
            qty=float(pos.qty) * 0.5,   # пример: половина объёма
            price=tp1_price,
            is_protective=True,
        )
        tp1_order_id = tp_order.id

    db.commit()
    return stop_order_id, tp1_order_id


# ---- 4) Закрытие позиции по рынку ----
def close_position_market(
    db: Session,
    *,
    position_id: int,
    exit_price: float,
    fee: float = 0.0,
) -> Decimal:
    """
    Закрываем всю позицию по рынку. Считаем реализованный PnL (для LONG).
    """
    pos = db.get(crud.Position, position_id)
    if not pos:
        raise ValueError("Position not found")

    # Создаём рыночный ордер на закрытие
    exit_order = crud.create_order(
        db,
        position_id=pos.id,
        client_order_id=make_client_order_id("EXIT", pos.symbol, datetime.utcnow()),
        symbol=pos.symbol,
        side=Side.SHORT,
        type=OrderType.MARKET,
        qty=float(pos.qty),
    )
    crud.update_order_fill(db, exit_order, filled_qty=float(pos.qty), avg_price=exit_price, status=OrderStatus.FILLED)
    crud.add_trade_fill(db, order_id=exit_order.id, price=exit_price, qty=float(pos.qty), fee=fee)

    realized = calc_realized_pnl_long(
        entry=pos.entry_price, exit=Decimal(str(exit_price)), qty=pos.qty, total_fees=Decimal(str(fee))
    )
    crud.close_position(db, pos, realized_pnl=float(realized), fees_paid=float(fee))
    db.commit()
    return realized


# ---- 5) Обновление дневного PnL (для kill-switch) ----
def update_daily_pnl_after_close(db: Session, *, realized_delta: float, equity: float) -> None:
    today = date.today()
    crud.upsert_daily_pnl(db, day=today, realized_delta=realized_delta, unrealized=0.0, equity=equity)
    db.commit()
