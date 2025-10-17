import os
import asyncio
from pathlib import Path
from typing import List


class EditorAgent:
    """Editor Agent - Compiles scenes into final video with audio."""
    
    def __init__(self):
        self.output_dir = Path("/app/backend/output/final")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def compile_movie(self, project_id: str, scenes: List[dict]) -> str:
        """Compile all scenes into a final movie."""
        
        try:
            from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
            import gc
            
            video_clips = []
            
            for scene in sorted(scenes, key=lambda x: x.get('scene_number', 0)):
                animation_path = scene.get('animation_path')
                voice_path = scene.get('voice_path')
                
                if animation_path and os.path.exists(animation_path):
                    video_clip = VideoFileClip(animation_path)
                    
                    # Add voiceover if available
                    if voice_path and os.path.exists(voice_path):
                        try:
                            audio_clip = AudioFileClip(voice_path)
                            # Adjust video duration to match audio if audio is longer
                            if audio_clip.duration > video_clip.duration:
                                video_clip = video_clip.with_duration(audio_clip.duration)
                            video_clip = video_clip.with_audio(audio_clip)
                        except Exception as e:
                            print(f"Audio error for scene: {e}")
                    
                    video_clips.append(video_clip)
            
            if not video_clips:
                raise Exception("No video clips to compile")
            
            # Concatenate all clips
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Export final movie with optimized settings
            output_path = self.output_dir / f"movie_{project_id}.mp4"
            final_video.write_videofile(
                str(output_path),
                fps=15,
                codec='libx264',
                audio_codec='aac',
                logger=None,
                preset='ultrafast',
                threads=2,
                bitrate='500k'  # Lower bitrate to reduce file size
            )
            
            # Close clips to free memory immediately
            for clip in video_clips:
                try:
                    clip.close()
                except:
                    pass
            final_video.close()
            
            # Force garbage collection
            gc.collect()
            
            return str(output_path)
            
        except Exception as e:
            print(f"Movie compilation error: {e}")
            raise Exception(f"Could not compile movie: {e}")
    
    async def add_background_music(self, video_path: str, music_path: str) -> str:
        """Add background music to the video (optional feature)."""
        # TODO: Implement background music mixing
        return video_path
