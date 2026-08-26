import re
import hashlib
import streamlit as st
from typing import List
from google import genai
from google.genai import types
from core.config import MODEL_NAME, PRESET_TOPICS, get_api_key, find_preset_topic
from core.prompts import LEO_SYSTEM_PROMPT, LEO_MISCONCEPTION_INSTRUCTION

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize input text by stripping control characters and capping max length."""
    if not text:
        return ""
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text.strip())
    return cleaned[:max_length]

@st.cache_resource(show_spinner=False)
def _get_cached_client(api_key: str):
    """Reuse Gemini client instance per API key."""
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print("Failed to initialize GenAI client.")
        return None

class LeoAgent:
    def __init__(
        self,
        topic: str,
        level: int = 1,
        misconception_mode: bool = False,
        api_key: str = None,
        grounding_context: str = "",
        document_concepts: List[str] = None,
    ):
        self.topic = sanitize_text(topic, max_length=100)
        self.level = max(1, min(5, level))
        self.misconception_mode = misconception_mode
        self.api_key = get_api_key(api_key)
        self.client = _get_cached_client(self.api_key)
        self.grounding_context = grounding_context
        self.document_concepts = document_concepts or []

    def get_starter_message(self) -> str:
        preset = find_preset_topic(self.topic)
        if preset:
            return preset["starter_question"]
        if self.document_concepts:
            concept_sample = ", ".join(self.document_concepts[:3])
            return f"Hey Teacher! I've been reading about {self.topic} (like {concept_sample}). Can you explain how it all works like I'm 10?"
        return f"Hey Teacher! I'm really curious about {self.topic}. Can you explain what it is like I'm 10?"

    def _offline_reply(self, teacher_input: str, conversation_history: List[dict]) -> str:
        """Return a dynamic context-aware response when offline."""
        words = re.findall(r'\b[A-Za-z]{4,}\b', teacher_input)
        common_words = {"this", "that", "with", "from", "they", "them", "have", "make", "just", "like", "when", "your", "what", "where", "which", "there", "about", "helps", "turns", "makes"}
        keywords = [w for w in words if w.lower() not in common_words]
        
        target_term = keywords[0] if keywords else (self.document_concepts[0] if self.document_concepts else self.topic)
        second_term = keywords[1] if len(keywords) > 1 else (self.document_concepts[1] if len(self.document_concepts) > 1 else "the next concept")
        
        templates = [
            f"Wait! You mentioned '{target_term}' — can you give me a real-world example of that, like on the playground?",
            f"Hold on! What's the difference between '{target_term}' and '{second_term}'?",
            f"Oh! But why does '{target_term}' happen first instead of something else?",
            f"Wait, if '{target_term}' works that way, what would happen if it suddenly stopped working?",
            f"Can you explain '{target_term}' using simple LEGO or video game steps?",
        ]
        
        seed_text = f"{self.topic}|{teacher_input}|{len(conversation_history)}"
        idx = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest(), 16) % len(templates)
        return templates[idx]


    def respond(self, teacher_input: str, conversation_history: List[dict]) -> str:
        """Generate Leo's response to the teacher explanation."""
        clean_input = sanitize_text(teacher_input, max_length=1500)
        
        if not self.client:
            return self._offline_reply(clean_input, conversation_history)

        misconception_text = ""
        if self.misconception_mode:
            misconception_text = LEO_MISCONCEPTION_INSTRUCTION.format(topic=self.topic)

        grounding_text = ""
        if self.grounding_context or self.document_concepts:
            concepts_str = ", ".join(self.document_concepts) if self.document_concepts else "key material concepts"
            grounding_text = f"""SOURCE GROUNDING MATERIAL FOR THIS SESSION:
The teacher has uploaded study material about "{self.topic}".
Key concepts in the document: {concepts_str}.

Grounding context snippet:
"{self.grounding_context[:1000]}"

IMPORTANT: Ask questions ONLY about concepts present in this uploaded material. Do NOT ask about unrelated topics."""

        system_instruction = LEO_SYSTEM_PROMPT.format(
            topic=self.topic,
            level=self.level,
            grounding_instruction=grounding_text,
            misconception_instruction=misconception_text,
        )


        contents = []
        for msg in conversation_history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            clean_msg = sanitize_text(msg["content"], max_length=1500)
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=clean_msg)]
            ))
        
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=clean_input)]
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
            print(f"Leo Agent warning: API call failed safely - {type(e).__name__}")
            return self._offline_reply(clean_input, conversation_history)
