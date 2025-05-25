from langchain_openai import OpenAIEmbeddings
from memory.chroma_client import client
import hashlib

collection = client.get_or_create_collection(name="user_memory")

def embed_text(text: str):
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    return embedding_model.embed_query(text)

def save_to_memory(user_id: str, text: str):
    embedding = embed_text(text)
    uid = hashlib.sha256(f"{user_id}:{text}".encode()).hexdigest()
    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[uid],
        metadatas=[{"user_id": user_id}]
    )

def search_memory(user_id: str, query: str, top_k: int = 3):
    embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where={"user_id": user_id}
    )
    return "\n".join(results.get("documents", [["No relevant memory"]])[0])