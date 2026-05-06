import json
import re
import os
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import StoryState
from agent.llm_fallback import invoke_with_fallback

logger = logging.getLogger(__name__)

def parse_json(text):
    # ✅ Fixed: \n? instead of \\n
    match = re.search(r"```(?:json)?\n?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        # If no code block, try cleaning and parsing directly
        text = text.strip()
    return json.loads(text)

def story_writer_node(state: StoryState) -> dict:
    
    prompt_path = os.path.join(os.path.dirname(__file__), '../../prompts/story_writer.txt')
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
    
    category = state.get("category", "Adventure")
    feedback_section = ""
    if state.get("client_feedback"):
        feedback_section = f"Client Feedback (incorporate this): {state['client_feedback']}"
    elif state.get("review_notes") and state.get("review_passed") is False:
        feedback_section = f"Reviewer Feedback (fix this): {state['review_notes']}"
    
    system_prompt = system_prompt.format(category=category, feedback_section=feedback_section)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please write the story.")
    ]
    
    response = invoke_with_fallback(messages, openai_model="gpt-4o", temperature=0.7)
    
    try:
        data = parse_json(response.content)
        retry_count = state.get("retry_count", 0)
        if state.get("review_passed") is False:
            retry_count += 1
            
        return {
            "title": data.get("title", "Untitled"),
            "summary": data.get("summary", ""),
            "paragraphs": data.get("paragraphs", []),
            "moral": data.get("moral", ""),
            "age_range": data.get("age_range", "5-8"),
            "story_text": "\n\n".join(data.get("paragraphs", [])),
            "retry_count": retry_count,
            "review_passed": None,
            "review_notes": ""
        }
    except Exception as e:
        print(f"Error parsing story: {e}")
        print(f"Raw response was: {response.content[:300]}")
        return {}
