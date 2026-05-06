import os
import json
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)  # override=True ensures .env always wins over shell env vars

from agent.pipeline import app as workflow_app
from scheduler import start_scheduler, generate_single_story

app = FastAPI(title="StoryNest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'db/stories.json')

def get_db():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_db(stories):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(stories, f, indent=2)

@app.on_event("startup")
def startup_event():
    start_scheduler()
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        # Pre-seed 3 sample stories
        sample_stories = [
            {
                "run_id": str(uuid.uuid4()),
                "category": "Adventure",
                "title": "The Brave Little Fox",
                "story_text": "In a lush green forest, there lived a brave little fox named Felix. He was always curious and loved exploring.\n\nOne day, Felix heard a soft whimper coming from the old oak tree. He approached carefully and found a trapped baby bird.\n\nFelix used his sharp teeth to gently break the twigs holding the bird. They became best friends instantly.\n\nFrom that day on, Felix and the bird explored the forest together, helping any animals in need.",
                "paragraphs": [
                    "In a lush green forest, there lived a brave little fox named Felix. He was always curious and loved exploring.",
                    "One day, Felix heard a soft whimper coming from the old oak tree. He approached carefully and found a trapped baby bird.",
                    "Felix used his sharp teeth to gently break the twigs holding the bird. They became best friends instantly.",
                    "From that day on, Felix and the bird explored the forest together, helping any animals in need."
                ],
                "summary": "Felix the fox saves a trapped baby bird. They become best friends and explore together.",
                "moral": "Courage and kindness can turn strangers into best friends.",
                "age_range": "5-8",
                "image_urls": [
                    f"https://picsum.photos/seed/felix1/800/500",
                    f"https://picsum.photos/seed/felix2/800/500",
                    f"https://picsum.photos/seed/felix3/800/500",
                    f"https://picsum.photos/seed/felix4/800/500"
                ],
                "facebook_caption": "Check out this amazing story about Felix the fox! #StoryNest #KidsBooks #Adventure",
                "instagram_caption": "Felix the brave little fox goes on an adventure! 🦊✨ #KidsStory #BedtimeStories #ReadingTime #ChildrensBooks #StoryNest",
                "status": "pending_approval",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "run_id": str(uuid.uuid4()),
                "category": "Sci-Fi",
                "title": "Luna's Space Journey",
                "story_text": "Luna was a bright young girl who dreamed of visiting the stars. She built a shiny rocket ship in her backyard.\n\nWith a loud countdown, she blasted off into the sparkling galaxy. Planets zoomed past her window in brilliant colors.\n\nShe met a friendly alien who taught her how to dance in zero gravity. They laughed and played among the asteroids.\n\nLuna returned home safely, knowing the universe was full of wonderful surprises and new friends.",
                "paragraphs": [
                    "Luna was a bright young girl who dreamed of visiting the stars. She built a shiny rocket ship in her backyard.",
                    "With a loud countdown, she blasted off into the sparkling galaxy. Planets zoomed past her window in brilliant colors.",
                    "She met a friendly alien who taught her how to dance in zero gravity. They laughed and played among the asteroids.",
                    "Luna returned home safely, knowing the universe was full of wonderful surprises and new friends."
                ],
                "summary": "Luna builds a rocket and visits space. She makes a friendly alien friend before returning home.",
                "moral": "Dream big, and you'll find friends in the most unexpected places.",
                "age_range": "6-10",
                "image_urls": [
                    f"https://picsum.photos/seed/luna1/800/500",
                    f"https://picsum.photos/seed/luna2/800/500",
                    f"https://picsum.photos/seed/luna3/800/500",
                    f"https://picsum.photos/seed/luna4/800/500"
                ],
                "facebook_caption": "Blast off into space with Luna! #SpaceStory #KidsSciFi #StoryNest",
                "instagram_caption": "Join Luna on her wonderful space journey! 🚀🌟👽 #SpaceKids #StoryTime #ImaginativePlay #SciFiForKids #StoryNest",
                "status": "pending_approval",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "run_id": str(uuid.uuid4()),
                "category": "Fable",
                "title": "The Ant and the Diamond",
                "story_text": "An ant was carrying a piece of sugar when he found a glowing diamond. It was beautiful but very heavy.\n\nHe tried to lift it, but couldn't move it even an inch. Other ants passed by, carrying their food.\n\nThe ant realized that the diamond, while pretty, couldn't feed his family. He left it and picked up his sugar.\n\nWhen winter came, he was happy and well-fed, knowing he had made the right choice.",
                "paragraphs": [
                    "An ant was carrying a piece of sugar when he found a glowing diamond. It was beautiful but very heavy.",
                    "He tried to lift it, but couldn't move it even an inch. Other ants passed by, carrying their food.",
                    "The ant realized that the diamond, while pretty, couldn't feed his family. He left it and picked up his sugar.",
                    "When winter came, he was happy and well-fed, knowing he had made the right choice."
                ],
                "summary": "An ant finds a heavy diamond but chooses to take sugar instead. The practical choice keeps his family fed during winter.",
                "moral": "Practicality is often more valuable than beauty.",
                "age_range": "5-9",
                "image_urls": [
                    f"https://picsum.photos/seed/ant1/800/500",
                    f"https://picsum.photos/seed/ant2/800/500",
                    f"https://picsum.photos/seed/ant3/800/500",
                    f"https://picsum.photos/seed/ant4/800/500"
                ],
                "facebook_caption": "A classic tale about making the right choices. #Fable #KidsLearning #StoryNest",
                "instagram_caption": "What will the ant choose? A diamond or food? 🐜💎🍞 #Fable #KidsStory #LifeLessons #StoryNest #ReadToKids",
                "status": "pending_approval",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        save_db(sample_stories)

@app.get("/stories")
def get_public_stories():
    stories = get_db()
    published = [s for s in stories if s.get("status") == "published"]
    return sorted(published, key=lambda x: x.get("created_at", ""), reverse=True)

@app.get("/stories/{run_id}")
def get_story(run_id: str):
    stories = get_db()
    story = next((s for s in stories if s.get("run_id") == run_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@app.get("/admin/stories")
def get_all_stories():
    stories = get_db()
    return sorted(stories, key=lambda x: x.get("created_at", ""), reverse=True)

class FeedbackModel(BaseModel):
    feedback: str

@app.post("/admin/approve/{run_id}")
def approve_story(run_id: str):
    stories = get_db()
    story = next((s for s in stories if s.get("run_id") == run_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story["status"] = "published"
    story["published_at"] = datetime.now(timezone.utc).isoformat()
    save_db(stories)
    return {"message": "Story approved and published"}

@app.post("/admin/reject/{run_id}")
def reject_story(run_id: str, feedback_model: FeedbackModel, background_tasks: BackgroundTasks):
    stories = get_db()
    story = next((s for s in stories if s.get("run_id") == run_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story["status"] = "rejected_by_client"
    save_db(stories)
    
    def re_run_story(old_story, feedback):
        new_run_id = str(uuid.uuid4())
        initial_state = {
            "run_id": new_run_id,
            "category": old_story.get("category"),
            "status": "generating",
            "client_feedback": feedback,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        workflow_app.invoke(initial_state)

    background_tasks.add_task(re_run_story, story, feedback_model.feedback)
    return {"message": "Story rejected. Regeneration started."}

@app.post("/admin/generate")
def manually_generate_story(background_tasks: BackgroundTasks):
    stories = get_db()
    today_str = datetime.now(timezone.utc).date().isoformat()
    today_count = sum(1 for s in stories if s.get("created_at", "").startswith(today_str))
    
    if today_count >= 3:
        raise HTTPException(status_code=400, detail="Daily limit of 3 stories reached")
        
    background_tasks.add_task(generate_single_story)
    return {"message": "Story generation started in background"}

@app.get("/admin/stats")
def get_stats():
    stories = get_db()
    today_str = datetime.now(timezone.utc).date().isoformat()
    today_count = sum(1 for s in stories if s.get("created_at", "").startswith(today_str))
    pending_count = sum(1 for s in stories if s.get("status") == "pending_approval")
    published_count = sum(1 for s in stories if s.get("status") == "published")
    
    return {
        "today_count": today_count,
        "total": len(stories),
        "pending": pending_count,
        "published": published_count
    }
