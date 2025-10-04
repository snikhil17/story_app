"""Utility functions for the DreamWeaver story generation system."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
import yaml
import os
from typing import Dict, Any


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider)


def load_prompts_config() -> Dict[str, Any]:
    """Load prompts configuration from YAML file."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "configs", 
        "prompts.yaml"
    )
    
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def get_agent_prompt(agent_name: str) -> str:
    """Get the system prompt for a specific agent."""
    prompts_config = load_prompts_config()
    return prompts_config.get(agent_name, {}).get("system_prompt", "")


def format_story_metadata(story_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format story metadata for consistent output."""
    return {
        "title": story_data.get("title", "Untitled Story"),
        "age_group": story_data.get("age_group", "6-12"),
        "genre": story_data.get("genre", "Adventure"),
        "educational_themes": story_data.get("educational_themes", []),
        "characters": story_data.get("characters", []),
        "setting": story_data.get("setting", ""),
        "estimated_reading_time": story_data.get("estimated_reading_time", "10 minutes"),
        "created_at": story_data.get("created_at", ""),
    }


def validate_story_requirements(requirements: Dict[str, Any]) -> bool:
    """Validate that story requirements contain necessary fields."""
    required_fields = ["story_prompt", "age_group"]
    
    for field in required_fields:
        if field not in requirements or not requirements[field]:
            return False
    
    return True


def extract_story_elements(story_prompt: str) -> Dict[str, Any]:
    """Extract basic story elements from a user prompt."""
    # This is a simple extractor - in a real implementation,
    # you might use NLP techniques for better extraction
    
    elements = {
        "genre": "Adventure",  # Default
        "themes": [],
        "characters": [],
        "setting": "",
        "conflict": "",
    }
    
    # Simple keyword-based extraction
    prompt_lower = story_prompt.lower()
    
    # Genre detection
    if any(word in prompt_lower for word in ["mystery", "detective", "clue"]):
        elements["genre"] = "Mystery"
    elif any(word in prompt_lower for word in ["space", "robot", "future", "alien"]):
        elements["genre"] = "Science Fiction"
    elif any(word in prompt_lower for word in ["magic", "wizard", "fairy", "dragon"]):
        elements["genre"] = "Fantasy"
    elif any(word in prompt_lower for word in ["animal", "nature", "forest"]):
        elements["genre"] = "Nature/Animal"
    
    return elements
