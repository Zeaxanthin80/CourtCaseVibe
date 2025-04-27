# CourtCaseVibe To-Do List

---

**Objective:**  
Create a web app that:
- Uploads court hearing audio files
- Transcribes the audio to text (using Whisper)
- Extracts statute references (using SpaCy and legal NER models)
- Cross-references statutes with the official Florida Statutes site (http://www.leg.state.fl.us/statutes/) via scraping
- Flags discrepancies, inaccuracies, or low semantic match scores
- Allows downloading of a summary report

---

## **Phase 1: Environment & Dependencies**

---

**Task:**
Set up the Python virtual environment and install the core libraries for transcription, NER, and web backend.

**Instructions:**
1. Create the GitHub repository for the project:  
   - Go to GitHub and create a new repository called `CourtCaseVibe`.
   - Copy the repository URL for later use.
   
2. Initialize the Git repository locally:  
   ```bash
   git init
   git remote add origin <your-github-repo-url>
   git commit --allow-empty -m "Initial commit"
   ```

3. Create the Python virtual environment inside the `backend/` directory.
4. Install the following libraries and add them to `requirements.txt`:
   - `openai-whisper`
   - `spacy`
   - `transformers`
   - `fastapi`
   - `uvicorn`
   - `requests`
   - `beautifulsoup4`
5. Generate `.gitignore` to exclude virtual environment files and unnecessary artifacts.

**Expected Files:**
- `backend/requirements.txt`
- `.gitignore`

**Commit Message:**  
"Set up virtual environment and install core libraries"

---

## **Phase 2: Audio Upload & Transcription**

---

**Task:**
Implement the feature to upload audio files and transcribe them using Whisper.

**Instructions:**
1. Implement a backend FastAPI (or Flask) route to handle file uploads.
2. In the backend, integrate the `openai-whisper` model to transcribe the audio.
3. Return the transcription/s to the frontend for display (separated by hearing and trial dates).
4. Create a simple form in the frontend for uploading audio files with a "+" option to add more than one for each hearing and trial date.

**Expected Files:**
- `backend/app/main.py` (with the file upload route and transcription logic)
- `frontend/index.html` (or React component with upload form)

**Commit Message:**  
"Implement audio upload and transcription feature"

---

## **Phase 3: Statute Extraction & NER**

---

**Task:**
Extract statute references from the transcript using SpaCy and display them.

**Instructions:**
1. Load the SpaCy legal NER model in the backend.
2. Process the transcription to extract statute references (e.g., "Section 32B").
3. Highlight extracted references in the transcript displayed on the frontend.

**Expected Files:**
- `backend/app/main.py` (with SpaCy processing logic)
- `frontend/index.html` (with highlights for statute references)

**Commit Message:**  
"Integrate SpaCy for statute extraction and NER"

---

## **Phase 4: Statute Database & Cross-Referencing**

---

**Task:**
Create a small local statutes database and implement a lookup service to cross-reference extracted statutes.

**Instructions:**
1. Gather or simulate a small statutes database (e.g., JSON or SQLite).
2. Implement a service to query the statutes database by reference.
3. Compute semantic similarity between transcript references and statute text using `Sentence-BERT`.
4. Flag discrepancies or low-similarity matches.
5. Display flagged references on the frontend with an alert or color highlight.

**Expected Files:**
- `backend/app/services/statute_lookup.py` (with lookup and similarity logic)
- `frontend/index.html` (with alerts for flagged discrepancies)

**Commit Message:**  
"Add statute lookup and semantic comparison functionality"

---

### **Live Statute Lookup Enhancement**

---

**Task:**
Add the ability to fetch statutes in real-time from the Florida Statutes website (`http://www.leg.state.fl.us/statutes/`).

**Instructions:**
1. Implement a web scraper or API client to fetch live statute text based on extracted references.
2. Normalize and cache fetched statute texts in a local database for faster subsequent lookups.
3. Integrate this functionality into the backend service for real-time comparison.
  - Build statute URL patterns (e.g., `.../0456.013.html`)
  - Fetch and semantically match against transcript mentions

**Expected Files:**
- `backend/app/services/statute_lookup.py` (with web scraping and caching logic)

**Commit Message:**  
"Implement live Florida Statutes lookup and caching"

---

## **Phase 5: Reporting & Export**

---

**Task:**
Generate a summary report and add a download button on the frontend.

**Instructions:**
1. Generate a JSON or PDF report summarizing:
   - Transcription accuracy metrics
   - List of statute references with match scores
   - Discrepancy flags
2. Create a “Download Report” button in the frontend to allow users to export the report.

**Expected Files:**
- `backend/app/services/report_generation.py` (with report generation logic)
- `frontend/index.html` (with the download button and report functionality)

**Commit Message:**  
"Add summary report generation and export functionality"

---

## **Phase 6: Testing & Refinement**

---

**Task:**
Test the app with multiple court hearing samples and refine the functionality.

**Instructions:**
1. Test with several court audio files and check for transcription accuracy and statute matching.
2. Refine the NER model’s statute extraction thresholds.
3. Adjust the similarity score thresholds for statute matches.
4. Improve UI/UX (styling, responsiveness).

**Expected Files:**
- `backend/tests/test_transcription.py` (for testing the transcription feature)
- `frontend/styles.css` (for UI improvements)

**Commit Message:**  
"Finalize testing, UI polish, and feature refinement"

---

### **Phase 7: Documentation & Demo**

---

**Task:**
Prepare final documentation and an optional demo video.

**Instructions:**
1. Write the final 1–2 page project report detailing:
   - Problem statement
   - Tools & models used
   - Integration and workflow
   - Challenges faced and solutions
   - Future improvements
2. Record a short demo video (under 3 minutes) walking through the app.
3. Add the final README to the repository.

**Expected Files:**
- `README.md` (final version, read and update as needed)
- Demo video file (optional)

**Commit Message:**  
"Add final documentation, report, and optional demo video"

---



