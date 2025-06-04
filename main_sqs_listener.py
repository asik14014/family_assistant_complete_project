import os
import asyncio
from services.amazon.sqs_listener import listen_to_queue

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(listen_to_queue())