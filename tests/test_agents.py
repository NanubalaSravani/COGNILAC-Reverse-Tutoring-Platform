import unittest
from core.agents import LeoAgent, sanitize_text

class TestAgents(unittest.TestCase):
    def test_sanitize_text(self):
        raw_text = "  Hello \x00 World \x1f!  "
        sanitized = sanitize_text(raw_text, max_length=10)
        self.assertNotIn("\x00", sanitized)
        self.assertLessEqual(len(sanitized), 10)

    def test_leo_agent_starter_message_preset(self):
        agent = LeoAgent(topic="Photosynthesis", level=1)
        starter = agent.get_starter_message()
        self.assertTrue("plants" in starter.lower() or "leaves" in starter.lower())

    def test_leo_agent_starter_message_custom(self):
        agent = LeoAgent(topic="Quantum Physics", level=1)
        starter = agent.get_starter_message()
        self.assertIn("Quantum Physics", starter)

    def test_leo_agent_adaptive_response_references_teacher_input(self):
        agent = LeoAgent(topic="OLAP Operations", level=1, api_key="")
        teacher_input = "OLAP operations include roll-up, drill-down, slice, dice, and pivot."
        reply = agent.respond(teacher_input, [])
        self.assertFalse(reply.lower().startswith("what is it and how does it work"))
        self.assertTrue(any(term in reply for term in ["roll", "drill", "slice", "dice", "pivot", "OLAP"]))

if __name__ == "__main__":
    unittest.main()
