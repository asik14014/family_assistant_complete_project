import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()
print("Environment variables loaded")

if __name__ == "__main__":
    uvicorn.run("interface:app", host="0.0.0.0", port=8000)