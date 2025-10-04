"""FastAPI integration for the DreamWeaver story generation system."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime

from src.dreamweaver.graph import DreamWeaverOrchestrator
from src.dreamweaver.configuration import DreamWeaverConfiguration

# Initialize FastAPI app
app = FastAPI(
    title="DreamWeaver Story Generation API",
    description="AI-powered story generation system for children with educational enhancement",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None

# Request/Response models
class StoryRequest(BaseModel):
    """Request model for story generation."""
    story_prompt: str = Field(..., description="The story request from the user")
    target_age_group: str = Field(default="6-12", description="Target age group for the story")
    output_format: str = Field(default="children_book", description="Desired output format")
    educational_themes: Optional[List[str]] = Field(default=None, description="Educational themes to include")
    include_educational_enhancement: bool = Field(default=True, description="Whether to enhance with educational content")
    story_length: str = Field(default="medium", description="Desired story length")


class StoryResponse(BaseModel):
    """Response model for story generation."""
    success: bool
    story_id: str
    story: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    workflow_trace: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generated_at: str


class StoryStatus(BaseModel):
    """Model for story generation status."""
    story_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    progress: Optional[str] = None
    completed_steps: List[str] = []
    estimated_completion: Optional[str] = None


class ConfigurationUpdate(BaseModel):
    """Model for updating DreamWeaver configuration."""
    planner_model: Optional[str] = None
    writer_model: Optional[str] = None
    critique_model: Optional[str] = None
    inject_education_model: Optional[str] = None
    tool_user_model: Optional[str] = None
    formatter_model: Optional[str] = None
    supervisor_model: Optional[str] = None
    enable_educational_enhancement: Optional[bool] = None
    max_revision_rounds: Optional[int] = None


# In-memory storage for story generation status (use database in production)
story_status_storage: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the DreamWeaver orchestrator on startup."""
    global orchestrator
    orchestrator = DreamWeaverOrchestrator()
    await orchestrator.initialize()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DreamWeaver Story Generation API",
        "version": "1.0.0",
        "description": "AI-powered story generation for children with educational enhancement",
        "endpoints": {
            "generate_story": "/api/v1/stories/generate",
            "story_status": "/api/v1/stories/{story_id}/status",
            "health": "/health",
            "configuration": "/api/v1/config"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_ready": orchestrator is not None
    }


@app.post("/api/v1/stories/generate", response_model=StoryResponse)
async def generate_story(
    request: StoryRequest,
    background_tasks: BackgroundTasks
):
    """Generate a new story using the DreamWeaver system."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Story generation system not initialized")
    
    # Generate unique story ID
    story_id = str(uuid.uuid4())
    
    # Initialize status tracking
    story_status_storage[story_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "request": request.dict(),
        "completed_steps": [],
        "progress": "Initializing story generation..."
    }
    
    # Start background story generation
    background_tasks.add_task(
        generate_story_background,
        story_id,
        request
    )
    
    return StoryResponse(
        success=True,
        story_id=story_id,
        story=None,
        metadata={"status": "pending", "message": "Story generation started"},
        workflow_trace=None,
        error=None,
        generated_at=datetime.now().isoformat()
    )


@app.get("/api/v1/stories/{story_id}/status", response_model=StoryStatus)
async def get_story_status(story_id: str):
    """Get the status of a story generation request."""
    if story_id not in story_status_storage:
        raise HTTPException(status_code=404, detail="Story not found")
    
    status_data = story_status_storage[story_id]
    
    return StoryStatus(
        story_id=story_id,
        status=status_data["status"],
        progress=status_data.get("progress"),
        completed_steps=status_data.get("completed_steps", []),
        estimated_completion=status_data.get("estimated_completion")
    )


@app.get("/api/v1/stories/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str):
    """Get the completed story if generation is finished."""
    if story_id not in story_status_storage:
        raise HTTPException(status_code=404, detail="Story not found")
    
    status_data = story_status_storage[story_id]
    
    if status_data["status"] != "completed":
        raise HTTPException(
            status_code=202, 
            detail=f"Story generation in progress. Status: {status_data['status']}"
        )
    
    return StoryResponse(
        success=status_data.get("success", False),
        story_id=story_id,
        story=status_data.get("story"),
        metadata=status_data.get("metadata"),
        workflow_trace=status_data.get("workflow_trace"),
        error=status_data.get("error"),
        generated_at=status_data.get("completed_at", datetime.now().isoformat())
    )


@app.post("/api/v1/stories/generate/sync", response_model=StoryResponse)
async def generate_story_sync(request: StoryRequest):
    """Generate a story synchronously (blocking)."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Story generation system not initialized")
    
    try:
        result = await orchestrator.generate_story(
            story_request=request.story_prompt,
            target_age_group=request.target_age_group,
            output_format=request.output_format,
            educational_themes=request.educational_themes
        )
        
        return StoryResponse(
            success=result["success"],
            story_id=str(uuid.uuid4()),
            story=result.get("story"),
            metadata=result.get("metadata"),
            workflow_trace=result.get("workflow_trace"),
            error=result.get("error"),
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")


@app.get("/api/v1/config")
async def get_configuration():
    """Get current DreamWeaver configuration."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Story generation system not initialized")
    
    config = orchestrator.config
    return {
        "models": {
            "planner": config.planner_model,
            "writer": config.writer_model,
            "critique": config.critique_model,
            "inject_education": config.inject_education_model,
            "tool_user": config.tool_user_model,
            "formatter": config.formatter_model,
            "supervisor": config.supervisor_model
        },
        "settings": {
            "default_age_group": config.default_age_group,
            "default_story_length": config.default_story_length,
            "enable_educational_enhancement": config.enable_educational_enhancement,
            "enable_critique_review": config.enable_critique_review,
            "max_revision_rounds": config.max_revision_rounds
        },
        "supported_formats": config.supported_output_formats,
        "educational_focus_areas": config.educational_focus_areas
    }


@app.post("/api/v1/config/update")
async def update_configuration(config_update: ConfigurationUpdate):
    """Update DreamWeaver configuration."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Story generation system not initialized")
    
    # Update configuration fields
    config = orchestrator.config
    update_dict = config_update.dict(exclude_unset=True)
    
    for field, value in update_dict.items():
        if hasattr(config, field):
            setattr(config, field, value)
    
    # Reinitialize orchestrator with new config
    await orchestrator.initialize()
    
    return {"message": "Configuration updated successfully", "updated_fields": list(update_dict.keys())}


