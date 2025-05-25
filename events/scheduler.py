import threading
import time
from datetime import datetime

scheduled_tasks = []

def schedule_task(callback, run_at: datetime, args=()):
    scheduled_tasks.append({"time": run_at, "callback": callback, "args": args})

def run_scheduler_loop(interval_seconds: int = 30):
    def loop():
        while True:
            now = datetime.utcnow()
            for task in scheduled_tasks[:]:
                if now >= task["time"]:
                    task["callback"](*task["args"])
                    scheduled_tasks.remove(task)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print("Scheduler started.")
