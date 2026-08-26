import unittest
from core.document_processor import extract_text_from_file, extract_concepts_and_topic, get_relevant_chunks

class TestDocumentProcessor(unittest.TestCase):
    def test_txt_extraction(self):
        sample_txt = "OLAP Operations Guide\nRoll-up\nDrill-down\nSlice and Dice\nPivot operations."
        extracted = extract_text_from_file(sample_txt.encode('utf-8'), "olap_guide.txt")
        self.assertIn("OLAP Operations Guide", extracted)

    def test_topic_and_concept_extraction(self):
        text = """OLAP Operations in Data Warehousing
1. Roll-up
2. Drill-down
3. Slice
4. Dice
5. Pivot
OLAP cubes allow multidimensional analysis."""
        topic, concepts = extract_concepts_and_topic(text, "olap.pdf")
        self.assertEqual(topic, "OLAP Operations in Data Warehousing")
        self.assertGreaterEqual(len(concepts), 3)

    def test_chunk_retrieval(self):
        text = """Paragraph 1 about Roll-up and summarizing daily sales into monthly sales.

Paragraph 2 about Drill-down which goes from monthly sales to daily transactions.

Paragraph 3 about Slice and Dice operations."""
        chunks = get_relevant_chunks(text, query="Drill-down transactions", max_chars=300)
        self.assertIn("Drill-down", chunks)

if __name__ == "__main__":
    unittest.main()
