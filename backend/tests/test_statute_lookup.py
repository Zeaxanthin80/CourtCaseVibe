"""
Tests for the statute lookup service
"""
import unittest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.statute_lookup import StatuteLookupService

class TestStatuteLookupService(unittest.TestCase):
    """Test cases for the StatuteLookupService class"""
    
    def setUp(self):
        """Set up test cases with a temporary database"""
        # Create a temporary directory for the test database
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Initialize the lookup service with the test database
        self.lookup_service = StatuteLookupService(db_path=os.path.join(self.temp_dir.name, 'test_statutes.db'))
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    @patch('app.services.statute_lookup.requests.get')
    def test_build_statute_url(self, mock_get):
        """Test URL building for Florida statutes"""
        # Test with simple statute ID
        url = self.lookup_service.build_statute_url("123.45")
        self.assertIn("123.45", url, "URL should contain the statute ID")
        self.assertIn("www.leg.state.fl.us", url, "URL should point to Florida statutes website")
        
        # Test with chapter only
        url = self.lookup_service.build_statute_url("123")
        self.assertIn("123", url, "URL should contain the chapter number")
    
    @patch('app.services.statute_lookup.requests.get')
    def test_fetch_statute_with_cache(self, mock_get):
        """Test fetching a statute with caching"""
        # Mock the response from the website
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><div class='Statute'>Test statute text</div></body></html>"
        mock_get.return_value = mock_response
        
        # First call should hit the website
        result1 = self.lookup_service.fetch_statute("123.45")
        self.assertEqual(mock_get.call_count, 1, "Should make one request to the website")
        
        # Reset the mock to verify the second call
        mock_get.reset_mock()
        
        # Second call should use the cache
        result2 = self.lookup_service.fetch_statute("123.45")
        self.assertEqual(mock_get.call_count, 0, "Should not make another request")
        
        # Should return the same data
        self.assertEqual(result1["statute_id"], result2["statute_id"], "Cached result should have same statute ID")
        self.assertEqual(result1["text"], result2["text"], "Cached result should have same text")
        
        # Force refresh should bypass cache
        mock_get.reset_mock()
        result3 = self.lookup_service.fetch_statute("123.45", force_refresh=True)
        self.assertEqual(mock_get.call_count, 1, "Should make a request when force_refresh is True")
    
    @patch('app.services.statute_lookup.requests.get')
    def test_extract_statute_text(self, mock_get):
        """Test extracting statute text from HTML"""
        # Mock the response with a valid statute
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <h1>Title XLVI</h1>
                <h2>Chapter 316</h2>
                <div class='Statute'>
                    <span class='StatuteNum'>316.193</span>
                    <span class='StatuteTitle'>Driving under the influence</span>
                    <div class='StatuteText'>
                        <p>(1) A person is guilty of the offense of driving under the influence if:</p>
                        <p>(a) The person is driving or in actual physical control of a vehicle; and</p>
                        <p>(b) The person has a blood-alcohol level of 0.08 or more.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Fetch the statute
        result = self.lookup_service.fetch_statute("316.193")
        
        # Verify the result
        self.assertEqual(result["statute_id"], "316.193", "Should extract the correct statute ID")
        self.assertIn("Driving under the influence", result["title"], "Should extract the statute title")
        self.assertIn("person is guilty", result["text"], "Should extract the statute text")
        
        # Test with a malformed response
        mock_response.text = "<html><body>Invalid statute page</body></html>"
        result = self.lookup_service.fetch_statute("999.999")
        self.assertIn("error", result, "Should return an error for malformed response")
    
    def test_similarity_calculation(self):
        """Test calculating similarity between statute text and transcript"""
        # Simple test case
        transcript_text = "If you drive under the influence, you're guilty of DUI."
        statute_text = "A person is guilty of the offense of driving under the influence."
        
        similarity = self.lookup_service.calculate_similarity(transcript_text, statute_text)
        
        # Similarity should be relatively high for similar content
        self.assertGreater(similarity, 0.5, "Similar texts should have high similarity score")
        
        # Test with completely different texts
        different_text = "This text has nothing to do with driving or alcohol."
        diff_similarity = self.lookup_service.calculate_similarity(different_text, statute_text)
        
        # Similarity should be lower for different content
        self.assertLess(diff_similarity, similarity, "Different texts should have lower similarity")
    
    def test_batch_process_statutes(self):
        """Test batch processing of statutes"""
        with patch.object(self.lookup_service, 'fetch_statute') as mock_fetch:
            # Mock the fetch_statute method to return test data
            mock_fetch.side_effect = lambda statute_id, _: {
                "statute_id": statute_id,
                "text": f"Test statute text for {statute_id}",
                "url": f"http://test.com/{statute_id}"
            }
            
            # Create test data for batch processing
            statutes = [
                {"statute_id": "123.45", "text": "Section 123.45 says something"},
                {"statute_id": "456.78", "text": "Chapter 456.78 requires compliance"}
            ]
            
            # Process the statutes
            results = self.lookup_service.batch_process_statutes(statutes)
            
            # Verify results
            self.assertEqual(len(results), 2, "Should process all statute entries")
            self.assertEqual(results[0]["statute_id"], "123.45", "Should maintain statute IDs")
            self.assertEqual(results[1]["statute_id"], "456.78", "Should maintain statute IDs")
            self.assertTrue("similarity_score" in results[0], "Should calculate similarity scores")
            self.assertTrue("is_discrepancy" in results[0], "Should determine discrepancies")

if __name__ == '__main__':
    unittest.main()
