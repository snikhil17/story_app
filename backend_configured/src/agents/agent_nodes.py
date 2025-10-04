"""
Agent Nodes with LangGraph React Agent Integration for Composer Engine

This module provides agent functions that use LangGraph's create_react_agent,
adapted from the Composer system for the new one-graph-workflow architecture.
Enhanced with ReAct pattern for reasoning and action capabilities.
"""

import json
import gc
import tracemalloc
# from memory_profiler import profile
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

# LangGraph imports for React agent functionality
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# Import output manager for saving results
try:
    from ..utils.output_manager import save_run_output
    OUTPUT_MANAGER_AVAILABLE = True
except ImportError:
    OUTPUT_MANAGER_AVAILABLE = False
    # Note: logger defined below, so we can't use it here

# Load environment variables
load_dotenv()

# Image style mapping from frontend selections to aesthetic descriptions
def get_aesthetic_from_image_style(image_style: str, return_details: bool = False) -> str | dict:
    """Map frontend image style selection to detailed aesthetic description for image generation.
    
    Args:
        image_style: The style name (e.g. 'ghibli', 'disney', etc.)
        return_details: If True, returns the detailed style dict; if False, returns formatted string
        
    Returns:
        If return_details=True: dict with 'medium', 'lighting', 'colors', 'details', 'mood' keys
        If return_details=False: formatted string for backward compatibility
    """
    
    print(f"🎨 [DEBUG] get_aesthetic_from_image_style called with: '{image_style}', return_details={return_details}")
    
    style_map = {
    'ghibli': {
        'medium': 'hand-painted watercolor, traditional animation cel, visible brushstrokes, organic textures',
        'lighting': 'soft natural light, dappled sunlight through trees, gentle shadows, warm afternoon glow',
        'colors': 'muted earth tones, sage greens, sky blues, warm browns, dusty yellows, subtle gradients',
        'details': 'intricate grass rendering, cumulus cloud formations, environmental storytelling, wind movement in nature',
        'mood': 'nostalgic, peaceful, contemplative, wonder, connection with nature'
    },
    
    'disney': {
        'medium': 'digital painting, clean vector illustration, polished cel animation, smooth gradients',
        'lighting': 'three-point lighting, warm key light, rim lighting for depth, magical sparkles',
        'colors': 'saturated primaries, vibrant technicolor palette, warm highlights, jewel-like clarity',
        'details': 'smooth animation curves, appeal in character design, clear staging, refined linework',
        'mood': 'magical, optimistic, theatrical, enchanting, joyful celebration'
    },
    
    'fantasy': {
        'medium': 'digital oil painting, concept art rendering, photobashing techniques, matte painting',
        'lighting': 'dramatic chiaroscuro, volumetric lighting, mystical glows, god rays, torch light',
        'colors': 'deep jewel tones, rich purples, burnished golds, emerald greens, crimson reds',
        'details': 'ornate armor designs, flowing fabrics, magical particles, ancient runes, weathered textures',
        'mood': 'epic, heroic, mysterious, awe-inspiring, ancient power'
    },
    
    'watercolor': {
        'medium': 'wet-on-wet watercolor, transparent washes, visible paper texture, paint blooms',
        'lighting': 'diffused natural light, soft shadows, luminous transparency, gentle highlights',
        'colors': 'delicate pastels, flowing color bleeds, harmonious earth tones, occasional vivid accents',
        'details': 'organic paint flows, granulation effects, lost and found edges, spontaneous mixing',
        'mood': 'dreamy, ethereal, gentle, impressionistic, serene contemplation'
    },
    
    'splash-art': {
        'medium': 'digital hyperrealistic painting, mixed media effects, paint splatter overlay, sharp rendering',
        'lighting': 'intense rim lighting, color contrast lighting, dramatic spotlights, neon accents',
        'colors': 'electric vibrant hues, complementary color explosions, saturated neons, high contrast',
        'details': 'motion blur effects, speed lines, particle explosions, dynamic hair and fabric, energy trails',
        'mood': 'explosive energy, intense action, powerful impact, competitive spirit, climactic moment'
    },
    
    'cover-art': {
        'medium': 'professional illustration, mixed traditional and digital, publication-ready finish',
        'lighting': 'cinematic mood lighting, strategic focal illumination, atmospheric depth, golden hour tones',
        'colors': 'genre-appropriate palette, sophisticated color harmony, strategic accent colors, rich darks',
        'details': 'symbolic visual metaphors, layered narrative elements, intricate textures, refined details',
        'mood': 'intriguing, evocative, mysterious promise, emotional resonance, story invitation'
    },
    
    'cartoon': {
        'medium': 'vector art style, cel-shaded rendering, bold clean outlines, flat color fills',
        'lighting': 'simple two-tone shading, bright even lighting, minimal shadows, clear visibility',
        'colors': 'primary color dominance, bright saturated hues, limited palette, high contrast combinations',
        'details': 'simplified shapes, exaggerated features, rubber hose animation influence, bouncy forms',
        'mood': 'playful, energetic, friendly, humorous, accessible fun'
    },
    
    'minimalist': {
        'medium': 'clean vector graphics, geometric abstraction, precise digital illustration, flat design',
        'lighting': 'ambient uniform lighting, subtle shadows if any, emphasis on form over lighting',
        'colors': 'restricted palette 2-3 colors max, monochromatic schemes, strategic color placement',
        'details': 'essential elements only, meaningful negative space, perfect balance, intentional simplicity',
        'mood': 'sophisticated, contemplative, modern elegance, zen-like clarity, quiet confidence'
    },
    
    'vintage': {
        'medium': 'lithograph printing, engraving techniques, aged paper texture, traditional illustration methods',
        'lighting': 'classic three-quarter lighting, soft window light, nostalgic warmth, gentle contrasts',
        'colors': 'sepia tones, muted ochres, faded blues, antique cream, dusty roses, aged color palette',
        'details': 'crosshatching, stippling, art nouveau flourishes, decorative borders, hand-lettered elements',
        'mood': 'nostalgic, timeless, romantic, old-world charm, storybook wonder'
    },
    
    'anime': {
        'medium': 'digital anime production, vector-like clean lines, cel-shaded coloring, crisp rendering',
        'lighting': 'dramatic sunset/sunrise lighting, lens flares, bloom effects, colored shadows, backlight halos',
        'colors': 'vibrant anime color design, gradient skies, pastel tones with vivid accents, clear color separation',
        'details': 'detailed eyes with multiple highlights, flowing hair with individual strands, speed lines, sakura petals',
        'mood': 'emotional intensity, slice of life beauty, dramatic tension, youthful energy, japanese aesthetic'
    }
}
    
    # Get style data or fallback to ghibli
    style_data = style_map.get(image_style, style_map['ghibli'])
    
    if return_details:
        # Return the detailed dictionary
        print(f"🎨 [DEBUG] Returning detailed style info for '{image_style}': {style_data}")
        return style_data
    else:
        # Create formatted aesthetic description for backward compatibility
        result = f"{style_data['medium']}, {style_data['lighting']}, {style_data['colors']}, {style_data['details']}, {style_data['mood']}"
        print(f"🎨 [DEBUG] Mapped '{image_style}' to: '{result}'")
        return result

logger = logging.getLogger(__name__)

# Global LLM instance
_llm = None

# Pydantic models for structured output
class ContentSection(BaseModel):
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    scene_description: str = Field(description="Brief description of the scene for image generation")
    type: Optional[str] = Field(description="Content type (for poetry/music)", default=None)

class FormattedStory(BaseModel):
    title: str = Field(description="Content title")
    summary: str = Field(description="Brief summary")
    reading_time: Optional[int] = Field(description="Estimated reading time in minutes", default=None)
    estimated_duration: Optional[int] = Field(description="Estimated duration for poetry/music", default=None)
    chapters: Optional[list[ContentSection]] = Field(description="Story chapters", default=None)
    sections: Optional[list[ContentSection]] = Field(description="Content sections for poetry/music", default=None)
    word_count: int = Field(description="Total word count")
    themes: list[str] = Field(description="Main themes")
    characters: Optional[list[str]] = Field(description="Main characters (for stories)", default=None)
    mood: Optional[str] = Field(description="Overall mood (for poetry/music)", default=None)
    rhyme_scheme: Optional[str] = Field(description="Rhyme scheme (for poetry)", default=None)
    musical_style: Optional[str] = Field(description="Musical style (for music)", default=None)

class FormatterOutput(BaseModel):
    formatted_story: Optional[FormattedStory] = Field(description="The formatted story structure", default=None)
    formatted_content: Optional[FormattedStory] = Field(description="The formatted content structure", default=None)
    image_prompts: list[str] = Field(description="Specific image generation prompts for each scene")

# Global checkpointer for agent memory
_checkpointer = InMemorySaver()

# LangGraph Tools for React Agents
@tool
def analyze_story_plan(plan_data: str, user_requirements: str) -> str:
    """Analyze a story plan and provide feedback for improvement."""
    try:
        plan = json.loads(plan_data) if isinstance(plan_data, str) else plan_data
        analysis = {
            "structure_score": 8.5,
            "creativity_score": 9.0,
            "age_appropriateness": "good",
            "suggestions": ["Add more character development", "Include educational themes"]
        }
        return f"Plan analysis complete: {json.dumps(analysis, indent=2)}"
    except Exception as e:
        return f"Error analyzing plan: {str(e)}"

@tool
def validate_content_format(content: str, content_type: str) -> str:
    """Validate content formatting and structure."""
    try:
        word_count = len(content.split())
        validation = {
            "word_count": word_count,
            "content_type": content_type,
            "structure_valid": True,
            "recommendations": []
        }
        
        if word_count < 50:
            validation["recommendations"].append("Content seems too short")
        elif word_count > 1000:
            validation["recommendations"].append("Content might be too long for target audience")
            
        return f"Content validation: {json.dumps(validation, indent=2)}"
    except Exception as e:
        return f"Error validating content: {str(e)}"

@tool
def extract_image_scenes(content: str, image_count: int = 3) -> str:
    """Extract key scenes from content for image generation."""
    try:
        # Simple scene extraction logic
        sentences = content.split('.')[:image_count * 2]  # Get more than needed
        scenes = []
        
        for i in range(min(image_count, len(sentences))):
            if sentences[i].strip():
                scenes.append(f"Scene {i+1}: {sentences[i].strip()}")
        
        return f"Extracted scenes: {json.dumps(scenes, indent=2)}"
    except Exception as e:
        return f"Error extracting scenes: {str(e)}"

@tool
def load_configuration(use_case: str, config_type: str = "default") -> str:
    """Load configuration settings for specific use cases."""
    try:
        # This would normally load from your config system
        config = {
            "story_generator": {"word_count": 400, "reading_time": 5},
            "poetry_and_song": {"word_count": 200, "estimated_duration": 3},
            "educational_content": {"word_count": 300, "learning_objectives": 2}
        }
        
        result = config.get(use_case, config.get("story_generator"))
        return f"Configuration loaded: {json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error loading configuration: {str(e)}"

@tool
def expand_story_outline(plan: str, target_word_count: int) -> str:
    """Expand a story outline into detailed narrative sections."""
    try:
        # Parse plan if it's JSON
        plan_data = json.loads(plan) if isinstance(plan, str) else plan
        
        expansion = {
            "narrative_structure": "three-act structure",
            "detailed_scenes": 3,
            "target_words": target_word_count,
            "pacing_guide": "introduction (25%), development (50%), conclusion (25%)",
            "expansion_notes": "Focus on character development and descriptive language"
        }
        
        return f"Story expansion guide: {json.dumps(expansion, indent=2)}"
    except Exception as e:
        return f"Error expanding outline: {str(e)}"

@tool
def check_reading_level(content: str, target_age: int) -> str:
    """Check if content matches target reading level."""
    try:
        word_count = len(content.split())
        avg_word_length = sum(len(word) for word in content.split()) / max(word_count, 1)
        
        analysis = {
            "word_count": word_count,
            "average_word_length": round(avg_word_length, 2),
            "target_age": target_age,
            "complexity_score": "appropriate" if avg_word_length < 6 else "complex",
            "recommendations": []
        }
        
        if avg_word_length > 6:
            analysis["recommendations"].append("Consider using simpler words")
        if word_count > 500 and target_age < 8:
            analysis["recommendations"].append("Content might be too long for age group")
            
        return f"Reading level analysis: {json.dumps(analysis, indent=2)}"
    except Exception as e:
        return f"Error checking reading level: {str(e)}"

