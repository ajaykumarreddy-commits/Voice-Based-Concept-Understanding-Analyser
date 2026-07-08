# Voice-Based Concept Understanding Analyser (VBCUA)

Voice-Based Concept Understanding Analyser (VBCUA) is an AI-powered web application designed to evaluate how effectively users understand and explain technical concepts through spoken communication. 

The platform combines speech-to-text transcription, semantic similarity analysis, digital signal processing (DSP) feature extraction, and intelligent scoring mechanisms to assess both the conceptual clarity and fluency of speech delivery.

---

## 🏗️ Architecture Overview

The project is structured with a decoupled FastAPI backend and a Streamlit frontend client:

```text
/Users/harsha/projects/vbcua/
├── backend/
│   ├── database.py       # SQLAlchemy models, SQLite configuration, and seed concepts
│   ├── analyzer.py       # Audio feature extraction (Librosa) and AI evaluation (Gemini)
│   ├── report_generator.py # PDF report building (ReportLab)
│   └── main.py           # FastAPI endpoints (Concepts, Evaluation, History, PDF Reports)
├── frontend/
│   └── app.py            # Streamlit dashboard interface & interactive charts
├── venv/                 # Python Virtual Environment
├── uploads/              # Temporary folder for user-recorded/uploaded voice files
├── reports/              # Storage directory for compiled PDF feedback reports
├── vbcua.db              # SQLite Database file
└── README.md             # Project documentation
```

---

## ⚡ Setup & Installation

### 1. Prerequisites
- Python 3.10 or higher
- System libraries required by `librosa` and `soundfile` (pre-installed on macOS)

### 2. Create Virtual Environment & Install Dependencies
Navigate to the project directory and set up Python dependencies:
```bash
cd /Users/harsha/projects/vbcua
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy librosa soundfile reportlab matplotlib plotly google-generativeai python-multipart pydantic jinja2 streamlit
```

---

## 🚀 How to Run the Application

The application requires running both the FastAPI backend server and the Streamlit frontend client.

### 1. Launch the Backend API
Start the Uvicorn web server:
```bash
cd /Users/harsha/projects/vbcua
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
*The API docs will be interactive and accessible at [http://localhost:8000/docs](http://localhost:8000/docs).*

### 2. Launch the Streamlit Frontend Client
In a new terminal window/tab, launch the dashboard:
```bash
cd /Users/harsha/projects/vbcua
source venv/bin/activate
streamlit run frontend/app.py --server.port 8501
```
*Open your web browser to [http://localhost:8501](http://localhost:8501) to begin using the application.*

---

## 🎙️ How to Use VBCUA

1. **Select a Concept**: In the sidebar, select a concept (e.g. *Machine Learning*, *Cloud Computing*, *Database Indexing*). Review the expected keywords and definitions.
2. **Submit Explanation**: Record your voice directly in the browser using the mic widget, or upload a pre-recorded WAV/MP3 file.
3. **Analyze**: Click the **Analyze Explanation** button.
4. **View Evaluation (Tab 1)**: Inspect your composite scores, transcripts, and AI-generated feedback (Strengths & Knowledge Gaps).
5. **Analyze Signal Fluency (Tab 2)**: View audio signal metrics (Speech Rate in WPM, Filler Words count, Silence Pause Ratio) and zoomable DSP charts (Waveform & Mel-Spectrogram).
6. **Download PDF & Track Progress (Tab 3)**: Download official PDF reports and track your conceptual mastery trends over time in real time.

---

## 🔑 Configure Gemini API (Optional)

The application includes a fully functional offline mock fallback mode. To utilize real AI speech evaluation and transcriptions, pass your Google Gemini API Key as an environment variable when launching the backend:

```bash
GEMINI_API_KEY="your_api_key_here" uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
