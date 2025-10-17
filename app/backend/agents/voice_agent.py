import os
import asyncio
from pathlib import Path
from gtts import gTTS


class VoiceAgent:
    """Voice Agent - Generates voiceovers using Google Text-to-Speech."""
    
    def __init__(self):
        self.output_dir = Path("/app/backend/output/voices")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_voiceover(self, scene_id: str, text: str, language: str = "en") -> str:
        """Generate voiceover for a scene using gTTS."""
        
        if not text or text.strip() == "":
            return None
        
        try:
            # Run gTTS in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            output_path = self.output_dir / f"voice_{scene_id}.mp3"
            
            await loop.run_in_executor(
                None,
                self._generate_tts,
                text,
                str(output_path),
                language
            )
            
            return str(output_path)
            
        except Exception as e:
            print(f"Voice generation error: {e}")
            return None
    
    def _generate_tts(self, text: str, output_path: str, language: str):
        """Generate TTS (runs in thread pool)."""
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)
