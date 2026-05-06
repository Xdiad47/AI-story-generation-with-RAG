import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.vector_store import vector_store

def test_query(q):
    print(f"Query: {q}")
    results = vector_store.vector_store.similarity_search_with_score(q, k=3)
    for doc, score in results:
        print(f"Score: {score:.4f} | Title: {doc.metadata.get('title')}")
    print("-" * 20)

if __name__ == "__main__":
    test_query("fox")
    test_query("brave")
    test_query("pizza")
    test_query("space journey")