@tool
def format_content_structure(content: str, content_type: str) -> str:
    """Format content into structured sections suitable for mobile display."""
    try:
        # Split content into manageable sections
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if content_type == "story":
            structure = {
                "type": "story",
                "chapters": [],
                "estimated_sections": min(len(paragraphs) // 2, 5)
            }
            
            # Group paragraphs into chapters
            chapter_size = max(2, len(paragraphs) // structure["estimated_sections"])
            for i in range(0, len(paragraphs), chapter_size):
                chapter_paragraphs = paragraphs[i:i + chapter_size]
                structure["chapters"].append({
                    "title": f"Chapter {len(structure['chapters']) + 1}",
                    "content": "\n\n".join(chapter_paragraphs),
                    "scene_description": chapter_paragraphs[0][:100] + "..."
                })
                
        else:  # poetry or music
            structure = {
                "type": content_type,
                "sections": [],
                "estimated_verses": min(len(paragraphs), 6)
            }
            
            for i, paragraph in enumerate(paragraphs[:structure["estimated_verses"]]):
                structure["sections"].append({
                    "title": f"Verse {i + 1}",
                    "content": paragraph,
                    "scene_description": paragraph[:100] + "..."
                })
        
        return f"Content structure: {json.dumps(structure, indent=2)}"
    except Exception as e:
        return f"Error formatting structure: {str(e)}"

@tool
def generate_image_prompts(content: str, image_count: int, aesthetic_style: str) -> str:
    """Generate specific image prompts based on content scenes."""
    try:
        # Extract key scenes from content
        sentences = content.replace('\n', ' ').split('.')
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:image_count * 2]
        
        prompts = []
        for i in range(min(image_count, len(key_sentences))):
            scene = key_sentences[i]
            # Create descriptive prompt
            prompt = f"{aesthetic_style}, {scene[:100]}, children's book illustration, colorful, engaging"
            prompts.append(prompt)
        
        # Ensure we have the requested number of prompts
        while len(prompts) < image_count:
            prompts.append(f"{aesthetic_style}, magical scene, children's book illustration, colorful, whimsical")
        
        result = {
            "image_prompts": prompts[:image_count],
            "prompt_count": len(prompts[:image_count]),
            "aesthetic_style": aesthetic_style
        }
        
        return f"Generated prompts: {json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error generating image prompts: {str(e)}"

@tool
def generate_personalized_image_prompts(content: str, image_count: int, aesthetic_style: str, personalization_data: dict) -> str:
    """Generate highly detailed, personalized image prompts based on content and character details."""
    try:
        # Extract personalization details
        child_name = personalization_data.get("child_name", "the child")
        child_age = personalization_data.get("child_age", 5)
        child_gender = personalization_data.get("child_gender", "neutral")
        interests = personalization_data.get("interests", [])
        location = personalization_data.get("location", "")
        companions = personalization_data.get("companions", [])
        reading_level = personalization_data.get("reading_level", "medium")
        
        # Create detailed character description template
        def create_character_description(name: str, age: int, gender: str) -> str:
            """Create consistent character description for all images."""
            gender_features = {
                "she": "a girl with gentle features and curious eyes",
                "he": "a boy with bright features and curious eyes", 
                "they": "a child with kind features and curious eyes",
                "neutral": "a child with bright, curious eyes"
            }
            
            age_descriptors = {
                range(2, 4): "toddler",
                range(4, 6): "young child", 
                range(6, 9): "child",
                range(9, 13): "pre-teen"
            }
            
            age_desc = "child"
            for age_range, desc in age_descriptors.items():
                if age in age_range:
                    age_desc = desc
                    break
            
            base_desc = f"{name}, a {age_descriptors.get(range(age, age+1), age_desc)} {gender_features.get(gender, gender_features['neutral'])}"
            
            # Add physical characteristics based on personalization
            if location and any(region in location.lower() for region in ['india', 'mumbai', 'delhi', 'bangalore']):
                base_desc += ", with soft dark hair and warm brown eyes"
            else:
                base_desc += ", with bright expressive features"
                
            return base_desc

        # Create environment context
        def create_environment_context(location: str, interests: list) -> str:
            """Create environment description based on location and interests."""
            env_desc = ""
            if location:
                if any(city in location.lower() for city in ['mumbai', 'delhi', 'bangalore', 'pune']):
                    env_desc = f"in a vibrant {location} neighborhood with colorful houses and lush greenery"
                else:
                    env_desc = f"in a charming {location} setting"
            
            # Add interest-based environmental elements
            if 'nature' in interests or 'animals' in interests:
                env_desc += ", surrounded by beautiful nature and friendly animals"
            elif 'science' in interests:
                env_desc += ", with elements of discovery and learning"
            elif 'art' in interests or 'music' in interests:
                env_desc += ", with creative and artistic elements"
                
            return env_desc

        # Extract story chapters/scenes for prompts
        chapters = content.split('Chapter ')
        scenes = []
        
        if len(chapters) > 1:
            for i, chapter in enumerate(chapters[1:], 1):  # Skip first empty split
                if chapter.strip():
                    lines = chapter.strip().split('\n')
                    title = lines[0].split(':')[1].strip() if ':' in lines[0] else f"Scene {i}"
                    scene_content = ' '.join(lines[1:5])  # First few lines for context
                    scenes.append({"title": title, "content": scene_content})
        else:
            # Fallback: split by paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()][:image_count]
            for i, para in enumerate(paragraphs, 1):
                scenes.append({"title": f"Scene {i}", "content": para[:200]})

        # Generate detailed prompts
        prompts = []
        character_desc = create_character_description(child_name, child_age, child_gender)
        env_context = create_environment_context(location, interests)
        
        for i in range(min(image_count, len(scenes))):
            scene = scenes[i]
            
            # Create companion description if available
            companion_desc = ""
            if companions and i < len(companions):
                comp = companions[i % len(companions)]  # Cycle through companions
                companion_desc = f" with {comp.get('name', 'a friend')}, their {comp.get('type', 'companion')}"
                if comp.get('description'):
                    companion_desc += f" ({comp['description']})"
            
            # Build comprehensive prompt with all details
            detailed_prompt = f"{character_desc}{companion_desc} {scene['content'][:150]}. CHARACTER FOCUS: {character_desc}, age-appropriate proportions for a {child_age}-year-old, cheerful and engaging expression. COMPANIONS: {companion_desc if companion_desc else 'None'}. ENVIRONMENT: {env_context}, {scene['title'].lower()} setting. LIGHTING & MOOD: Warm, inviting lighting creating a joyful and magical atmosphere, {aesthetic_style} style with vibrant, child-friendly color palette. COMPOSITION: Eye-level shot, centered subject with adequate margins, 16:9 aspect ratio, responsive layout. TECHNICAL: {aesthetic_style}, digital painting, masterpiece, ultra-detailed, high-quality rendering, intricate details, polished finish, character-focused composition, age-accurate proportions, sharp focus, personalized and authentic. NEGATIVE: --no age mismatch, gender confusion, character inaccuracy, generic appearance, wrong proportions, blurry details, poor composition"
            
            prompts.append(detailed_prompt)
        
        # Fill remaining prompts if needed
        while len(prompts) < image_count:
            fallback_prompt = f"{character_desc} in a magical adventure. {env_context}. CHARACTER FOCUS: {character_desc}, joyful expression. ENVIRONMENT: Magical, whimsical setting perfect for {child_name}'s adventure. LIGHTING & MOOD: Bright, cheerful lighting, {aesthetic_style} style. COMPOSITION: Centered, engaging composition. TECHNICAL: {aesthetic_style}, high-quality, detailed, child-friendly."
            prompts.append(fallback_prompt)
        
        result = {
            "image_prompts": prompts[:image_count],
            "prompt_count": len(prompts[:image_count]),
            "aesthetic_style": aesthetic_style,
            "personalization_applied": True,
            "character_description": character_desc,
            "environment_context": env_context
        }
        
        return f"Generated personalized prompts: {json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error generating personalized image prompts: {str(e)}"

def get_llm() -> ChatGoogleGenerativeAI:
    """Get or create the LLM instance with automatic .env loading for LangGraph compatibility."""
    global _llm
    if _llm is None:
        # Ensure .env is loaded
        load_dotenv()
        
        model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables.\n"
                "Please ensure your .env file contains:\n"
                "GOOGLE_API_KEY=your_actual_api_key_here"
            )
        
        try:
            _llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.7
            )
            logger.info(f"✅ LLM initialized successfully for LangGraph: {model_name}")
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM: {e}")
    
    return _llm

def create_react_agent_for_task(agent_name: str, tools: Optional[List] = None, custom_prompt: Optional[str] = None, format_vars: Optional[Dict[str, Any]] = None) -> Any:
    """Create a React agent for a specific task with config-based prompt loading and optional variable substitution."""
    if tools is None:
        tools = []
    
    # Get LLM
    llm = get_llm()
    
    # Use ONLY config-based prompt loading (single source of truth)
    if custom_prompt is None:
        custom_prompt = load_prompt_from_config(agent_name, "system_prompt", format_vars)
    else:
        logger.info(f"📋 PROMPT SOURCE: {agent_name} using CUSTOM PROMPT (directly provided)")
        logger.info(f"📏 CUSTOM PROMPT LENGTH: {len(custom_prompt)} characters")
    
    # Create the React agent with memory
    try:
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=custom_prompt,
            checkpointer=_checkpointer
        )
        logger.info(f"✅ Created React agent for {agent_name} with {len(tools)} tools")
        return agent
    except Exception as e:
        logger.error(f"Failed to create React agent for {agent_name}: {e}")
        # Fallback to direct LLM if agent creation fails
        return llm

# COMMENTED OUT: Priority-based prompt loading system (redundant, use config only)
# def create_react_agent_for_task_with_priority(agent_name: str, tools: Optional[List] = None, custom_prompt: Optional[str] = None, inline_prompt: Optional[str] = None) -> Any:
#     """DEPRECATED: Create a React agent with priority-based prompt loading."""
#     if tools is None:
#         tools = []
#     
#     # Get LLM
#     llm = get_llm()
#     
#     # Use the priority-based prompt loading system
#     if custom_prompt is None:
#         custom_prompt = load_prompt_with_priority(agent_name, "system_prompt", inline_prompt)
#     else:
#         logger.info(f"📋 PROMPT SOURCE: {agent_name} using CUSTOM PROMPT (directly provided)")
#         logger.info(f"📏 CUSTOM PROMPT LENGTH: {len(custom_prompt)} characters")
#     
#     # Create the React agent with memory
#     try:
#         agent = create_react_agent(
#             model=llm,
#             tools=tools,
#             prompt=custom_prompt,
#             checkpointer=_checkpointer
#         )
#         logger.info(f"✅ Created React agent for {agent_name} with {len(tools)} tools")
#         return agent
#     except Exception as e:
#         logger.error(f"Failed to create React agent for {agent_name}: {e}")
#         # Fallback to direct LLM if agent creation fails
#         return llm

# COMMENTED OUT: Priority-based prompt loading (redundant, use config only)
# def load_prompt_with_priority(agent_name: str, prompt_type: str = "system_prompt", inline_prompt: Optional[str] = None) -> str:
#     """
#     DEPRECATED: Load prompt following the specified priority order.
#     Use load_prompt_from_config instead for single source of truth.
#     
#     Args:
#         agent_name: Name of the agent
#         prompt_type: Type of prompt to load
#         inline_prompt: Optional inline prompt from the function
#         
#     Returns:
#         Prompt string with source tracking
#     """
#     # Priority 1: Try to load from config (prompts.yaml)
#     try:
#         from ..composer.config_loader import ConfigLoader
#         config_loader = ConfigLoader()
#         
#         # Use the correct method to get agent prompt
#         config_prompt = config_loader.get_agent_prompt(agent_name, prompt_type)
#         
#         if config_prompt and config_prompt.strip():
#             # Enhanced logging for prompt source tracking
#             logger.info(f"📋 PROMPT SOURCE: {agent_name}.{prompt_type} loaded FROM YAML (prompts.yaml) - PRIORITY 1")
#             logger.info(f"📏 PROMPT LENGTH: {len(config_prompt)} characters")
#             logger.info(f"📝 PROMPT PREVIEW: {config_prompt[:150]}...")
#             return config_prompt
#             
#     except Exception as e:
#         logger.warning(f"Could not load prompt from config for {agent_name}: {e}")
#     
#     # Priority 2: Use inline prompt from function if available
#     if inline_prompt and inline_prompt.strip():
#         logger.info(f"📋 PROMPT SOURCE: {agent_name}.{prompt_type} using INLINE PROMPT (from function) - PRIORITY 2")
#         logger.info(f"📏 PROMPT LENGTH: {len(inline_prompt)} characters")
#         logger.info(f"📝 PROMPT PREVIEW: {inline_prompt[:150]}...")
#         return inline_prompt
#     
#     # Priority 3: Fallback prompt
#     fallback_prompt = f"You are a helpful {agent_name} assistant for children's content creation."
#     logger.warning(f"📋 PROMPT SOURCE: {agent_name}.{prompt_type} using FALLBACK (hardcoded) - PRIORITY 3")
#     logger.warning(f"📏 FALLBACK LENGTH: {len(fallback_prompt)} characters")
#     return fallback_prompt

def load_prompt_from_config(agent_name: str, prompt_type: str = "system_prompt", format_vars: Optional[Dict[str, Any]] = None) -> str:
    """
    Load prompt from prompts.yaml configuration with optional variable substitution.
    Single source of truth - no priority system, no inline prompts.
    
    Args:
        agent_name: Name of the agent
        prompt_type: Type of prompt to load (system_prompt or user_prompt)
        format_vars: Optional dictionary of variables for string formatting (e.g., {aesthetic: "Studio Ghibli style"})
        
    Returns:
        Prompt string from configuration with variables substituted
    """
    try:
        from ..composer.config_loader import ConfigLoader
        config_loader = ConfigLoader()
        
        # Load the prompt from config
        prompt = config_loader.get_agent_prompt(agent_name, prompt_type)
        
        if prompt and prompt.strip():
            # Apply variable substitution if format_vars provided
            if format_vars:
                try:
                    prompt = prompt.format(**format_vars)
                    logger.info(f"📝 Applied variable substitution to {agent_name}.{prompt_type}")
                    logger.info(f"🔧 Variables: {list(format_vars.keys())}")
                except KeyError as e:
                    logger.warning(f"⚠️ Missing variable for formatting {agent_name}.{prompt_type}: {e}")
                    # Continue with unformatted prompt rather than failing
                except Exception as e:
                    logger.warning(f"⚠️ Error formatting {agent_name}.{prompt_type}: {e}")
                    # Continue with unformatted prompt rather than failing
            
            # Log prompt source for debugging
            logger.info(f"📋 Loaded {agent_name}.{prompt_type} from prompts.yaml")
            logger.info(f"📐 Prompt length: {len(prompt)} characters")
            return prompt
        else:
            # If prompt not found, raise error instead of fallback
            raise ValueError(f"Prompt {agent_name}.{prompt_type} not found in prompts.yaml")
            
    except Exception as e:
        logger.error(f"Failed to load prompt for {agent_name}.{prompt_type}: {e}")
        # Instead of complex fallback, fail fast
        raise ValueError(f"Required prompt {agent_name}.{prompt_type} missing from prompts.yaml") from e


def log_llm_interaction(agent_name: str, system_prompt: str, user_prompt: str, 
                       llm_response: str, execution_time: float):
    """Log LLM interaction details."""
    logger.info(f"🤖 {agent_name.upper()} LLM CALL")
    logger.info(f"⏱️ Execution time: {execution_time:.2f}s")
    logger.info(f"📝 User prompt length: {len(user_prompt)} chars")
    logger.info(f"📄 Response length: {len(llm_response)} chars")

