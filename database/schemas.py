# database/schemas.py
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

# Дублируем значения перечислений как строки (для API/валидации)
class Side(str):
    LONG = "LONG"
    SHORT = "SHORT"

class OrderType(str):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(str):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

# ---- Positions ----
class PositionCreate(BaseModel):
    symbol: str
    side: str = Side.LONG
    qty: float
    entry_price: float
    stop_price: Optional[float] = None
    tp1_price: Optional[float] = None
    strategy: str = "trend_ema_rsi"
    strategy_version: str = "v1"
    exchange: str = "binance"

class PositionRead(BaseModel):
    id: int
    symbol: str
    side: str
    qty: float
    entry_price: float
    stop_price: Optional[float]
    tp1_price: Optional[float]
    opened_at: datetime
    closed_at: Optional[datetime]
    realized_pnl: Optional[float]
    fees_paid: Optional[float]
    class Config:
        from_attributes = True

# ---- Orders ----
class OrderCreate(BaseModel):
    position_id: int
    client_order_id: str
    symbol: str
    side: str
    type: str
    qty: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    is_protective: bool = False

class OrderRead(BaseModel):
    id: int
    position_id: int
    client_order_id: str
    exchange_order_id: Optional[str]
    symbol: str
    side: str
    type: str
    status: str
    price: Optional[float]
    stop_price: Optional[float]
    qty: float
    filled_qty: float
    avg_fill_price: Optional[float]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ---- Trades ----
class TradeCreate(BaseModel):
    order_id: int
    price: float
    qty: float
    fee: float = 0.0
    fee_asset: Optional[str] = None
    exchange_trade_id: Optional[str] = None
    ts: Optional[datetime] = None

class TradeRead(BaseModel):
    id: int
    order_id: int
    price: float
    qty: float
    fee: Optional[float]
    fee_asset: Optional[str]
    ts: datetime
    class Config:
        from_attributes = True

# ---- Signal Log ----
class SignalLogCreate(BaseModel):
    symbol: str
    timeframe: str
    bar_ts: datetime
    strategy: str = "trend_ema_rsi"
    strategy_version: str = "v1"
    ema_fast: float
    ema_slow: float
    rsi: float
    atr: float
    entry_signal: bool
    exit_signal: bool
    decided_action: str = "HOLD"
    notes: Optional[str] = None

class SignalLogRead(BaseModel):
    id: int
    symbol: str
    timeframe: str
    bar_ts: datetime
    strategy: str
    ema_fast: float
    ema_slow: float
    rsi: float
    atr: float
    entry_signal: bool
    exit_signal: bool
    decided_action: str
    notes: Optional[str]
    class Config:
        from_attributes = True

# ---- Daily PnL ----
class DailyPnLUpsert(BaseModel):
    day: date
    realized_delta: float = 0.0
    unrealized: float = 0.0
    equity: Optional[float] = None

class DailyPnLRead(BaseModel):
    id: int
    day: date
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    class Config:
        from_attributes = True
