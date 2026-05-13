import os
import hashlib
import logging
import logging
import urllib.parse
import requests
import re
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
            raw_prompt = response.content.strip()
            
            # Extract just the prompt if it's wrapped in quotes, otherwise strip common prefixes
            match = re.search(r'"([^"]*)"', raw_prompt)
            if match and len(match.group(1)) > 50:
                clean_prompt = match.group(1).strip()
            else:
                clean_prompt = re.sub(r'^(Here is a .*?:|Here\'s a .*?:|DALL-E prompt:|Prompt:|\*\*Prompt:\*\*|Here is a potential DALL-E prompt .*?:)', '', raw_prompt, flags=re.IGNORECASE | re.DOTALL).strip()
                
            image_prompts.append(clean_prompt)
        except Exception as e:
            logger.warning("[image_agent] Failed to generate image prompt for paragraph %d: %s", i, e)
            image_prompts.append("A magical kids story scene.")

        hash_str = hashlib.md5(f"{title}_{i}".encode("utf-8")).hexdigest()
        seed = int(hash_str[:8], 16)
        encoded_prompt = urllib.parse.quote(image_prompts[-1])
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=500&nologo=true&seed={seed}&model=flux"
        image_urls.append(url)
        
        # Pre-warm the image by fetching it now so it's cached for the frontend
        # Flux takes up to 40 seconds to generate, so we must wait up to 90 seconds
        try:
            requests.get(url, timeout=90)
        except Exception as e:
            logger.warning("[image_agent] Failed to pre-warm image %d: %s", i, e)

    return {
        "image_prompts": image_prompts,
        "image_urls": image_urls,
    }
