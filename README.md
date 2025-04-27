# CourtCaseVibe

**Automated Court Hearing Transcription & Statute Verification**

---

## Introduction

CourtCaseVibe is a web-based prototype that allows users to upload court hearing audio, automatically transcribe the content, extract and identify statute references, and cross-reference them against an official legal-statute database. The system flags transcription discrepancies and potential misrepresentations of law, enabling more accurate and efficient legal review. Live cross-referencing with the Florida Statutes site (`http://www.leg.state.fl.us/statutes/`) is supported via a built-in scraper and caching mechanism.

---

## Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/CourtCaseVibe.git
   cd CourtCaseVibe
   ```

2. **Set up the environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate       # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the backend server**
   ```bash
   # If using FastAPI
   uvicorn app.main:app --reload

   # Or if using Flask
   flask run
   ```

4. **Serve the frontend**
   - If React:
     ```bash
     cd frontend
     npm install
     npm start
     ```
   - If plain HTML/CSS/JS, open `frontend/index.html` in your browser.

5. **Use the app**
   - Navigate to `http://localhost:3000` (or the port your frontend uses).
   - Upload a court hearing audio file (.mp3, .wav, etc.).
   - Wait for transcription to complete—Whisper will generate the text.
   - View the transcript with highlighted statute references.
   - Review flagged discrepancies where transcript mentions diverge from the statute database.
   - **Live Statute Lookup:** The app fetches and caches official Florida Statute text for each reference from `http://www.leg.state.fl.us/statutes/` and displays semantic match scores and discrepancy flags.
   - Download a summary report (JSON or PDF) of findings via the “Download Report” button.

---

## Deployment

CourtCaseVibe currently runs locally but can be deployed to any cloud service. Example with Heroku:

```bash
# Create Procfile
echo "web: uvicorn app.main:app --host=0.0.0.0 --port=\$PORT" > Procfile

# Login & create app
heroku login
heroku create your-app-name

# Push code & scale
git push heroku main
heroku ps:scale web=1

# Open deployed app
heroku open
```

Once deployed, use the provided URL (e.g., `https://your-app-name.herokuapp.com`) to access the full transcription and live Florida Statutes cross-reference functionality.

---

## Project Phases & Version Control

See `INSTRUCTIONS.md` for the detailed phase-by-phase to-do list. Remember to commit often:

```bash
git add .
git commit -m "Phase X: [short description]"
git push origin main
```

---

## Future Improvements

- Expand statute coverage across all jurisdictions
- Fine-tune NER and similarity thresholds
- Integrate full case-law documents
- Enhance UI/UX and multi-language support

---

> Built with VS Code’s Agent + Vibe Coding, Python, Whisper, SpaCy, Transformers, and React/Flask (or FastAPI).
