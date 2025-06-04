import os
from dotenv import load_dotenv
from events.scheduler import run_scheduler_loop

load_dotenv()
print("Environment variables loaded")

if __name__ == "__main__":
    run_scheduler_loop()