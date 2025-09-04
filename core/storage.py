# Redis/PG (позы, сделки, метрики)
from .types import Position, Side

class InMemoryStore:
    def __init__(self):
        self.position = Position(side=Side.FLAT, qty=0.0, entry=None, stop=None, tp1=None, meta={})
        self.day_pnl_pct = 0.0
        self.equity = 10_000.0  # стартовый equity

    def get_position(self) -> Position:
        return self.position

    def set_position(self, pos: Position):
        self.position = pos

    def get_equity(self) -> float:
        return self.equity

    def set_equity(self, value: float):
        self.equity = value

    def get_day_pnl_pct(self) -> float:
        return self.day_pnl_pct

    def set_day_pnl_pct(self, v: float):
        self.day_pnl_pct = v
