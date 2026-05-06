import os
import json
import sys

# Add backend to path so we can import db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.vector_store import vector_store

def index_all():
    db_path = os.path.join(os.path.dirname(__file__), "../db/stories.json")
    
    if not os.path.exists(db_path):
        print(f"No database found at {db_path}")
        return
        
    with open(db_path, "r") as f:
        try:
            stories = json.load(f)
        except json.JSONDecodeError:
            print("Failed to decode stories.json")
            return
            
    print(f"Indexing {len(stories)} stories into ChromaDB...")
    
    for story in stories:
        # Check if story has required text
        if not story.get("story_text"):
            print(f"Skipping story {story.get('run_id')} - no text")
            continue
            
        print(f"Indexing: {story.get('title')} ({story.get('run_id')})")
        vector_store.add_story(
            story_id=story["run_id"],
            text=story["story_text"],
            metadata={
                "run_id": story["run_id"],
                "title": story.get("title", ""),
                "category": story.get("category", ""),
                "moral": story.get("moral", ""),
                "age_range": story.get("age_range", ""),
                "created_at": story.get("created_at", "")
            }
        )
        
    print("Indexing complete!")

if __name__ == "__main__":
    index_all()