@app.get("/api/v1/templates")
async def get_story_templates():
    """Get available story templates and examples."""
    return {
        "templates": [
            {
                "name": "Environmental Adventure",
                "description": "Stories about nature and environmental conservation",
                "example_prompt": "A story about children who discover they can communicate with forest animals and help solve an environmental problem",
                "educational_themes": ["environmental_science", "conservation", "empathy"],
                "age_groups": ["6-8", "8-12"]
            },
            {
                "name": "STEM Discovery",
                "description": "Stories that introduce science, technology, engineering, and math concepts",
                "example_prompt": "A young inventor creates a robot friend and they explore the principles of coding and engineering",
                "educational_themes": ["stem", "problem_solving", "creativity"],
                "age_groups": ["8-12", "12-16"]
            },
            {
                "name": "Cultural Journey",
                "description": "Stories that explore different cultures and promote understanding",
                "example_prompt": "A child travels to different countries and learns about diverse traditions and customs",
                "educational_themes": ["cultural_awareness", "geography", "social_emotional"],
                "age_groups": ["6-8", "8-12"]
            },
            {
                "name": "Friendship & Emotions",
                "description": "Stories focused on social-emotional learning and relationships",
                "example_prompt": "A shy child learns about friendship and emotional intelligence through magical encounters",
                "educational_themes": ["social_emotional", "empathy", "communication"],
                "age_groups": ["4-6", "6-8"]
            }
        ]
    }


async def generate_story_background(story_id: str, request: StoryRequest):
    """Background task for story generation."""
    try:
        # Update status to in progress
        story_status_storage[story_id]["status"] = "in_progress"
        story_status_storage[story_id]["progress"] = "Starting story generation..."
        
        # Generate the story
        result = await orchestrator.generate_story(
            story_request=request.story_prompt,
            target_age_group=request.target_age_group,
            output_format=request.output_format,
            educational_themes=request.educational_themes
        )
        
        # Update storage with results
        story_status_storage[story_id].update({
            "status": "completed",
            "success": result["success"],
            "story": result.get("story"),
            "metadata": result.get("metadata"),
            "workflow_trace": result.get("workflow_trace"),
            "error": result.get("error"),
            "completed_at": datetime.now().isoformat(),
            "progress": "Story generation completed!"
        })
        
    except Exception as e:
        # Update storage with error
        story_status_storage[story_id].update({
            "status": "failed",
            "success": False,
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
            "progress": f"Story generation failed: {str(e)}"
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