def log_prompt_usage_summary(state: Dict[str, Any]):
    """Log a comprehensive summary of which prompts were used during the run."""
    logger.info("=" * 80)
    logger.info("📊 PROMPT USAGE SUMMARY FOR THIS RUN")
    logger.info("=" * 80)
    
    # Extract run information
    use_case = state.get("use_case", "unknown")
    workflow_step = state.get("workflow_step", "unknown")
    current_agent = state.get("current_agent", "unknown")
    
    logger.info(f"🎯 Use Case: {use_case}")
    logger.info(f"🏁 Final Workflow Step: {workflow_step}")
    logger.info(f"🤖 Last Active Agent: {current_agent}")
    logger.info(f"🔄 Total State Keys: {len(state.keys())}")
    
    # Log the sequence of agents that ran (if trackable from state)
    agents_run = []
    if state.get("content"):
        agents_run.extend(["planner", "writer"])
    if state.get("formatted_story") or state.get("formatted_content"):
        agents_run.append("content_generator")
    if state.get("critique_feedback"):
        agents_run.append("critique")
    if state.get("image_metadata") or state.get("story_image_prompts"):
        agents_run.append("image_generator")
    
    logger.info(f"🔄 Agents Run Sequence: {' → '.join(agents_run)}")
    logger.info("=" * 80)

def simple_save_output(state: Dict[str, Any]) -> str:
    """Simple output saving function."""
    try:
        import os
        from pathlib import Path
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"composer_run_{timestamp}"
        base_dir = Path(__file__).parent.parent.parent / "outputs" / "runs"
        run_dir = base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []  # Track what files we save
        
        # Save story content if available (standardized as content.txt)
        if state.get("content"):
            filepath = run_dir / "content.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(state["content"])
            saved_files.append("content.txt")
        
        # Save poetry content if available (standardized as content.txt)
        if state.get("poetry_content"):
            filepath = run_dir / "content.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(state["poetry_content"])
            saved_files.append("content.txt")
        
        # Save music content if available
        if state.get("music_content"):
            filepath = run_dir / "music_content.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(state["music_content"])
            saved_files.append("music_content.txt")
        
        # Save formatted story if available
        if state.get("formatted_story"):
            # Save JSON format for programmatic access
            filepath = run_dir / "formatted_story.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["formatted_story"], f, indent=2, ensure_ascii=False)
            saved_files.append("formatted_story.json")
            
            # Save user-friendly text format (standardized as content.txt)
            formatted_story = state["formatted_story"]
            filepath = run_dir / "content.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {formatted_story.get('title', 'Untitled Story')}\n\n")
                
                if "chapters" in formatted_story:
                    for i, chapter in enumerate(formatted_story["chapters"], 1):
                        f.write(f"Chapter {i}: {chapter.get('title', f'Chapter {i}')}\n")
                        f.write("=" * 50 + "\n")
                        f.write(f"{chapter.get('content', '')}\n\n")
                elif "content" in formatted_story:
                    f.write(f"{formatted_story['content']}\n")
            saved_files.append("content.txt")
        
        # Save formatted content (poetry/music) if available
        if state.get("formatted_content"):
            # Save JSON format for programmatic access
            filepath = run_dir / "formatted_content.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["formatted_content"], f, indent=2, ensure_ascii=False)
            saved_files.append("formatted_content.json")
            
            # Save user-friendly text format (standardized as content.txt)
            formatted_content = state["formatted_content"]
            filepath = run_dir / "content.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {formatted_content.get('title', 'Untitled Content')}\n\n")
                
                if "sections" in formatted_content:
                    for i, section in enumerate(formatted_content["sections"], 1):
                        f.write(f"Section {i}: {section.get('title', f'Section {i}')}\n")
                        if section.get('type'):
                            f.write(f"Type: {section['type']}\n")
                        f.write("=" * 50 + "\n")
                        f.write(f"{section.get('content', '')}\n\n")
                elif "content" in formatted_content:
                    f.write(f"{formatted_content['content']}\n")
            saved_files.append("content.txt")
        
        # Save story image prompts if available
        if state.get("story_image_prompts"):
            filepath = run_dir / "story_image_prompts.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["story_image_prompts"], f, indent=2, ensure_ascii=False)
            saved_files.append("story_image_prompts.json")
        
        # Save image descriptions if available
        if state.get("image_descriptions"):
            filepath = run_dir / "image_descriptions.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(state["image_descriptions"])
            saved_files.append("image_descriptions.txt")
        
        # Save image metadata if available
        if state.get("image_metadata"):
            filepath = run_dir / "image_metadata.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["image_metadata"], f, indent=2, ensure_ascii=False)
            saved_files.append("image_metadata.json")
        
        # Save used image prompts if available
        if state.get("used_image_prompts"):
            filepath = run_dir / "used_image_prompts.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["used_image_prompts"], f, indent=2, ensure_ascii=False)
            saved_files.append("used_image_prompts.json")
        
        # Save plan if available
        if state.get("plan"):
            filepath = run_dir / "story_plan.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["plan"], f, indent=2, ensure_ascii=False)
            saved_files.append("story_plan.json")
        
        # Save critique if available
        if state.get("critique_feedback"):
            filepath = run_dir / "story_critique.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state["critique_feedback"], f, indent=2, ensure_ascii=False)
            saved_files.append("story_critique.json")
        
        # Save complete state for debugging
        if state:
            state_copy = dict(state)
            # Remove large objects that can't be serialized
            for key in ["agent_config"]:
                state_copy.pop(key, None)
            
            filepath = run_dir / "complete_state.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state_copy, f, indent=2, ensure_ascii=False, default=str)
            saved_files.append("complete_state.json")
        
        # Log what was saved
        logger.info(f"📁 Saved {len(saved_files)} files to: {run_dir}")
        for filename in saved_files:
            logger.info(f"   💾 {filename}")
        
        # Debug: log available state keys for troubleshooting
        available_content_keys = [key for key in state.keys() if 'content' in key.lower()]
        logger.info(f"🔍 Available content keys in state: {available_content_keys}")
        
        # Log comprehensive prompt usage summary
        log_prompt_usage_summary(state)
        
        return str(run_dir)
    except Exception as e:
        logger.error(f"Error in simple_save_output: {e}")
        return ""

def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Story planning agent with LangGraph React Agent integration.
    Creates detailed story blueprints using ReAct pattern for enhanced reasoning.
    """
    start_time = time.time()
    
    print(f"🔍 [DEBUG] planner_node called - image_style in state: {state.get('image_style', 'NOT FOUND')}")
    print(f"🔍 [DEBUG] planner_node - ALL STATE KEYS: {list(state.keys())}")
    
    try:
        # Extract input data including personalization
        user_input = state.get("user_input", "")
        age_group = state.get("target_audience", "6-12")
        educational_themes = state.get("style_preferences", {}).get("educational_themes", [])
        
        # Extract personalization parameters
        child_name = state.get("child_name", "Hero")
        child_age = state.get("child_age", 8)
        child_gender = state.get("child_gender", "neutral")
        interests = state.get("interests", [])
        reading_level = state.get("reading_level", "medium")
        companions = state.get("companions", [])
        location = state.get("location", "")
        region = state.get("region", "")
        mother_tongue = state.get("mother_tongue", "")
        language_of_story = state.get("language_of_story", "english")
        moral_lesson = state.get("moral_lesson", "")
        theme = state.get("theme", "adventure")
        story_length = state.get("story_length", "medium")
        
        # Load story length constraints from use case config
        try:
            from ..composer.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            use_case_config = config_loader.get_use_case_config("story_generator")
            
            # Get story length constraints
            length_constraints = use_case_config.get("settings", {}).get("story_length_constraints", {})
            story_config = length_constraints.get(story_length, length_constraints.get("medium", {}))
            
            # Extract word count constraint
            word_count = story_config.get("word_count", 400)
            
            # Store in state for later use
            state["word_count"] = word_count 
            
            logger.info(f"📝 Planner loaded story constraints: {story_length} - {word_count} words")
            
        except Exception as e:
            logger.warning(f"Could not load story length constraints in planner: {e}. Using defaults.")
            word_count = 400
        
        # Define tools for the planner agent
        planner_tools = [
            analyze_story_plan,
            load_configuration,
            validate_content_format
        ]
        
        # COMMENTED OUT: Inline prompt (redundant, use config only)
        # inline_prompt = f"""You are an expert story planner specializing in creating engaging, age-appropriate content for children.
        # 
        # Your task is to create detailed story plans that are:
        # 1. Age-appropriate for the target audience: {age_group}
        # 2. Written in the specified language: {language_of_story}
        # 3. Personalized for the child: {child_name}
        # 4. Incorporating themes: {theme}
        # 
        # Always use the available tools to analyze and validate your plans. Think step by step and use reasoning to create the best possible story plan.
        # 
        # When creating a plan, provide a JSON response with the following structure:
        # {{
        #     "title": "Story title",
        #     "plot_content": "Detailed plot description",
        #     "themes": ["theme1", "theme2"],
        #     "characters": ["character1", "character2"],
        #     "setting": "Story setting",
        #     "word_count": {word_count}
        # }}"""
        
        # Create React agent using ONLY config-based prompt loading
        agent = create_react_agent_for_task(
            agent_name="planner",
            tools=planner_tools
        )
        
        # Prepare comprehensive input for the agent
        planning_input = f"""Create a detailed story plan based on these requirements:

User Input: {user_input}
Target Age Group: {age_group}
Story Length: {story_length} ({word_count} words)

Personalization Details:
- Child's Name: {child_name}
- Child's Age: {child_age}
- Child's Gender: {child_gender}
- Interests: {', '.join(interests) if interests else 'general activities'}
- Reading Level: {reading_level}
- Companions: {str(companions)}
- Location: {location or 'neighborhood'}
- Region: {region or 'local area'}
- Mother Tongue: {mother_tongue or 'local language'}
- Language of Story: {language_of_story}
- Moral Lesson: {moral_lesson or 'friendship and kindness'}
- Theme: {theme}
- Educational Themes: {', '.join(educational_themes) if educational_themes else 'General learning'}

Please analyze the requirements using available tools and create a comprehensive story plan."""

        # Execute the React agent
        config = {"configurable": {"thread_id": f"planner_{int(time.time())}"}}
        
        try:
            # Try React agent execution
            response = agent.invoke(
                {"messages": [{"role": "user", "content": planning_input}]},
                config=config
            )
            
            # Extract response from React agent
            if isinstance(response, dict) and "messages" in response:
                response_text = response["messages"][-1].content
            else:
                response_text = str(response)
                
        except Exception as agent_error:
            logger.warning(f"React agent failed for planner, falling back to direct LLM: {agent_error}")
            logger.info(f"🔄 PROMPT SOURCE: planner FALLING BACK to YAML PROMPTS (prompts.yaml)")
            
            # Fallback to direct LLM call
            llm = get_llm()
            system_prompt = load_prompt_from_config("planner", "system_prompt")
            user_prompt_template = load_prompt_from_config("planner", "user_prompt")
            
            # Format the user prompt with personalization values
            user_prompt = user_prompt_template.format(
                user_input=user_input,
                age_group=age_group,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
                interests=', '.join(interests) if interests else 'general activities',
                reading_level=reading_level,
                companions=str(companions),
                location=location or 'neighborhood',
                region=region or 'local area',
                mother_tongue=mother_tongue or 'local language',
                language_of_story=language_of_story,
                moral_lesson=moral_lesson or 'friendship and kindness',
                theme=theme,
                word_count=word_count,
                educational_themes=', '.join(educational_themes) if educational_themes else 'General learning'
            )

            # Call LLM directly
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure response_text is a string
        if isinstance(response_text, list):
            response_text = str(response_text)
        elif not isinstance(response_text, str):
            response_text = str(response_text)
        
        # Parse response
        try:
            if response_text.strip().startswith('{'):
                plan_data = json.loads(response_text)
            else:
                # Extract JSON from response if wrapped in markdown
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group(1))
                else:
                    # Fallback structured plan
                    plan_data = {
                        "title": f"Story about {user_input}",
                        "characters": [{"name": "Main Character", "traits": ["brave", "curious"]}],
                        "setting": "A magical place",
                        "plot_outline": {
                            "beginning": "Introduction to the main character",
                            "middle": "Adventure and challenges", 
                            "end": "Resolution and learning"
                        },
                        "educational_opportunities": educational_themes or ["creativity"],
                        "target_length": "10-15 minutes",
                        "themes": ["friendship", "courage"]
                    }
        except json.JSONDecodeError:
            # Fallback plan
            plan_data = {
                "title": f"Story about {user_input}",
                "plot_content": response_text,
                "themes": educational_themes or ["learning"]
            }
        
        execution_time = time.time() - start_time
        
        # Log interaction
        log_llm_interaction("planner", "React Agent", planning_input, response_text, execution_time)
        
        # Update state
        state["plan"] = plan_data
        state["current_agent"] = "planner"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "planning_complete"
        
        logger.info(f"🎯 Planner React agent completed successfully in {execution_time:.2f}s")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in planner_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Planning error: {str(e)}"]
        state["current_agent"] = "planner"
        state["workflow_step"] = "error"
        return state

