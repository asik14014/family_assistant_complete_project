# Family Assistant

A modular Python-based AI assistant for family productivity. Includes:

- 🤖 Telegram bot interface
- 🧠 GPT-powered memory and orchestrator
- 📬 Gmail integration
- 📅 Google Calendar events
- 📝 Todoist task management
- 🌦️ OpenWeatherMap weather alerts
- 🏖️ Holiday reminders via Calendarific
- 🕒 Background job scheduler
- 🌐 FastAPI web dashboard

## Setup
1. Create and fill out a `.env` file using `.env.example`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot or web app:
   ```bash
   python main.py         # To run scheduler + bot
   uvicorn interface:app --reload   # To run the web dashboard
   ```

## Optional
- Connect to a PostgreSQL DB instead of SQLite for production
- Deploy with Docker or Azure App Service
