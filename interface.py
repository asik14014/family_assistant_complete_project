from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from services.weather_client import get_weather
from services.holiday_client import get_next_holiday
from services.todoist_client import get_tasks
from services.calendar_client import get_upcoming_events
from services.gmail_client import get_unread_email_summary

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    weather = get_weather("Calgary")
    holiday = get_next_holiday()
    tasks = get_tasks()
    events = get_upcoming_events()
    email_summary = get_unread_email_summary()

    html_content = f"""
    <html>
        <head><title>Family Assistant Dashboard</title></head>
        <body>
            <h1>Welcome to Your Family Assistant</h1>
            <h2>📬 Email</h2>
            <p>{email_summary}</p>
            <h2>🌦️ Weather (Calgary)</h2>
            <p>{weather}</p>
            <h2>📅 Next Holiday</h2>
            <p>{holiday}</p>
            <h2>✅ Todoist Tasks</h2>
            <ul>{''.join(f'<li>{task["content"]}</li>' for task in tasks)}</ul>
            <h2>📆 Upcoming Events</h2>
            <ul>{''.join(f'<li>{event["summary"]} - {event["start"]}</li>' for event in events)}</ul>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