def writer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Story writing agent with LLM integration.
    Transforms story plans into engaging narrative prose.
    """
    start_time = time.time()
    
    try:
        # Extract input data including personalization
        plan = state.get("plan", {})
        user_input = state.get("user_input", "")
        age_group = state.get("target_audience", "6-12")
        story_length = state.get("story_length", "medium")
        
        # Extract personalization parameters
        child_name = state.get("child_name", "Hero")
        child_age = state.get("child_age", 8)
        child_gender = state.get("child_gender", "neutral")
        interests = state.get("interests", [])
        reading_level = state.get("reading_level", "medium")
        companions = state.get("companions", [])
        location = state.get("location", "")
        region = state.get("region", "")
        mother_tongue = state.get("mother_tongue", "")
        language_of_story = state.get("language_of_story", "english")
        moral_lesson = state.get("moral_lesson", "")
        theme = state.get("theme", "adventure")
        
        if not plan:
            raise ValueError("No story plan available for writing")
        
        # Load story length constraints from use case config
        try:
            from ..composer.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            use_case_config = config_loader.get_use_case_config("story_generator")
            
            # Get story length constraints
            length_constraints = use_case_config.get("settings", {}).get("story_length_constraints", {})
            story_config = length_constraints.get(story_length, length_constraints.get("medium", {}))
            
            # Get image count for page distribution
            image_count = use_case_config.get("settings", {}).get("image_generation", {}).get("count", 3)
            
            # Extract constraints
            word_count = story_config.get("word_count", 400)
            words_per_page = story_config.get("words_per_chapter", 135)  # Use words_per_chapter from config
            reading_time = story_config.get("reading_time", 5)
            
            # Store in state for later use
            state["word_count"] = word_count
            state["words_per_page"] = words_per_page
            state["reading_time"] = reading_time
            
            logger.info(f"📖 Story length constraints loaded: {story_length} - {word_count} words, {words_per_page} words/page")
            
        except Exception as e:
            logger.warning(f"Could not load story length constraints: {e}. Using defaults.")
            word_count = 400
            words_per_page = 135
            reading_time = 5
            image_count = 3
        
        # Define tools for the writer agent
        writer_tools = [
            expand_story_outline,
            check_reading_level,
            validate_content_format,
            load_configuration
        ]
        
        # COMMENTED OUT: Inline prompt (redundant, use config only)
        # inline_prompt = f"""You are an expert story writer specializing in creating engaging, age-appropriate narratives for children.
        # 
        # Your task is to transform story plans into compelling narratives that are:
        # 1. Age-appropriate for the target audience: {age_group}
        # 2. Written in the specified language: {language_of_story}
        # 3. Personalized for the child: {child_name}
        # 4. Approximately {word_count} words long
        # 5. Incorporating themes: {theme}
        # 
        # Always use the available tools to validate and enhance your writing. Think step by step to create the best possible story.
        # 
        # Focus on:
        # - Engaging opening that captures attention
        # - Character development and relatable situations  
        # - Educational value woven naturally into the narrative
        # - Age-appropriate vocabulary and sentence structure
        # - Satisfying conclusion with clear resolution"""
        
        # Create React agent using ONLY config-based prompt loading
        agent = create_react_agent_for_task(
            agent_name="writer",
            tools=writer_tools
        )
        
        # Prepare comprehensive input for the writing agent
        writing_input = f"""Transform the following story plan into a complete narrative:

STORY PLAN:
{json.dumps(plan, indent=2)}

WRITING REQUIREMENTS:
- Target Age Group: {age_group}
- Story Length: {story_length} ({word_count} words total, ~{words_per_page} words per page)
- Reading Time: {reading_time} minutes

PERSONALIZATION DETAILS:
- Child's Name: {child_name}
- Child's Age: {child_age}
- Child's Gender: {child_gender}
- Interests: {', '.join(interests) if interests else 'general activities'}
- Reading Level: {reading_level}
- Companions: {str(companions)}
- Location: {location or 'neighborhood'}
- Region: {region or 'local area'}
- Language of Story: {language_of_story}
- Moral Lesson: {moral_lesson or 'friendship and kindness'}
- Theme: {theme}

Please use your tools to analyze the plan, check reading level appropriateness, and create a complete, engaging story."""

        # Execute the React agent
        config = {"configurable": {"thread_id": f"writer_{int(time.time())}"}}
        
        try:
            # Try React agent execution
            response = agent.invoke(
                {"messages": [{"role": "user", "content": writing_input}]},
                config=config
            )
            
            # Extract response from React agent
            if isinstance(response, dict) and "messages" in response:
                story_content = response["messages"][-1].content
            else:
                story_content = str(response)
                
        except Exception as agent_error:
            logger.warning(f"React agent failed for writer, falling back to direct LLM: {agent_error}")
            
            # Fallback to direct LLM call
            llm = get_llm()
            system_prompt = load_prompt_from_config("writer", "system_prompt")
            user_prompt_template = load_prompt_from_config("writer", "user_prompt")
            
            # Prepare story length constraints text
            story_length_constraints = f"Story Length: {story_length.title()} ({word_count} words total, ~{words_per_page} words per page, {reading_time} min read)"
            
            # Format the user prompt with personalization values
            user_prompt = user_prompt_template.format(
                plan=json.dumps(plan, indent=2),
                user_input=user_input,
                age_group=age_group,
                story_length_constraints=story_length_constraints,
                word_count=word_count,
                words_per_page=words_per_page,
                image_count=image_count,
                # Personalization parameters
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
                interests=', '.join(interests) if interests else 'general activities',
                reading_level=reading_level,
                companions=str(companions),
                location=location or 'neighborhood',
                region=region or 'local area',
                mother_tongue=mother_tongue or 'local language',
                language_of_story=language_of_story,
                moral_lesson=moral_lesson or 'friendship and kindness',
                theme=theme
            )

            # Call LLM directly
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = llm.invoke(messages)
            story_content = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure story_content is a string
        if isinstance(story_content, list):
            story_content = str(story_content)
        elif not isinstance(story_content, str):
            story_content = str(story_content)
        
        execution_time = time.time() - start_time
        
        # Log interaction
        log_llm_interaction("writer", "React Agent", writing_input, story_content, execution_time)
        
        # Update state
        state["content"] = story_content
        state["current_agent"] = "writer"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "writing_complete"
        
        return state
        
    except Exception as e:
        logger.error(f"Error in writer_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Writing error: {str(e)}"]
        state["current_agent"] = "writer"
        state["workflow_step"] = "error"
        return state

@tool
def analyze_content_quality(content: str, age_group: str) -> str:
    """Analyze content quality including readability, engagement, and age-appropriateness."""
    try:
        # Basic quality metrics
        word_count = len(content.split())
        sentences = content.split('.')
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Age appropriateness check
        age_numeric = int(age_group.split('-')[0]) if '-' in age_group else 8
        complexity_score = "simple" if avg_sentence_length < 12 else "moderate" if avg_sentence_length < 18 else "complex"
        
        # Content analysis
        analysis = {
            "readability": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "complexity": complexity_score
            },
            "age_appropriateness": {
                "target_age": age_group,
                "suitable": complexity_score in ["simple", "moderate"] if age_numeric < 12 else True,
                "reading_level": "appropriate" if complexity_score != "complex" or age_numeric >= 12 else "too advanced"
            },
            "engagement_factors": {
                "has_dialogue": '"' in content or "'" in content,
                "has_action": any(word in content.lower() for word in ["ran", "jumped", "flew", "raced", "discovered"]),
                "descriptive": len([w for w in content.split() if len(w) > 6]) / max(word_count, 1) > 0.15
            }
        }
        
        return f"Content quality analysis: {json.dumps(analysis, indent=2)}"
    except Exception as e:
        return f"Error analyzing content quality: {str(e)}"

def critique_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    React agent for story critique with quality analysis tools.
    Reviews and provides feedback on story quality.
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔍 DEBUG: State keys at start of critique_node: {list(state.keys())}")
        
        # Extract input data
        content = state.get("content", "")
        plan = state.get("plan", {})
        age_group = state.get("target_audience", "6-12")
        
        # Debug logging to check if story_image_prompts are preserved
        story_image_prompts = state.get("story_image_prompts", [])
        logger.info(f"🔍 DEBUG: critique_node received story_image_prompts: {len(story_image_prompts)} prompts")
        if story_image_prompts:
            logger.info(f"   📝 First prompt: {story_image_prompts[0][:100]}...")
        
        if not content:
            raise ValueError("No story content available for critique")
        
        # Create React agent for critique with analysis tools
        critique_tools = [analyze_content_quality]
        
        # COMMENTED OUT: Inline prompt (redundant, use config only)
        # inline_prompt = f"""You are a story critique specialist. Your task is to review content quality and provide constructive feedback.
        # 
        # Available tools:
        # - analyze_content_quality: Analyze readability, engagement, and age-appropriateness
        # 
        # Your analysis should provide:
        # - Overall quality score (1-10)
        # - Specific strengths of the content
        # - Areas for improvement
        # - Assessment of age-appropriateness for target audience: {age_group}
        # 
        # Be constructive and specific in your feedback."""

        try:
            # Create React agent using ONLY config-based prompt loading
            agent = create_react_agent_for_task(
                agent_name="critique",
                tools=critique_tools
            )
            
            # Prepare context for the agent
            context = f"""
Content to critique: {content}

Plan context: {json.dumps(plan, indent=2) if plan else 'N/A'}

Target audience: {age_group}

Please analyze this content's quality, readability, and appropriateness for the target audience. Provide specific, actionable feedback.
"""
            
            # Execute React agent with correct format
            config = {"configurable": {"thread_id": f"critique_{int(time.time())}"}}
            
            response = agent.invoke(
                {"messages": [{"role": "user", "content": context}]},
                config=config
            )
            
            # Extract response from React agent
            if isinstance(response, dict) and "messages" in response:
                critique_text = response["messages"][-1].content
            else:
                critique_text = str(response)
            
        except Exception as agent_error:
            logger.warning(f"React agent failed: {agent_error}, falling back to direct LLM")
            
            # Fallback to direct LLM call
            llm = get_llm()
            system_prompt = load_prompt_from_config("critique", "system_prompt")
            user_prompt_template = load_prompt_from_config("critique", "user_prompt")
            
            # Format the user prompt with actual values
            user_prompt = user_prompt_template.format(
                content=content,
                plan=json.dumps(plan, indent=2),
                age_group=age_group
            )
    
            # Call LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = llm.invoke(messages)
            critique_text = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure critique_text is a string
        if isinstance(critique_text, list):
            critique_text = str(critique_text)
        elif not isinstance(critique_text, str):
            critique_text = str(critique_text)
        
        # Parse critique response
        try:
            if critique_text.strip().startswith('{'):
                critique_data = json.loads(critique_text)
            else:
                # Extract JSON if wrapped
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', critique_text, re.DOTALL)
                if json_match:
                    critique_data = json.loads(json_match.group(1))
                else:
                    # Fallback structure
                    critique_data = {
                        "score": 8.0,
                        "strengths": ["Engaging story", "Age appropriate"],
                        "improvements": ["Could add more details"],
                        "overall_assessment": critique_text
                    }
        except json.JSONDecodeError:
            critique_data = {
                "score": 7.5,
                "overall_assessment": critique_text
            }
        
        execution_time = time.time() - start_time
        
        # Log interaction with proper variable handling
        log_system_prompt = locals().get('system_prompt', 'critique_agent')
        log_user_prompt = locals().get('user_prompt', locals().get('context', 'critique_request'))
        log_llm_interaction("critique", log_system_prompt, log_user_prompt, critique_text, execution_time)
        
        # Update state (preserve important data from previous steps)
        state["quality_score"] = critique_data.get("score", 7.5)
        state["critique_feedback"] = critique_data
        state["current_agent"] = "critique"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "critique_complete"  # Don't mark as completed yet - let image generator run
        
        # Debug logging to ensure story_image_prompts are still in state
        story_image_prompts = state["story_image_prompts"] if "story_image_prompts" in state else []
        logger.info(f"🔍 DEBUG: critique_node preserving story_image_prompts: {len(story_image_prompts)} prompts")
        logger.info(f"🔍 DEBUG: critique_node - final state keys: {list(state.keys())}")
        
        # Debug: Print state keys at end of critique_node before return
        # print(f"🔍 DEBUG: State keys at end of critique_node: {list(state.keys())}")
        logger.info(f"🔍 DEBUG: State keys at end of critique_node: {list(state.keys())}")
        
        # Note: Output saving will be handled by the final node in the workflow
        logger.info(f"🎭 critique_node completed - output saving deferred to final workflow step")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in critique_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Critique error: {str(e)}"]
        state["current_agent"] = "critique"
        state["workflow_step"] = "error"
        return state

@tool
def generate_rhyme_scheme(poem_type: str, target_age: int) -> str:
    """Generate appropriate rhyme scheme based on poem type and target age."""
    try:
        age_schemes = {
            "nursery_rhyme": ["AABA", "ABAB", "AABB"] if target_age < 8 else ["ABAB", "ABCB"],
            "story_poem": ["ABAB", "ABCB"] if target_age < 10 else ["ABAB", "ABCB", "ABABCC"],
            "nature_poem": ["AABB", "ABAB"] if target_age < 10 else ["ABAB", "ABCB", "ABABCDCD"],
            "adventure_poem": ["AABB", "ABAB", "ABCB"]
        }
        
        schemes = age_schemes.get(poem_type, ["ABAB", "AABB"])
        recommended = schemes[0]
        
        result = {
            "poem_type": poem_type,
            "target_age": target_age,
            "recommended_scheme": recommended,
            "alternative_schemes": schemes[1:],
            "explanation": f"For {poem_type} targeting age {target_age}, {recommended} provides good rhythm and memorability"
        }
        
        return f"Rhyme scheme recommendation: {json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error generating rhyme scheme: {str(e)}"

@tool
def create_musical_rhythm(poem_content: str, style: str) -> str:
    """Create musical rhythm suggestions for poem content."""
    try:
        # Analyze poem structure
        lines = [line.strip() for line in poem_content.split('\n') if line.strip()]
        syllable_counts = []
        
        for line in lines:
            # Simple syllable counting (approximate)
            syllables = sum(1 for char in line if char.lower() in 'aeiou')
            syllable_counts.append(syllables)
        
        avg_syllables = sum(syllable_counts) / max(len(syllable_counts), 1)
        
        # Musical style suggestions
        rhythm_suggestions = {
            "children's_song": {
                "tempo": "moderate (120-140 BPM)",
                "rhythm_pattern": "4/4 time with simple beats",
                "instruments": ["piano", "acoustic guitar", "xylophone"]
            },
            "lullaby": {
                "tempo": "slow (60-80 BPM)", 
                "rhythm_pattern": "3/4 or 6/8 time, gentle sway",
                "instruments": ["acoustic guitar", "soft piano", "harp"]
            },
            "adventure_song": {
                "tempo": "upbeat (140-160 BPM)",
                "rhythm_pattern": "4/4 time with strong beat",
                "instruments": ["drums", "electric guitar", "trumpet"]
            }
        }
        
        suggestion = rhythm_suggestions.get(style, rhythm_suggestions["children's_song"])
        suggestion.update({
            "syllable_analysis": {
                "average_syllables_per_line": round(avg_syllables, 1),
                "total_lines": len(lines),
                "rhythm_consistency": "good" if max(syllable_counts) - min(syllable_counts) <= 3 else "needs_adjustment"
            }
        })
        
        return f"Musical rhythm suggestions: {json.dumps(suggestion, indent=2)}"
    except Exception as e:
        return f"Error creating rhythm suggestions: {str(e)}"

