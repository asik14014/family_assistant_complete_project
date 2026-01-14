# модели pydantic
import yaml
from dataclasses import dataclass

@dataclass
class Config:
    pair: str
    timeframe: str
    indicators: dict
    entry_long: dict
    exit_long: dict
    risk: dict

def load_config(path="config.yaml") -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(**data)
