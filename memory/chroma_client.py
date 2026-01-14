import os
import chromadb
from chromadb.config import Settings

path=os.getenv("CHROMA_DB_PATH", "./chroma")

if not isinstance(path, str):
    raise ValueError("CHROMA_DB_PATH must be a string")

client = chromadb.PersistentClient(path=path)