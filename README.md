# CourtCaseVibe

**Court Audio Transcription, Statute Analysis, and Verification System**

CourtCaseVibe is a comprehensive system for transcribing court hearing audio, extracting statutory references, verifying them against the Florida Statutes, and generating detailed reports.

## Features

- **Audio Upload & Transcription**: Upload court hearing audio files and get accurate transcriptions using the WhisperAI model
- **Statute Extraction & NER**: Automatically identify references to Florida Statutes in transcriptions
- **Statute Verification**: Cross-reference extracted statute mentions with the official Florida Statutes website
- **Reporting & Export**: Generate comprehensive reports in PDF or JSON format
- **Testing & Quality Assurance**: Comprehensive test suite to ensure reliable operation

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/CourtCaseVibe.git
   cd CourtCaseVibe
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r backend/requirements.txt
   ```

## Running the Application

1. Start the backend server:
   ```
   cd backend
   uvicorn app.main:app --reload
   ```

2. Open the frontend in your browser:
   - Navigate to the `frontend` directory
   - Open `index.html` in your web browser

## Running Tests

The application includes a comprehensive test suite:

```
cd backend
python tests/run_tests.py
```

You can also run individual test files:

```
python -m unittest tests/test_statute_extractor.py
python -m unittest tests/test_statute_lookup.py
python -m unittest tests/test_api.py
```

## Generate Sample Data

For testing purposes, you can generate sample data:

```
cd backend
python tests/sample_data.py
```

This will create:
- Sample audio files
- Sample transcription results
- Sample reports in JSON and PDF formats

## Contact

For any questions or issues, please contact [your contact information].
