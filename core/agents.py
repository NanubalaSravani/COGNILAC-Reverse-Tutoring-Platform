from typing import List
from google import genai
from google.genai import types
from core.config import MODEL_NAME, PRESET_TOPICS, get_api_key
from core.prompts import LEO_SYSTEM_PROMPT, LEO_MISCONCEPTION_INSTRUCTION

class LeoAgent:
    def __init__(self, topic: str, level: int = 1, misconception_mode: bool = False, api_key: str = None):
        self.topic = topic
        self.level = level
        self.misconception_mode = misconception_mode
        self.api_key = get_api_key(api_key)
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def get_starter_message(self) -> str:
        if self.topic in PRESET_TOPICS:
            return PRESET_TOPICS[self.topic]["starter_question"]
        return f"Hey Teacher! I'm really curious about {self.topic}. What is it and how does it work?"

    def respond(self, teacher_input: str, conversation_history: List[dict]) -> str:
        """Generate Leo's response to the teacher explanation."""
        if not self.client:
            # Fallback mock response if no API key set
            return f"Whoa, so {self.topic} is like a super smart puzzle? But wait, why does it work that way in real life?"

        misconception_text = ""
        if self.misconception_mode:
            misconception_text = LEO_MISCONCEPTION_INSTRUCTION.format(topic=self.topic)

        system_instruction = LEO_SYSTEM_PROMPT.format(
            topic=self.topic,
            level=self.level,
            misconception_instruction=misconception_text,
        )

        # Build contents from history
        contents = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))
        
        # Append current user explanation
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=teacher_input)]
        ))

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=250,
        )

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            print(f"Leo Agent warning: {e}")
            return f"That sounds cool, Teacher! But can you give me an example I can see at the playground?"
