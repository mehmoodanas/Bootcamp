"""Retrieval: embed the question and find the most similar chunks in ChromaDB.

Run a quick check:  uv run python retrieve.py
"""
import time

import chromadb
from openai import OpenAI

import config

# Created once and reused for every question
_embed_client = OpenAI(base_url=config.EMBEDDING_BASE_URL, api_key=config.EMBEDDING_API_KEY)
_db = chromadb.PersistentClient(path=config.CHROMA_DIR)


def get_collection():
    """Open the collection that ingest.py created."""
    return _db.get_collection(name=config.COLLECTION_NAME, embedding_function=None)


def retrieve_chunks(query: str, top_k: int = config.TOP_K) -> dict:
    """Step 5 Retrieve: return the top_k chunks with source, page and relevance score."""
    start = time.time()

    # Step 3 Embed the question with the SAME model as the chunks
    response = _embed_client.embeddings.create(model=config.EMBEDDING_MODEL, input=[query])
    query_vector = response.data[0].embedding

    results = get_collection().query(
        query_embeddings=[query_vector],   # pass our own vector, never let Chroma embed
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for text, meta, distance in zip(results["documents"][0],
                                    results["metadatas"][0],
                                    results["distances"][0]):
        retrieved.append({
            "content": text,
            "source": meta["source"],
            "page": meta["page"],
            # cosine distance -> similarity (1 = identical, 0 = unrelated)
            "relevance_score": round(1 - distance, 4),
        })

    return {
        "query": query,
        "retrieved_chunks": retrieved,
        "retrieval_time_ms": round((time.time() - start) * 1000),
        "embedding_model": config.EMBEDDING_MODEL,
        "top_k": top_k,
    }


if __name__ == "__main__":
    # Quick check with three of your own questions: is the expected chunk in the list, at which rank?
    test_queries = [
        "How many days per week can employees work remotely?",
        "What was the quarterly revenue in Q1 2026?",
        "What is the response time for critical issues on the Enterprise tier?",
    ]
    for q in test_queries:
        result = retrieve_chunks(q)
        print(f"\nQUESTION: {q}  ({result['retrieval_time_ms']} ms)")
        for rank, chunk in enumerate(result["retrieved_chunks"], start=1):
            preview = chunk["content"][:90].replace("\n", " ")
            print(f"  {rank}. {chunk['relevance_score']:.3f}  {chunk['source']} p{chunk['page']}  | {preview}")
