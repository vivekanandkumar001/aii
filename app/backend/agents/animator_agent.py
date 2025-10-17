import os
import asyncio
from pathlib import Path
import json


class AnimatorAgent:
    """Animator Agent - Creates 3D scenes using Blender (simplified version using MoviePy for MVP)."""
    
    def __init__(self):
        self.output_dir = Path("/app/backend/output/animations")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_scene_animation(self, scene_id: str, scene_data: dict) -> str:
        """Create a 3D animated scene. For MVP, creates a simple video with text."""
        
        try:
            from moviepy import TextClip, ColorClip, CompositeVideoClip
            
            description = scene_data.get('description', 'Scene')
            duration = scene_data.get('duration', 5.0)
            scene_number = scene_data.get('scene_number', 1)
            
            # Use smaller resolution to save memory
            width, height = 854, 480  # 480p instead of 720p
            
            # Create a simple colored background
            background = ColorClip(
                size=(width, height),
                color=(50, 50, 100),
                duration=duration
            )
            
            # Create text overlay with scene description
            title_text = TextClip(
                text=f"Scene {scene_number}",
                font="Arial",
                font_size=40,
                color="white",
                size=(800, None),
                method='caption'
            ).with_position(('center', 80)).with_duration(duration)
            
            # Create description text (truncate if too long)
            desc_short = description[:100] + "..." if len(description) > 100 else description
            desc_text = TextClip(
                text=desc_short,
                font="Arial",
                font_size=24,
                color="white",
                size=(750, None),
                method='caption'
            ).with_position(('center', 'center')).with_duration(duration)
            
            # Composite the video
            video = CompositeVideoClip([background, title_text, desc_text])
            
            # Export the video
            output_path = self.output_dir / f"scene_{scene_id}.mp4"
            video.write_videofile(
                str(output_path),
                fps=15,  # Lower FPS to save memory
                codec='libx264',
                audio=False,
                logger=None,
                preset='ultrafast',  # Faster encoding
                threads=2  # Limit threads
            )
            
            # Close clips to free memory immediately
            video.close()
            background.close()
            title_text.close()
            desc_text.close()
            
            return str(output_path)
            
        except Exception as e:
            print(f"Animation error: {e}")
            # Fallback: create a very simple video
            return await self._create_fallback_animation(scene_id, scene_data)
    
    async def _create_fallback_animation(self, scene_id: str, scene_data: dict) -> str:
        """Create a basic fallback animation."""
        try:
            from moviepy import ColorClip
            
            duration = scene_data.get('duration', 5.0)
            
            # Just a colored background (smaller resolution)
            video = ColorClip(
                size=(854, 480),
                color=(30, 30, 80),
                duration=duration
            )
            
            output_path = self.output_dir / f"scene_{scene_id}.mp4"
            video.write_videofile(
                str(output_path),
                fps=15,
                codec='libx264',
                audio=False,
                logger=None,
                preset='ultrafast',
                threads=2
            )
            
            video.close()
            
            return str(output_path)
            
        except Exception as e:
            print(f"Fallback animation error: {e}")
            raise Exception(f"Could not create animation: {e}")
