#!/usr/bin/env python3
"""
Simple FastAPI Application for Composer System
Uses the existing ComposerAPI from src.main
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib
import secrets

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr
from contextlib import asynccontextmanager
try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Firebase Admin SDK not available. Firebase authentication will be disabled.")

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from src.main import ComposerAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Authentication and User Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FirebaseTokenRequest(BaseModel):
    firebase_token: str

class UserProfile(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    provider: str  # "firebase" or "email"
    created_at: datetime
    last_login: datetime

class UserFormData(BaseModel):
    child_name: Optional[str] = None
    child_age: Optional[int] = None
    child_gender: Optional[str] = None
    interests: Optional[List[str]] = None
    reading_level: Optional[str] = None
    location: Optional[str] = None
    mother_tongue: Optional[str] = None
    language_preference: Optional[str] = None

class UserFormUpdateRequest(BaseModel):
    form_data: UserFormData

# Simple in-memory user database (replace with proper database in production)
user_database: Dict[str, Dict[str, Any]] = {}
user_forms: Dict[str, UserFormData] = {}

# Security
security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest() + ":" + salt

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        hash_part, salt = hashed.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_part
    except ValueError:
        return False

def generate_simple_token(user_id: str) -> str:
    """Generate a simple token for email/password users"""
    timestamp = str(int(datetime.now().timestamp()))
    token_data = f"{user_id}:{timestamp}"
    return secrets.token_urlsafe(32) + ":" + token_data

async def get_current_user(token: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user from token"""
    if not token:
        return None
    
    try:
        # Try Firebase token first if available
        if FIREBASE_AVAILABLE:
            try:
                from firebase_admin import auth as firebase_auth
                decoded_token = firebase_auth.verify_id_token(token.credentials)
                user_id = decoded_token['uid']
                
                # Get or create user profile
                if user_id not in user_database:
                    user_database[user_id] = {
                        "uid": user_id,
                        "email": decoded_token.get('email'),
                        "name": decoded_token.get('name'),
                        "provider": "firebase",
                        "created_at": datetime.now(timezone.utc),
                        "last_login": datetime.now(timezone.utc)
                    }
                else:
                    user_database[user_id]["last_login"] = datetime.now(timezone.utc)
                
                return user_database[user_id]
            except Exception as e:
                logger.debug(f"Firebase token verification failed: {e}")
        
        # Try simple token for email/password users
        if ":" in token.credentials:
            try:
                token_part, data_part = token.credentials.split(":", 1)
                user_id, timestamp = data_part.split(":")
                
                # Simple validation (in production, use proper JWT)
                if user_id in user_database and user_database[user_id]["provider"] == "email":
                    user_database[user_id]["last_login"] = datetime.now(timezone.utc)
                    return user_database[user_id]
            except ValueError:
                pass
        
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

# Global cache for the latest generated story
latest_story_cache: Optional[Dict[str, Any]] = None

