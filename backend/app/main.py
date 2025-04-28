from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
import whisper
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time
from app.services.statute_extractor import StatuteExtractor
from app.services.statute_lookup import StatuteLookupService

app = FastAPI(title="CourtCaseVibe API", description="API for court case audio transcription and statute verification")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define storage paths
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load Whisper model (small to balance speed and accuracy)
# Note: The first time this runs, it will download the model
model = None

def get_whisper_model():
    global model
    if model is None:
        model = whisper.load_model("small")  # Options: tiny, base, small, medium, large
    return model

# Initialize the statute extractor
statute_extractor = StatuteExtractor()

# Initialize the statute lookup service
statute_lookup = StatuteLookupService()

class TranscriptionRequest(BaseModel):
    hearing_date: str
    file_ids: List[str]

class StatuteReference(BaseModel):
    statute_id: str
    start_idx: int
    end_idx: int
    text: str
    match_type: str

class StatuteComparison(BaseModel):
    statute_id: str
    transcript_text: str
    statute_text: str
    similarity_score: float
    is_discrepancy: bool
    url: str
    title: Optional[str] = None
    error: Optional[str] = None

class TranscriptionResponse(BaseModel):
    transcription: str
    highlighted_transcription: str
    file_id: str
    hearing_date: str
    statutes: List[StatuteReference]
    statute_comparisons: List[StatuteComparison] = []

@app.get("/")
async def root():
    return {"message": "Welcome to CourtCaseVibe API"}

@app.post("/upload/", status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    hearing_date: str = Form(...)
):
    if not file.filename.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
        raise HTTPException(status_code=400, detail="Only audio files are allowed")
    
    # Create a unique filename to prevent collisions
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    new_filename = f"{file_id}{file_extension}"
    
    # Save the file
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "hearing_date": hearing_date,
        "stored_path": file_path
    }

@app.post("/transcribe/")
async def transcribe_audio(request: TranscriptionRequest):
    model = get_whisper_model()
    results = []
    
    for file_id in request.file_ids:
        # Find the file with the matching ID prefix
        matching_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(file_id)]
        
        if not matching_files:
            raise HTTPException(status_code=404, detail=f"File ID {file_id} not found")
            
        file_path = os.path.join(UPLOAD_DIR, matching_files[0])
        
        # Transcribe with Whisper
        try:
            result = model.transcribe(file_path)
            transcription = result["text"]
            
            # Extract statute references using our StatuteExtractor
            statutes, highlighted_text = statute_extractor.get_highlighted_json(transcription)
            
            # Convert statutes to StatuteReference model objects
            statute_references = [
                StatuteReference(
                    statute_id=statute["statute_id"],
                    start_idx=statute["start_idx"],
                    end_idx=statute["end_idx"],
                    text=statute["text"],
                    match_type=statute["match_type"]
                ) for statute in statutes
            ]
            
            # Lookup and compare statutes with the Florida Statutes website
            statute_comparisons = []
            if statutes:
                # Prepare statute data for batch processing
                statute_data = [
                    {"statute_id": statute["statute_id"], "text": statute["text"]} 
                    for statute in statutes
                ]
                
                # Process statutes in batch
                comparison_results = statute_lookup.batch_process_statutes(statute_data)
                
                # Convert to Pydantic models
                statute_comparisons = [
                    StatuteComparison(
                        statute_id=comp["statute_id"],
                        transcript_text=comp["transcript_text"],
                        statute_text=comp["statute_text"],
                        similarity_score=comp["similarity_score"],
                        is_discrepancy=comp["is_discrepancy"],
                        url=comp["url"],
                        title=comp.get("title"),
                        error=comp.get("error")
                    ) for comp in comparison_results
                ]
            
            results.append(TranscriptionResponse(
                transcription=transcription,
                highlighted_transcription=highlighted_text,
                file_id=file_id,
                hearing_date=request.hearing_date,
                statutes=statute_references,
                statute_comparisons=statute_comparisons
            ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    
    return results

@app.get("/statute/{statute_id}")
async def get_statute(statute_id: str, force_refresh: bool = False):
    """
    Endpoint to look up a specific statute by ID
    
    Args:
        statute_id: The ID of the statute to look up (e.g., "456.013")
        force_refresh: Whether to bypass the cache and fetch fresh data
        
    Returns:
        Statute information from the Florida Statutes website
    """
    try:
        result = statute_lookup.fetch_statute(statute_id, force_refresh)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statute: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
