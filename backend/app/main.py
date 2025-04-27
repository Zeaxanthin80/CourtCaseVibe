from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
import whisper
from pydantic import BaseModel
from typing import List, Optional
import time

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

class TranscriptionRequest(BaseModel):
    hearing_date: str
    file_ids: List[str]

class TranscriptionResponse(BaseModel):
    transcription: str
    file_id: str
    hearing_date: str

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
            
            results.append(TranscriptionResponse(
                transcription=transcription,
                file_id=file_id,
                hearing_date=request.hearing_date
            ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
