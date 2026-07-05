import os
import json
import numpy as np
import librosa
import soundfile as sf
import google.generativeai as genai

# Setup Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def analyze_audio_features(file_path):
    """
    Extracts audio features using librosa.
    Returns a dictionary of:
    - average_pitch
    - pitch_variance
    - average_energy
    - pause_rate (percentage of silent frames)
    - duration (seconds)
    """
    try:
        # Load audio
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        if duration == 0:
            return {
                "average_pitch": 0.0,
                "pitch_variance": 0.0,
                "average_energy": 0.0,
                "pause_rate": 0.0,
                "duration": 0.0
            }
            
        # 1. Pitch estimation (YIN algorithm)
        # Voice pitch generally ranges from 50Hz to 400Hz
        f0 = librosa.yin(y, fmin=50, fmax=400, sr=sr)
        # Filter out NaN/inf or extremely low values
        f0 = f0[~np.isnan(f0)]
        f0 = f0[f0 > 0]
        
        avg_pitch = float(np.mean(f0)) if len(f0) > 0 else 0.0
        pitch_var = float(np.var(f0)) if len(f0) > 0 else 0.0
        
        # 2. RMS Energy
        rms = librosa.feature.rms(y=y)
        avg_energy = float(np.mean(rms))
        
        # 3. Pause Analysis
        # Determine silence threshold (e.g. 10% of max energy or -30dB)
        # Using a simple energy threshold
        db_rms = librosa.amplitude_to_db(rms, ref=np.max)
        silence_threshold_db = -30  # dB
        silent_frames = np.sum(db_rms < silence_threshold_db)
        total_frames = len(db_rms[0]) if len(db_rms.shape) > 1 else len(db_rms)
        pause_rate = float(silent_frames / total_frames) if total_frames > 0 else 0.0
        
        return {
            "average_pitch": avg_pitch,
            "pitch_variance": pitch_var,
            "average_energy": avg_energy,
            "pause_rate": pause_rate,
            "duration": duration
        }
    except Exception as e:
        print(f"Error extracting audio features: {e}")
        return {
            "average_pitch": 0.0,
            "pitch_variance": 0.0,
            "average_energy": 0.0,
            "pause_rate": 0.0,
            "duration": 5.0  # default fallback
        }

def count_filler_words(text):
    """
    Count occurrence of common speech filler words.
    """
    fillers = ["um", "uh", "like", "you know", "actually", "basically", "so"]
    words = text.lower().replace(",", "").replace(".", "").split()
    count = 0
    for w in words:
        if w in fillers:
            count += 1
    return count

def evaluate_concept_with_gemini(audio_file_path, reference_concept_name, reference_concept_text, keywords_list):
    """
    Evaluates the concept understanding using Gemini API by sending the audio.
    If Gemini API key is missing or calls fail, fall back to mock response.
    """
    if not api_key:
        return get_mock_evaluation(reference_concept_name, reference_concept_text, keywords_list)

    try:
        # Upload the audio file to Gemini File API
        print(f"Uploading file {audio_file_path} to Gemini...")
        audio_file = genai.upload_file(path=audio_file_path)
        
        # Select appropriate model supporting audio input
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
        Analyze this audio recording of a user explaining the concept: '{reference_concept_name}'.
        Compare their explanation to the reference explanation:
        "{reference_concept_text}"
        
        Expected key details/keywords: {', '.join(keywords_list)}

        Task:
        1. Transcribe the audio recording exactly as spoken.
        2. Evaluate the quality of the conceptual explanation:
           - Semantic Score (0 to 100): How closely their explanation aligns with the definition and reference text.
           - Completeness Score (0 to 100): How many of the expected key details/keywords they correctly explained.
           - Overall Score (0 to 100): Average score weighing semantics and completeness.
        3. Provide structured qualitative feedback:
           - Strengths: What parts did they explain correctly.
           - Gaps: What critical aspects or keywords did they miss.
           - Suggestions: Concrete advice for improving their conceptual explanation next time.

        Return the response strictly as a JSON object with this exact format:
        {{
          "transcript": "transcribed text here",
          "semantic_score": 85,
          "completeness_score": 75,
          "overall_score": 80,
          "feedback": {{
             "strengths": ["strength 1", "strength 2"],
             "gaps": ["gap 1", "gap 2"],
             "suggestions": ["suggestion 1", "suggestion 2"]
          }}
        }}
        """
        
        print("Sending request to Gemini...")
        response = model.generate_content(
            [audio_file, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Cleanup uploaded file
        try:
            genai.delete_file(name=audio_file.name)
        except Exception as delete_err:
            print(f"Failed to delete Gemini file: {delete_err}")
            
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        print(f"Gemini evaluation failed: {e}. Falling back to mock evaluation.")
        return get_mock_evaluation(reference_concept_name, reference_concept_text, keywords_list)

def get_mock_evaluation(concept_name, reference_text, keywords_list):
    """
    Mock evaluation return value.
    """
    mock_transcript = f"Here is my explanation of {concept_name}. I think it is very important because it helps us process data, use servers on the internet and make decisions with custom algorithms. That is my summary."
    
    # Calculate simple mockup scores
    matched_keywords = [k for k in keywords_list if k.lower() in mock_transcript.lower()]
    completeness = int((len(matched_keywords) / max(len(keywords_list), 1)) * 100)
    semantic = 70  # default mock similarity
    
    overall = int((completeness + semantic) / 2)
    
    return {
        "transcript": mock_transcript,
        "semantic_score": semantic,
        "completeness_score": completeness,
        "overall_score": overall,
        "feedback": {
            "strengths": [
                "Mentioned key elements of the concept.",
                "Used clear sentence structure."
            ],
            "gaps": [
                f"Missed describing key details such as: {[k for k in keywords_list if k not in matched_keywords]}."
            ],
            "suggestions": [
                "Try to explain the concept more comprehensively next time.",
                "Review the reference definition to cover all core criteria."
            ]
        }
    }
