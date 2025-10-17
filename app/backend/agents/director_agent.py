import os
import asyncio
from typing import List, Dict
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv

load_dotenv()


class DirectorAgent:
    """Director Agent - Breaks down stories into scenes and creates detailed scripts."""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.model = "gpt-4o-mini"
        self.provider = "openai"
    
    async def analyze_story(self, story_input: str, genre: str = "general") -> Dict:
        """Analyze story and break it down into acts and scenes."""
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"director_{asyncio.current_task().get_name()}",
            system_message="You are a professional film director specializing in 3D animated movies. Your job is to break down stories into detailed scenes with camera directions, character actions, and dialogue."
        ).with_model(self.provider, self.model)
        
        prompt = f"""
Analyze this story and break it down into a detailed scene-by-scene breakdown for a 3D animated movie.
Genre: {genre}

Story:
{story_input}

Provide a JSON response with the following structure:
{{
    "title": "Movie title",
    "genre": "{genre}",
    "total_duration": "estimated duration in seconds",
    "scenes": [
        {{
            "scene_number": 1,
            "description": "Detailed visual description of what happens in this scene",
            "dialogue": "Character dialogue or narration (if any)",
            "camera_direction": "Camera angles and movements",
            "duration": 5
        }}
    ]
}}

Keep each scene between 3-8 seconds. Make scenes simple and clear for 3D animation. Focus on basic character movements and clear backgrounds.
"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse the response
        import json
        try:
            # Extract JSON from markdown code blocks if present
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            scene_data = json.loads(response_text)
            return scene_data
        except Exception as e:
            # Fallback: create a simple scene breakdown
            return {
                "title": "Untitled Animation",
                "genre": genre,
                "total_duration": "30",
                "scenes": [
                    {
                        "scene_number": 1,
                        "description": story_input[:200],
                        "dialogue": "This is a simple animated story.",
                        "camera_direction": "Wide shot, slow pan",
                        "duration": 5
                    }
                ]
            }
    
    async def refine_scene(self, scene_description: str) -> str:
        """Refine a scene description for better 3D animation."""
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"director_refine_{asyncio.current_task().get_name()}",
            system_message="You are a 3D animation expert. Simplify scene descriptions for easy 3D rendering."
        ).with_model(self.provider, self.model)
        
        prompt = f"""Simplify this scene for basic 3D animation:
{scene_description}

Provide a clear, simple description focusing on:
- Basic shapes and colors
- Simple character actions
- Clear background
- Minimal complexity

Return only the simplified description."""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return response.strip()
