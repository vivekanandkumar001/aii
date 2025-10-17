from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from enum import Enum


class ProjectStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SceneStatus(str, Enum):
    PENDING = "pending"
    SCRIPT_GENERATED = "script_generated"
    ANIMATING = "animating"
    VOICE_GENERATING = "voice_generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    story_input: str
    genre: Optional[str] = "general"
    status: ProjectStatus = ProjectStatus.PENDING
    total_scenes: int = 0
    completed_scenes: int = 0
    video_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str
    story_input: str
    genre: Optional[str] = "general"


class Scene(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    scene_number: int
    description: str
    dialogue: Optional[str] = None
    camera_direction: Optional[str] = None
    duration: Optional[float] = 5.0  # seconds
    status: SceneStatus = SceneStatus.PENDING
    animation_path: Optional[str] = None
    voice_path: Optional[str] = None
    video_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


class Character(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    voice_type: str = "male"  # male, female, neutral
    project_id: str


class JobStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str  # director, animator, voice, editor
    project_id: str
    scene_id: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0  # 0-100
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