def poetry_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    React agent for poetry creation with specialized poetry tools.
    Creates poems based on user input and themes.
    """
    start_time = time.time()
    
    try:
        # Extract input data
        user_input = state.get("user_input", "")
        age_group = state.get("target_audience", "6-12")
        
        if not user_input:
            raise ValueError("No user input available for poetry creation")
        
        # Create React agent for poetry with specialized tools
        poetry_tools = [generate_rhyme_scheme, create_musical_rhythm]
        
        # COMMENTED OUT: Inline prompt (redundant, use config only)
        # age_numeric = int(age_group.split('-')[0]) if '-' in age_group else 8
        # inline_prompt = f"""You are a poetry creation specialist for children. Your task is to create engaging, age-appropriate poems.
        # 
        # Available tools:
        # - generate_rhyme_scheme: Get appropriate rhyme schemes for different poem types
        # - create_musical_rhythm: Generate musical rhythm suggestions for poems
        # 
        # Your poems should:
        # - Be suitable for age group: {age_group}
        # - Include clear rhythm and rhyme
        # - Be engaging and educational
        # - Use vocabulary appropriate for the target age
        # - Have a positive, uplifting tone
        # 
        # Create a complete poem based on the user's request."""

        try:
            # Create React agent using ONLY config-based prompt loading
            agent = create_react_agent_for_task(
                agent_name="poetry_agent",
                tools=poetry_tools
            )
            
            # Prepare context for the agent
            context = f"""
User request: {user_input}
Target audience: {age_group}

Please create a beautiful, age-appropriate poem based on this request. Consider using your tools to determine the best rhyme scheme and musical rhythm for the content.
"""
            
            # Execute React agent with correct format
            config = {"configurable": {"thread_id": f"poetry_{int(time.time())}"}}
            
            response = agent.invoke(
                {"messages": [{"role": "user", "content": context}]},
                config=config
            )
            
            # Extract response from React agent
            if isinstance(response, dict) and "messages" in response:
                poetry_content = response["messages"][-1].content
            else:
                poetry_content = str(response)
            
        except Exception as agent_error:
            logger.warning(f"React agent failed: {agent_error}, falling back to direct LLM")
            
            # Fallback to direct LLM call
            llm = get_llm()
            system_prompt = load_prompt_from_config("poetry_agent", "system_prompt")
            user_prompt_template = load_prompt_from_config("poetry_agent", "user_prompt")
            
            # Format the user prompt with actual values
            user_prompt = user_prompt_template.format(
                user_input=user_input,
                age_group=age_group
            )
    
            # Call LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = llm.invoke(messages)
            poetry_content = response.content if hasattr(response, 'content') else str(response)
        
            response = llm.invoke(messages)
            poetry_content = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure poetry_content is a string
        if isinstance(poetry_content, list):
            poetry_content = str(poetry_content)
        elif not isinstance(poetry_content, str):
            poetry_content = str(poetry_content)
        
        execution_time = time.time() - start_time
        
        # Log interaction with proper variable handling
        log_system_prompt = locals().get('system_prompt', 'poetry_agent')
        log_user_prompt = locals().get('user_prompt', locals().get('context', 'poetry_request'))
        log_llm_interaction("poetry_agent", log_system_prompt, log_user_prompt, poetry_content, execution_time)
        
        # Update state
        state["poetry_content"] = poetry_content
        state["current_agent"] = "poetry_agent"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "poetry_complete"
        
        return state
        
    except Exception as e:
        logger.error(f"Error in poetry_agent_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Poetry error: {str(e)}"]
        state["current_agent"] = "poetry_agent"
        state["workflow_step"] = "error"
        return state

@tool
def compose_melody_structure(lyrics: str, style: str) -> str:
    """Compose melody structure suggestions based on lyrics and musical style."""
    try:
        # Analyze lyrics structure
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        verses = []
        current_verse = []
        
        for line in lines:
            if line:
                current_verse.append(line)
            else:
                if current_verse:
                    verses.append(current_verse)
                    current_verse = []
        
        if current_verse:
            verses.append(current_verse)
        
        # Generate melody structure based on style
        melody_structures = {
            "children's_song": {
                "verse_pattern": "AABA",
                "chorus_pattern": "simple repetitive melody",
                "key_signature": "C major or G major (easy to sing)",
                "range": "one octave, comfortable for children"
            },
            "lullaby": {
                "verse_pattern": "ABAC",
                "chorus_pattern": "gentle descending melody",
                "key_signature": "F major or D minor (soothing)",
                "range": "limited range, soft dynamics"
            },
            "adventure_song": {
                "verse_pattern": "ABAB",
                "chorus_pattern": "strong, memorable hook",
                "key_signature": "E major or A major (bright)",
                "range": "wider range, energetic"
            }
        }
        
        structure = melody_structures.get(style, melody_structures["children's_song"])
        # Fix the dictionary update type issue
        lyrics_analysis = {
            "total_verses": len(verses),
            "lines_per_verse": [len(verse) for verse in verses],
            "suggested_song_structure": "Intro - Verse - Chorus - Verse - Chorus - Bridge - Chorus - Outro"
        }
        
        musical_elements = {
            "tempo_marking": "Andante (walking pace)" if style == "lullaby" else "Moderato (moderate)",
            "dynamics": "soft (p-mp)" if style == "lullaby" else "moderate (mf)",
            "instrumentation": "piano, guitar" if style == "lullaby" else "full ensemble"
        }
        
        # Create result structure to avoid type conflicts
        result_structure = {
            "verse_pattern": structure["verse_pattern"],
            "chorus_pattern": structure["chorus_pattern"], 
            "key_signature": structure["key_signature"],
            "range": structure["range"],
            "lyrics_analysis": {
                "total_verses": len(verses),
                "lines_per_verse": [len(verse) for verse in verses],
                "suggested_song_structure": "Intro - Verse - Chorus - Verse - Chorus - Bridge - Chorus - Outro"
            },
            "musical_elements": {
                "tempo_marking": "Andante (walking pace)" if style == "lullaby" else "Moderato (moderate)",
                "dynamics": "soft (p-mp)" if style == "lullaby" else "moderate (mf)",
                "instrumentation": "piano, guitar" if style == "lullaby" else "full ensemble"
            }
        }
        
        return f"Melody structure: {json.dumps(result_structure, indent=2)}"
    except Exception as e:
        return f"Error composing melody structure: {str(e)}"

def music_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    React agent for music creation with musical composition tools.
    Creates song lyrics and musical descriptions.
    """
    start_time = time.time()
    
    try:
        # Extract input data
        user_input = state.get("user_input", "")
        poetry_content = state.get("poetry_content", "")
        age_group = state.get("target_audience", "6-12")
        
        if not user_input:
            raise ValueError("No user input available for music creation")
        
        # Create React agent for music with composition tools
        music_tools = [compose_melody_structure, create_musical_rhythm]
        
        # COMMENTED OUT: Inline prompt (redundant, use config only)
        # inline_prompt = f"""You are a music composition specialist for children. Your task is to create engaging song lyrics and musical arrangements.
        # 
        # Available tools:
        # - compose_melody_structure: Generate melody structure suggestions based on lyrics and style
        # - create_musical_rhythm: Create musical rhythm suggestions for content
        # 
        # Your musical content should:
        # - Be suitable for age group: {age_group}
        # - Include clear rhythm and melody suggestions
        # - Be singable and memorable
        # - Use vocabulary appropriate for the target age
        # - Have a positive, uplifting tone
        # - Complement any existing poetry content
        # 
        # Create song lyrics and musical arrangement suggestions based on the user's request."""

        try:
            # Create React agent using ONLY config-based prompt loading
            agent = create_react_agent_for_task(
                agent_name="music_agent",
                tools=music_tools
            )
            
            # Prepare context for the agent
            context = f"""
User request: {user_input}
Target audience: {age_group}
Related poetry content: {poetry_content if poetry_content else 'None provided'}

Please create song lyrics and musical arrangement suggestions based on this request. Consider the existing poetry content if provided, and use your tools to create appropriate melody structure and rhythm.
"""
            
            # Execute React agent with correct format
            config = {"configurable": {"thread_id": f"music_{int(time.time())}"}}
            
            response = agent.invoke(
                {"messages": [{"role": "user", "content": context}]},
                config=config
            )
            
            # Extract response from React agent
            if isinstance(response, dict) and "messages" in response:
                music_content = response["messages"][-1].content
            else:
                music_content = str(response)
            
        except Exception as agent_error:
            logger.warning(f"React agent failed: {agent_error}, falling back to direct LLM")
            
            # Fallback to direct LLM call
            llm = get_llm()
            system_prompt = load_prompt_from_config("music_agent", "system_prompt")
            user_prompt_template = load_prompt_from_config("music_agent", "user_prompt")
            
            # Format the user prompt with actual values
            user_prompt = user_prompt_template.format(
                user_input=user_input,
                poetry_content=poetry_content,
                age_group=age_group
            )
    
            # Call LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = llm.invoke(messages)
            music_content = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure music_content is a string
        if isinstance(music_content, list):
            music_content = str(music_content)
        elif not isinstance(music_content, str):
            music_content = str(music_content)
        
        execution_time = time.time() - start_time
        
        # Log interaction with proper variable handling
        log_system_prompt = locals().get('system_prompt', 'music_agent')
        log_user_prompt = locals().get('user_prompt', locals().get('context', 'music_request'))
        log_llm_interaction("music_agent", log_system_prompt, log_user_prompt, music_content, execution_time)
        
        # Update state
        state["music_content"] = music_content
        state["current_agent"] = "music_agent"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "completed"  # End workflow here
        
        # Save complete run output - music_agent is often the final node
        try:
            run_dir = simple_save_output(state)
            if run_dir:
                state["output_directory"] = run_dir
                logger.info(f"📁 Complete workflow output saved to: {run_dir}")
        except Exception as e:
            logger.error(f"Error saving run output: {e}")
            state["errors"] = state.get("errors", []) + [f"Output saving error: {str(e)}"]
        
        return state
        
    except Exception as e:
        logger.error(f"Error in music_agent_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Music error: {str(e)}"]
        state["current_agent"] = "music_agent"
        state["workflow_step"] = "error"
        return state

