import json
import os
from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END
from agent.state import StoryState
from agent.nodes.orchestrator import orchestrator_node
from agent.nodes.story_writer import story_writer_node
from agent.nodes.quality_reviewer import quality_reviewer_node
from agent.nodes.image_agent import image_agent_node
from agent.nodes.social_media_agent import social_media_agent_node

def save_to_db(state: StoryState):
    db_path = os.path.join(os.path.dirname(__file__), '../db/stories.json')
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    if not os.path.exists(db_path):
        with open(db_path, 'w') as f:
            json.dump([], f)
            
    with open(db_path, 'r') as f:
        try:
            stories = json.load(f)
        except json.JSONDecodeError:
            stories = []
            
    story_dict = dict(state)
    if "status" not in story_dict or story_dict["status"] in ["generating", "pending_approval"]:
        story_dict["status"] = "pending_approval"
        
    if "created_at" not in story_dict:
        story_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    idx_to_replace = next((i for i, s in enumerate(stories) if s["run_id"] == state["run_id"]), None)
    if idx_to_replace is not None:
        stories[idx_to_replace] = story_dict
    else:
        stories.append(story_dict)
        
    with open(db_path, 'w') as f:
        json.dump(stories, f, indent=2)
        
    # Index in ChromaDB
    from db.vector_store import vector_store
    vector_store.add_story(
        story_id=story_dict["run_id"],
        text=story_dict["story_text"],
        metadata={
            "run_id": story_dict["run_id"],
            "title": story_dict.get("title", ""),
            "category": story_dict.get("category", ""),
            "moral": story_dict.get("moral", ""),
            "age_range": story_dict.get("age_range", ""),
            "created_at": story_dict["created_at"]
        }
    )
        
    return {"status": story_dict["status"]}

def set_failed(state: StoryState):
    db_path = os.path.join(os.path.dirname(__file__), '../db/stories.json')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    if not os.path.exists(db_path):
        with open(db_path, 'w') as f:
            json.dump([], f)
            
    with open(db_path, 'r') as f:
        try:
            stories = json.load(f)
        except json.JSONDecodeError:
            stories = []
            
    story_dict = dict(state)
    story_dict["status"] = "review_failed"
    
    if "created_at" not in story_dict:
        story_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        
    idx_to_replace = next((i for i, s in enumerate(stories) if s["run_id"] == state["run_id"]), None)
    if idx_to_replace is not None:
        stories[idx_to_replace] = story_dict
    else:
        stories.append(story_dict)
        
    with open(db_path, 'w') as f:
        json.dump(stories, f, indent=2)
        
    return {"status": "review_failed"}

def route(state: StoryState):
    if not state.get("category"):
        return "orchestrator"
    
    if not state.get("story_text"):
        return "story_writer"
        
    if state.get("review_passed") is None:
        return "quality_reviewer"
        
    if state.get("review_passed") is False:
        if state.get("retry_count", 0) < 2:
            return "story_writer"
        else:
            return "failed"
            
    if not state.get("image_urls"):
        return "image_agent"
        
    if not state.get("facebook_caption"):
        return "social_media_agent"
        
    return "save"


workflow = StateGraph(StoryState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("story_writer", story_writer_node)
workflow.add_node("quality_reviewer", quality_reviewer_node)
workflow.add_node("image_agent", image_agent_node)
workflow.add_node("social_media_agent", social_media_agent_node)
workflow.add_node("save", save_to_db)
workflow.add_node("failed", set_failed)

workflow.add_conditional_edges(START, route, {
    "orchestrator": "orchestrator",
    "story_writer": "story_writer",
    "quality_reviewer": "quality_reviewer",
    "image_agent": "image_agent",
    "social_media_agent": "social_media_agent",
    "save": "save",
    "failed": "failed"
})

nodes = ["orchestrator", "story_writer", "quality_reviewer", "image_agent", "social_media_agent"]
for node in nodes:
    workflow.add_conditional_edges(node, route, {
        "orchestrator": "orchestrator",
        "story_writer": "story_writer",
        "quality_reviewer": "quality_reviewer",
        "image_agent": "image_agent",
        "social_media_agent": "social_media_agent",
        "save": "save",
        "failed": "failed"
    })

workflow.add_edge("save", END)
workflow.add_edge("failed", END)

app = workflow.compile()
