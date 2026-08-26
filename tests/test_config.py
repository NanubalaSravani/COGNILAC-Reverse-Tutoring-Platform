import unittest
from core.config import PRESET_TOPICS, find_preset_topic, get_api_key

class TestConfig(unittest.TestCase):
    def test_preset_topics_not_empty(self):
        self.assertGreaterEqual(len(PRESET_TOPICS), 4)
        self.assertIn("🌱 Photosynthesis", PRESET_TOPICS)

    def test_find_preset_topic_lookup(self):
        # Test lookup by clean title
        photo = find_preset_topic("Photosynthesis")
        self.assertIsNotNone(photo)
        self.assertEqual(photo["title"], "Photosynthesis")

        # Test lookup by emoji key
        ml = find_preset_topic("🤖 Machine Learning")
        self.assertIsNotNone(ml)
        self.assertEqual(ml["title"], "Machine Learning")

        # Test invalid lookup
        none_result = find_preset_topic("NonexistentTopicX")
        self.assertIsNone(none_result)

    def test_get_api_key_priority(self):
        self.assertEqual(get_api_key("  ui_key_123  "), "ui_key_123")

if __name__ == "__main__":
    unittest.main()
