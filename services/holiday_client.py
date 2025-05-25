import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
HOLIDAY_API_KEY = os.getenv("HOLIDAY_API_KEY")
BASE_URL = "https://calendarific.com/api/v2/holidays"

def get_holidays(country: str = "CA", year: int = None):
    if not year:
        year = datetime.utcnow().year
    params = {
        "api_key": HOLIDAY_API_KEY,
        "country": country,
        "year": year
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        return {"error": data.get("meta", {}).get("error_detail", "Failed to fetch holidays")}
    return [{
        "name": h["name"],
        "date": h["date"]["iso"],
        "description": h.get("description", "")
    } for h in data["response"]["holidays"] if h.get("type") and "National holiday" in h["type"]]

def get_next_holiday(country: str = "CA"):
    holidays = get_holidays(country)
    if isinstance(holidays, dict) and holidays.get("error"):
        return holidays
    today = datetime.utcnow().date()
    for h in holidays:
        holiday_date = datetime.fromisoformat(h["date"]).date()
        if holiday_date >= today:
            return h
    return {"message": "No upcoming holidays found."}

def find_holiday_by_name(name_query: str, country: str = "CA"):
    holidays = get_holidays(country)
    if isinstance(holidays, dict) and holidays.get("error"):
        return holidays
    return [h for h in holidays if name_query.lower() in h["name"].lower()]