def image_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Image generation agent with actual image generation capabilities.
    Uses configurable settings from use case YAML and story-specific prompts when available.
    """
    start_time = time.time()
    
    print(f"🔍 [DEBUG] image_generator_node called - image_style in state: {state.get('image_style', 'NOT FOUND')}")
    
    try:
        # Debug: Print state keys before image generator starts
        # print(f"🔍 DEBUG: State keys at start of image_generator_node: {list(state.keys())}")
        logger.info(f"🔍 DEBUG: State keys at start of image_generator_node: {list(state.keys())}")
        
        # Extract input data
        user_input = state.get("user_input", "")
        content = state.get("content", "")
        poetry_content = state.get("poetry_content", "")
        music_content = state.get("music_content", "")
        plan = state.get("plan", {})
        use_case = state.get("use_case", "story_generator")
        
        # Direct access to story_image_prompts (consistent with formatter print statement)
        story_image_prompts = state["story_image_prompts"] if "story_image_prompts" in state else []
        formatted_story = state.get("formatted_story", {})
        formatted_content = state.get("formatted_content", {})
        
        # Debug logging
        logger.info(f"🔍 DEBUG: 'story_image_prompts' in state: {'story_image_prompts' in state}")
        logger.info(f"🔍 DEBUG: state keys: {list(state.keys())}")
        logger.info(f"🔍 Image generator received story_image_prompts: {len(story_image_prompts)} prompts")
        if story_image_prompts:
            for i, prompt in enumerate(story_image_prompts):
                logger.info(f"   📝 Prompt {i+1}: {prompt[:100]}...")
        else:
            # For poetry/music workflows, this is expected
            if poetry_content or music_content:
                logger.info("ℹ️ Poetry/Music workflow - no story_image_prompts expected, will generate basic prompts")
            else:
                logger.warning("⚠️ No story_image_prompts found in state")
            
            # COMMENTED OUT: Fallback reconstruction - Use ONLY story_image_prompts from content generator/formatter
            # # Try to extract prompts from formatted_story if available
            # if formatted_story and "chapters" in formatted_story:
            #     logger.info("🔧 Attempting to create basic prompts from formatted story chapters")
            #     # Get basic aesthetic from config, but allow override from image_style parameter
            #     try:
            #         from ..composer.config_loader import ConfigLoader
            #         config_loader = ConfigLoader()
            #         use_case_config = config_loader.get_use_case_config(use_case)
            #         
            #         # Check if image_style is provided in state and override aesthetic
            #         if "image_style" in state and state["image_style"]:
            #             aesthetic = get_aesthetic_from_image_style(state["image_style"])
            #             logger.info(f"🎨 Using custom image style: {state['image_style']} -> {aesthetic}")
            #         else:
            #             aesthetic = use_case_config.get("settings", {}).get("image_generation", {}).get("aesthetic", "ghibli")
            #         
            #         # Get aspect ratio and composition guide
            #         aspect_ratio = use_case_config.get("settings", {}).get("image_generation", {}).get("aspect_ratio", "16:9")
            #         composition_guide = use_case_config.get("settings", {}).get("image_generation", {}).get("composition_guide", "centered subject with adequate margins")
            #     except Exception:
            #         aesthetic = "ghibli"
            #         aspect_ratio = "16:9"
            #         composition_guide = "centered subject with adequate margins"
            #     
            # COMMENTED OUT: All fallback reconstruction sections - Use ONLY story_image_prompts from content generator/formatter
            #     # Create basic prompts from chapter scene descriptions
            #     story_image_prompts = []
            #     for i, chapter in enumerate(formatted_story["chapters"]):
            #         if isinstance(chapter, dict):
            #             scene_desc = chapter.get("scene_description", f"Scene from {user_input}")
            #         else:
            #             scene_desc = str(chapter)
            #         prompt = f"A {aesthetic} illustration showing {scene_desc}. Create with {aspect_ratio} aspect ratio, {composition_guide}."
            #         story_image_prompts.append(prompt)
            #         logger.info(f"🔧 Created prompt {i+1}: {prompt}")
            #     
            #     # Update state with the created prompts
            #     state["story_image_prompts"] = story_image_prompts
            #     logger.info(f"🔧 Updated state with {len(story_image_prompts)} reconstructed prompts")
            # 
            # # Try to extract prompts from formatted_content (poetry/music) if available
            # elif formatted_content and "sections" in formatted_content:
            # COMMENTED OUT: Complete fallback sections - Use ONLY story_image_prompts from content generator/formatter
            #     logger.info("🔧 Attempting to create prompts from formatted content sections")
            #     [entire formatted_content reconstruction section removed]
            # 
            # # For poetry/music content without formatted structure, create enhanced prompts
            # elif poetry_content or music_content:
            #     logger.info("🔧 Creating enhanced prompts for poetry/music content")
            #     [entire poetry/music fallback section removed]
            
            # If no story_image_prompts are available after content generation, log and skip image generation
            if not story_image_prompts:
                logger.warning("⚠️ No story_image_prompts available - ensure content_generator_node creates proper image prompts")
                return {"image_urls": [], "enhanced_content": formatted_content}
        
        logger.info(f"📸 Using story_image_prompts from state: {len(story_image_prompts)} prompts available")
        
        # Get use case configuration for image generation
        try:
            from ..composer.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            use_case_config = config_loader.get_use_case_config(use_case)
        except Exception as e:
            logger.warning(f"Could not load use case config: {e}")
            use_case_config = {"settings": {"image_generation": {"enabled": True, "count": 3}}}
        
        # Create image generator with configuration
        from .image_generator import ConfigurableImageGenerator
        generator = ConfigurableImageGenerator(use_case_config, unique_prefix=datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # Override aesthetic if image_style is provided
        if "image_style" in state and state["image_style"]:
            custom_aesthetic = get_aesthetic_from_image_style(state["image_style"])
            generator.aesthetic = custom_aesthetic
            logger.info(f"🎨 Image generator using custom style: {state['image_style']} -> {custom_aesthetic}")
        
        # Generate images based on story-specific prompts if available
        generated_files = []
        image_descriptions = []
        used_prompts = []  # Track the actual prompts used for each image
        
        if story_image_prompts:
            # Use the formatter generated prompts
            logger.info(f"Using {len(story_image_prompts)} story-specific image prompts")
            # tracemalloc.start()
            for i, prompt in enumerate(story_image_prompts):
                # Create a short, descriptive title for the filename
                scene_title = f"scene_{i + 1}"
                if formatted_story and "chapters" in formatted_story and i < len(formatted_story["chapters"]):
                    chapter_title = formatted_story["chapters"][i].get("title", f"Chapter {i + 1}")
                    # Create short title from chapter title (max 20 chars)
                    scene_title = chapter_title.lower().replace(' ', '_')[:20]
                image_path = generator.generate_single_image(prompt, i, scene_title)
                if image_path:
                    generated_files.append(image_path)
                    # Use scene description for display, not filename
                    scene_desc = f"Scene {i + 1}"
                    if formatted_story and "chapters" in formatted_story and i < len(formatted_story["chapters"]):
                        scene_desc = formatted_story["chapters"][i].get("scene_description", scene_desc)
                    image_descriptions.append(f"Image {i + 1}: {scene_desc} - {prompt[:100]}...")
                    used_prompts.append(prompt)  # Store the actual prompt used
                gc.collect()  # Force garbage collection after each image
                # Print top 5 memory allocations after each image
                # snapshot = tracemalloc.take_snapshot()
            #     top_stats = snapshot.statistics('lineno')
            #     print(f"\n[tracemalloc] Top 5 allocations after image {i+1}:")
            #     for stat in top_stats[:5]:
            #         print(stat)
            # tracemalloc.stop()
                
        # COMMENTED OUT: Fallback image generation - Use ONLY formatted prompts from content generator
        # elif content and plan:
        #     # Fallback: Use story content and plan for basic image generation
        #     logger.info("No story-specific prompts available, generating basic images")
        #     generated_files = generator.generate_story_images(content, user_input, plan)
        #     
        #     # Create basic descriptions and prompts
        #     for i, filepath in enumerate(generated_files):
        #         description = f"Image {i + 1}: Illustration showing a scene from the story about {user_input}"
        #         basic_prompt = f"An illustration for a children's story about {user_input}, {generator.aesthetic} style. Create with {generator.aspect_ratio} aspect ratio, {generator.composition_guide}."
        #         image_descriptions.append(description)
        #         used_prompts.append(basic_prompt)
        # else:
        #     # Last resort: Generate basic images based on user input
        #     logger.info("No story content available, generating basic images")
        #     image_count = generator.count
        #     
        #     for i in range(image_count):
        #         basic_prompt = f"An illustration for a children's story about {user_input}, {generator.aesthetic} style. Create with {generator.aspect_ratio} aspect ratio, {generator.composition_guide}."
        #         image_path = generator.generate_single_image(basic_prompt, i, f"Scene {i + 1}")
        #         if image_path:
        #             generated_files.append(image_path)
        #             image_descriptions.append(f"Image {i + 1}: Basic illustration for {user_input}")
        #             used_prompts.append(basic_prompt)
        else:
            # If no story_image_prompts available, log warning but don't generate fallback images
            logger.warning("⚠️ No story_image_prompts available - skipping image generation")
            logger.warning("🔧 Ensure content_generator_node or formatter_node creates story_image_prompts")
        
        execution_time = time.time() - start_time
        
        # Create summary description text
        descriptions_text = "\n".join([f"{i+1}. {desc}" for i, desc in enumerate(image_descriptions)])
        
        # Log interaction
        log_llm_interaction("image_generator", "Image generation system", f"Generate {len(generated_files)} images for: {user_input}", descriptions_text, execution_time)
        
        # Update state
        state["image_descriptions"] = descriptions_text
        state["image_urls"] = generated_files  # Now contains actual file paths
        state["used_image_prompts"] = used_prompts  # Store the actual prompts used
        state["image_metadata"] = {
            "status": "generated" if generated_files else "failed",
            "count": len(generated_files),
            "output_folder": str(generator.full_output_path),
            "style": generator.style,
            "aesthetic": generator.aesthetic,
            "used_story_prompts": bool(story_image_prompts),
            "prompts_used": len(used_prompts)
        }
        state["current_agent"] = "image_generator"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "completed"  # Mark workflow as completed after images are generated
        
        # Log success
        if generated_files:
            logger.info(f"✅ Generated {len(generated_files)} images in {generator.full_output_path}")
            if story_image_prompts:
                logger.info("✨ Used formatter generated prompts for better context")
            for i, filepath in enumerate(generated_files):
                logger.info(f"   📄 Image {i+1}: {filepath}")
            
            # Print image names and prompts for user visibility
            # print("\n" + "="*60)
            # print("GENERATED IMAGES AND PROMPTS:")
            # print("="*60)
            for i, filepath in enumerate(generated_files):
                image_name = filepath.split('/')[-1] if '/' in filepath else filepath
                prompt = used_prompts[i] if i < len(used_prompts) else "No specific prompt available"
            #     print(f"image_name_saved: {image_name}: {prompt}")
            # print("="*60 + "\n")
        else:
            logger.warning("⚠️ No images were generated successfully")
        
        # Save complete run output at the end of the workflow - image_generator is the final node
        try:
            run_dir = simple_save_output(state)
            if run_dir:
                state["output_directory"] = run_dir
                logger.info(f"📁 Complete workflow output saved to: {run_dir} (FINAL NODE)")
        except Exception as e:
            logger.error(f"Error saving run output: {e}")
            state["errors"] = state.get("errors", []) + [f"Output saving error: {str(e)}"]
        
        return state
        
    except Exception as e:
        logger.error(f"Error in image_generator_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Image generation error: {str(e)}"]
        state["current_agent"] = "image_generator"
        state["workflow_step"] = "error"
        return state

# @profile
def formatter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    React agent for content formatting with tool capabilities.
    Formats various types of content (stories, poetry, songs) for mobile/web display 
    and creates targeted image prompts.
    """
    start_time = time.time()
    
    print(f"🔍 [DEBUG] formatter_node called - image_style in state: {state.get('image_style', 'NOT FOUND')}")
    
    try:
        # Extract input data
        content = state.get("content", "")
        plan = state.get("plan", {})
        user_input = state.get("user_input", "")
        age_group = state.get("target_audience", "6-12")
        use_case = state.get("use_case", "story_generator")
        
        # Determine content type based on use case or available data
        poetry_content = state.get("poetry_content", "")
        music_content = state.get("music_content", "")
        
        if poetry_content or music_content:
            content_type = "poetry and music"
            main_content = f"**Poetry Content:**\n{poetry_content}\n\n**Music Content:**\n{music_content}"
        else:
            content_type = "story"
            main_content = content
        
        if not main_content:
            raise ValueError(f"No {content_type} content available for formatting")
        
        # Get use case configuration for image generation settings
        config_data = {}
        try:
            from ..composer.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            use_case_config = config_loader.get_use_case_config(use_case)
            image_settings = use_case_config.get("settings", {}).get("image_generation", {})
            image_count = image_settings.get("count", 3)
            
            # Get story length constraints if available
            word_count = state.get("word_count", 400)
            words_per_page = state.get("words_per_page", 135)
            
            # Check if image_style is provided in state and override aesthetic
            if "image_style" in state and state["image_style"]:
                print(f"🎨 [DEBUG] formatter_node - Found image_style in state: '{state['image_style']}'")
                aesthetic = get_aesthetic_from_image_style(state["image_style"])
                print(f"🎨 [DEBUG] formatter_node - Converted to aesthetic: '{aesthetic}'")
                logger.info(f"🎨 Formatter using custom image style: {state['image_style']} -> {aesthetic}")
            else:
                print("🎨 [DEBUG] formatter_node - No image_style in state, using default ghibli")
                aesthetic = get_aesthetic_from_image_style("ghibli")  # Use default ghibli style with full description
                
            # Get aspect ratio and composition guide
            aspect_ratio = image_settings.get("aspect_ratio", "16:9")
            composition_guide = image_settings.get("composition_guide", "centered subject with adequate margins")
            
            config_data = {
                "image_count": image_count,
                "aesthetic": aesthetic,
                "word_count": word_count,
                "words_per_page": words_per_page,
                "aspect_ratio": aspect_ratio,
                "composition_guide": composition_guide
            }
        except Exception as e:
            logger.warning(f"Could not load use case config: {e}")
            config_data = {
                "image_count": 3,
                "aesthetic": get_aesthetic_from_image_style("ghibli"),  # Use default ghibli style with full description
                "word_count": 400,
                "words_per_page": 135,
                "aspect_ratio": "16:9",
                "composition_guide": "centered subject with adequate margins"
            }
        
        # Create React agent for formatting with specific tools
        # Use personalized image prompts if personalization data is available
        has_personalization = any(key in state for key in ["child_name", "child_age", "child_gender", "interests"])
        if has_personalization:
            logger.info("🎭 Using personalized image prompt generator")
            formatter_tools = [format_content_structure, generate_personalized_image_prompts, validate_content_format]
        else:
            logger.info("🎨 Using standard image prompt generator")
            formatter_tools = [format_content_structure, generate_image_prompts, validate_content_format]
        
        # COMMENTED OUT: Inline prompt (redundant, use config only)
        # inline_prompt = f"""You are a content formatting specialist. Your task is to format {content_type} content for mobile/web display and create targeted image prompts.
        # 
        # Available tools:
        # - format_content_structure: Format content into structured sections
        # - generate_image_prompts: Create specific image prompts based on content scenes  
        # - validate_content_format: Validate formatted content structure
        # 
        # Your output should be a properly structured JSON containing:
        # - formatted_content (for poetry/music) or formatted_story (for stories)
        # - image_prompts array with {config_data['image_count']} prompts using aesthetic: {config_data['aesthetic']}
        # 
        # Consider the target audience: {age_group}. Make content engaging and age-appropriate."""

        try:
            # Create React agent using ONLY config-based prompt loading with variable substitution
            agent = create_react_agent_for_task(
                agent_name="formatter",
                tools=formatter_tools,
                format_vars=config_data  # Pass all config data for prompt variable substitution
            )
            
            # Prepare context for the agent
            personalization_context = ""
            if has_personalization:
                personalization_data = {
                    "child_name": state.get("child_name", "the child"),
                    "child_age": state.get("child_age", 5),
                    "child_gender": state.get("child_gender", "neutral"),
                    "interests": state.get("interests", []),
                    "location": state.get("location", ""),
                    "companions": state.get("companions", []),
                    "reading_level": state.get("reading_level", "medium")
                }
                personalization_context = f"""
Personalization Data: {json.dumps(personalization_data, indent=2)}
Use generate_personalized_image_prompts with this personalization data to create highly detailed, character-specific image prompts.
"""
                
            context = f"""
Content Type: {content_type}
Content: {main_content}
Plan: {json.dumps(plan, indent=2) if plan else 'N/A'}
User Input: {user_input}
Age Group: {age_group}
Image Count: {config_data['image_count']}
Aesthetic: {config_data['aesthetic']}
Word Count Target: {config_data['word_count']}
Words per Page: {config_data['words_per_page']}
Aspect Ratio: {config_data['aspect_ratio']}
Composition Guide: {config_data['composition_guide']}{personalization_context}

Please format this content into a structured format suitable for mobile display and create {config_data['image_count']} targeted image prompts.
{f"IMPORTANT: Use generate_personalized_image_prompts for personalized content with detailed character descriptions." if has_personalization else "Use generate_image_prompts for standard content."}
"""
            
            # Execute React agent with correct format
            config = {"configurable": {"thread_id": f"formatter_{int(time.time())}"}}
            
            response = agent.invoke(
                {"messages": [{"role": "user", "content": context}]},
                config=config
            )
            
            # Extract response from React agent
            if isinstance(response, dict) and "messages" in response:
                formatted_response = response["messages"][-1].content
            else:
                formatted_response = str(response)
            
        except Exception as agent_error:
            logger.warning(f"React agent failed: {agent_error}, falling back to direct LLM")
            
            # Fallback to direct LLM call
            llm = get_llm()
            system_prompt = load_prompt_from_config("formatter", "system_prompt", config_data)
            user_prompt_template = load_prompt_from_config("formatter", "user_prompt", config_data)
            
            # Set up JSON output parser
            parser = JsonOutputParser(pydantic_object=FormatterOutput)
            format_instructions = parser.get_format_instructions()
            
            # Format the user prompt with actual values and parser instructions
            user_prompt = user_prompt_template.format(
                content_type=content_type,
                content=main_content,
                plan=json.dumps(plan, indent=2) if plan else "N/A",
                user_input=user_input,
                age_group=age_group,
                image_count=config_data["image_count"],
                aesthetic=config_data["aesthetic"],
                format_instructions=format_instructions,
                word_count=config_data["word_count"],
                words_per_page=config_data["words_per_page"],
                aspect_ratio=config_data["aspect_ratio"],
                composition_guide=config_data["composition_guide"]
            )
    
            # Call LLM with structured output
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = llm.invoke(messages)
            formatted_response = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure formatted_response is always a string
        if isinstance(formatted_response, list):
            formatted_response = str(formatted_response)
        elif not isinstance(formatted_response, str):
            formatted_response = str(formatted_response)
        
        # Parse the response - try React agent response first, then JSON parsing
        formatted_data = None
        system_prompt = "formatter_agent"
        # Get context from the prepared agent context or create fallback
        user_prompt = locals().get('context', f"Format {content_type} content for {user_input}")
        
        try:
            # First try to parse as JSON directly
            if formatted_response.strip().startswith('{'):
                formatted_data = json.loads(formatted_response)
                logger.info(f"✅ Direct JSON parsing successful")
            else:
                # Extract JSON from response if wrapped in markdown
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', formatted_response, re.DOTALL)
                if json_match:
                    formatted_data = json.loads(json_match.group(1))
                    logger.info(f"✅ Markdown JSON extraction successful")
                else:
                    logger.warning(f"🚫 No JSON found in response")
                    formatted_data = None
                    
        except Exception as parse_error:
            logger.warning(f"🚫 JSON parsing failed: {parse_error}")
            logger.warning(f"🔍 Raw response length: {len(formatted_response)}")
            logger.warning(f"🔍 Response preview: {formatted_response[:200]}...")
            formatted_data = None
        
        # Final fallback structure if all parsing fails
        if not formatted_data:
            logger.warning("🚫 LLM parsing completely failed - using fallback structure with basic image generation")
            
            # Create fallback structure based on content type
            if content_type == "poetry and music":
                # For poetry/music, create a formatted_content structure
                formatted_data = {
                    "formatted_content": {
                        "title": plan.get("title", f"Poetry and Music about {user_input}"),
                        "summary": f"A collection of poetry and music about {user_input}",
                        "estimated_duration": 5,
                        "sections": [
                            {
                                "title": "The Poetry",
                                "type": "poetry",
                                "content": poetry_content if poetry_content else "Beautiful poetry content",
                                "scene_description": f"A poetic scene about {user_input}"
                            },
                            {
                                "title": "The Song",
                                "type": "music", 
                                "content": music_content if music_content else "Musical content",
                                "scene_description": f"A musical scene about {user_input}"
                            }
                        ],
                        "word_count": len(main_content.split()),
                        "themes": ["creativity", "expression"],
                        "mood": "joyful",
                        "rhyme_scheme": "ABAB",
                        "musical_style": "children's song"
                    },
                    "image_prompts": [
                        f"A {config_data['aesthetic']} illustration showing a poetic scene about {user_input}, featuring artistic and creative elements. Create with {config_data['aspect_ratio']} aspect ratio, {config_data['composition_guide']}.",
                        f"A {config_data['aesthetic']} illustration showing a musical scene about {user_input}, with instruments and joyful expression. Create with {config_data['aspect_ratio']} aspect ratio, {config_data['composition_guide']}."
                    ]
                }
            else:
                # For stories, create a formatted_story structure
                formatted_data = {
                    "formatted_story": {
                        "title": plan.get("title", f"Story about {user_input}"),
                        "summary": f"A story about {user_input}",
                        "reading_time": 3,
                        "chapters": [{"title": "Complete Story", "content": main_content, "scene_description": f"Main scene from {user_input}"}],
                        "word_count": len(main_content.split()),
                        "themes": ["adventure", "friendship"],
                        "characters": [user_input]
                    },
                    "image_prompts": [
                        f"A {config_data['aesthetic']} illustration showing a scene from a story about {user_input}. Create with {config_data['aspect_ratio']} aspect ratio, {config_data['composition_guide']}."
                    ]
                }
            
            logger.info(f"🔧 Created fallback structure for {content_type} with {len(formatted_data.get('image_prompts', []))} image prompts")
        
        execution_time = time.time() - start_time
        
        # Log interaction
        log_llm_interaction("formatter", system_prompt, user_prompt, formatted_response, execution_time)
        
        # Debug: Print state keys after LLM call
        logger.info(f"🔍 DEBUG: State keys after formatter LLM call: {list(state.keys())}")
        
        # Debug: Log the parsed data structure
        logger.info(f"🔍 DEBUG: formatted_data keys: {list(formatted_data.keys()) if formatted_data else 'None'}")
        logger.info(f"🔍 DEBUG: formatted_data content: {formatted_data}")
        
        # Update state with formatted content (handle both story and poetry/music content)
        if content_type == "story":
            state["formatted_story"] = formatted_data.get("formatted_story")
        else:
            state["formatted_content"] = formatted_data.get("formatted_content")
        
        # Ensure image_prompts is always set (fallback if parsing failed)
        image_prompts = formatted_data.get("image_prompts", [])
        if not image_prompts:
            # Fallback: create basic prompts if none were generated
            logger.warning("🔧 No image_prompts found in formatted_data, creating fallback prompts")
            image_prompts = [
                f"A {config_data['aesthetic']} illustration of a scene from a children's story about {user_input}, scene {i+1}. Create with {config_data['aspect_ratio']} aspect ratio, {config_data['composition_guide']}"
                for i in range(config_data['image_count'])
            ]
            logger.info(f"🔧 Created {len(image_prompts)} fallback image prompts")
        
        state["story_image_prompts"] = image_prompts
        
        # Debug: Print state keys after setting story_image_prompts
        # print(f"🔍 DEBUG: State keys after setting story_image_prompts: {list(state.keys())}")
        # print(f"🔍 DEBUG: story_image_prompts value: {state['story_image_prompts']}")
        logger.info(f"🔍 DEBUG: State keys after setting story_image_prompts: {list(state.keys())}")
        
        # Additional debug logging for the state update
        logger.info(f"🔍 DEBUG: formatted_data.get('image_prompts', []): {formatted_data.get('image_prompts', [])}")
        logger.info(f"🔍 DEBUG: state['story_image_prompts'] after setting: {state['story_image_prompts']}")
        logger.info(f"🔍 DEBUG: Final story_image_prompts count: {len(state['story_image_prompts'])}")
        
        state["current_agent"] = "formatter"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "formatting_complete"
        
        # Debug logging to ensure prompts are set
        logger.info(f"✅ Content formatting completed successfully")
        if content_type == "story":
            logger.info(f"📖 Formatted story title: {formatted_data.get('formatted_story', {}).get('title', 'Untitled')}")
        else:
            logger.info(f"📖 Formatted content title: {formatted_data.get('formatted_content', {}).get('title', 'Untitled')}")
        logger.info(f"🎯 Generated {len(state['story_image_prompts'])} targeted image prompts")
        logger.info(f"🔍 DEBUG: story_image_prompts being set in state: {state['story_image_prompts']}")
        if state["story_image_prompts"]:
            for i, prompt in enumerate(state["story_image_prompts"], 1):
                logger.info(f"   🎨 Image Prompt {i}: {prompt}")
        
        # Print final content and image prompts for user visibility
        if content_type == "story":
            formatted_story = formatted_data.get("formatted_story", {})
            # print("\n" + "="*80)
            # print("FINAL STORY USER WILL SEE:")
            # print("="*80)
            # print(f"Title: {formatted_story.get('title', 'Untitled Story')}")
            # print("-" * 40)
            if "chapters" in formatted_story and formatted_story["chapters"]:
                for i, chapter in enumerate(formatted_story["chapters"], 1):
                    print(f"\nChapter {i}: {chapter.get('title', f'Chapter {i}')}")
                    # print(f"Content: {chapter.get('content', '')[:200]}...")
            else:
                content_preview = formatted_story.get('content', '')[:500]
                # print(f"Story Content: {content_preview}...")
            # print("="*80)
        else:
            formatted_content = formatted_data.get("formatted_content", {})
            # print("\n" + "="*80)
            # print("FINAL CONTENT USER WILL SEE:")
            # print("="*80)
            # print(f"Title: {formatted_content.get('title', 'Untitled Content')}")
            # print("-" * 40)
            if "sections" in formatted_content and formatted_content["sections"]:
                for i, section in enumerate(formatted_content["sections"], 1):
                    print(f"\nSection {i}: {section.get('title', f'Section {i}')}")
                    # print(f"Type: {section.get('type', 'content')}")
                    # print(f"Content: {section.get('content', '')[:200]}...")
            # print("="*80)
        
        # print("\nIMAGE GENERATION PROMPTS:")
        # print("-" * 40)
        # for i, prompt in enumerate(state["story_image_prompts"], 1):
        #     print(f"Image {i} prompt: {prompt}")
        # print("="*80 + "\n")
        
        # Log the raw LLM response for debugging
        logger.debug(f"Raw LLM response: {formatted_response}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in formatter_node: {e}")
        state["errors"] = state.get("errors", []) + [f"Content formatting error: {str(e)}"]
        state["current_agent"] = "formatter"
        state["workflow_step"] = "error"
        return state