# Initialize FastAPI app
app = FastAPI(
    title="Composer Story Generation API",
    description="AI-powered story generation system using LangGraph Composer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Alternative Vite port
        "http://localhost:8080",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174",
        "http://127.0.0.1:8080",
        "*"  # Allow all origins for development - configure appropriately for production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files for simple_ui
simple_ui_path = Path(__file__).parent.parent / "simple_ui" / "dist"
if simple_ui_path.exists():
    app.mount("/static", StaticFiles(directory=str(simple_ui_path)), name="static")
    logger.info(f"✅ Mounted simple_ui static files from {simple_ui_path}")
else:
    logger.warning(f"⚠️ Simple UI dist directory not found at {simple_ui_path}")

# Global composer API instance
composer_api: Optional[ComposerAPI] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global composer_api
    try:
        composer_api = ComposerAPI()
        logger.info("✅ Composer API started successfully")
        
        # Initialize Firebase Admin SDK if available
        if FIREBASE_AVAILABLE:
            try:
                import firebase_admin
                from firebase_admin import credentials
                
                # Check if Firebase app is already initialized
                try:
                    firebase_admin.get_app()
                    logger.info("✅ Firebase Admin SDK already initialized")
                except ValueError:
                    # Initialize with default credentials or service account
                    # In production, set GOOGLE_APPLICATION_CREDENTIALS environment variable
                    # or provide path to service account key file
                    firebase_admin.initialize_app()
                    logger.info("✅ Firebase Admin SDK initialized")
            except Exception as e:
                logger.warning(f"⚠️ Firebase Admin SDK initialization failed: {e}")
                logger.info("Firebase authentication will fall back to token verification only")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Composer API: {e}")
        raise

def get_composer_api() -> ComposerAPI:
    """Get the composer API instance with error handling."""
    if composer_api is None:
        raise HTTPException(status_code=500, detail="API not properly initialized")
    return composer_api

# Pydantic models for API requests/responses
class StoryGenerationRequest(BaseModel):
    user_input: str = Field(..., description="The story request or prompt")
    target_age_group: str = Field(default="6-12", description="Target age group")
    educational_themes: List[str] = Field(default=[], description="Educational themes to include")
    use_case: str = Field(default="story_generator", description="Use case to execute")

# Comprehensive personalized story request model
class ComprehensiveStoryRequest(BaseModel):
    # Core story request
    request: str = Field(..., description="Story request in plain text")
    
    # Child personalization
    child_name: Optional[str] = Field(None, description="Child's name to be the lead character")
    age: int = Field(..., description="Child's age")
    child_gender: Optional[str] = Field("neutral", description="Child's gender (he/she/they/neutral)")
    
    # Story customization
    interests: List[str] = Field(default=[], description="Child's interests/hobbies as base environment")
    reading_level: str = Field(default="medium", description="Vocabulary complexity: simple/medium/advanced")
    
    # Social context
    companions: List[Dict[str, Any]] = Field(default=[], description="Friends/pets to include with importance")
    
    # Cultural context
    location: Optional[str] = Field(None, description="Specific location for cultural context")
    region: Optional[str] = Field(None, description="Cultural/geographical region")
    mother_tongue: Optional[str] = Field(None, description="Native language for word integration")
    language_of_story: str = Field(default="english", description="Primary story language: english or hindi")
    
    # Story settings
    theme: str = Field(default="adventure", description="Story theme (fantasy, adventure, etc.)")
    moral_lesson: Optional[str] = Field(None, description="Optional moral lesson")
    story_length: str = Field(default="medium", description="Story length: short, medium, long")
    
    # Image generation
    include_images: bool = Field(default=True, description="Whether to include images")
    image_style: Optional[str] = Field(default="ghibli", description="Image generation style")
    
    # Use case selection
    use_case: Optional[str] = Field(default="story_generator", description="Use case to execute")

# Legacy frontend-compatible model for backward compatibility
class FrontendStoryRequest(BaseModel):
    theme: str = Field(..., description="Story theme (fantasy, adventure, etc.)")
    character_name: Optional[str] = Field(None, description="Main character name")
    age_group: str = Field(..., description="Target age group")
    moral_lesson: Optional[str] = Field(None, description="Optional moral lesson")
    story_length: str = Field(default="medium", description="Story length: short, medium, long")
    include_images: bool = Field(default=True, description="Whether to include images")
    image_style: Optional[str] = Field(None, description="Image generation style")
    use_case: Optional[str] = Field(default="story_generator", description="Use case to execute")

class StoryChapter(BaseModel):
    id: str
    title: str
    content: str
    image: Optional[str] = None

class StoryMetadata(BaseModel):
    theme: str
    ageGroup: str
    readingTime: int
    characters: List[str]
    moralLesson: Optional[str] = None
    genre: str

class FrontendStoryResponse(BaseModel):
    id: str
    title: str
    content: str
    chapters: List[StoryChapter]
    metadata: StoryMetadata
    images: Optional[List[str]] = None

class WorkflowResponse(BaseModel):
    status: str
    result: Dict[str, Any]
    execution_time: Optional[float] = None

# API Routes
@app.get("/")
async def root():
    """Serve the simple_ui frontend or API information."""
    simple_ui_index = Path(__file__).parent.parent / "simple_ui" / "dist" / "index.html"
    if simple_ui_index.exists():
        return FileResponse(simple_ui_index)
    else:
        # Fallback to API information
        return {
            "message": "Composer Story Generation API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "frontend": "Simple UI not found - serve manually or build the frontend"
        }

@app.get("/api")
async def api_root():
    """API root endpoint with information."""
    return {
        "message": "Composer Story Generation API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-07-14"}

@app.get("/use-cases")
async def list_use_cases():
    """List all available use cases."""
    try:
        api = get_composer_api()
        use_cases = api.list_use_cases()
        return use_cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-story-raw", response_model=WorkflowResponse)
async def generate_story(request: StoryGenerationRequest):
    """Generate a story using the specified use case."""
    try:
        api = get_composer_api()
        
        # Map API parameters to workflow parameters
        theme = request.educational_themes[0] if request.educational_themes else "adventure"
        
        # Run the workflow with correct parameter names
        result = api.run_workflow(
            use_case=request.use_case,
            user_input=request.user_input,
            target_audience=request.target_age_group,
            theme=theme
        )
        
        return WorkflowResponse(
            status="success",
            result=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow-info/{use_case}")
async def get_workflow_info(use_case: str):
    """Get information about a specific workflow."""
    try:
        api = get_composer_api()
        info = api.get_workflow_info(use_case)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quick-story")
async def quick_story_generation(request: StoryGenerationRequest):
    """Quick story generation using the default story generator."""
    try:
        from src.main import run_story_generation
        
        # Use the convenience function with correct parameter mapping
        result = run_story_generation(
            user_input=request.user_input,
            target_audience=request.target_age_group,
            theme=request.educational_themes[0] if request.educational_themes else "adventure"
        )
        
        return WorkflowResponse(
            status="success",
            result=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-story", response_model=FrontendStoryResponse)
async def generate_story_frontend(
    request: FrontendStoryRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Generate a story using the frontend-compatible format. Uses saved user form data if available."""
    try:
        api = get_composer_api()
        
        # Convert frontend request to backend format
        user_input = f"Create a {request.theme} story"
        if request.character_name:
            user_input += f" with a character named {request.character_name}"
        if request.moral_lesson:
            user_input += f" that teaches about {request.moral_lesson}"
        
        # Base workflow parameters
        workflow_kwargs = {
            "target_audience": request.age_group,
            "theme": request.theme,
            "story_length": request.story_length
        }
        
        # Enhance with user form data if available
        if current_user:
            user_id = current_user["uid"]
            saved_form = user_forms.get(user_id, UserFormData())
            
            # Add personalization from saved form data
            if saved_form.child_name and not request.character_name:
                user_input = user_input.replace("character named", f"character named {saved_form.child_name}")
                workflow_kwargs["child_name"] = saved_form.child_name
            elif request.character_name:
                workflow_kwargs["child_name"] = request.character_name
            
            if saved_form.child_age:
                workflow_kwargs["child_age"] = str(saved_form.child_age)
                workflow_kwargs["target_audience"] = f"age {saved_form.child_age}"
            
            if saved_form.reading_level:
                workflow_kwargs["reading_level"] = saved_form.reading_level
            
            if saved_form.interests:
                # Convert list to comma-separated string for the workflow
                workflow_kwargs["interests"] = ", ".join(saved_form.interests) if saved_form.interests else ""
            
            if saved_form.child_gender:
                workflow_kwargs["child_gender"] = saved_form.child_gender
            
            if saved_form.location:
                workflow_kwargs["location"] = saved_form.location
            
            if saved_form.mother_tongue:
                workflow_kwargs["mother_tongue"] = saved_form.mother_tongue
            
            if saved_form.language_preference:
                workflow_kwargs["language_of_story"] = saved_form.language_preference
            
            logger.info(f"📝 Enhanced story generation with user {user_id} form data")
        
        # Add image style if provided
        if request.include_images and request.image_style:
            workflow_kwargs["image_style"] = request.image_style
        
        # Map story length to reading time
        length_map = {"short": 3, "medium": 5, "long": 8}
        reading_time = length_map.get(request.story_length, 5)
        
        # Run the workflow
        result = api.run_workflow(
            use_case=request.use_case or "story_generator",  # Use provided use case or default
            user_input=user_input,
            **workflow_kwargs
        )
        
        # Debug: Log the actual result structure
        logger.info(f"📊 Full workflow result: {result}")
        logger.info(f"📊 Result type: {type(result)}")
        logger.info(f"📊 Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Extract content from result with better parsing (handles both story and poetry)
        content = ""
        content_type = "story"
        formatted_story_structure = None
        
        # Try different possible result structures
        if isinstance(result, dict):
            # FIRST: Check for formatted_story structure (this has proper chapters)
            if "formatted_story" in result and result["formatted_story"]:
                formatted_story_structure = result["formatted_story"]
                logger.info(f"📚 Found structured formatted_story with chapters")
                content_type = "story"
                
                # Extract content from chapters or sections for fallback display
                if isinstance(formatted_story_structure, dict):
                    content_parts = []
                    if "chapters" in formatted_story_structure:
                        for chapter in formatted_story_structure["chapters"]:
                            if isinstance(chapter, dict) and "content" in chapter:
                                content_parts.append(chapter["content"])
                    elif "sections" in formatted_story_structure:
                        for section in formatted_story_structure["sections"]:
                            if isinstance(section, dict) and "content" in section:
                                content_parts.append(section["content"])
                    elif "content" in formatted_story_structure:
                        content_parts.append(formatted_story_structure["content"])
                    
                    if content_parts:
                        content = "\n\n".join(content_parts)
                        logger.info(f"📖 Extracted content from formatted structure: {len(content)} chars")
            
            # If no formatted_story, try standard output.story format
            if not content and "output" in result and isinstance(result["output"], dict):
                content = result["output"].get("story", "")
                if content:
                    logger.info(f"📖 Found story in output.story: {len(content)} chars")
                    content_type = "story"
            
            # If not found, try direct output as string
            if not content and "output" in result:
                output = result["output"]
                if isinstance(output, str):
                    content = output
                    logger.info(f"📖 Found content as direct output string: {len(content)} chars")
            
            # Try poetry and music content (for poetry_and_song use case)
            if not content:
                if "poetry_content" in result and result["poetry_content"]:
                    content = str(result["poetry_content"])
                    content_type = "poetry"
                    logger.info(f"🎭 Found poetry content: {len(content)} chars")
                elif "music_content" in result and result["music_content"]:
                    content = str(result["music_content"])
                    content_type = "music"
                    logger.info(f"🎵 Found music content: {len(content)} chars")
            
            # Try other possible keys
            if not content:
                for key in ["story", "content", "text", "result"]:
                    if key in result and result[key]:
                        content = str(result[key])
                        logger.info(f"📖 Found content in key '{key}': {len(content)} chars")
                        break
        
        # Final fallback with error logging
        if not content:
            logger.error(f"❌ No content found in result: {result}")
            content = f"Sorry, there was an issue generating your {request.use_case or 'content'}. Please try again."
        
        # Create chapters based on content type and structure
        chapters = []
        
        if content_type == "poetry":
            # For poetry, treat as single "chapter" but format appropriately
            chapters = [StoryChapter(
                id="1",
                title="Poetry",
                content=content
            )]
        elif content_type == "music":
            # For music, treat as single "chapter" but format appropriately
            chapters = [StoryChapter(
                id="1", 
                title="Song",
                content=content
            )]
        else:
            # For stories, use structured data if available
            if formatted_story_structure and isinstance(formatted_story_structure, dict):
                if "chapters" in formatted_story_structure:
                    # Use the properly structured chapters from formatted_story
                    for i, chapter_data in enumerate(formatted_story_structure["chapters"]):
                        if isinstance(chapter_data, dict):
                            chapters.append(StoryChapter(
                                id=str(i + 1),
                                title=chapter_data.get("title", f"Chapter {i + 1}"),
                                content=chapter_data.get("content", "")
                            ))
                    logger.info(f"📚 Created {len(chapters)} chapters from structured data")
                elif "sections" in formatted_story_structure:
                    # Use the properly structured sections from formatted_story
                    for i, section_data in enumerate(formatted_story_structure["sections"]):
                        if isinstance(section_data, dict):
                            chapters.append(StoryChapter(
                                id=str(i + 1),
                                title=section_data.get("title", f"Section {i + 1}"),
                                content=section_data.get("content", "")
                            ))
                    logger.info(f"📚 Created {len(chapters)} sections from structured data")
                elif "content" in formatted_story_structure:
                    # Single content block
                    chapters = [StoryChapter(
                        id="1",
                        title=formatted_story_structure.get("title", f"The {request.theme.title()} Adventure"),
                        content=formatted_story_structure["content"]
                    )]
            
            # Fallback: parse content by paragraphs if no structured data
            if not chapters and content:
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                if len(paragraphs) <= 3:
                    # Short story - single chapter
                    character_name = request.character_name
                    if current_user and not character_name:
                        saved_form = user_forms.get(current_user["uid"], UserFormData())
                        character_name = saved_form.child_name
                    
                    title = f"The {request.theme.title()} Adventure"
                    if character_name:
                        title = f"{character_name}'s {request.theme.title()} Adventure"
                    
                    chapters = [StoryChapter(
                        id="1",
                        title=title,
                        content=content
                    )]
                else:
                    # Longer story - multiple chapters
                    chapter_size = max(1, len(paragraphs) // 3)
                    for i in range(0, len(paragraphs), chapter_size):
                        chapter_paragraphs = paragraphs[i:i + chapter_size]
                        chapters.append(StoryChapter(
                            id=str(len(chapters) + 1),
                            title=f"Chapter {len(chapters) + 1}",
                            content='\n\n'.join(chapter_paragraphs)
                        ))
                logger.info(f"📖 Created {len(chapters)} chapters from paragraph parsing")
        
        # Ensure we have at least one chapter
        if not chapters:
            chapters = [StoryChapter(
                id="1",
                title="Story",
                content=content or "No content available"
            )]
        
        # Create metadata with potential user data
        character_name = request.character_name
        if current_user and not character_name:
            saved_form = user_forms.get(current_user["uid"], UserFormData())
            character_name = saved_form.child_name
        
        metadata = StoryMetadata(
            theme=request.theme,
            ageGroup=request.age_group,
            readingTime=reading_time,
            characters=[character_name] if character_name else ["Hero"],
            moralLesson=request.moral_lesson,
            genre=request.theme
        )
        
        # Generate title and unique ID
        import uuid
        story_id = str(uuid.uuid4())
        title = f"The Magical {request.theme.title()} Adventure"
        if character_name:
            title = f"{character_name}'s {request.theme.title()} Adventure"
        
        # Find associated images if requested
        images = []
        if request.include_images:
            # Get the latest images from the outputs directory
            images_base = Path("outputs/images")
            if images_base.exists():
                # Get the most recent images directory
                image_dirs = sorted([d for d in images_base.iterdir() if d.is_dir()], 
                                  key=lambda x: x.name, reverse=True)
                if image_dirs:
                    latest_image_dir = image_dirs[0]
                    logger.info(f"Using latest images directory: {latest_image_dir.name}")
                    for img_file in latest_image_dir.glob("*.png"):
                        image_url = f"http://localhost:8000/api/images/{latest_image_dir.name}/{img_file.name}"
                        images.append(image_url)
                        logger.info(f"Added image to new story: {image_url}")
        
        # Create the story response
        story_response = FrontendStoryResponse(
            id=story_id,
            title=title,
            content=content,  # Use 'content' instead of 'story_content'
            chapters=chapters,
            metadata=metadata,
            images=images if request.include_images else None
        )
        
        # Cache the latest story globally for immediate access
        global latest_story_cache
        latest_story_cache = story_response.dict()
        logger.info(f"✅ Content cached globally: {title} ({len(content)} chars)")
        if current_user:
            logger.info(f"📝 Story enhanced with user {current_user['uid']} preferences")
        
        return story_response
        
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")

@app.get("/stories/{story_id}", response_model=FrontendStoryResponse)
async def get_story_by_id(story_id: str):
    """Get a story by ID (mock implementation)."""
    # In a real implementation, this would fetch from a database
    return FrontendStoryResponse(
        id=story_id,
        title="Sample Story",
        content="This is a sample story content.",
        chapters=[StoryChapter(
            id="1",
            title="Sample Chapter",
            content="This is a sample story content."
        )],
        metadata=StoryMetadata(
            theme="adventure",
            ageGroup="6-8",
            readingTime=5,
            characters=["Hero"],
            genre="adventure"
        )
    )

@app.get("/api/story-file/{run_id}/{filename}")
async def get_story_file(run_id: str, filename: str):
    """Serve story files from the outputs directory."""
    try:
        file_path = Path("outputs/runs") / run_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Story file not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/{image_dir}")
async def list_images(image_dir: str):
    """List available images in a directory."""
    try:
        # Use absolute path to avoid working directory issues
        current_dir = Path(__file__).parent
        images_path = current_dir / "outputs" / "images" / image_dir
        
        # Debug logging
        logger.info(f"📁 Looking for images directory at: {images_path}")
        logger.info(f"🔍 Directory exists: {images_path.exists()}")
        
        if not images_path.exists():
            raise HTTPException(status_code=404, detail=f"Image directory not found at {images_path}")
        
        images = [f.name for f in images_path.glob("*.png")]
        logger.info(f"🖼️ Found {len(images)} images: {images}")
        
        return {"images": images}
        
    except Exception as e:
        logger.error(f"❌ Error listing images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/{image_dir}/{filename}")
async def get_image(image_dir: str, filename: str):
    """Serve image files from the outputs directory."""
    try:
        from fastapi.responses import FileResponse
        import os
        
        # Use absolute path to avoid working directory issues
        current_dir = Path(__file__).parent
        image_path = current_dir / "outputs" / "images" / image_dir / filename
        
        # Debug logging
        logger.info(f"🖼️ Looking for image at: {image_path}")
        logger.info(f"🔍 Image exists: {image_path.exists()}")
        logger.info(f"📁 Current working directory: {os.getcwd()}")
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image not found at {image_path}")
        
        return FileResponse(image_path)
        
    except Exception as e:
        logger.error(f"❌ Error serving image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-story")
async def get_latest_story():
    """Get the latest generated story from cache or outputs directory."""
    try:
        # First check if we have a cached story
        global latest_story_cache
        if latest_story_cache:
            logger.info("📖 Returning cached latest story")
            return latest_story_cache
        
        logger.info("🔍 No cached story, reading from file system...")
        
        # Find the most recent run directory
        outputs_path = Path("outputs/runs")
        if not outputs_path.exists():
            raise HTTPException(status_code=404, detail="No stories found")
        
        run_dirs = [d for d in outputs_path.iterdir() if d.is_dir()]
        if not run_dirs:
            raise HTTPException(status_code=404, detail="No story runs found")
        
        # Get the most recent directory by name (assuming timestamp format)
        # But ensure it has complete story content
        latest_run = None
        for run_dir in sorted(run_dirs, key=lambda x: x.name, reverse=True):
            # Check if this run has complete content
            formatted_story_file = run_dir / "formatted_story.json"
            content_file = run_dir / "content.txt"
            if formatted_story_file.exists() or content_file.exists():
                latest_run = run_dir
                break
        
        if not latest_run:
            raise HTTPException(status_code=404, detail="No complete story runs found")
        
        logger.info(f"Using run directory: {latest_run.name}")
        
        # First try to load structured story from formatted_story.json
        formatted_story_file = latest_run / "formatted_story.json"
        chapters = []
        story_content = ""
        title = "Untitled Story"
        
        if formatted_story_file.exists():
            # Load structured story data
            with open(formatted_story_file, 'r', encoding='utf-8') as f:
                formatted_data = json.load(f)
                
            title = formatted_data.get('title', 'Untitled Story')
            
            # Convert structured chapters or sections to frontend format
            if formatted_data.get('chapters'):
                for i, chapter_data in enumerate(formatted_data['chapters'], 1):
                    chapters.append(StoryChapter(
                        id=f"chapter-{i}",
                        title=chapter_data.get('title', f"Chapter {i}"),
                        content=chapter_data.get('content', '')
                    ))
                    # Build full story content for backward compatibility
                    story_content += f"Chapter {i}: {chapter_data.get('title', f'Chapter {i}')}\n"
                    story_content += "=" * 50 + "\n"
                    story_content += f"{chapter_data.get('content', '')}\n\n"
            elif formatted_data.get('sections'):
                for i, section_data in enumerate(formatted_data['sections'], 1):
                    chapters.append(StoryChapter(
                        id=f"section-{i}",
                        title=section_data.get('title', f"Section {i}"),
                        content=section_data.get('content', '')
                    ))
                    # Build full story content for backward compatibility
                    story_content += f"Section {i}: {section_data.get('title', f'Section {i}')}\n"
                    story_content += "=" * 50 + "\n"
                    story_content += f"{section_data.get('content', '')}\n\n"
        
        # Fallback to plain text parsing if structured data not available
        if not chapters:
            # Look for the content file (unified naming for both story and poetry)
            story_file = latest_run / "content.txt"
            if not story_file.exists():
                # Fallback to old naming for backward compatibility
                story_file = latest_run / "formatted_story.txt"
                if not story_file.exists():
                    story_file = latest_run / "poetry_content.txt"
                    if not story_file.exists():
                        raise HTTPException(status_code=404, detail="Content file not found in latest run")
            
            with open(story_file, 'r', encoding='utf-8') as f:
                story_content = f.read()
            
            # Parse the story into chapters
            chapters = parse_story_chapters(story_content)
        
        # Find associated images - use better matching logic
        run_name_parts = latest_run.name.split('_')
        date_part = "20250716"  # Default fallback
        time_part = None
        
        if len(run_name_parts) >= 4:
            date_part = run_name_parts[2]  # 20250716
            time_part = run_name_parts[3]  # 122627
        
        logger.info(f"Run directory: {latest_run.name}, extracted date: {date_part}, time: {time_part}")
        
        images = []
        images_base = Path("outputs/images")
        
        if images_base.exists():
            # Find the closest matching images directory by timestamp
            matching_dirs = list(images_base.glob(f"images_{date_part}_*"))
            logger.info(f"Found image directories for date {date_part}: {[d.name for d in matching_dirs]}")
            
            if matching_dirs and time_part:
                # Sort directories by timestamp and find the closest one
                def extract_time(dir_name):
                    parts = dir_name.split('_')
                    return parts[2] if len(parts) >= 3 else "000000"
                
                # Find the directory with timestamp closest to (but not later than) our run time
                matching_dirs.sort(key=lambda d: extract_time(d.name))
                
                target_time = int(time_part)
                best_match = None
                best_diff = float('inf')
                
                for img_dir in matching_dirs:
                    img_time = int(extract_time(img_dir.name))
                    # Prefer images created within 30 minutes before the run
                    time_diff = target_time - img_time
                    if 0 <= time_diff <= 3000 and time_diff < best_diff:  # 30 minutes = 3000 in HHMMSS format
                        best_match = img_dir
                        best_diff = time_diff
                
                # If no match within 30 minutes, use the latest available directory
                if not best_match and matching_dirs:
                    best_match = matching_dirs[-1]
                
                if best_match:
                    logger.info(f"Using images directory: {best_match.name}")
                    for img_file in best_match.glob("*.png"):
                        # Use full localhost base URL to ensure images load correctly
                        image_url = f"http://localhost:8000/api/images/{best_match.name}/{img_file.name}"
                        images.append(image_url)
                        logger.info(f"Added image: {image_url}")
                else:
                    logger.warning("No suitable images directory found")
            else:
                logger.warning(f"No matching images directories found for date {date_part}")
        
        return FrontendStoryResponse(
            id=latest_run.name,
            title=title,
            content=story_content,
            chapters=chapters,
            metadata=StoryMetadata(
                theme="educational adventure",
                ageGroup="8-12",
                readingTime=15,
                characters=["Aadhvita", "Arithmos"],
                moralLesson="Mathematics is the magical language of logic",
                genre="educational fantasy"
            ),
            images=images
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_story_chapters(content: str) -> List[StoryChapter]:
    """Parse story content into chapters."""
    chapters = []
    
    # Split by chapter headers
    chapter_sections = content.split('Chapter ')
    
    if len(chapter_sections) > 1:
        # Skip the title section (index 0) and process actual chapters
        for i in range(1, len(chapter_sections)):
            section = chapter_sections[i].strip()
            lines = section.split('\n')
            
            # Extract chapter number and title
            header_line = lines[0] if lines else ""
            if ':' in header_line:
                chapter_num_title = header_line.split(':', 1)
                chapter_num = chapter_num_title[0].strip()
                chapter_title = chapter_num_title[1].strip()
            else:
                chapter_num = str(i)
                chapter_title = header_line
            
            # Extract content (skip header and separator lines)
            content_lines = []
            for line in lines[1:]:
                if line.strip() and not line.startswith('=='):
                    content_lines.append(line)
            
            chapter_content = '\n'.join(content_lines).strip()
            
            chapters.append(StoryChapter(
                id=f"chapter-{i}",
                title=f"Chapter {chapter_num}: {chapter_title}",
                content=chapter_content
            ))
    else:
        # If no chapters found, create a single chapter
        chapters.append(StoryChapter(
            id="chapter-1",
            title="Complete Story",
            content=content
        ))
    
    return chapters

@app.post("/generate-story-personalized", response_model=FrontendStoryResponse)
async def generate_story_personalized(
    request: ComprehensiveStoryRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Generate a fully personalized story with comprehensive customization including:
    - Child name personalization and gender-appropriate language
    - Interest-based story environment
    - Reading level appropriate vocabulary
    - Companion integration with child as lead
    - Cultural/regional context
    - Mother tongue word integration
    - Primary story language (English/Hindi)
    
    If user is logged in and has form data, it will be used to enhance personalization.
    """
    try:
        api = get_composer_api()
        
        # Start with request data
        personalization_params = {
            "child_name": request.child_name,
            "child_age": request.age,
            "child_gender": request.child_gender,
            "interests": request.interests,
            "reading_level": request.reading_level,
            "companions": request.companions,
            "location": request.location,
            "region": request.region,
            "mother_tongue": request.mother_tongue,
            "language_of_story": request.language_of_story,
            "theme": request.theme,
            "moral_lesson": request.moral_lesson,
            "story_length": request.story_length,
            "target_audience": f"age {request.age}",
            "include_images": request.include_images,
            "image_style": request.image_style
        }
        
        # If user is logged in, merge with their saved form data
        if current_user:
            user_id = current_user["uid"]
            saved_form = user_forms.get(user_id, UserFormData())
            
            # Use saved form data as fallback for empty request fields
            if not request.child_name and saved_form.child_name:
                personalization_params["child_name"] = saved_form.child_name
            if not request.child_gender and saved_form.child_gender:
                personalization_params["child_gender"] = saved_form.child_gender
            if not request.interests and saved_form.interests:
                personalization_params["interests"] = saved_form.interests
            if not request.reading_level and saved_form.reading_level:
                personalization_params["reading_level"] = saved_form.reading_level
            if not request.location and saved_form.location:
                personalization_params["location"] = saved_form.location
            if not request.mother_tongue and saved_form.mother_tongue:
                personalization_params["mother_tongue"] = saved_form.mother_tongue
            if not request.language_of_story and saved_form.language_preference:
                personalization_params["language_of_story"] = saved_form.language_preference
            
            # Use saved age if not provided and available
            if saved_form.child_age and saved_form.child_age != request.age:
                personalization_params["child_age"] = saved_form.child_age
                personalization_params["target_audience"] = f"age {saved_form.child_age}"
        
        # Use the plain text request directly
        user_input = request.request
        
        # Log personalization details
        logger.info(f"🎭 PERSONALIZED STORY REQUEST:")
        logger.info(f"📝 Request: {request.request}")
        logger.info(f"👤 Child: {personalization_params['child_name']} (age {personalization_params['child_age']}, {personalization_params['child_gender']})")
        logger.info(f"🎯 Interests: {personalization_params['interests']}")
        logger.info(f"📚 Reading Level: {personalization_params['reading_level']}")
        logger.info(f"🌍 Location: {personalization_params['location']}, {personalization_params['region']}")
        logger.info(f"🗣️ Mother Tongue: {personalization_params['mother_tongue']}")
        logger.info(f"🌐 Story Language: {personalization_params['language_of_story']}")
        if current_user:
            logger.info(f"� User: {current_user['uid']} (form data applied)")
        
        # Run the workflow with full personalization
        result = api.run_workflow(
            use_case=request.use_case or "story_generator",
            user_input=user_input,
            **personalization_params
        )
        
        # Extract and process content with better structured story handling
        content = ""
        content_type = "story"
        formatted_story_structure = None
        
        if isinstance(result, dict):
            # FIRST: Check for formatted_story structure (this has proper chapters)
            if "formatted_story" in result and result["formatted_story"]:
                formatted_story_structure = result["formatted_story"]
                logger.info(f"📚 Found structured formatted_story for personalized content")
                
                # Extract content from structured format
                if isinstance(formatted_story_structure, dict):
                    content_parts = []
                    if "chapters" in formatted_story_structure:
                        for chapter in formatted_story_structure["chapters"]:
                            if isinstance(chapter, dict) and "content" in chapter:
                                content_parts.append(chapter["content"])
                    elif "sections" in formatted_story_structure:
                        for section in formatted_story_structure["sections"]:
                            if isinstance(section, dict) and "content" in section:
                                content_parts.append(section["content"])
                    elif "content" in formatted_story_structure:
                        content_parts.append(formatted_story_structure["content"])
                    
                    if content_parts:
                        content = "\n\n".join(content_parts)
                        content_type = "story"
                
            # SECOND: Try standard output formats
            elif "output" in result and isinstance(result["output"], dict):
                content = result["output"].get("story", "")
                if content:
                    content_type = "story"
            elif "output" in result and isinstance(result["output"], str):
                content = result["output"]
            else:
                # Try poetry and music content first
                if "poetry_content" in result and result["poetry_content"]:
                    content = str(result["poetry_content"])
                    content_type = "poetry"
                elif "music_content" in result and result["music_content"]:
                    content = str(result["music_content"])
                    content_type = "music"
                else:
                    # Try other possible keys
                    for key in ["story", "content", "text", "result"]:
                        if key in result and result[key]:
                            content = str(result[key])
                            break
        
        if not content:
            logger.error(f"❌ No content found in result: {result}")
            # Create error message in appropriate language
            if personalization_params['language_of_story'] == "hindi":
                content = "माफ करें, कहानी बनाने में समस्या हुई। कृपया फिर से कोशिश करें।"
            else:
                content = f"Sorry, there was an issue generating your {request.use_case or 'content'}. Please try again."
        
        # Create chapters with proper structure handling and language-appropriate titles
        chapters = []
        
        # First try to use structured story data
        if formatted_story_structure and isinstance(formatted_story_structure, dict):
            if "chapters" in formatted_story_structure:
                # Use the properly structured chapters from formatted_story
                for i, chapter_data in enumerate(formatted_story_structure["chapters"]):
                    chapter_title = chapter_data.get("title", f"Chapter {i+1}")
                    if personalization_params['language_of_story'] == "hindi":
                        chapter_title = f"अध्याय {i+1}: {chapter_title}"
                    
                    chapters.append(StoryChapter(
                        id=str(i+1),
                        title=chapter_title,
                        content=chapter_data.get("content", "")
                    ))
            elif "sections" in formatted_story_structure:
                # Use the properly structured sections from formatted_story
                for i, section_data in enumerate(formatted_story_structure["sections"]):
                    section_title = section_data.get("title", f"Section {i+1}")
                    if personalization_params['language_of_story'] == "hindi":
                        section_title = f"अनुभाग {i+1}: {section_title}"
                    
                    chapters.append(StoryChapter(
                        id=str(i+1),
                        title=section_title,
                        content=section_data.get("content", "")
                    ))
        
        # Fallback to paragraph-based chapter creation
        if not chapters:
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            if len(paragraphs) <= 3:
                # Single chapter
                if personalization_params['language_of_story'] == "hindi":
                    chapter_title = f"{personalization_params['child_name'] or 'नायक'} का {personalization_params['theme']} रोमांच"
                else:
                    chapter_title = f"The {personalization_params['theme'].title()} Adventure"
                    if personalization_params['child_name']:
                        chapter_title = f"{personalization_params['child_name']}'s {personalization_params['theme'].title()} Adventure"
                
                chapters = [StoryChapter(
                    id="1",
                    title=chapter_title,
                    content=content
                )]
            else:
                # Multiple chapters
                chapter_size = max(1, len(paragraphs) // 3)
                for i in range(0, len(paragraphs), chapter_size):
                    chapter_paragraphs = paragraphs[i:i + chapter_size]
                    chapter_num = len(chapters) + 1
                    
                    if personalization_params['language_of_story'] == "hindi":
                        chapter_title = f"अध्याय {chapter_num}"
                    else:
                        chapter_title = f"Chapter {chapter_num}"
                    
                    chapters.append(StoryChapter(
                        id=str(chapter_num),
                        title=chapter_title,
                        content='\n\n'.join(chapter_paragraphs)
                    ))
        
        # Create enhanced metadata with personalization info
        characters = [personalization_params['child_name']] if personalization_params['child_name'] else ["Hero"]
        if personalization_params['companions']:
            characters.extend([comp.get("name", "Friend") for comp in personalization_params['companions']])
        
        # Map reading times based on length and reading level
        base_times = {"short": 3, "medium": 5, "long": 8}
        level_multipliers = {"simple": 0.8, "medium": 1.0, "advanced": 1.3}
        reading_time = int(base_times.get(personalization_params['story_length'], 5) * 
                          level_multipliers.get(personalization_params['reading_level'], 1.0))
        
        metadata = StoryMetadata(
            theme=personalization_params['theme'],
            ageGroup=f"age {personalization_params['child_age']}",
            readingTime=reading_time,
            characters=characters,
            moralLesson=personalization_params['moral_lesson'],
            genre=personalization_params['theme']
        )
        
        # Generate story title in appropriate language
        import uuid
        story_id = str(uuid.uuid4())
        
        if personalization_params['language_of_story'] == "hindi":
            if personalization_params['child_name']:
                title = f"{personalization_params['child_name']} का जादुई {personalization_params['theme']} रोमांच"
            else:
                title = f"जादुई {personalization_params['theme']} रोमांच"
        else:
            if personalization_params['child_name']:
                title = f"{personalization_params['child_name']}'s Magical {personalization_params['theme'].title()} Adventure"
            else:
                title = f"The Magical {personalization_params['theme'].title()} Adventure"
        
        # Handle images (same logic as before)
        images = []
        if personalization_params['include_images']:
            # Use absolute path to avoid working directory issues
            current_dir = Path(__file__).parent
            images_base = current_dir / "outputs" / "images"
            logger.info(f"🖼️ Looking for images at: {images_base}")
            
            if images_base.exists():
                image_dirs = sorted([d for d in images_base.iterdir() if d.is_dir()], 
                                  key=lambda x: x.name, reverse=True)
                if image_dirs:
                    latest_image_dir = image_dirs[0]
                    logger.info(f"📁 Using latest image directory: {latest_image_dir.name}")
                    
                    for img_file in latest_image_dir.glob("*.png"):
                        image_url = f"http://localhost:8000/api/images/{latest_image_dir.name}/{img_file.name}"
                        images.append(image_url)
                        logger.info(f"🔗 Added image URL: {image_url}")
                else:
                    logger.warning("⚠️ No image directories found")
            else:
                logger.warning(f"⚠️ Images base directory not found at: {images_base}")
        
        # Create personalized response
        story_response = FrontendStoryResponse(
            id=story_id,
            title=title,
            content=content,
            chapters=chapters,
            metadata=metadata,
            images=images if personalization_params['include_images'] else None
        )
        
        # Cache the latest story
        global latest_story_cache
        latest_story_cache = story_response.dict()
        logger.info(f"✅ Personalized story cached: {title} (Language: {personalization_params['language_of_story']})")
        
        return story_response
        
    except Exception as e:
        logger.error(f"❌ Error generating personalized story: {e}")
        error_msg = f"Failed to generate personalized story: {str(e)}"
        if request.language_of_story == "hindi":
            error_msg = f"व्यक्तिगत कहानी बनाने में विफल: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/latest-content")
async def get_latest_content():
    """Get the latest generated content (story/poetry) as plain text."""
    try:
        # Find the most recent run directory
        outputs_path = Path("outputs/runs")
        if not outputs_path.exists():
            raise HTTPException(status_code=404, detail="No content found")
        
        run_dirs = [d for d in outputs_path.iterdir() if d.is_dir()]
        if not run_dirs:
            raise HTTPException(status_code=404, detail="No content runs found")
        
        # Get the most recent directory by name (assuming timestamp format)
        latest_run = max(run_dirs, key=lambda x: x.name)
        
        # Look for the content file (unified naming)
        content_file = latest_run / "content.txt"
        if not content_file.exists():
            # Fallback to old naming for backward compatibility
            content_file = latest_run / "formatted_story.txt"
            if not content_file.exists():
                content_file = latest_run / "poetry_content.txt"
                if not content_file.exists():
                    raise HTTPException(status_code=404, detail="Content file not found in latest run")
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Return plain text content
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting latest content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest content: {str(e)}")

@app.get("/latest-formatted-content")
async def get_latest_formatted_content():
    """Get the latest generated content in structured JSON format with proper formatting."""
    try:
        # Find the most recent run directory
        outputs_path = Path("outputs/runs")
        if not outputs_path.exists():
            raise HTTPException(status_code=404, detail="No content found")
        
        run_dirs = [d for d in outputs_path.iterdir() if d.is_dir()]
        if not run_dirs:
            raise HTTPException(status_code=404, detail="No content runs found")
        
        # Get the most recent directory by name (assuming timestamp format)
        latest_run = max(run_dirs, key=lambda x: x.name)
        
        # First try to load structured formatted content
        formatted_content_file = latest_run / "formatted_content.json"
        if formatted_content_file.exists():
            with open(formatted_content_file, 'r', encoding='utf-8') as f:
                formatted_data = json.load(f)
            logger.info(f"📋 Returning formatted content from {latest_run.name}")
            return formatted_data
        
        # Fallback to plain text if formatted content not available
        content_file = latest_run / "content.txt"
        if not content_file.exists():
            content_file = latest_run / "formatted_story.txt"
            if not content_file.exists():
                content_file = latest_run / "poetry_content.txt"
                if not content_file.exists():
                    raise HTTPException(status_code=404, detail="Content file not found in latest run")
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a basic structured response
        return {
            "title": "Generated Content",
            "type": "text",
            "content": content,
            "run_id": latest_run.name,
            "timestamp": latest_run.stat().st_mtime
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting latest formatted content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest formatted content: {str(e)}")

# Authentication Endpoints
@app.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user with email and password"""
    try:
        # Check if user already exists
        user_id = user_data.email.lower()
        if user_id in user_database:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        hashed_password = hash_password(user_data.password)
        user_database[user_id] = {
            "uid": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": hashed_password,
            "provider": "email",
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
        
        # Generate token
        token = generate_simple_token(user_id)
        
        # Return user data without password hash
        user_response = {k: v for k, v in user_database[user_id].items() if k != "password_hash"}
        
        return {
            "user": user_response,
            "token": token,
            "message": "User registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login")
async def login_user(user_data: UserLogin):
    """Login user with email and password"""
    try:
        user_id = user_data.email.lower()
        
        # Check if user exists
        if user_id not in user_database:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = user_database[user_id]
        
        # Verify password
        if not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        user["last_login"] = datetime.now(timezone.utc)
        
        # Generate token
        token = generate_simple_token(user_id)
        
        # Return user data without password hash
        user_response = {k: v for k, v in user.items() if k != "password_hash"}
        
        return {
            "user": user_response,
            "token": token,
            "message": "Login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/auth/firebase")
async def authenticate_firebase(token_request: FirebaseTokenRequest):
    """Authenticate user with Firebase ID token"""
    if not FIREBASE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Firebase authentication not available")
    
    try:
        from firebase_admin import auth as firebase_auth
        
        # Verify Firebase token
        decoded_token = firebase_auth.verify_id_token(token_request.firebase_token)
        user_id = decoded_token['uid']
        
        # Get or create user profile
        if user_id not in user_database:
            user_database[user_id] = {
                "uid": user_id,
                "email": decoded_token.get('email'),
                "name": decoded_token.get('name'),
                "provider": "firebase",
                "created_at": datetime.now(timezone.utc),
                "last_login": datetime.now(timezone.utc)
            }
        else:
            user_database[user_id]["last_login"] = datetime.now(timezone.utc)
        
        return {
            "user": user_database[user_id],
            "message": "Firebase authentication successful"
        }
        
    except Exception as e:
        logger.error(f"Firebase authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

@app.get("/auth/me")
async def get_current_user_profile(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Get current user profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "user": current_user,
        "form_data": user_forms.get(current_user["uid"], UserFormData()).dict()
    }

@app.post("/auth/logout")
async def logout_user(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Logout user (mainly for logging purposes)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    logger.info(f"User {current_user['uid']} logged out")
    return {"message": "Logout successful"}

# User Form Management
@app.get("/user/form")
async def get_user_form(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Get user form data"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = current_user["uid"]
    form_data = user_forms.get(user_id, UserFormData())
    
    return {
        "form_data": form_data.dict(),
        "has_data": bool(any(v for v in form_data.dict().values() if v not in [None, [], ""]))
    }

@app.post("/user/form")
async def update_user_form(
    form_request: UserFormUpdateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Update user form data"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = current_user["uid"]
    
    # Get existing form data
    existing_form = user_forms.get(user_id, UserFormData())
    
    # Update only provided fields
    update_data = form_request.form_data.dict(exclude_unset=True)
    existing_data = existing_form.dict()
    
    # Merge the data
    for key, value in update_data.items():
        if value is not None:
            existing_data[key] = value
    
    # Save updated form data
    user_forms[user_id] = UserFormData(**existing_data)
    
    logger.info(f"Updated form data for user {user_id}")
    
    return {
        "message": "Form data updated successfully",
        "form_data": user_forms[user_id].dict()
    }

@app.get("/user/form/check")
async def check_user_form_status(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Check if user needs to fill the form"""
    if not current_user:
        return {"needs_form": True, "message": "User not authenticated"}
    
    user_id = current_user["uid"]
    form_data = user_forms.get(user_id, UserFormData())
    
    # Check if essential fields are filled
    essential_fields = ["child_name", "child_age", "interests"]
    has_essential_data = any(
        getattr(form_data, field, None) not in [None, [], ""]
        for field in essential_fields
    )
    
    return {
        "needs_form": not has_essential_data,
        "form_data": form_data.dict(),
        "message": "Form check completed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )