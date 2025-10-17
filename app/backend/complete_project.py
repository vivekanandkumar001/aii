#!/usr/bin/env python3
"""Manual script to complete a project compilation."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from agents.editor_agent import EditorAgent
from models import ProjectStatus
from datetime import datetime, timezone

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def complete_project(project_id: str):
    """Complete the compilation for a project."""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Get project
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            print(f"Project {project_id} not found")
            return
        
        print(f"Project: {project['title']}")
        print(f"Status: {project['status']}")
        print(f"Scenes: {project['completed_scenes']}/{project['total_scenes']}")
        
        # Get all scenes
        scenes_data = await db.scenes.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
        print(f"Found {len(scenes_data)} scenes in database")
        
        # Check if all scenes have animation paths
        missing = [s for s in scenes_data if not s.get('animation_path')]
        if missing:
            print(f"Warning: {len(missing)} scenes missing animation paths")
        
        # Initialize editor agent
        editor = EditorAgent()
        
        print("Starting final video compilation...")
        final_video_path = await editor.compile_movie(project_id, scenes_data)
        
        print(f"Final video created: {final_video_path}")
        
        # Update project status
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": ProjectStatus.COMPLETED.value,
                "video_url": final_video_path,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        print("Project marked as completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Mark as failed
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": ProjectStatus.FAILED.value,
                "error_message": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python complete_project.py <project_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    asyncio.run(complete_project(project_id))