def determine_content_type(state: Dict[str, Any]) -> str:
    """
    Determine content type based on use case configuration.
    Takes content type directly from use case config rather than keyword detection.
    """
    try:
        use_case = state.get("use_case", "story_generator")
        
        # Load use case config to get content type
        try:
            from ..composer.config_loader import ConfigLoader
        except ImportError:
            # Fallback for standalone testing
            try:
                from composer.config_loader import ConfigLoader
            except ImportError:
                # Direct mapping as fallback
                use_case_to_content_type = {
                    "story_generator": "story",
                    "poetry_and_song": "poetry_and_music", 
                    "educational_content": "educational"
                }
                content_type = use_case_to_content_type.get(use_case, "story")
                logger.info(f"🎯 Using direct mapping: '{use_case}' -> '{content_type}'")
                return content_type
                
        config_loader = ConfigLoader()
        use_case_config = config_loader.get_use_case_config(use_case)
        
        # Get content type from config
        content_type = use_case_config.get("content_type", "story")
        logger.info(f"🎯 Determined content type '{content_type}' for use case '{use_case}'")
        
        return content_type
        
    except Exception as e:
        logger.warning(f"Could not determine content type from config: {e}. Using fallback mapping.")
        
        # Fallback direct mapping
        use_case = state.get("use_case", "story_generator")
        use_case_to_content_type = {
            "story_generator": "story",
            "poetry_and_song": "poetry_and_music", 
            "educational_content": "educational"
        }
        content_type = use_case_to_content_type.get(use_case, "story")
        logger.info(f"🎯 Fallback mapping: '{use_case}' -> '{content_type}'")
        return content_type

def get_content_type_prompts(content_type: str, prompt_key: str = "content_generator") -> tuple:
    """
    Get system and user prompts for the specified content type.
    Returns base prompts that adapt based on content type.
    """
    try:
        # Try different import paths for robustness
        try:
            from ..composer.config_loader import ConfigLoader
        except ImportError:
            from composer.config_loader import ConfigLoader
            
        config_loader = ConfigLoader()
        
        # Get the universal content_generator prompts
        system_prompt = config_loader.get_agent_prompt(prompt_key, "system_prompt")
        user_prompt = config_loader.get_agent_prompt(prompt_key, "user_prompt")
        
        # Enhanced logging for prompt source tracking
        logger.info(f"📋 PROMPT SOURCE: {prompt_key}.system_prompt loaded FROM YAML (prompts.yaml) for content_type: {content_type}")
        logger.info(f"📋 PROMPT SOURCE: {prompt_key}.user_prompt loaded FROM YAML (prompts.yaml) for content_type: {content_type}")
        logger.info(f"📏 SYSTEM PROMPT LENGTH: {len(system_prompt)} characters")
        logger.info(f"📏 USER PROMPT LENGTH: {len(user_prompt)} characters")
        logger.info(f"📝 SYSTEM PROMPT PREVIEW: {system_prompt[:150]}...")
        
        return system_prompt, user_prompt
        
    except Exception as e:
        logger.warning(f"Error loading prompts for content type {content_type}: {e}")
        logger.warning(f"📋 PROMPT SOURCE: {prompt_key} using FALLBACK PROMPTS (embedded in code)")
        
        # Fallback prompts with content_type parameter
        system_prompt = f"""You are an expert {content_type} content generator specializing in creating engaging, age-appropriate content for children.

Your task is to create {content_type} content that is:
1. Age-appropriate for the target audience: {{age_group}}
2. Written in the specified language: {{language_of_story}}  
3. Properly structured and formatted for digital reading
4. Enhanced with detailed image generation prompts

Content Type: {content_type}
Use Case: {{use_case}}

Always adapt your writing style, vocabulary, and themes to match the content type and target audience."""

        user_prompt = """Create {content_type} content based on the following plan and specifications:

Content Type: {content_type}
Use Case: {use_case}
Plan: {plan}
User Input: {user_input}
Target Age Group: {age_group}

{story_length_constraints}

Personalization:
- Child's Name: {child_name}
- Child's Age: {child_age} 
- Child's Gender: {child_gender}
- Interests: {interests}
- Reading Level: {reading_level}
- Companions: {companions}
- Location: {location}
- Region: {region}
- Language of Story: {language_of_story}
- Moral Lesson: {moral_lesson}
- Theme: {theme}

Generate {image_count} detailed image prompts using this aesthetic: {aesthetic}
Use aspect ratio: {aspect_ratio} and composition guide: {composition_guide}

{format_instructions}"""

        logger.info(f"📏 FALLBACK SYSTEM PROMPT LENGTH: {len(system_prompt)} characters")
        logger.info(f"📏 FALLBACK USER PROMPT LENGTH: {len(user_prompt)} characters")

        return system_prompt, user_prompt

def get_output_structure_for_content_type(content_type: str) -> str:
    """
    Determine the expected output structure based on content type.
    """
    content_type_mappings = {
        "story": "formatted_story",
        "educational": "formatted_story", 
        "poetry_and_music": "formatted_content"
    }
    
    return content_type_mappings.get(content_type, "formatted_story")

