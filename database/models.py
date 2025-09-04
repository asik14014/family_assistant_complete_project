from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, DateTime, Date, Enum as SQLEnum,
    ForeignKey, Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .db import Base

# ====== Enums ======
class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

# ====== Positions ======
class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)          # e.g. ETH/USDT
    exchange: Mapped[str] = mapped_column(String(32), default="binance") # optional
    strategy: Mapped[str] = mapped_column(String(64), index=True)        # e.g. "trend_ema_rsi"
    strategy_version: Mapped[str] = mapped_column(String(32), default="v1")

    status: Mapped[PositionStatus] = mapped_column(SQLEnum(PositionStatus), default=PositionStatus.OPEN, index=True)
    side: Mapped[Side] = mapped_column(SQLEnum(Side), index=True)

    qty: Mapped[float] = mapped_column(Numeric(28, 10))
    entry_price: Mapped[float] = mapped_column(Numeric(28, 10))
    stop_price: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)
    tp1_price: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    realized_pnl: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)
    fees_paid: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="position", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_positions_status_symbol", "status", "symbol"),
    )

# ====== Orders ======
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)

    client_order_id: Mapped[str] = mapped_column(String(64), index=True)      # ваш идемпотентный id
    exchange_order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[Side] = mapped_column(SQLEnum(Side))
    type: Mapped[OrderType] = mapped_column(SQLEnum(OrderType))
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.NEW, index=True)

    price: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)
    stop_price: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(28, 10))
    filled_qty: Mapped[float] = mapped_column(Numeric(28, 10), default=0)
    avg_fill_price: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)

    is_protective: Mapped[bool] = mapped_column(Boolean, default=False)  # стоп/тейк/oco
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    position: Mapped["Position"] = relationship("Position", back_populates="orders")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("client_order_id", name="uq_orders_client_order_id"),
        Index("ix_orders_symbol_status", "symbol", "status"),
    )


# ====== Trades (fills) ======
class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    exchange_trade_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    price: Mapped[float] = mapped_column(Numeric(28, 10))
    qty: Mapped[float] = mapped_column(Numeric(28, 10))
    fee: Mapped[Optional[float]] = mapped_column(Numeric(28, 10), nullable=True)
    fee_asset: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    order: Mapped["Order"] = relationship("Order", back_populates="trades")


# ====== Signal/Audit ======
class SignalLog(Base):
    __tablename__ = "signal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16))
    bar_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    strategy: Mapped[str] = mapped_column(String(64), index=True)
    strategy_version: Mapped[str] = mapped_column(String(32), default="v1")

    ema_fast: Mapped[Optional[float]] = mapped_column(Numeric(28, 10))
    ema_slow: Mapped[Optional[float]] = mapped_column(Numeric(28, 10))
    rsi: Mapped[Optional[float]] = mapped_column(Numeric(28, 10))
    atr: Mapped[Optional[float]] = mapped_column(Numeric(28, 10))

    entry_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    exit_signal: Mapped[bool] = mapped_column(Boolean, default=False)

    decided_action: Mapped[str] = mapped_column(String(16), default="HOLD")  # BUY/SELL/HOLD
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_signal_unique", "symbol", "timeframe", "bar_ts", unique=True),
    )


# ====== Daily PnL ======
class DailyPnL(Base):
    __tablename__ = "daily_pnl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day: Mapped[date] = mapped_column(Date, index=True, unique=True)
    realized_pnl: Mapped[float] = mapped_column(Numeric(28, 10), default=0)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(28, 10), default=0)
    equity: Mapped[float] = mapped_column(Numeric(28, 10), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)