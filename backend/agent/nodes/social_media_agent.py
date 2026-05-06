import json
import re
import os
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import StoryState
from agent.llm_fallback import invoke_with_fallback

logger = logging.getLogger(__name__)

def parse_json(text):
    # ✅ Fixed: \n? instead of \n (handles both wrapped and unwrapped responses)
    match = re.search(r"```(?:json)?\n?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        text = text.strip()
    return json.loads(text)

def social_media_agent_node(state: StoryState) -> dict:
    
    prompt_path = os.path.join(os.path.dirname(__file__), '../../prompts/social_media.txt')
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
    
    # Use .replace() instead of .format() — Groq-generated content may
    # contain {word} patterns that Python's .format() treats as placeholders.
    system_prompt = (system_prompt
                     .replace("{title}", state.get("title", ""))
                     .replace("{category}", state.get("category", ""))
                     .replace("{summary}", state.get("summary", ""))
                     .replace("{moral}", state.get("moral", "")))
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate the social media captions.")
    ]
    
    response = invoke_with_fallback(messages, openai_model="gpt-4o", temperature=0.7)
    
    try:
        data = parse_json(response.content)
        return {
            "facebook_caption": data.get("facebook", ""),
            "instagram_caption": data.get("instagram", "")
        }
    except Exception as e:
        print(f"Error parsing social media JSON: {e}")
        return {
            "facebook_caption": "Check out our new story! #kids #story",
            "instagram_caption": "Read this amazing story today! ✨📚 #kids #story"
        }
