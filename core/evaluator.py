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


from core.agents import sanitize_text, _get_cached_client

class EvaluatorAgent:
    def __init__(self, api_key: str = None):
        self.api_key = get_api_key(api_key)
        self.client = _get_cached_client(self.api_key)

    def _evaluate_offline(
        self,
        topic: str,
        explanation: str,
        level: int,
        misconception_active: bool,
        document_concepts: List[str] = None,
    ) -> EvaluationResult:
        """Dynamic heuristic evaluator when running in offline mode without Gemini API key."""
        text = explanation.lower()
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # 1. Simplicity based on avg word length
        avg_word_len = sum(len(w) for w in words) / max(1, word_count)
        if avg_word_len <= 4.5:
            simplicity = 92
        elif avg_word_len <= 5.5:
            simplicity = 82
        elif avg_word_len <= 6.5:
            simplicity = 70
        else:
            simplicity = 55

        # 2. Causal Reasoning
        causal_words = ["because", "so", "causes", "leads to", "due to", "why", "helps", "creates", "turns into", "results"]
        causal_matches = sum(1 for cw in causal_words if cw in text)
        causal_reasoning = min(95, 60 + (causal_matches * 12))

        # 3. Document Concept Alignment
        doc_concepts = document_concepts or []
        if doc_concepts:
            mastered = [c for c in doc_concepts if c.lower() in text or any(w in text for w in c.lower().split())]
            gaps = [c for c in doc_concepts if c not in mastered]
            
            if not mastered:
                mastered = [f"{topic} intro"]
            if not gaps:
                gaps = ["Advanced edge cases"]
                
            primary_gap = f"Difference and mechanism of {gaps[0]}" if gaps else "Deepen causal steps."
            next_chall = f"Can you explain {gaps[0]} using a simple 10-year-old example?" if gaps else "What happens next in this process?"
            concept_coverage = int((len(mastered) / max(1, len(doc_concepts))) * 100)
            factual_accuracy = min(95, max(60, concept_coverage))
        else:
            mastered = [f"{topic} core concept"] if word_count >= 10 else [f"Basic {topic} intro"]
            gaps = ["Deeper systemic limits"] if word_count >= 15 else ["Causal step sequence", "Everyday analogy"]
            primary_gap = f"Missing specific cause-and-effect mechanism for {topic}." if causal_matches == 0 else "Focus on deepening real-world playground examples."
            next_chall = f"What would happen if {topic} inputs were cut in half?"
            word_length_factor = min(30, word_count // 3)
            factual_accuracy = min(95, 65 + word_length_factor)

        conceptual_understanding = int((factual_accuracy * 0.6) + (causal_reasoning * 0.4))

        # 4. Jargon Detection
        jargon_candidates = ["photosynthesis", "algorithm", "bandwidth", "encryption", "chlorophyll", "neural network", "cryptographic", "olap", "multidimensional"]
        detected_jargon = [j for j in jargon_candidates if j in text and not any(exp in text for exp in ["like", "means", "is when", "called"])]
        jargon_independence = max(40, 95 - (len(detected_jargon) * 20))
        
        level_change = 0
        score_estimate = int(factual_accuracy * 0.3 + conceptual_understanding * 0.25 + causal_reasoning * 0.2 + simplicity * 0.15 + jargon_independence * 0.1)
        if score_estimate >= 82 and level < 5:
            level_change = 1
        elif score_estimate < 60 and level > 1:
            level_change = -1

        result = EvaluationResult(
            factual_accuracy=factual_accuracy,
            conceptual_understanding=conceptual_understanding,
            causal_reasoning=causal_reasoning,
            simplicity=simplicity,
            jargon_independence=jargon_independence,
            jargon_detected=detected_jargon,
            mastered_concepts=mastered[:3],
            knowledge_gaps=gaps[:3],
            primary_knowledge_gap=primary_gap,
            misconception_detected=misconception_active,
            teacher_corrected_misconception=misconception_active and any(w in text for w in ["no", "not", "actually", "instead", "incorrect"]),
            misconception_feedback="Successfully addressed student misconception in explanation." if misconception_active else "",
            actionable_feedback="Try using a playground analogy to explain the cause-and-effect step." if simplicity < 80 else "Great simple breakdown! Ask Leo what step comes next.",
            next_challenge=next_chall,
            level_change=level_change,
        )
        result.compute_mastery_deterministically()
        return result

    def evaluate_turn(
        self,
        topic: str,
        teacher_explanation: str,
        conversation_history: List[dict],
        level: int = 1,
        misconception_active: bool = False,
        use_search_grounding: bool = False,
        grounding_context: str = "",
        document_concepts: List[str] = None,
    ) -> EvaluationResult:
        """Evaluates the teacher's latest explanation in parallel."""
        clean_topic = sanitize_text(topic, max_length=100)
        clean_explanation = sanitize_text(teacher_explanation, max_length=1500)

        if not self.client:
            return self._evaluate_offline(clean_topic, clean_explanation, level, misconception_active, document_concepts)

        grounding_text = ""
        if grounding_context or document_concepts:
            concepts_str = ", ".join(document_concepts) if document_concepts else "key study material concepts"
            grounding_text = f"""SOURCE GROUNDING STUDY MATERIAL FOR EVALUATION:
Uploaded Document Topic: "{clean_topic}"
Key Concepts in Material: {concepts_str}.

Relevant Study Material Excerpt:
"{grounding_context[:1200]}"

EVALUATION RULE: Compare the Teacher's explanation strictly against the uploaded study material above. Identify concepts explained vs missing from this document."""

        system_instruction = EVALUATOR_SYSTEM_PROMPT.format(
            topic=clean_topic,
            level=max(1, min(5, level)),
            misconception_active=misconception_active,
            grounding_instruction=grounding_text,
        )


        history_summary = []
        for msg in conversation_history[-4:]:  # last 4 turns context
            role = "Teacher" if msg["role"] == "user" else "Leo"
            clean_msg = sanitize_text(msg["content"], max_length=500)
            history_summary.append(f"{role}: {clean_msg}")
        
        user_prompt = f"""Conversation Context:
{chr(10).join(history_summary)}

Latest Teacher Explanation:
"{clean_explanation}"

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
            print(f"Evaluator warning: Safe fallback triggered - {type(e).__name__}")
            return self._evaluate_offline(clean_topic, clean_explanation, level, misconception_active)
