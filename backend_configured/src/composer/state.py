"""
Composer State Management - Unified state for all workflows

This module defines the ComposerState which is a unified state object
that can handle any use case workflow by dynamically including the
necessary fields based on the configuration.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import operator


class ComposerState(TypedDict):
    """
    Unified state for all composer workflows.
    
    This state is designed to be flexible and accommodate any use case
    by dynamically including fields as needed.
    """
    # Core workflow fields
    use_case: str
    user_input: str
    workflow_step: str
    current_agent: str
    completed_steps: List[str]
    
    # Content fields (dynamically populated based on use case)
    plan: Optional[str]
    content: Optional[str]
    poetry_content: Optional[str]
    music_content: Optional[str]
    educational_content: Optional[str]
    formatted_content: Optional[str]
    
    # Quality and feedback
    quality_score: Optional[float]
    critique_feedback: Optional[str]
    revision_count: int
    max_revisions: int
    
    # Configuration
    target_audience: str
    theme: str
    style_preferences: Dict[str, Any]
    agent_config: Dict[str, Any]
    
    # Personalization fields
    child_name: Optional[str]
    child_age: Optional[int]
    child_gender: Optional[str]
    interests: List[str]
    reading_level: Optional[str]
    companions: List[Dict[str, Any]]
    location: Optional[str]
    region: Optional[str]
    mother_tongue: Optional[str]
    language_of_story: Optional[str]
    moral_lesson: Optional[str]
    
    # Story length configuration
    story_length: Optional[str]  # 'short', 'medium', 'long'
    word_count: Optional[int]
    words_per_page: Optional[int]
    reading_time: Optional[int]
    
    # Image generation
    image_urls: List[str]
    image_metadata: Dict[str, Any]
    comic_pages: List[Dict[str, Any]]
    story_image_prompts: List[str]  # Added to preserve image prompts between nodes
    formatted_story: Optional[Dict[str, Any]]  # Added to preserve formatted story structure
    image_style: Optional[str]  # Image generation style (e.g., 'ghibli', 'disney', 'watercolor', etc.)
    include_images: Optional[bool]  # Whether to include images in the output
    
    # Research and tools
    research_results: List[Dict[str, Any]]
    tool_outputs: List[Dict[str, Any]]
    
    # Execution tracking
    agent_results: Annotated[List[Dict[str, Any]], operator.add]
    execution_times: Dict[str, float]
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    session_id: str


def create_initial_state(
    use_case: str,
    user_input: str,
    target_audience: str = "children",
    theme: str = "adventure",
    style_preferences: Optional[Dict[str, Any]] = None,
    max_revisions: int = 3,
    session_id: Optional[str] = None,
    **kwargs
) -> ComposerState:
    """
    Create an initial state for a composer workflow.
    
    Args:
        use_case: The use case name (e.g., 'story_generator', 'poetry_and_song')
        user_input: The user's request or prompt
        target_audience: Target audience for the content
        theme: Theme or genre for the content
        style_preferences: Style preferences for content generation
        max_revisions: Maximum number of revisions allowed
        session_id: Unique session identifier
        **kwargs: Additional parameters to include in the state (e.g., image_style)
        
    Returns:
        Initialized ComposerState
    """
    import uuid
    
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    if style_preferences is None:
        style_preferences = {}
    
    now = datetime.now()
    
    # Create the base state
    state = ComposerState(
        # Core workflow fields
        use_case=use_case,
        user_input=user_input,
        workflow_step="initialization",
        current_agent="",
        completed_steps=[],
        
        # Content fields
        plan=None,
        content=None,
        poetry_content=None,
        music_content=None,
        educational_content=None,
        formatted_content=None,
        
        # Quality and feedback
        quality_score=None,
        critique_feedback=None,
        revision_count=0,
        max_revisions=max_revisions,
        
        # Configuration
        target_audience=target_audience,
        theme=theme,
        style_preferences=style_preferences,
        agent_config={},
        
        # Personalization fields (with defaults)
        child_name=kwargs.get('child_name'),
        child_age=kwargs.get('child_age'),
        child_gender=kwargs.get('child_gender'),
        interests=kwargs.get('interests', []),
        reading_level=kwargs.get('reading_level'),
        companions=kwargs.get('companions', []),
        location=kwargs.get('location'),
        region=kwargs.get('region'),
        mother_tongue=kwargs.get('mother_tongue'),
        language_of_story=kwargs.get('language_of_story', 'english'),
        moral_lesson=kwargs.get('moral_lesson'),
        
        # Story length configuration
        story_length=None,
        word_count=None,
        words_per_page=None,
        reading_time=None,
        
        # Image generation
        image_urls=[],
        image_metadata={},
        comic_pages=[],
        story_image_prompts=[],
        formatted_story=None,
        image_style=kwargs.get('image_style'),
        include_images=kwargs.get('include_images', True),
        
        # Research and tools
        research_results=[],
        tool_outputs=[],
        
        # Execution tracking
        agent_results=[],
        execution_times={},
        errors=[],
        warnings=[],
        
        # Metadata
        created_at=now,
        updated_at=now,
        session_id=session_id
    )
    
    # Add any additional kwargs to the state
    for key, value in kwargs.items():
        print(f"🔍 [DEBUG] Adding to state: {key} = {value}")
        if key == 'image_style':
            print(f"🎨 [DEBUG] IMAGE_STYLE being added to state: {value}")
        state[key] = value
    
    print(f"🔍 [DEBUG] Final state keys: {list(state.keys())}")
    print(f"🎨 [DEBUG] image_style in final state: {state.get('image_style', 'NOT FOUND')}")
    
    return state


def should_continue_workflow(state: ComposerState) -> bool:
    """
    Determine if the workflow should continue based on current state.
    
    Args:
        state: Current composer state
        
    Returns:
        True if workflow should continue, False if it should end
    """
    # Stop if there are critical errors
    if state["errors"]:
        return False
    
    # Stop if workflow is marked as completed
    if state["workflow_step"] == "completed":
        return False
    
    # Stop if we've exceeded max revisions
    if state["revision_count"] >= state["max_revisions"]:
        return False
    
    return True


def update_state_with_agent_result(
    state: ComposerState,
    agent_name: str,
    result: Dict[str, Any],
    execution_time: float
) -> ComposerState:
    """
    Update state with results from an agent execution.
    
    Args:
        state: Current state
        agent_name: Name of the agent that executed
        result: Results from the agent
        execution_time: Time taken for execution
        
    Returns:
        Updated state
    """
    # Update execution tracking
    state["execution_times"][agent_name] = execution_time
    state["agent_results"].append({
        "agent": agent_name,
        "result": result,
        "execution_time": execution_time,
        "timestamp": datetime.now()
    })
    
    # Mark step as completed
    if agent_name not in state["completed_steps"]:
        state["completed_steps"].append(agent_name)
    
    # Update current agent and timestamp
    state["current_agent"] = agent_name
    state["updated_at"] = datetime.now()
    
    return state
