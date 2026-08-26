import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from core.config import MODEL_NAME, get_api_key
from core.prompts import EVALUATOR_SYSTEM_PROMPT

class EvaluationResult(BaseModel):
    factual_accuracy: int = Field(default=80, ge=0, le=100)
    conceptual_understanding: int = Field(default=75, ge=0, le=100)
    causal_reasoning: int = Field(default=70, ge=0, le=100)
    simplicity: int = Field(default=80, ge=0, le=100)
    jargon_independence: int = Field(default=85, ge=0, le=100)
    overall_mastery: int = Field(default=78, ge=0, le=100)
    jargon_detected: List[str] = Field(default_factory=list)
    mastered_concepts: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)
    primary_knowledge_gap: str = Field(default="Need deeper causal explanation.")
    misconception_detected: bool = Field(default=False)
    teacher_corrected_misconception: bool = Field(default=False)
    misconception_feedback: str = Field(default="")
    actionable_feedback: str = Field(default="Good explanation! Try using simpler analogies.")
    next_challenge: str = Field(default="Why does this mechanism work?")
    level_change: int = Field(default=0)

    def compute_mastery_deterministically(self) -> int:
        """Deterministically calculate Overall Mastery from weighted 5 metrics."""
        score = (
            self.factual_accuracy * 0.30 +
            self.conceptual_understanding * 0.25 +
            self.causal_reasoning * 0.20 +
            self.simplicity * 0.15 +
            self.jargon_independence * 0.10
        )
        self.overall_mastery = int(round(score))
        return self.overall_mastery


class EvaluatorAgent:
    def __init__(self, api_key: str = None):
        self.api_key = get_api_key(api_key)
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def evaluate_turn(
        self,
        topic: str,
        teacher_explanation: str,
        conversation_history: List[dict],
        level: int = 1,
        misconception_active: bool = False,
        use_search_grounding: bool = False,
    ) -> EvaluationResult:
        """Evaluates the teacher's latest explanation in parallel."""
        if not self.client:
            # Fallback offline evaluation if no API key provided
            result = EvaluationResult(
                factual_accuracy=85,
                conceptual_understanding=80,
                causal_reasoning=75,
                simplicity=85,
                jargon_independence=90,
                jargon_detected=[],
                mastered_concepts=[f"{topic} basics"],
                knowledge_gaps=["Deeper mechanism details"],
                primary_knowledge_gap="Missing step-by-step cause and effect.",
                misconception_detected=misconception_active,
                teacher_corrected_misconception=misconception_active,
                misconception_feedback="Identified misconception accurately." if misconception_active else "",
                actionable_feedback="Great start! Add a simple analogy to lock in understanding.",
                next_challenge="How does this process begin?",
                level_change=1,
            )
            result.compute_mastery_deterministically()
            return result

        system_instruction = EVALUATOR_SYSTEM_PROMPT.format(
            topic=topic,
            level=level,
            misconception_active=misconception_active,
        )

        history_summary = []
        for msg in conversation_history[-4:]:  # last 4 turns context
            role = "Teacher" if msg["role"] == "user" else "Leo"
            history_summary.append(f"{role}: {msg['content']}")
        
        user_prompt = f"""Conversation Context:
{chr(10).join(history_summary)}

Latest Teacher Explanation:
"{teacher_explanation}"

Evaluate this explanation strictly across the 5 dimensions and return JSON.
"""

        tools = []
        if use_search_grounding:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            tools=tools if tools else None,
            response_mime_type="application/json",
            response_schema=EvaluationResult,
        )

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=config,
            )
            
            raw_text = response.text
            cleaned = re.sub(r"^```json\s*", "", raw_text.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned)

            data = json.loads(cleaned)
            result = EvaluationResult(**data)
            # Override LLM overall mastery with deterministic calculation
            result.compute_mastery_deterministically()
            return result
        except Exception as e:
            print(f"Evaluator warning: {e}")
            result = EvaluationResult(
                factual_accuracy=80,
                conceptual_understanding=75,
                causal_reasoning=70,
                simplicity=80,
                jargon_independence=85,
                jargon_detected=[],
                mastered_concepts=[f"{topic} concepts"],
                knowledge_gaps=["Specific causal sequence"],
                primary_knowledge_gap="Clarify how inputs convert to outputs.",
                actionable_feedback="Focus on breaking down key terms into simple steps.",
                next_challenge="What happens next in the process?",
                level_change=0,
            )
            result.compute_mastery_deterministically()
            return result
