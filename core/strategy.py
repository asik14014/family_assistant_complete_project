# state-machine: FLAT/LONG/EXIT
import pandas as pd
from .types import Position, Side

class TrendFollowingStrategy:
    def __init__(self, params: dict):
        self.params = params
        self.cooldown = 0  # бары до следующего входа

    def on_bar(self, df: pd.DataFrame, pos: Position) -> dict:
        """
        df: OHLCV + индикаторы ('ema_fast','ema_slow','rsi','atr')
        pos: текущее состояние позиции
        return: dict{action: 'BUY'|'SELL'|'HOLD', size, stop, tp1, reason}
        """
        last = df.iloc[-1]
        ema_f, ema_s, rsi = last['ema_fast'], last['ema_slow'], last['rsi']
        atr_val, close = last['atr'], last['close']

        # выход по правилам
        exit_cross = (df['ema_fast'].iloc[-2] >= df['ema_slow'].iloc[-2]) and (ema_f < ema_s)
        exit_rsi   = rsi > self.params['exit_rsi']

        if pos.side == Side.LONG and (exit_cross or exit_rsi):
            return dict(action='SELL', size=pos.qty, reason='exit')

        # вход
        if self.cooldown > 0:
            self.cooldown -= 1
            return dict(action='HOLD')

        entry_cross = (df['ema_fast'].iloc[-2] <= df['ema_slow'].iloc[-2]) and (ema_f > ema_s)
        entry_rsi   = rsi < self.params['entry_rsi']

        if pos.side == Side.FLAT and entry_cross and entry_rsi:
            stop = close - self.params['stop_atr_mult'] * atr_val
            # qty посчитает RiskEngine снаружи
            self.cooldown = self.params.get('cooldown_bars', 0)
            return dict(action='BUY', stop=stop, reason='entry')

        return dict(action='HOLD')
