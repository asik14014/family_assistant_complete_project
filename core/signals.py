# кроссы, фильтры
import pandas as pd

def crosses_above(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left.shift(1) <= right.shift(1)) & (left > right)

def crosses_below(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left.shift(1) >= right.shift(1)) & (left < right)

def confirm(series_bool: pd.Series, bars: int) -> pd.Series:
    """TRUE, если сигнал был TRUE N последних баров подряд (простое подтверждение)."""
    return series_bool.rolling(bars).apply(lambda x: x.all(), raw=False).astype(bool)
