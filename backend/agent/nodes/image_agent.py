import os
import hashlib
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import StoryState
from agent.llm_fallback import invoke_with_fallback

logger = logging.getLogger(__name__)

def image_agent_node(state: StoryState) -> dict:
    prompt_path = os.path.join(os.path.dirname(__file__), '../../prompts/image_prompt.txt')
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    paragraphs = state.get("paragraphs", [])
    category = state.get("category", "")
    title = state.get("title", "Untitled")

    image_prompts = []
    image_urls = []

    for i, paragraph in enumerate(paragraphs):
        prompt_text = system_prompt.format(paragraph=paragraph, category=category)
        messages = [
            SystemMessage(content="You are a DALL-E prompt generator."),
            HumanMessage(content=prompt_text)
        ]

        try:
            response = invoke_with_fallback(messages, openai_model="gpt-4o", temperature=0.7)
            image_prompts.append(response.content.strip())
        except Exception as e:
            logger.warning("[image_agent] Failed to generate image prompt for paragraph %d: %s", i, e)
            image_prompts.append("A magical kids story scene.")

        hash_str = hashlib.md5(f"{title}_{i}".encode("utf-8")).hexdigest()
        image_urls.append(f"https://picsum.photos/seed/{hash_str}/800/500")

    return {
        "image_prompts": image_prompts,
        "image_urls": image_urls,
    }
