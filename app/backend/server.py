from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime

# Import models
from models import (
    Project, ProjectCreate, Scene, ProjectStatus, SceneStatus
)

# Import agents
from agents.workflow_agent import WorkflowAgent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create output directories
output_dir = Path("/app/backend/output")
(output_dir / "animations").mkdir(parents=True, exist_ok=True)
(output_dir / "voices").mkdir(parents=True, exist_ok=True)
(output_dir / "final").mkdir(parents=True, exist_ok=True)

# Initialize Workflow Agent
workflow_agent = WorkflowAgent(db)

# Create the main app without a prefix
app = FastAPI(title="Swami - Autonomous 3D Animation Generator")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ==================== PROJECT ENDPOINTS ====================

@api_router.post("/projects", response_model=Project)
async def create_project(input: ProjectCreate, background_tasks: BackgroundTasks):
    """Create a new 3D animation project."""
    project = Project(
        title=input.title,
        story_input=input.story_input,
        genre=input.genre
    )
    
    # Save to database
    project_dict = project.model_dump()
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    project_dict['updated_at'] = project_dict['updated_at'].isoformat()
    
    await db.projects.insert_one(project_dict)
    
    # Start processing in background
    background_tasks.add_task(workflow_agent.start_project, project.id)
    
    return project


@api_router.get("/projects", response_model=List[Project])
async def get_projects():
    """Get all projects."""
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for project in projects:
        if isinstance(project.get('created_at'), str):
            project['created_at'] = datetime.fromisoformat(project['created_at'])
        if isinstance(project.get('updated_at'), str):
            project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    return projects


@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a specific project by ID."""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert ISO string timestamps
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    return project


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and its scenes."""
    # Delete all scenes for this project
    await db.scenes.delete_many({"project_id": project_id})
    
    # Delete the project
    result = await db.projects.delete_one({"id": project_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}


# ==================== SCENE ENDPOINTS ====================

@api_router.get("/projects/{project_id}/scenes", response_model=List[Scene])
async def get_project_scenes(project_id: str):
    """Get all scenes for a project."""
    scenes = await db.scenes.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps
    for scene in scenes:
        if isinstance(scene.get('created_at'), str):
            scene['created_at'] = datetime.fromisoformat(scene['created_at'])
    
    # Sort by scene number
    scenes.sort(key=lambda x: x.get('scene_number', 0))
    
    return scenes


@api_router.get("/scenes/{scene_id}", response_model=Scene)
async def get_scene(scene_id: str):
    """Get a specific scene by ID."""
    scene = await db.scenes.find_one({"id": scene_id}, {"_id": 0})
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Convert ISO string timestamp
    if isinstance(scene.get('created_at'), str):
        scene['created_at'] = datetime.fromisoformat(scene['created_at'])
    
    return scene


# ==================== STATS ENDPOINT ====================

@api_router.get("/stats")
async def get_stats():
    """Get overall system statistics."""
    total_projects = await db.projects.count_documents({})
    completed_projects = await db.projects.count_documents({"status": ProjectStatus.COMPLETED.value})
    processing_projects = await db.projects.count_documents({"status": ProjectStatus.PROCESSING.value})
    failed_projects = await db.projects.count_documents({"status": ProjectStatus.FAILED.value})
    
    total_scenes = await db.scenes.count_documents({})
    
    return {
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "processing_projects": processing_projects,
        "failed_projects": failed_projects,
        "total_scenes": total_scenes
    }


# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "Swami - Autonomous 3D Animation Generator API", "status": "running"}


# Include the router in the main app
app.include_router(api_router)

# Mount static files for serving videos
app.mount("/output", StaticFiles(directory="/app/backend/output"), name="output")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
