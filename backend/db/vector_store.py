import os
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._init_chroma()
        return cls._instance

    def _init_chroma(self):
        # Use local embeddings (no API key required)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = Chroma(
            collection_name="stories",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PATH,
            collection_metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

    def add_story(self, story_id: str, text: str, metadata: dict):
        """
        Adds or updates a story in the vector store.
        """
        # Ensure all metadata values are strings or numbers (Chroma requirement)
        clean_metadata = {k: str(v) for k, v in metadata.items() if v is not None}
        
        # We use run_id as the unique ID in Chroma
        self.vector_store.add_texts(
            texts=[text],
            metadatas=[clean_metadata],
            ids=[story_id]
        )

    def search_stories(self, query: str, n_results: int = 5, threshold: float = 0.2):
        """
        Performs semantic search with a relevance threshold.
        """
        results = self.vector_store.similarity_search_with_relevance_scores(query, k=n_results)
        
        # Filter results based on the threshold
        filtered_results = [doc for doc, score in results if score >= threshold]
        
        return filtered_results

    def check_duplicate(self, text: str, threshold: float = 0.9):
        """
        Checks if a similar story already exists.
        Returns (is_duplicate, score, original_story_id)
        """
        results = self.vector_store.similarity_search_with_relevance_scores(text, k=1)
        if not results:
            return False, 0, None
        
        doc, score = results[0]
        if score > threshold:
            return True, score, doc.metadata.get("run_id")
        return False, score, doc.metadata.get("run_id")

    def delete_story(self, story_id: str):
        """
        Removes a story from the vector store by its run_id.
        """
        self.vector_store.delete(ids=[story_id])

# Singleton instance
vector_store = VectorStore()
