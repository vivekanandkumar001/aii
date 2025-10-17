import asyncio
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from agents.director_agent import DirectorAgent
from agents.animator_agent import AnimatorAgent
from agents.voice_agent import VoiceAgent
from agents.editor_agent import EditorAgent
from models import Project, Scene, ProjectStatus, SceneStatus


class WorkflowAgent:
    """Workflow Orchestrator - Manages the entire pipeline from story to final video."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.director = DirectorAgent()
        self.animator = AnimatorAgent()
        self.voice = VoiceAgent()
        self.editor = EditorAgent()
        self.active_projects = {}  # Track running projects
    
    async def start_project(self, project_id: str):
        """Start processing a project through the entire pipeline."""
        
        if project_id in self.active_projects:
            print(f"Project {project_id} is already running")
            return
        
        self.active_projects[project_id] = True
        
        try:
            # Get project from database
            project_data = await self.db.projects.find_one({"id": project_id}, {"_id": 0})
            if not project_data:
                raise Exception(f"Project {project_id} not found")
            
            project = Project(**project_data)
            
            # Update status to processing
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": {"status": ProjectStatus.PROCESSING.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Step 1: Director analyzes story and creates scenes
            print(f"[Director] Analyzing story for project {project_id}")
            scene_breakdown = await self.director.analyze_story(project.story_input, project.genre)
            
            # Create scene documents
            scenes = []
            for scene_data in scene_breakdown.get('scenes', []):
                scene = Scene(
                    project_id=project_id,
                    scene_number=scene_data['scene_number'],
                    description=scene_data['description'],
                    dialogue=scene_data.get('dialogue'),
                    camera_direction=scene_data.get('camera_direction'),
                    duration=scene_data.get('duration', 5.0)
                )
                scenes.append(scene)
            
            # Save scenes to database
            for scene in scenes:
                scene_dict = scene.model_dump()
                scene_dict['created_at'] = scene_dict['created_at'].isoformat()
                await self.db.scenes.insert_one(scene_dict)
            
            # Update project with total scenes
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": {"total_scenes": len(scenes), "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Step 2: Process each scene (Animator + Voice)
            for scene in scenes:
                print(f"[Processing] Scene {scene.scene_number} for project {project_id}")
                
                # Update scene status
                await self.db.scenes.update_one(
                    {"id": scene.id},
                    {"$set": {"status": SceneStatus.ANIMATING.value}}
                )
                
                # Animator creates the scene
                animation_path = await self.animator.create_scene_animation(
                    scene.id,
                    scene.model_dump()
                )
                
                # Update scene with animation path
                await self.db.scenes.update_one(
                    {"id": scene.id},
                    {"$set": {"animation_path": animation_path, "status": SceneStatus.VOICE_GENERATING.value}}
                )
                
                # Voice agent generates voiceover
                voice_path = None
                if scene.dialogue:
                    voice_path = await self.voice.generate_voiceover(scene.id, scene.dialogue)
                    await self.db.scenes.update_one(
                        {"id": scene.id},
                        {"$set": {"voice_path": voice_path}}
                    )
                
                # Mark scene as completed
                await self.db.scenes.update_one(
                    {"id": scene.id},
                    {"$set": {"status": SceneStatus.COMPLETED.value}}
                )
                
                # Update project progress
                await self.db.projects.update_one(
                    {"id": project_id},
                    {"$inc": {"completed_scenes": 1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
                )
            
            # Step 3: Editor compiles all scenes into final movie
            print(f"[Editor] Compiling final movie for project {project_id}")
            scenes_data = await self.db.scenes.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
            
            final_video_path = await self.editor.compile_movie(project_id, scenes_data)
            
            # Update project with final video and mark as completed
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": {
                    "status": ProjectStatus.COMPLETED.value,
                    "video_url": final_video_path,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            print(f"[SUCCESS] Project {project_id} completed! Video: {final_video_path}")
            
        except Exception as e:
            print(f"[ERROR] Project {project_id} failed: {e}")
            # Mark project as failed
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": {
                    "status": ProjectStatus.FAILED.value,
                    "error_message": str(e),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        finally:
            # Remove from active projects
            if project_id in self.active_projects:
                del self.active_projects[project_id]
    
    async def process_multiple_projects(self, project_ids: List[str]):
        """Process multiple projects in parallel."""
        tasks = [self.start_project(project_id) for project_id in project_ids]
        await asyncio.gather(*tasks)
