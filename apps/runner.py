# основной луп
from services.trading_service import TradingService
from core.data_feed import MarketDataFeedImpl      # твоя реализация
from core.execution import ExecutionAdapterImpl    # твоя реализация

def main():
    feed = MarketDataFeedImpl(pair="ETH/USDT", timeframe="15m")  # реализуй history()/stream()
    ex   = ExecutionAdapterImpl(...)                             # ccxt/ключи/лимиты

    svc = TradingService(
        pair="ETH/USDT",
        timeframe="15m",
        data_feed=feed,
        exchange=ex,
        equity_provider=lambda: 10_000.0,  # подставь свою функцию/БД
        cfg_path="config.yaml",
    )

    # backfill + live loop on bar close
    for bar in feed.stream():        # yield закрытые бары
        svc.on_bar_close(bar)

if __name__ == "__main__":
    main()