def content_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Universal content generation and formatting agent with LLM integration.
    This node adapts its behavior based on the content type determined from the use case:
    - For "story" content: Creates narrative chapters with storytelling focus
    - For "poetry_and_music" content: Creates verses and songs with rhythm focus  
    - For "educational" content: Creates learning-focused content with educational objectives
    - Formats content for mobile/web display with structured chapters/sections
    - Creates targeted image generation prompts appropriate for the content type
    """
    start_time = time.time()
    
    print(f"🔍 [DEBUG] content_generator_node called - image_style in state: {state.get('image_style', 'NOT FOUND')}")
    print(f"🔍 [DEBUG] content_generator_node - ALL STATE KEYS: {list(state.keys())}")
    print(f"🔍 [DEBUG] content_generator_node - STATE TYPE: {type(state)}")
    
    try:
        # Determine content type from use case
        content_type = determine_content_type(state)
        use_case = state.get("use_case", "story_generator")
        
        logger.info(f"🎯 Content generator starting for content type: '{content_type}' (use case: '{use_case}')")
        
        # Extract input data including personalization (same as original content_generator)
        plan = state.get("plan", {})
        user_input = state.get("user_input", "")
        age_group = state.get("target_audience", "6-12")
        story_length = state.get("story_length", "medium")
        
        # Extract personalization parameters
        child_name = state.get("child_name", "Hero")
        child_age = state.get("child_age", 8)
        child_gender = state.get("child_gender", "neutral")
        interests = state.get("interests", [])
        reading_level = state.get("reading_level", "medium")
        companions = state.get("companions", [])
        location = state.get("location", "")
        region = state.get("region", "")
        mother_tongue = state.get("mother_tongue", "")
        language_of_story = state.get("language_of_story", "english")
        moral_lesson = state.get("moral_lesson", "")
        theme = state.get("theme", "adventure")
        
        if not plan:
            raise ValueError(f"No plan available for {content_type} content generation")
        
        # Load content type-specific constraints from use case config
        try:
            from ..composer.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            use_case_config = config_loader.get_use_case_config(use_case)
            
            # Get story/content length constraints and image settings
            length_constraints = use_case_config.get("settings", {}).get("story_length_constraints", {})
            content_config = length_constraints.get(story_length, length_constraints.get("medium", {}))
            image_settings = use_case_config.get("settings", {}).get("image_generation", {})
            
            # Extract constraints and image settings
            word_count = content_config.get("word_count", 400)
            words_per_page = content_config.get("words_per_chapter", 135)
            reading_time = content_config.get("reading_time", 5)
            image_count = image_settings.get("count", 3)
            
            # Check if image_style is provided in state and get detailed style information
            if "image_style" in state and state["image_style"]:
                print(f"🎨 [DEBUG] content_generator_node - Found image_style in state: '{state['image_style']}'")
                # Get detailed style information for intelligent prompt formatting
                style_details = get_aesthetic_from_image_style(state["image_style"], return_details=True)
                aesthetic = get_aesthetic_from_image_style(state["image_style"])  # Keep for backward compatibility
                print(f"🎨 [DEBUG] content_generator_node - Converted to aesthetic: '{aesthetic}'")
                print(f"🎨 [DEBUG] content_generator_node - Style details: {style_details}")
                logger.info(f"🎨 Content generator using custom image style: {state['image_style']} -> {aesthetic}")
            else:
                print("🎨 [DEBUG] content_generator_node - No image_style in state, using default ghibli")
                style_details = get_aesthetic_from_image_style("ghibli", return_details=True)  # Get detailed ghibli style info
                aesthetic = get_aesthetic_from_image_style("ghibli")  # Use default ghibli style with full description
                
            # Get aspect ratio and composition guide
            aspect_ratio = image_settings.get("aspect_ratio", "16:9")
            composition_guide = image_settings.get("composition_guide", "centered subject with adequate margins")
            
            # Store in state for later use
            state["word_count"] = word_count
            state["words_per_page"] = words_per_page
            state["reading_time"] = reading_time
            state["content_type"] = content_type  # Store for downstream agents
            
            logger.info(f"📖 {content_type.title()} generator loaded constraints: {story_length} - {word_count} words, {words_per_page} words/page")
            
        except Exception as e:
            logger.warning(f"Could not load use case config for {content_type}: {e}. Using defaults.")
            word_count = 400
            words_per_page = 135
            reading_time = 5
            image_count = 3
            style_details = get_aesthetic_from_image_style("ghibli", return_details=True)  # Get detailed ghibli style info for defaults
            aesthetic = get_aesthetic_from_image_style("ghibli")  # Use default ghibli style with full description
            aspect_ratio = "16:9"
            composition_guide = "centered subject with adequate margins"
        
        # Get content type-specific prompts
        system_prompt, user_prompt_template = get_content_type_prompts(content_type)
        
        # Get LLM
        llm = get_llm()
        
        # Set up JSON output parser for structured formatting
        parser = JsonOutputParser(pydantic_object=FormatterOutput)
        format_instructions = parser.get_format_instructions()
        
        # Prepare content length constraints text
        content_length_constraints = f"Content Length: {story_length.title()} ({word_count} words total, ~{words_per_page} words per page, {reading_time} min read)"
        
        # Format the user prompt with all necessary variables, including content_type and detailed style info
        user_prompt = user_prompt_template.format(
            content_type=content_type,  # Key addition for content type awareness
            use_case=use_case,
            plan=json.dumps(plan, indent=2),
            user_input=user_input,
            age_group=age_group,
            story_length_constraints=content_length_constraints,
            word_count=word_count,
            words_per_page=words_per_page,
            image_count=image_count,
            aesthetic=aesthetic,
            format_instructions=format_instructions,
            aspect_ratio=aspect_ratio,
            composition_guide=composition_guide,
            # Detailed style information for intelligent prompt generation (as raw JSON)
            style_map=json.dumps(style_details, indent=2),
            # Personalization parameters
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            interests=', '.join(interests) if interests else 'general activities',
            reading_level=reading_level,
            companions=str(companions),
            location=location or 'neighborhood',
            region=region or 'local area',
            mother_tongue=mother_tongue or 'local language',
            language_of_story=language_of_story,
            moral_lesson=moral_lesson or 'friendship and kindness',
            theme=theme
        )

        # print("###############################################")
        # print(user_prompt_template)
        # print("###############################################")
              

        # Call LLM with structured output
        messages = [
            SystemMessage(content=system_prompt.format(
                content_type=content_type,
                use_case=use_case,
                age_group=age_group,
                language_of_story=language_of_story
            )),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure response_text is a string
        if isinstance(response_text, list):
            response_text = str(response_text)
        elif not isinstance(response_text, str):
            response_text = str(response_text)
        
        # Parse the response using the JSON parser
        try:
            formatted_data = parser.parse(response_text)
            logger.info(f"✅ Successfully parsed LLM response for {content_type} with {len(formatted_data.get('image_prompts', []))} image prompts")
        except Exception as parse_error:
            logger.warning(f"🚫 JSON parsing failed for {content_type}: {parse_error}")
            logger.warning(f"🔍 Raw response length: {len(response_text)}")
            logger.warning(f"🔍 Response preview: {response_text[:200]}...")
            
            # Fallback to manual parsing if needed
            if response_text.strip().startswith('{'):
                try:
                    formatted_data = json.loads(response_text)
                    logger.info(f"✅ Manual JSON parsing successful for {content_type}")
                except json.JSONDecodeError as json_error:
                    logger.warning(f"🚫 Manual JSON parsing also failed for {content_type}: {json_error}")
                    formatted_data = None
            else:
                # Extract JSON from response if wrapped in markdown
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    try:
                        formatted_data = json.loads(json_match.group(1))
                        logger.info(f"✅ Markdown JSON extraction successful for {content_type}")
                    except json.JSONDecodeError as json_error:
                        logger.warning(f"🚫 Markdown JSON extraction failed for {content_type}: {json_error}")
                        formatted_data = None
                else:
                    logger.warning(f"🚫 No JSON found in response for {content_type}")
                    formatted_data = None
            
            # Final fallback structure if all parsing fails - create appropriate structure for content type
            if not formatted_data:
                logger.warning(f"🚫 LLM parsing completely failed for {content_type} - using fallback structure")
                
                # Use raw response as content
                raw_content = response_text
                
                # Create content type-appropriate fallback structure
                if content_type == "poetry_and_music":
                    formatted_data = {
                        "formatted_content": {
                            "title": plan.get("title", f"Poetry and Music about {user_input}"),
                            "summary": f"A collection of poetry and music about {user_input}",
                            "estimated_duration": reading_time,
                            "sections": [{"title": f"Complete {content_type.title()}", "content": raw_content, "scene_description": f"Main scene from {user_input}"}],
                            "word_count": len(raw_content.split()),
                            "themes": ["creativity", "expression"],
                            "mood": "joyful"
                        },
                        "image_prompts": [
                            f"A {aesthetic} illustration showing a creative scene about {user_input}. Create with {aspect_ratio} aspect ratio, {composition_guide}."
                        ]
                    }
                else:  # story or educational
                    formatted_data = {
                        "formatted_story": {
                            "title": plan.get("title", f"{content_type.title()} about {user_input}"),
                            "summary": f"A {content_type} about {user_input}",
                            "reading_time": reading_time,
                            "chapters": [{"title": f"Complete {content_type.title()}", "content": raw_content, "scene_description": f"Main scene from {user_input}"}],
                            "word_count": len(raw_content.split()),
                            "themes": ["adventure", "learning"] if content_type == "educational" else ["adventure", "friendship"],
                            "characters": [user_input]
                        },
                        "image_prompts": [
                            f"A {aesthetic} illustration showing a scene from a {content_type} about {user_input}. Create with {aspect_ratio} aspect ratio, {composition_guide}."
                        ]
                    }
                
                logger.info(f"🔧 Created fallback structure for {content_type} with {len(formatted_data.get('image_prompts', []))} image prompts")
        
        execution_time = time.time() - start_time
        
        # Log interaction
        log_llm_interaction("content_generator", system_prompt, user_prompt, response_text, execution_time)
        
        # Extract the appropriate output structure based on content type
        output_structure = get_output_structure_for_content_type(content_type)
        formatted_content = formatted_data.get(output_structure, {})
        
        # If expected structure is empty, try the alternative structure
        if not formatted_content:
            alternative_structure = "formatted_content" if output_structure == "formatted_story" else "formatted_story"
            formatted_content = formatted_data.get(alternative_structure, {})
            logger.info(f"🔄 Using alternative structure '{alternative_structure}' instead of expected '{output_structure}'")
        
        # Extract raw content for backward compatibility
        if "sections" in formatted_content:
            # Combine all section content (works for both poetry/music and stories with sections)
            raw_content = ""
            for section in formatted_content["sections"]:
                if isinstance(section, dict):
                    section_content = section.get("content", "")
                else:
                    section_content = str(section)
                raw_content += section_content + "\n\n"
            raw_content = raw_content.strip()
            
            # Store in appropriate state keys based on content type
            if content_type == "poetry_and_music":
                state["poetry_content"] = raw_content
                state["music_content"] = raw_content  # For consistency
            else:
                # For stories that used sections instead of chapters
                pass  # raw_content will be used for state["content"]
            
        elif "chapters" in formatted_content:
            # Combine all chapter content for stories/educational
            raw_content = ""
            for chapter in formatted_content["chapters"]:
                if isinstance(chapter, dict):
                    chapter_content = chapter.get("content", "")
                else:
                    chapter_content = str(chapter)
                raw_content += chapter_content + "\n\n"
            raw_content = raw_content.strip()
        else:
            # Fallback to raw response
            logger.warning(f"🚫 No sections or chapters found in formatted_content for {content_type}, using raw response")
            raw_content = response_text
        
        # Ensure image_prompts is always set
        image_prompts = formatted_data.get("image_prompts", [])
        if not image_prompts:
            # Fallback: create basic prompts if none were generated
            logger.warning(f"🔧 No image_prompts found in formatted_data for {content_type}, creating fallback prompts")
            image_prompts = [
                f"A {aesthetic} illustration of a scene from a children's {content_type} about {user_input}, scene {i+1}. Create with {aspect_ratio} aspect ratio, {composition_guide}"
                for i in range(image_count)
            ]
            logger.info(f"🔧 Created {len(image_prompts)} fallback image prompts for {content_type}")
        
        # Update state with all necessary outputs (content type agnostic)
        state["content"] = raw_content  # For backward compatibility
        
        # Set the appropriate formatted structure based on content type and actual structure used
        if content_type == "poetry_and_music":
            state["formatted_content"] = formatted_content  # For poetry/music content
        else:
            # For stories/educational, set the correct key based on what was actually used
            if "chapters" in formatted_content:
                state["formatted_story"] = formatted_content  # Expected structure
            elif "sections" in formatted_content:
                state["formatted_story"] = formatted_content  # Alternative structure used
            else:
                # Fallback: create a basic structure
                state["formatted_story"] = {
                    "title": plan.get("title", f"{content_type.title()} about {user_input}"),
                    "summary": f"A {content_type} about {user_input}",
                    "reading_time": reading_time,
                    "chapters": [{"title": f"Complete {content_type.title()}", "content": raw_content, "scene_description": f"Main scene from {user_input}"}],
                    "word_count": len(raw_content.split()),
                    "themes": ["adventure", "learning"] if content_type == "educational" else ["adventure", "friendship"],
                    "characters": [user_input]
                }
            
        state["story_image_prompts"] = image_prompts  # For image_generator_node
        state["current_agent"] = "content_generator"
        state["updated_at"] = datetime.now()
        state["workflow_step"] = "content_generation_complete"
        
        # Debug logging
        logger.info(f"✅ {content_type.title()} content generation and formatting completed successfully")
        logger.info(f"📖 Generated content title: {formatted_content.get('title', 'Untitled')}")
        logger.info(f"📝 Raw content length: {len(raw_content)} characters")
        logger.info(f"🎯 Generated {len(image_prompts)} targeted image prompts")
        
        if content_type == "poetry_and_music":
            logger.info(f"📊 Sections created: {len(formatted_content.get('sections', []))}")
        else:
            logger.info(f"📊 Chapters created: {len(formatted_content.get('chapters', []))}")
        
        if image_prompts:
            for i, prompt in enumerate(image_prompts, 1):
                logger.info(f"   🎨 Image Prompt {i}: {prompt}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in content_generator_node for {state.get('use_case', 'unknown')}: {e}")
        state["errors"] = state.get("errors", []) + [f"Content generation error: {str(e)}"]
        state["current_agent"] = "content_generator"
        state["workflow_step"] = "error"
        return state

def get_available_agents():
    """Return list of available agent functions."""
    return ["planner", "writer", "formatter", "content_generator", "critique", "poetry_agent", "music_agent", "image_generator"]
