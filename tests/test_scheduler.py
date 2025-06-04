import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime, timedelta
import time

from events.scheduler import schedule_task, run_scheduler_loop, scheduled_tasks


def test_schedule_task_executes_and_removed():
    executed = []

    def callback():
        executed.append(True)

    # Start the scheduler with a short interval
    run_scheduler_loop(interval_seconds=0.05)

    # Schedule the task to run shortly
    run_at = datetime.utcnow() + timedelta(seconds=0.1)
    schedule_task(callback, run_at)

    # Wait for the scheduler to execute the task
    time.sleep(0.2)

    assert executed == [True]
    assert scheduled_tasks == []
