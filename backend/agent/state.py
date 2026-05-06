from typing import List, Optional, Literal
from typing_extensions import TypedDict, NotRequired

class StoryState(TypedDict):
    run_id: str
    category: str
    title: NotRequired[str]
    story_text: NotRequired[str]
    paragraphs: NotRequired[List[str]]
    summary: NotRequired[str]
    moral: NotRequired[str]
    age_range: NotRequired[str]
    review_passed: NotRequired[Optional[bool]]
    review_notes: NotRequired[str]
    image_prompts: NotRequired[List[str]]
    image_urls: NotRequired[List[str]]
    facebook_caption: NotRequired[str]
    instagram_caption: NotRequired[str]
    status: Literal["generating", "review_failed", "pending_approval", "approved", "rejected_by_client", "published"]
    client_feedback: NotRequired[Optional[str]]
    retry_count: NotRequired[int]
    created_at: str
    published_at: NotRequired[str]
