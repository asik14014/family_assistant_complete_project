from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Callable

import pandas as pd
from sqlalchemy.orm import Session

# --- utils / core / db imports (адаптируй пути под свой проект) ---
from utils.config import load_config
from core.indicators import ema, rsi, atr
from core.strategy import TrendFollowingStrategy
from core.risk import RiskEngine, RiskConfig
from core.types import Side
from core.data_feed import MarketDataFeed          # твой реал фид (REST+WS)
from core.execution import ExecutionAdapter        # обёртка над биржей (ccxt/WS)

from database.db import SessionLocal
from database import crud
from database.models import OrderType, OrderStatus
from database.trade_service import (
    open_long_with_entry_order, on_entry_fill,
    place_protective_orders_after_entry, close_position_market,
    update_daily_pnl_after_close,
)
from database.schemas import SignalLogCreate


class TradingService:
    """
    Единый «оркестратор» Trend Following (EMA20/50 + RSI).
    Отвечает за:
      - расчёт индикаторов и сигналов (on bar close)
      - Risk checks (per-trade, daily kill-switch)
      - исполнение ордеров через ExchangeAdapter
      - запись всего аудита в Postgres (positions / orders / trades / signal_logs / daily_pnl)
    """

    def __init__(
        self,
        *,
        pair: str,
        timeframe: str,
        data_feed: MarketDataFeed,
        exchange: ExecutionAdapter,
        session_factory: Callable[[], Session] = SessionLocal,
        equity_provider: Callable[[], float] | None = None,
        strategy_name: str = "trend_ema_rsi",
        strategy_version: str = "v1",
        cfg_path: str = "config.yaml",
    ):
        self.pair = pair
        self.tf = timeframe
        self.feed = data_feed
        self.ex = exchange
        self.session_factory = session_factory
        self.strategy_name = strategy_name
        self.strategy_version = strategy_version

        cfg = load_config(cfg_path)
        self.params = {
            "entry_rsi": cfg.entry_long['all'][1]['right'],
            "exit_rsi":  cfg.exit_long['any'][1]['right'],
            "stop_atr_mult": cfg.risk['stop_atr_mult'],
            "cooldown_bars": cfg.entry_long.get('cooldown_bars', 0),
        }
        self.strat = TrendFollowingStrategy(self.params)

        self.risk = RiskEngine(
            RiskConfig(
                per_trade_risk_pct=cfg.risk['per_trade_risk_pct'],
                max_daily_loss_pct=cfg.risk['max_daily_loss_pct'],
                stop_atr_mult=cfg.risk['stop_atr_mult']
            ),
            equity_provider=equity_provider or (lambda: 10_000.0)
        )

    # ---------- Публичный вход: вызываем на закрытии свечи ----------
    def on_bar_close(self, bar: dict) -> None:
        """
        bar: dict with keys open, high, low, close, volume, ts (utc)
        """
        with self.session_factory() as db:
            # 1) соберём историю для индикаторов (можно хранить локально или тянуть из feed)
            hist = self._get_recent_history()  # pd.DataFrame
            hist = self._calc_indicators(hist)

            # 2) риск оверлей (kill switch)
            if self._is_kill_switch(db):
                self._log_signal(db, hist, entry=False, exit=False, decided="HOLD", notes="kill-switch")
                db.commit()
                return

            # 3) сигналы стратегии
            decided, ctx = self._decide_action(db, hist)

            # 4) исполнение
            if decided == "BUY":
                self._enter_long(db, hist, ctx)
            elif decided == "SELL":
                self._exit_long(db, hist, ctx)
            else:
                # менеджмент открытой позиции (трейлинг/перенос в б/у и т.п.)
                self._manage_open_position(db, hist)

            db.commit()

    # ---------- Внутренние шаги ----------
    def _get_recent_history(self) -> pd.DataFrame:
        """
        Загрузи последние N баров (REST backfill + кэш). Должны быть колонки:
        ['open','high','low','close','volume'] и index=datetime (UTC).
        """
        # Реализуй: self.feed.history(limit=500) -> list[Bar]
        raise NotImplementedError

    def _calc_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['ema_fast'] = ema(df['close'], 20)
        df['ema_slow'] = ema(df['close'], 50)
        df['rsi']      = rsi(df['close'], 14)
        df['atr']      = atr(df['high'], df['low'], df['close'], 14)
        return df.dropna()

    def _is_kill_switch(self, db: Session) -> bool:
        # дотяни дневной pnl из БД (или посчитай локально)
        today = date.today()
        row = db.scalar(crud.select(crud.DailyPnL).where(crud.DailyPnL.day == today))  # можно сделать helper
        if not row:
            return False
        return float(row.realized_pnl or 0) / max(float(row.equity or 1), 1) * 100 <= -abs(self.risk.cfg.max_daily_loss_pct)

    def _decide_action(self, db: Session, df: pd.DataFrame) -> tuple[str, dict]:
        pos = crud.get_open_position_by_symbol(db, self.pair)
        action = self.strat.on_bar(df, pos)  # BUY/SELL/HOLD
        entry_sig = action.get('action') == 'BUY'
        exit_sig  = action.get('action') == 'SELL'
        self._log_signal(db, df, entry=entry_sig, exit=exit_sig, decided=action['action'], notes=action.get('reason'))
        return action['action'], action

    def _enter_long(self, db: Session, df: pd.DataFrame, action_ctx: dict) -> None:
        last = df.iloc[-1]
        atr_val = float(last['atr'])
        price   = float(last['close'])

        # размер позиции с учётом ATR-стопа
        qty = float(self.risk.position_size(price=price, atr_val=atr_val))
        if qty <= 0:
            return

        # 1) создаём Position + entry order в БД
        pos, entry_order_id = open_long_with_entry_order(
            db,
            symbol=self.pair,
            entry_price=price,
            stop_price=action_ctx.get('stop') or (price - self.risk.cfg.stop_atr_mult * atr_val),
            qty=qty,
            strategy=self.strategy_name,
            strategy_version=self.strategy_version,
            tp1_price=None,  # можно посчитать как R=1
        )

        # 2) исполняем ордер на бирже
        #    (пример — market buy; верни exchange_order_id, price, filled_qty, fee)
        ex_res = self.ex.buy_market(self.pair, qty)
        filled_qty = qty   # адаптируй под ex_res
        avg_price  = price # адаптируй под ex_res
        fee        = 0.0

        # 3) фиксируем fill и ставим защиту (стоп/тейк)
        on_entry_fill(
            db,
            order_id=entry_order_id,
            filled_qty=filled_qty,
            avg_price=avg_price,
            exchange_order_id=str(ex_res.get("orderId", "")),
            fee=fee,
        )
        place_protective_orders_after_entry(
            db,
            position_id=pos.id,
            stop_price=action_ctx.get('stop') or (price - self.risk.cfg.stop_atr_mult * atr_val),
            tp1_price=None,
        )

    def _exit_long(self, db: Session, df: pd.DataFrame, action_ctx: dict) -> None:
        pos = crud.get_open_position_by_symbol(db, self.pair)
        if not pos:
            return
        price = float(df.iloc[-1]['close'])

        # исполняем закрытие по рынку
        realized = close_position_market(db, position_id=pos.id, exit_price=price, fee=0.0)
        # апдейтим дневной PnL (для kill-switch)
        equity = self.risk.equity_provider() + float(realized)
        update_daily_pnl_after_close(db, realized_delta=float(realized), equity=equity)

    def _manage_open_position(self, db: Session, df: pd.DataFrame) -> None:
        """
        Простейший менеджмент: перенос стопа в б/у при достижении R=1
        и трейлинг по Chandelier (atr*3). Расширишь под свой план.
        """
        pos = crud.get_open_position_by_symbol(db, self.pair)
        if not pos:
            return

        last = df.iloc[-1]
        atr_val = float(last['atr'])
        price   = float(last['close'])

        # перенос в безубыток при R>=1
        stop_target = float(pos.entry_price) - (pos.stop_price and float(pos.entry_price) - float(pos.stop_price) or 0)
        if stop_target > 0:
            r = (price - float(pos.entry_price)) / stop_target
            if r >= 1.0 and (not pos.stop_price or float(pos.stop_price) < float(pos.entry_price)):
                pos.stop_price = Decimal(str(pos.entry_price))  # б/у
                db.add(pos)

        # примитивный трейлинг (Chandelier)
        chand = price - 3.0 * atr_val
        if not pos.stop_price or float(pos.stop_price) < chand:
            pos.stop_price = Decimal(str(chand))
            db.add(pos)

        db.commit()

    # ---------- лог сигналов ----------
    def _log_signal(self, db: Session, df: pd.DataFrame, *, entry: bool, exit: bool, decided: str, notes: Optional[str]) -> None:
        last = df.iloc[-1]
        crud.log_signal(
            db,
            symbol=self.pair,
            timeframe=self.tf,
            bar_ts=pd.Timestamp(last.name).to_pydatetime(),
            strategy=self.strategy_name,
            strategy_version=self.strategy_version,
            ema_fast=float(last['ema_fast']),
            ema_slow=float(last['ema_slow']),
            rsi=float(last['rsi']),
            atr=float(last['atr']),
            entry_signal=entry,
            exit_signal=exit,
            decided_action=decided,
            notes=notes,
        )

    # в services/trading_service.py
    def force_buy_intent(self, *, symbol: str, ref_price: float, bar_ts, source: str):
        # Проверка: позиция не открыта, нет kill-switch, cooldown и т.д.
        with self.session_factory() as db:
            pos = crud.get_open_position_by_symbol(db, symbol)
            if pos: return
            # рассчитать ATR из истории (или принять вход по ref_price)
            hist = self._get_recent_history()
            hist = self._calc_indicators(hist)
            # можно добавить лёгкий фильтр: rsi<65, ema_fast>ema_slow
            self._enter_long(db, hist, {"stop": None})  # внутри посчитает размер/стоп

    def force_sell_intent(self, *, symbol: str, ref_price: float, bar_ts, source: str):
        with self.session_factory() as db:
            pos = crud.get_open_position_by_symbol(db, symbol)
            if not pos: return
            hist = self._get_recent_history()
            hist = self._calc_indicators(hist)
            self._exit_long(db, hist, {"reason": f"tv:{source}"})

