# apps/init_db.py
from database.db import engine
from database.models import Base

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init()