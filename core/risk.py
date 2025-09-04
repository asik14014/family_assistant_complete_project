# дневные лимиты, size calc, ATR-стоп
from .types import Position, Side
from dataclasses import dataclass

@dataclass
class RiskConfig:
    per_trade_risk_pct: float
    max_daily_loss_pct: float
    stop_atr_mult: float

class RiskEngine:
    def __init__(self, cfg: RiskConfig, equity_provider):
        self.cfg = cfg
        self.equity_provider = equity_provider  # функция или объект, возвращающий текущий equity

    def position_size(self, price: float, atr_val: float) -> float:
        equity = self.equity_provider()
        risk_amount = equity * (self.cfg.per_trade_risk_pct / 100.0)
        stop_dist = atr_val * self.cfg.stop_atr_mult
        if stop_dist <= 0: 
            return 0.0
        qty = risk_amount / stop_dist
        return max(qty, 0.0)

    def daily_kill_switch(self, day_pnl_pct: float) -> bool:
        return day_pnl_pct <= -abs(self.cfg.max_daily_loss_pct)
