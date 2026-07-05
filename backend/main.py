import os
import sys
import shutil
import json

# Ensure parent/sibling imports work when running from project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, Concept, SessionAttempt
from analyzer import analyze_audio_features, count_filler_words, evaluate_concept_with_gemini
from report_generator import generate_pdf_report

# Initialize database
init_db()

app = FastAPI(title="Voice-Based Concept Understanding Analyser (VBCUA) Backend")

# Ensure upload and report folders exist
UPLOAD_DIR = "/Users/harsha/projects/vbcua/uploads"
REPORT_DIR = "/Users/harsha/projects/vbcua/reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/concepts")
def get_concepts(db: Session = Depends(get_db)):
    concepts = db.query(Concept).all()
    return [{
        "id": c.id,
        "name": c.name,
        "reference_text": c.reference_text,
        "keywords": json.loads(c.keywords) if c.keywords else []
    } for c in concepts]

@app.post("/api/evaluate")
async def evaluate_audio(
    file: UploadFile = File(...),
    concept_id: int = Form(...),
    db: Session = Depends(get_db)
):
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
        
    # Save uploaded file
    file_ext = os.path.splitext(file.filename)[1] or ".wav"
    temp_file_name = f"upload_{concept_id}_{os.urandom(4).hex()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, temp_file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 1. Extract audio signal features
        audio_features = analyze_audio_features(file_path)
        
        # 2. Evaluate concept understanding using Gemini / AI Engine
        keywords = json.loads(concept.keywords) if concept.keywords else []
        evaluation = evaluate_concept_with_gemini(
            audio_file_path=file_path,
            reference_concept_name=concept.name,
            reference_concept_text=concept.reference_text,
            keywords_list=keywords
        )
        
        transcript = evaluation.get("transcript", "")
        semantic_score = float(evaluation.get("semantic_score", 0))
        completeness_score = float(evaluation.get("completeness_score", 0))
        
        # 3. Fluency Calculation
        duration_min = audio_features["duration"] / 60.0 if audio_features["duration"] > 0 else 0.1
        word_count = len(transcript.split())
        speech_rate = word_count / duration_min
        filler_count = count_filler_words(transcript)
        
        # Calculate fluency score logic
        # Ideal: 130-150 words per minute, low filler words, moderate pause rate (0.1 - 0.25)
        fluency_base = 100
        # Filler word penalty
        fluency_base -= filler_count * 5
        # Speech rate variance penalty
        if speech_rate < 100:
            fluency_base -= (100 - speech_rate) * 0.5
        elif speech_rate > 170:
            fluency_base -= (speech_rate - 170) * 0.5
        # Pause rate penalty
        pause_rate = audio_features["pause_rate"]
        if pause_rate > 0.3:
            fluency_base -= (pause_rate - 0.3) * 100
        elif pause_rate < 0.05:
            fluency_base -= (0.05 - pause_rate) * 100
            
        fluency_score = max(30.0, min(100.0, fluency_base))
        overall_score = (semantic_score + completeness_score + fluency_score) / 3.0
        
        # 4. Save Attempt
        attempt = SessionAttempt(
            concept_id=concept.id,
            audio_path=file_path,
            transcript=transcript,
            semantic_score=semantic_score,
            completeness_score=completeness_score,
            fluency_score=fluency_score,
            overall_score=overall_score,
            speech_rate=speech_rate,
            filler_words_count=filler_count,
            pause_rate=pause_rate,
            average_pitch=audio_features["average_pitch"],
            pitch_variance=audio_features["pitch_variance"],
            average_energy=audio_features["average_energy"],
            feedback=json.dumps(evaluation.get("feedback", {}))
        )
        
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        
        return {
            "session_id": attempt.id,
            "concept_name": concept.name,
            "timestamp": attempt.timestamp.isoformat(),
            "transcript": attempt.transcript,
            "semantic_score": attempt.semantic_score,
            "completeness_score": attempt.completeness_score,
            "fluency_score": attempt.fluency_score,
            "overall_score": attempt.overall_score,
            "speech_rate": attempt.speech_rate,
            "filler_words_count": attempt.filler_words_count,
            "pause_rate": attempt.pause_rate,
            "feedback": evaluation.get("feedback", {})
        }
        
    except Exception as e:
        print(f"Error processing evaluation: {e}")
        # Clean up file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    attempts = db.query(SessionAttempt).order_by(SessionAttempt.timestamp.desc()).all()
    result = []
    for attempt in attempts:
        result.append({
            "id": attempt.id,
            "concept_name": attempt.concept.name if attempt.concept else "Unknown",
            "timestamp": attempt.timestamp.isoformat(),
            "overall_score": attempt.overall_score,
            "semantic_score": attempt.semantic_score,
            "completeness_score": attempt.completeness_score,
            "fluency_score": attempt.fluency_score,
            "speech_rate": attempt.speech_rate,
            "filler_words_count": attempt.filler_words_count,
            "pause_rate": attempt.pause_rate
        })
    return result

@app.get("/api/report/{session_id}")
def get_pdf_report(session_id: int, db: Session = Depends(get_db)):
    attempt = db.query(SessionAttempt).filter(SessionAttempt.id == session_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Session not found")
        
    concept = db.query(Concept).filter(Concept.id == attempt.concept_id).first()
    report_file_path = os.path.join(REPORT_DIR, f"report_{session_id}.pdf")
    
    # Generate the PDF dynamically if it doesn't exist
    if not os.path.exists(report_file_path):
        generate_pdf_report(attempt, concept, report_file_path)
        
    return FileResponse(report_file_path, media_type="application/pdf", filename=f"VBCUA_Report_{session_id}.pdf")
