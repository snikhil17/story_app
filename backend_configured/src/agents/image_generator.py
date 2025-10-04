"""
Enhanced Image Generator for Composer System

This module provides actual image generation capabilities using Google's Gemini API
with configurable settings from use cases.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from PIL import Image
from io import BytesIO

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("Google GenAI not available. Image generation will create placeholders.")

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigurableImageGenerator:
    """
    Image generator that uses configuration from use cases YAML.
    """
    
    def __init__(self, use_case_config: Dict[str, Any], unique_prefix: Optional[str] = None):
        """
        Initialize the image generator with use case configuration.
        
        Args:
            use_case_config: Configuration from use_cases.yaml
            unique_prefix: Unique prefix for generated files
        """
        self.use_case_config = use_case_config
        self.unique_prefix = unique_prefix or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract image generation settings
        self.settings = use_case_config.get("settings", {}).get("image_generation", {})
        self.enabled = self.settings.get("enabled", True)
        self.count = self.settings.get("count", 3)
        self.output_folder = self.settings.get("output_folder", "generated_images")
        self.style = self.settings.get("style", "Studio Ghibli")
        self.aesthetic = self.settings.get("aesthetic", "cartoony, cute, watercolor-like")
        self.aspect_ratio = self.settings.get("aspect_ratio", "16:9")
        self.composition_guide = self.settings.get("composition_guide", "centered subject with adequate margins")
        
        # Initialize Gemini client if available
        self.client = None
        if GENAI_AVAILABLE and self.enabled:
            try:
                import google.genai as genai_module
                if hasattr(genai_module, 'Client'):
                    self.client = genai_module.Client()
                    logger.info("✅ Gemini image generation client initialized")
                else:
                    logger.warning("Gemini Client not available")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                self.client = None
        
        # Create output directory
        self.create_output_folder()
        
    def create_output_folder(self):
        """Create the output folder if it doesn't exist."""
        # Create folder in the outputs directory with unique prefix
        base_path = Path(__file__).parent.parent.parent / "outputs" / "images"
        self.full_output_path = base_path / f"images_{self.unique_prefix}"
        self.full_output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Image output folder: {self.full_output_path}")
    
    def generate_single_image(self, prompt: str, image_index: int, title: str = "") -> Optional[str]:
        """
        Generate a single image using Gemini API.
        
        Args:
            prompt: Image generation prompt
            image_index: Index of the image (for filename)
            title: Title for the image (for filename)
            
        Returns:
            Path to generated image file or None if failed
        """
        if not self.enabled:
            logger.info("Image generation disabled in configuration")
            return None
            
        if not self.client:
            logger.warning("Gemini client not available, creating placeholder")
            return self.create_placeholder_image(image_index, title)
        
        try:
            logger.info(f"🎨 Generating image {image_index + 1}: {title}")
            logger.info(f"📝 Using prompt: {prompt[:100]}...")
            
            # Use the prompt as-is without any enhancement
            # The prompt should already contain all necessary style and technical specifications
            final_prompt = prompt
            
            # Import types locally to avoid unbound variable issues
            from google.genai import types as genai_types

            response = self.client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=final_prompt,  # Use the clean prompt without enhancement
                config=genai_types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            # Process the response with proper null checks
            if response and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.inline_data is not None and part.inline_data.data:
                            # Generate filename
                            safe_title = title.lower().replace(' ', '_').replace(',', '').replace('.', '') if title else f"image_{image_index + 1}"
                            # Truncate title to prevent filename too long errors (max 50 chars)
                            if len(safe_title) > 50:
                                safe_title = safe_title[:50]
                            filename = f"{self.unique_prefix}_{safe_title}_{image_index + 1:02d}.png"
                            filepath = self.full_output_path / filename
                            
                            # Save the image with proper type checking
                            image_data = part.inline_data.data
                            if isinstance(image_data, bytes):
                                buffer = BytesIO(image_data)
                                image = Image.open(buffer)
                                image.save(filepath)
                                image.close()  # Explicitly close the image
                                buffer.close()  # Explicitly close the buffer
                                del image
                                del buffer
                                del image_data
                                # Optionally, call gc.collect() in tight loops to force garbage collection
                                # import gc; gc.collect()
                                logger.info(f"✅ Saved image: {filepath}")
                                return str(filepath)
            
            logger.warning(f"No image data received for prompt: {prompt[:50]}...")
            return self.create_placeholder_image(image_index, title)
            
        except Exception as e:
            logger.error(f"Error generating image {image_index + 1}: {e}")
            return self.create_placeholder_image(image_index, title)
    
    def create_placeholder_image(self, image_index: int, title: str = "") -> str:
        """
        Create a placeholder image when actual generation fails.
        
        Args:
            image_index: Index of the image
            title: Title for the image
            
        Returns:
            Path to placeholder image file
        """
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple placeholder image
        width, height = 512, 512
        image = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(image)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Draw placeholder text
        text_lines = [
            f"Image {image_index + 1}",
            title if title else "Generated Image",
            "Placeholder"
        ]
        
        y_offset = height // 2 - 60
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y_offset), line, fill='darkblue', font=font)
            y_offset += 40
        
        # Save placeholder
        safe_title = title.lower().replace(' ', '_').replace(',', '').replace('.', '') if title else f"placeholder_{image_index + 1}"
        # Truncate title to prevent filename too long errors (max 50 chars)
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        filename = f"{self.unique_prefix}_{safe_title}_{image_index + 1:02d}_placeholder.png"
        filepath = self.full_output_path / filename
        image.save(filepath)
        
        logger.info(f"📷 Created placeholder image: {filepath}")
        return str(filepath)
    
    def generate_story_images(self, story_content: str, user_input: str, plan: Dict[str, Any]) -> List[str]:
        """
        Generate multiple images for a story based on content and plan.
        
        Args:
            story_content: The generated story text
            user_input: Original user request
            plan: Story plan from planner agent
            
        Returns:
            List of generated image file paths
        """
        logger.info(f"🎨 Starting image generation for {self.count} images")
        
        generated_files = []
        
        # Extract key scenes/moments for image generation
        image_prompts = self.extract_image_prompts(story_content, user_input, plan)
        
        # Generate the configured number of images
        for i in range(min(self.count, len(image_prompts))):
            prompt_info = image_prompts[i]
            print(f"############ Prompt for Image {i}")
            print(prompt_info["prompt"])
            print(f"############ Prompt for Image {i}")

            filepath = self.generate_single_image(
                prompt_info["prompt"], 
                i, 
                prompt_info["title"]
            )
            
            if filepath:
                generated_files.append(filepath)
            
            # Small delay between requests
            if i < self.count - 1:
                time.sleep(1)
        
        logger.info(f"✅ Generated {len(generated_files)} images out of {self.count} requested")
        return generated_files
    
    def extract_image_prompts(self, story_content: str, user_input: str, plan: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract key visual scenes from story content and plan.
        
        Args:
            story_content: The story text
            user_input: Original user request
            plan: Story plan
            
        Returns:
            List of prompt dictionaries with 'prompt' and 'title' keys
        """
        prompts = []
        
        # Extract characters and setting from plan
        characters = plan.get("characters", [])
        setting = plan.get("setting", "")
        title = plan.get("title", user_input)
        
        # Create prompts based on story structure
        if characters and setting:
            # Main character introduction
            main_char = characters[0] if characters else {"name": "main character", "traits": ["brave"]}
            char_name = main_char.get("name", "main character")
            char_traits = ", ".join(main_char.get("traits", ["brave", "curious"]))
            
            prompts.append({
                "title": "Character Introduction",
                "prompt": f"A {char_traits} character named {char_name} in {setting}, introducing the main character of the story about {user_input}"
            })
            
            # Middle scene - conflict/adventure
            if len(prompts) < self.count:
                prompts.append({
                    "title": "Adventure Scene", 
                    "prompt": f"{char_name} facing a challenge or adventure in {setting}, showing the main conflict or exciting moment from the story about {user_input}"
                })
            
            # Resolution scene
            if len(prompts) < self.count:
                prompts.append({
                    "title": "Happy Ending",
                    "prompt": f"{char_name} having learned and grown, showing the happy resolution in {setting}, celebrating the conclusion of the story about {user_input}"
                })
        else:
            # Fallback prompts if plan parsing fails
            prompts = [
                {"title": "Story Beginning", "prompt": f"The opening scene of a children's story about {user_input}"},
                {"title": "Story Middle", "prompt": f"An exciting adventure scene from a story about {user_input}"},
                {"title": "Story Ending", "prompt": f"The happy ending of a children's story about {user_input}"}
            ]
        
        # Ensure we have enough prompts
        while len(prompts) < self.count:
            prompts.append({
                "title": f"Scene {len(prompts) + 1}",
                "prompt": f"An illustration for a children's story about {user_input}"
            })
        
        return prompts[:self.count]
