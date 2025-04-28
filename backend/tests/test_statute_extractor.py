"""
Tests for the statute extractor service
"""
import unittest
import sys
import os
import re
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.statute_extractor import StatuteExtractor

class TestStatuteExtractor(unittest.TestCase):
    """Test cases for the StatuteExtractor class"""
    
    def setUp(self):
        """Set up test case"""
        self.extractor = StatuteExtractor()
        
    def test_extract_simple_statute(self):
        """Test extraction of a simple statute reference"""
        text = "According to Section 123.45, the defendant must comply with all regulations."
        statutes, _ = self.extractor.get_highlighted_json(text)
        
        # Assertions
        self.assertEqual(len(statutes), 1, "Should extract exactly one statute")
        self.assertEqual(statutes[0]["statute_id"], "123.45", "Should extract correct statute ID")
        self.assertEqual(statutes[0]["text"], "Section 123.45", "Should extract correct statute text")
        
    def test_extract_multiple_statutes(self):
        """Test extraction of multiple statute references"""
        text = "The property is regulated under Section 718.202 and Section 720.306 of Florida Statutes."
        statutes, _ = self.extractor.get_highlighted_json(text)
        
        # Assertions
        self.assertEqual(len(statutes), 2, "Should extract exactly two statutes")
        statute_ids = [s["statute_id"] for s in statutes]
        self.assertIn("718.202", statute_ids, "Should extract first statute ID")
        self.assertIn("720.306", statute_ids, "Should extract second statute ID")
        
    def test_extract_abbreviated_statutes(self):
        """Test extraction of abbreviated statute references"""
        text = "As stated in s. 316.193, F.S., driving under the influence is prohibited."
        statutes, _ = self.extractor.get_highlighted_json(text)
        
        # Assertions
        self.assertEqual(len(statutes), 1, "Should extract exactly one statute")
        self.assertEqual(statutes[0]["statute_id"], "316.193", "Should extract correct statute ID")
        
    def test_highlighting(self):
        """Test that highlighting produces valid HTML with correct tags"""
        text = "According to Section 123.45, the defendant must comply with all regulations."
        _, highlighted = self.extractor.get_highlighted_json(text)
        
        # Check that the HTML has the right format
        self.assertTrue("<span class=\"statute-reference\"" in highlighted, 
                      "Should contain the statute-reference span")
        self.assertTrue("data-statute-id=\"123.45\"" in highlighted,
                      "Should contain the statute ID as a data attribute")
        
        # Verify that the spans are balanced
        open_spans = len(re.findall(r'<span', highlighted))
        close_spans = len(re.findall(r'</span>', highlighted))
        self.assertEqual(open_spans, close_spans, "Should have balanced opening and closing span tags")
        
    def test_no_statutes(self):
        """Test handling of text with no statute references"""
        text = "This text contains no statute references whatsoever."
        statutes, highlighted = self.extractor.get_highlighted_json(text)
        
        # Assertions
        self.assertEqual(len(statutes), 0, "Should extract zero statutes")
        self.assertEqual(text, highlighted, "Highlighted text should be identical to original when no statutes")

if __name__ == '__main__':
    unittest.main()
