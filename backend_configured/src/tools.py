"""Tools for the DreamWeaver story generation system."""

from typing import Callable, Optional, cast, Any, Dict, List
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from datetime import datetime
import json


@tool
async def web_research_tool(query: str) -> Optional[List[Dict[str, Any]]]:
    """Research information from the web for story enhancement.
    
    This tool performs comprehensive web searches to gather factual information,
    current events, or reference material that can enhance story content.
    
    Args:
        query: The search query for research
        
    Returns:
        List of search results with relevant information
    """
    wrapped = TavilySearchResults(
        max_results=8,
        search_depth="advanced",
        include_raw_content=False,
        include_images=True
    )
    result = await wrapped.ainvoke({"query": f"educational children's content {query}"})
    return cast(List[Dict[str, Any]], result)


@tool
async def fact_checker_tool(fact: str) -> Optional[List[Dict[str, Any]]]:
    """Verify facts and information for story accuracy.
    
    This tool checks the accuracy of facts that will be included in educational
    stories to ensure children receive correct information.
    
    Args:
        fact: The fact or claim to verify
        
    Returns:
        Verification results and sources
    """
    wrapped = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_raw_content=True
    )
    result = await wrapped.ainvoke({"query": f"verify fact: {fact}"})
    return cast(List[Dict[str, Any]], result)


@tool
async def educational_content_search(topic: str, age_group: str = "6-12") -> Optional[List[Dict[str, Any]]]:
    """Search for educational content and activities related to a topic.
    
    This tool finds age-appropriate educational materials, activities, and
    learning resources that can be integrated into stories.
    
    Args:
        topic: The educational topic to search for
        age_group: Target age group for the content
        
    Returns:
        Educational resources and activity ideas
    """
    wrapped = TavilySearchResults(
        max_results=6,
        search_depth="basic",
        include_raw_content=False,
        include_images=True
    )
    result = await wrapped.ainvoke({
        "query": f"educational activities {topic} children age {age_group} learning resources"
    })
    return cast(List[Dict[str, Any]], result)


@tool
async def story_inspiration_search(genre: str, themes: str) -> Optional[List[Dict[str, Any]]]:
    """Search for story inspiration and similar content.
    
    This tool finds inspiration from existing stories, cultural references,
    and creative content that can inform story development.
    
    Args:
        genre: The story genre (fantasy, adventure, etc.)
        themes: Key themes or topics for the story
        
    Returns:
        Inspiration and reference material
    """
    wrapped = TavilySearchResults(
        max_results=7,
        search_depth="basic",
        include_raw_content=False,
        include_images=True
    )
    result = await wrapped.ainvoke({
        "query": f"children's {genre} stories {themes} inspiration examples"
    })
    return cast(List[Dict[str, Any]], result)


@tool
async def current_events_search(topic: str) -> Optional[List[Dict[str, Any]]]:
    """Search for current events and news related to a topic.
    
    This tool finds recent news and events that can make stories more
    relevant and connected to the real world.
    
    Args:
        topic: The topic to search for current events
        
    Returns:
        Recent news and events information
    """
    wrapped = TavilySearchResults(
        max_results=5,
        search_depth="basic",
        include_raw_content=False
    )
    result = await wrapped.ainvoke({
        "query": f"recent news current events {topic} children appropriate"
    })
    return cast(List[Dict[str, Any]], result)


@tool
async def get_current_date() -> str:
    """Get the current date for time-sensitive content."""
    return datetime.now().strftime("%Y-%m-%d")


@tool
async def get_current_time() -> str:
    """Get the current time for timestamping story creation."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_tools(selected_tools: List[str]) -> List[Callable[..., Any]]:
    """Convert a list of tool names to actual tool functions.
    
    Args:
        selected_tools: List of tool names to include
        
    Returns:
        List of tool functions
    """
    available_tools = {
        "web_research_tool": web_research_tool,
        "fact_checker_tool": fact_checker_tool,
        "educational_content_search": educational_content_search,
        "story_inspiration_search": story_inspiration_search,
        "current_events_search": current_events_search,
        "get_current_date": get_current_date,
        "get_current_time": get_current_time,
    }
    
    tools = []
    for tool_name in selected_tools:
        if tool_name in available_tools:
            tools.append(available_tools[tool_name])
    
    return tools


# Default tool sets for different agent types
DEFAULT_TOOL_SETS = {
    "planner": ["get_current_date", "story_inspiration_search"],
    "writer": ["get_current_time"],
    "critique": ["fact_checker_tool"],
    "inject_education": ["educational_content_search", "fact_checker_tool"],
    "tool_user": ["web_research_tool", "fact_checker_tool", "educational_content_search", 
                  "story_inspiration_search", "current_events_search", "get_current_date"],
    "formatter": ["get_current_time"],
    "supervisor": ["get_current_date"],
}
