from __future__ import annotations
import hmac, hashlib, os, json
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()
TV_SECRET = os.getenv("TV_WEBHOOK_SECRET", "changeme")

class TVPayload(BaseModel):
    symbol: str
    timeframe: str
    signal: str  # "BUY" | "SELL"
    price: float
    ts: int      # ms

def _verify(req: Request, raw_body: bytes):
    sig = req.headers.get("X-Signature")
    if not sig:
        raise HTTPException(401, "missing signature")
    calc = hmac.new(TV_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, sig):
        raise HTTPException(401, "bad signature")

@router.post("/tv/webhook")
async def tv_webhook(req: Request):
    raw = await req.body()
    _verify(req, raw)
    try:
        payload = TVPayload.model_validate_json(raw.decode())
    except Exception:
        raise HTTPException(400, "bad json")

    # дедуп по (symbol,timeframe,ts,signal)
    key = f"{payload.symbol}:{payload.timeframe}:{payload.ts}:{payload.signal}"
    # TODO: Redis SETNX(key, 1) EX 900 → если уже есть — 200 OK и return

    # Отправляем в роутер сигналов
    from services.signal_router import route_signal
    route_signal(
        symbol=payload.symbol.replace("PERP","").replace("BINANCE:",""),  # нормализация
        timeframe=payload.timeframe,
        signal=payload.signal,
        price=payload.price,
        bar_ts=datetime.fromtimestamp(payload.ts/1000.0),
        source="tradingview",
        meta={}
    )
    return {"ok": True}
