import uuid
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from agent.pipeline import app
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def generate_daily_stories():
    logger.info("Starting daily story generation...")
    for _ in range(3):
        generate_single_story()

def generate_single_story():
    run_id = str(uuid.uuid4())
    initial_state = {
        "run_id": run_id,
        "status": "generating",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"Generating story with run_id {run_id}")
    try:
        app.invoke(initial_state)
        logger.info(f"Story {run_id} generated successfully")
    except Exception as e:
        logger.error(f"Failed to generate story {run_id}: {e}")

def start_scheduler():
    scheduler.add_job(
        generate_daily_stories,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_story_gen",
        name="Generate daily kids stories",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started.")
