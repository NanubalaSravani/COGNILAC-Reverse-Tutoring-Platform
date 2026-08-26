import unittest
from core.evaluator import EvaluationResult, EvaluatorAgent

class TestEvaluator(unittest.TestCase):
    def test_deterministic_mastery_calculation(self):
        result = EvaluationResult(
            factual_accuracy=100,
            conceptual_understanding=100,
            causal_reasoning=100,
            simplicity=100,
            jargon_independence=100,
        )
        score = result.compute_mastery_deterministically()
        self.assertEqual(score, 100)

    def test_offline_evaluator_dynamics(self):
        agent = EvaluatorAgent(api_key="")
        simple_explanation = "Plants take sunlight and water to make food because it gives them energy."
        result = agent.evaluate_turn(
            topic="Photosynthesis",
            teacher_explanation=simple_explanation,
            conversation_history=[],
            level=1,
        )
        self.assertGreaterEqual(result.overall_mastery, 60)
        self.assertGreater(result.factual_accuracy, 0)
        self.assertGreater(result.simplicity, 0)
        self.assertGreater(len(result.mastered_concepts), 0)

if __name__ == "__main__":
    unittest.main()
