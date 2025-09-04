# WS/REST свечи
from typing import Iterable, List
from .types import Bar

class MarketDataFeed:
    """Заглушка: заменишь на ccxtpro или прямой WS. Должен yield готовые закрытые бары."""
    def __init__(self, pair: str, timeframe: str):
        self.pair, self.timeframe = pair, timeframe

    def history(self, limit: int) -> List[Bar]:
        """Верни последние N баров для стартового расчёта индикаторов (REST backfill)."""
        raise NotImplementedError

    def stream(self) -> Iterable[Bar]:
        """Итерируй закрытые бары (on bar close)."""
        raise NotImplementedError
