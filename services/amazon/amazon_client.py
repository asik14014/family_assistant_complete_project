import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

LWA_CLIENT_ID = os.getenv("LWA_CLIENT_ID")
LWA_CLIENT_SECRET = os.getenv("LWA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("LWA_REFRESH_TOKEN")

TOKEN_ENDPOINT = "https://api.amazon.com/auth/o2/token"

_cached_token = {
    "access_token": None,
    "expires_at": 0
}


def get_access_token() -> str:
    """Получить или вернуть кэшированный access_token от LWA."""

    now = int(time.time())
    if _cached_token["access_token"] and _cached_token["expires_at"] > now:
        return _cached_token["access_token"]

    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": LWA_CLIENT_ID,
            "client_secret": LWA_CLIENT_SECRET
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get access token: {response.text}")

    data = response.json()
    access_token = data["access_token"]
    expires_in = data["expires_in"]

    _cached_token["access_token"] = access_token
    _cached_token["expires_at"] = now + expires_in - 30  # запас в 30 сек

    return access_token
