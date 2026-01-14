import pandas as pd
from utils.config import load_config
from core.storage import InMemoryStore
from core.indicators import ema, rsi, atr
from core.strategy import TrendFollowingStrategy
from core.risk import RiskEngine, RiskConfig
from core.types import Side

# В реале сюда подключишь MarketDataFeed(history+stream) и ExecutionAdapter
def run_once(df: pd.DataFrame, cfg, store):
    # расчёт индикаторов
    df['ema_fast'] = ema(df['close'], cfg.indicators['ema_fast']['length'])
    df['ema_slow'] = ema(df['close'], cfg.indicators['ema_slow']['length'])
    df['rsi']      = rsi(df['close'], cfg.indicators['rsi']['length'])
    df['atr']      = atr(df['high'], df['low'], df['close'], cfg.indicators['atr']['length'])
    df = df.dropna()

    strat = TrendFollowingStrategy({
        "entry_rsi": cfg.entry_long['all'][1]['right'],  # 65
        "exit_rsi":  cfg.exit_long['any'][1]['right'],   # 75
        "stop_atr_mult": cfg.risk['stop_atr_mult'],
        "cooldown_bars": cfg.entry_long.get('cooldown_bars', 0),
    })

    risk = RiskEngine(
        RiskConfig(
            per_trade_risk_pct=cfg.risk['per_trade_risk_pct'],
            max_daily_loss_pct=cfg.risk['max_daily_loss_pct'],
            stop_atr_mult=cfg.risk['stop_atr_mult']
        ),
        equity_provider=store.get_equity
    )

    pos = store.get_position()
    action = strat.on_bar(df, pos)

    if action['action'] == 'BUY':
        last = df.iloc[-1]
        size = risk.position_size(price=last['close'], atr_val=last['atr'])
        if size > 0:
            pos.side = Side.LONG
            pos.qty = size
            pos.entry = float(last['close'])
            pos.stop  = float(action.get('stop', pos.entry - 2*last['atr']))
            store.set_position(pos)
            print(f"[BUY] qty={size:.4f} entry={pos.entry:.2f} stop={pos.stop:.2f} reason={action['reason']}")

    elif action['action'] == 'SELL' and pos.side == Side.LONG:
        last = df.iloc[-1]
        pnl = (last['close'] - (pos.entry or last['close'])) * pos.qty
        # обнови equity/PNL как нужно
        pos.side = Side.FLAT
        pos.qty = 0.0
        pos.entry = None
        pos.stop = None
        store.set_position(pos)
        print(f"[SELL] flat at {last['close']:.2f}; pnl={pnl:.2f} reason={action['reason']}")
    else:
        print("[HOLD]")

if __name__ == "__main__":
    cfg = load_config()
    store = InMemoryStore()

    # Заглушка истории: подставь сюда данные (OHLCV) из REST биржи
    # df должны содержать: index=datetime, columns=['open','high','low','close','volume']
    df = pd.DataFrame([
        # ... наполни историей ...
    ], columns=['open','high','low','close','volume'])
    # Пример: df = load_from_exchange(pair=cfg.pair, tf=cfg.timeframe, limit=500)

    if len(df) >= 100:
        run_once(df, cfg, store)
    else:
        print("Нужно больше исторических баров (>=100).")
