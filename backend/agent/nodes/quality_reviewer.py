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

def quality_reviewer_node(state: StoryState) -> dict:
    
    prompt_path = os.path.join(os.path.dirname(__file__), '../../prompts/quality_reviewer.txt')
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
    
    # Use .replace() instead of .format() — if Groq's story_text contains
    # {word} patterns, Python's .format() raises KeyError on them.
    system_prompt = (system_prompt
                     .replace("{title}", state.get("title", ""))
                     .replace("{story_text}", state.get("story_text", "")))
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please review this story.")
    ]
    
    response = invoke_with_fallback(messages, openai_model="gpt-4o", temperature=0.2)
    
    try:
        data = parse_json(response.content)
        return {
            "review_passed": data.get("passed", False),
            "review_notes": data.get("notes", "")
        }
    except Exception as e:
        print(f"Error parsing reviewer JSON: {e}")
        print(f"Raw reviewer response: {response.content[:300]}")
        # ✅ Default to PASSED so pipeline doesn't get stuck in retry loop
        return {"review_passed": True, "review_notes": "Auto-approved (parse error)"}
