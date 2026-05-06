import json
import os
from agent.state import StoryState

CATEGORIES = ["Epic", "Mythology", "Folktale", "Sci-Fi", "Fable", "Adventure"]

def get_last_category():
    db_path = os.path.join(os.path.dirname(__file__), '../../db/stories.json')
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            try:
                stories = json.load(f)
                if stories:
                    return stories[-1].get("category")
            except json.JSONDecodeError:
                pass
    return None

def orchestrator_node(state: StoryState) -> dict:
    if not state.get("category"):
        last_cat = get_last_category()
        if last_cat in CATEGORIES:
            idx = CATEGORIES.index(last_cat)
            next_cat = CATEGORIES[(idx + 1) % len(CATEGORIES)]
        else:
            next_cat = CATEGORIES[0]
        return {"category": next_cat}
    return {}
