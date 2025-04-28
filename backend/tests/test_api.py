"""
Tests for the FastAPI application endpoints
"""
import unittest
import sys
import os
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

class TestAPI(unittest.TestCase):
    """Test cases for the FastAPI application endpoints"""
    
    def setUp(self):
        """Set up test client and mocks"""
        self.client = TestClient(app)
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test audio file
        self.test_audio_path = os.path.join(self.temp_dir.name, "test_audio.mp3")
        with open(self.test_audio_path, "wb") as f:
            f.write(b"test audio data")  # Dummy audio data
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to CourtCaseVibe API"})
    
    @patch("app.main.get_whisper_model")
    @patch("app.main.os.makedirs")
    @patch("app.main.shutil.copyfileobj")
    def test_upload_endpoint(self, mock_copy, mock_makedirs, mock_get_model):
        """Test the audio upload endpoint"""
        # Prepare test data
        with open(self.test_audio_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            data = {"hearing_date": "2025-04-27"}
            
            # Make the request
            response = self.client.post("/upload/", files=files, data=data)
        
        # Check response
        self.assertEqual(response.status_code, 201)
        json_data = response.json()
        self.assertIn("file_id", json_data)
        self.assertEqual(json_data["hearing_date"], "2025-04-27")
        self.assertEqual(json_data["filename"], "test_audio.mp3")
    
    @patch("app.main.get_whisper_model")
    @patch("app.main.os.listdir")
    def test_transcribe_endpoint(self, mock_listdir, mock_get_model):
        """Test the transcribe endpoint"""
        # Mock the Whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "This is a test transcription mentioning Section 123.45 of Florida Statutes."}
        mock_get_model.return_value = mock_model
        
        # Mock file listing
        mock_listdir.return_value = ["test_file_id.mp3"]
        
        # Mock statute extraction to avoid dependence on SpaCy
        with patch("app.main.statute_extractor.get_highlighted_json") as mock_extract:
            # Return some dummy statutes and highlighted text
            mock_extract.return_value = (
                [{"statute_id": "123.45", "start_idx": 41, "end_idx": 53, "text": "Section 123.45", "match_type": "regex"}],
                "This is a test transcription mentioning <span class=\"statute-reference\" data-statute-id=\"123.45\">Section 123.45</span> of Florida Statutes."
            )
            
            # Mock statute lookup to avoid web requests
            with patch("app.main.statute_lookup.batch_process_statutes") as mock_lookup:
                mock_lookup.return_value = [{
                    "statute_id": "123.45",
                    "transcript_text": "Section 123.45",
                    "statute_text": "This is the official text of statute 123.45",
                    "similarity_score": 0.85,
                    "is_discrepancy": False,
                    "url": "http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0100-0199/0123/Sections/0123.45.html",
                    "title": "Some Legal Requirement"
                }]
                
                # Make the request
                response = self.client.post(
                    "/transcribe/",
                    json={"hearing_date": "2025-04-27", "file_ids": ["test_file_id"]}
                )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data), 1)
        self.assertIn("transcription", json_data[0])
        self.assertIn("highlighted_transcription", json_data[0])
        self.assertIn("statutes", json_data[0])
        self.assertIn("statute_comparisons", json_data[0])
        
        # Verify extracted statute
        statutes = json_data[0]["statutes"]
        self.assertEqual(len(statutes), 1)
        self.assertEqual(statutes[0]["statute_id"], "123.45")
    
    @patch("app.main.statute_lookup.fetch_statute")
    def test_statute_endpoint(self, mock_fetch):
        """Test the statute lookup endpoint"""
        # Mock the statute lookup
        mock_fetch.return_value = {
            "statute_id": "123.45",
            "text": "This is the official text of statute 123.45",
            "url": "http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0100-0199/0123/Sections/0123.45.html",
            "title": "Some Legal Requirement",
            "cached": True,
            "last_updated": "2025-04-27T12:00:00"
        }
        
        # Make the request
        response = self.client.get("/statute/123.45")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["statute_id"], "123.45")
        self.assertEqual(json_data["title"], "Some Legal Requirement")
        self.assertTrue(json_data["cached"])
    
    @patch("app.main.report_generator.generate_json_report")
    def test_generate_json_report(self, mock_generate):
        """Test the report generation endpoint for JSON reports"""
        # Mock the report generation
        mock_generate.return_value = "/tmp/report_12345.json"
        
        # Make the request
        response = self.client.post(
            "/generate-report",
            json={
                "format": "json",
                "transcriptions": [
                    {
                        "file_id": "test_file_id",
                        "hearing_date": "2025-04-27",
                        "transcription": "Test transcription",
                        "highlighted_transcription": "Test <span>transcription</span>",
                        "statutes": [],
                        "statute_comparisons": []
                    }
                ],
                "metadata": {"test": "data"}
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["format"], "json")
        self.assertIn("download_link", json_data)
        self.assertIn("/download-report/", json_data["download_link"])
    
    @patch("app.main.report_generator.generate_pdf_report")
    def test_generate_pdf_report(self, mock_generate):
        """Test the report generation endpoint for PDF reports"""
        # Mock the report generation
        mock_generate.return_value = "/tmp/report_12345.pdf"
        
        # Make the request
        response = self.client.post(
            "/generate-report",
            json={
                "format": "pdf",
                "transcriptions": [
                    {
                        "file_id": "test_file_id",
                        "hearing_date": "2025-04-27",
                        "transcription": "Test transcription",
                        "highlighted_transcription": "Test <span>transcription</span>",
                        "statutes": [],
                        "statute_comparisons": []
                    }
                ],
                "metadata": {"test": "data"}
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["format"], "pdf")
        self.assertIn("download_link", json_data)

if __name__ == '__main__':
    unittest.main()
