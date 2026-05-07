"""Quick script to inspect all data stored in ChromaDB."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "chroma_db")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection("stories")

data = collection.get(include=["metadatas", "documents"])
ids = data["ids"]
metas = data["metadatas"]
docs = data["documents"]

print(f"Total documents in ChromaDB: {len(ids)}")
print("=" * 60)

for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs)):
    print(f"\n[{i+1}] ID: {doc_id}")
    print(f"    Title:    {meta.get('title', 'N/A')}")
    print(f"    Category: {meta.get('category', 'N/A')}")
    print(f"    Moral:    {meta.get('moral', 'N/A')}")
    print(f"    Age:      {meta.get('age_range', 'N/A')}")
    print(f"    Created:  {meta.get('created_at', 'N/A')}")
    preview = doc[:120].replace("\n", " ") if doc else "N/A"
    print(f"    Text:     {preview}...")
