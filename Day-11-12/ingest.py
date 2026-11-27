"""Ingestion: load the PDFs, chunk them, embed them, store them in ChromaDB.

Run:  uv run python ingest.py
Rebuilds chroma_db/ from scratch every time, so re-running never duplicates chunks.
"""
import os
import re
import time

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

import config


def load_pages(pdf_path: str) -> list[dict]:
    """Step 1 Parse: read a PDF page by page, keep source and page number."""
    reader = PdfReader(pdf_path)
    source = os.path.basename(pdf_path)
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        # layout mode keeps table rows on one line (see parse_check.py)
        text = page.extract_text(extraction_mode="layout")
        # layout mode pads columns with many spaces; shrink them to one space
        text = re.sub(r"[ \t]+", " ", text)
        # remove empty lines
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if text:
            pages.append({"text": text, "source": source, "page": page_number})
    return pages


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Step 2 Chunk: split each page into chunks. Unit: characters."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    chunks = []
    for page in pages:
        for index, piece in enumerate(splitter.split_text(page["text"])):
            chunks.append({
                # stable ID: source + page + index, so the same chunk always gets the same ID
                "id": f"{page['source']}_p{page['page']}_c{index}",
                "text": piece,
                "source": page["source"],
                "page": page["page"],
            })
    return chunks


def embed_texts(client: OpenAI, texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Step 3 Embed: turn texts into vectors with the local embedding model."""
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        response = client.embeddings.create(model=config.EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in response.data)
        print(f"   embedded {min(start + batch_size, len(texts))}/{len(texts)}")
    return vectors


def store_chunks(chunks: list[dict], vectors: list[list[float]]):
    """Step 4 Store: save chunks and vectors in ChromaDB with cosine distance."""
    db = chromadb.PersistentClient(path=config.CHROMA_DIR)

    # delete the old collection first, so a re-run never doubles the count
    try:
        db.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass  # first run: the collection does not exist yet

    collection = db.create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # default is L2; cosine gives scores between 0 and 1
        embedding_function=None,            # we always pass our own embeddings
    )
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=vectors,
        metadatas=[{"source": c["source"], "page": c["page"]} for c in chunks],
    )
    return collection


def main() -> None:
    start = time.time()
    client = OpenAI(base_url=config.EMBEDDING_BASE_URL, api_key=config.EMBEDDING_API_KEY)

    # 1. Parse
    pdf_files = sorted(f for f in os.listdir(config.DOCUMENTS_DIR) if f.lower().endswith(".pdf"))
    pages = []
    for name in pdf_files:
        doc_pages = load_pages(os.path.join(config.DOCUMENTS_DIR, name))
        print(f"Parsed {name}: {len(doc_pages)} pages")
        pages.extend(doc_pages)

    # 2. Chunk
    chunks = chunk_pages(pages)
    lengths = [len(c["text"]) for c in chunks]
    print(f"\n{len(chunks)} chunks (chunk_size={config.CHUNK_SIZE} characters, "
          f"overlap={config.CHUNK_OVERLAP} characters)")
    print(f"Chunk length in characters: min {min(lengths)}, "
          f"average {sum(lengths) // len(lengths)}, max {max(lengths)}")

    # 3. Embed
    print(f"\nEmbedding with {config.EMBEDDING_MODEL} ...")
    vectors = embed_texts(client, [c["text"] for c in chunks])
    print(f"Vector dimensions: {len(vectors[0])}")

    # 4. Store
    collection = store_chunks(chunks, vectors)
    print(f"\ncollection.count() = {collection.count()}")
    print(f"Done in {time.time() - start:.1f} s. Stored in {config.CHROMA_DIR}/")


if __name__ == "__main__":
    main()
