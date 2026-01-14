from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Iterable
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from .models import (
    Position, Order, Trade, SignalLog, DailyPnL,
    PositionStatus, OrderStatus, OrderType, Side
)

# ---------- POSITIONS ----------
def get_open_position_by_symbol(db: Session, symbol: str) -> Optional[Position]:
    stmt = select(Position).where(
        Position.symbol == symbol,
        Position.status == PositionStatus.OPEN
    ).limit(1)
    return db.scalar(stmt)

def open_position(
    db: Session,
    *,
    symbol: str,
    side: Side,
    qty: float,
    entry_price: float,
    stop_price: Optional[float],
    tp1_price: Optional[float],
    strategy: str,
    strategy_version: str,
    exchange: str = "binance",
) -> Position:
    pos = Position(
        symbol=symbol, exchange=exchange, strategy=strategy, strategy_version=strategy_version,
        status=PositionStatus.OPEN, side=side,
        qty=qty, entry_price=entry_price, stop_price=stop_price, tp1_price=tp1_price
    )
    db.add(pos)
    db.flush()  # получить pos.id
    return pos

def close_position(
    db: Session, pos: Position, *, realized_pnl: float = 0.0, fees_paid: float = 0.0
) -> Position:
    pos.status = PositionStatus.CLOSED
    pos.closed_at = datetime.utcnow()
    pos.realized_pnl = realized_pnl
    pos.fees_paid = fees_paid
    db.add(pos)
    return pos


# ---------- ORDERS ----------
def create_order(
    db: Session,
    *,
    position_id: int,
    client_order_id: str,
    symbol: str,
    side: Side,
    type: OrderType,
    qty: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
    is_protective: bool = False,
) -> Order:
    order = Order(
        position_id=position_id,
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
        type=type,
        qty=qty,
        price=price,
        stop_price=stop_price,
        is_protective=is_protective,
        status=OrderStatus.NEW,
    )
    db.add(order)
    db.flush()
    return order

def set_order_exchange_ids_and_status(
    db: Session, order: Order, *, exchange_order_id: Optional[str], status: OrderStatus
) -> Order:
    order.exchange_order_id = exchange_order_id
    order.status = status
    order.updated_at = datetime.utcnow()
    db.add(order)
    return order

def update_order_fill(
    db: Session, order: Order, *, filled_qty: float, avg_price: Optional[float], status: OrderStatus
) -> Order:
    order.filled_qty = (order.filled_qty or 0) + filled_qty
    # если пришла усреднённая цена — пересчитай (простой способ)
    order.avg_fill_price = avg_price or order.avg_fill_price
    order.status = status
    order.updated_at = datetime.utcnow()
    db.add(order)
    return order

def cancel_order(db: Session, order: Order) -> Order:
    order.status = OrderStatus.CANCELED
    order.updated_at = datetime.utcnow()
    db.add(order)
    return order

def get_open_orders_by_position(db: Session, position_id: int) -> list[Order]:
    stmt = select(Order).where(
        Order.position_id == position_id,
        Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED])
    )
    return list(db.scalars(stmt))


# ---------- TRADES (fills) ----------
def add_trade_fill(
    db: Session,
    *,
    order_id: int,
    price: float,
    qty: float,
    fee: float = 0.0,
    fee_asset: Optional[str] = None,
    exchange_trade_id: Optional[str] = None,
    ts: Optional[datetime] = None,
) -> Trade:
    trade = Trade(
        order_id=order_id,
        price=price,
        qty=qty,
        fee=fee,
        fee_asset=fee_asset,
        exchange_trade_id=exchange_trade_id,
        ts=ts or datetime.utcnow(),
    )
    db.add(trade)
    db.flush()
    return trade

def get_trades_by_order(db: Session, order_id: int) -> list[Trade]:
    stmt = select(Trade).where(Trade.order_id == order_id).order_by(Trade.ts.asc())
    return list(db.scalars(stmt))


# ---------- SIGNAL LOG ----------
def log_signal(
    db: Session,
    *,
    symbol: str,
    timeframe: str,
    bar_ts: datetime,
    strategy: str,
    strategy_version: str,
    ema_fast: float,
    ema_slow: float,
    rsi: float,
    atr: float,
    entry_signal: bool,
    exit_signal: bool,
    decided_action: str,
    notes: Optional[str] = None,
) -> SignalLog:
    row = SignalLog(
        symbol=symbol, timeframe=timeframe, bar_ts=bar_ts,
        strategy=strategy, strategy_version=strategy_version,
        ema_fast=ema_fast, ema_slow=ema_slow, rsi=rsi, atr=atr,
        entry_signal=entry_signal, exit_signal=exit_signal,
        decided_action=decided_action, notes=notes
    )
    db.add(row)
    return row


# ---------- DAILY PNL ----------
def upsert_daily_pnl(
    db: Session,
    *,
    day: date,
    realized_delta: float = 0.0,
    unrealized: float = 0.0,
    equity: Optional[float] = None,
) -> DailyPnL:
    row = db.scalar(select(DailyPnL).where(DailyPnL.day == day))
    if not row:
        row = DailyPnL(day=day, realized_pnl=realized_delta, unrealized_pnl=unrealized, equity=equity or 0)
        db.add(row)
    else:
        row.realized_pnl = (row.realized_pnl or 0) + realized_delta
        row.unrealized_pnl = unrealized
        if equity is not None:
            row.equity = equity
        row.updated_at = datetime.utcnow()
        db.add(row)
    return row
