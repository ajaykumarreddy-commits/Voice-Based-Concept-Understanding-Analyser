import os
import requests
import json
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import librosa
import librosa.display
import pandas as pd
import plotly.express as px

# Configuration
API_BASE_URL = "http://localhost:8000"
UPLOADS_DIR = "/Users/harsha/projects/vbcua/uploads"

# Page layout setup
st.set_page_config(
    page_title="Voice-Based Concept Understanding Analyser",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Theme Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Title and Header customization */
    .title-text {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1E3A8A 0%, #0D9488 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle-text {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    
    /* Metrics Card styling */
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-left: 5px solid #1E3A8A;
        margin-bottom: 15px;
    }
    
    .metric-card.success {
        border-left-color: #10B981;
    }
    
    .metric-card.warning {
        border-left-color: #F59E0B;
    }
    
    .metric-card.info {
        border-left-color: #3B82F6;
    }
    
    .metric-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        color: #6B7280;
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1F2937;
    }
    
    .metric-desc {
        font-size: 0.85rem;
        color: #9CA3AF;
        margin-top: 5px;
    }
    
    /* Accent banner styling */
    .banner {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# Fetch technical concepts
@st.cache_data(ttl=5)
def get_concepts():
    try:
        response = requests.get(f"{API_BASE_URL}/api/concepts")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Cannot connect to Backend API. Please start the backend service first! Details: {e}")
    return []

# Fetch History
def get_history():
    try:
        response = requests.get(f"{API_BASE_URL}/api/history")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# Sidebar Config
st.sidebar.markdown("<h2 style='color:#1E3A8A;'>🎙️ Control Panel</h2>", unsafe_allow_html=True)

concepts = get_concepts()
if not concepts:
    st.sidebar.warning("No concepts loaded. Please ensure FastAPI is running.")
    concept_names = []
else:
    concept_names = [c["name"] for c in concepts]

selected_concept_name = st.sidebar.selectbox("Select Concept to Explain", concept_names)
selected_concept = next((c for c in concepts if c["name"] == selected_concept_name), None)

if selected_concept:
    st.sidebar.markdown(f"**Reference Definition:**\n{selected_concept['reference_text']}")
    st.sidebar.markdown(f"**Keywords:** {', '.join(selected_concept['keywords'])}")

# Recording Input or Upload File
st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
st.sidebar.markdown("### Provide Your Spoken Explanation")

audio_source = st.sidebar.radio("Audio Source", ["Record Audio", "Upload Audio File"])
uploaded_audio = None

if audio_source == "Record Audio":
    # Using Streamlit 1.58+ built-in audio_input or fallback
    try:
        uploaded_audio = st.sidebar.audio_input("Record your voice:")
    except AttributeError:
        # Fallback for older streamlit versions
        uploaded_audio = st.sidebar.file_uploader("Record a WAV file locally and upload it here:", type=["wav", "mp3", "m4a"])
else:
    uploaded_audio = st.sidebar.file_uploader("Upload explanation audio:", type=["wav", "mp3", "m4a"])

# Analysis trigger
evaluate_clicked = st.sidebar.button("Analyze Explanation", type="primary", disabled=(uploaded_audio is None))

# Title Layout
st.markdown("<h1 class='title-text'>Voice-Based Concept Understanding Analyser (VBCUA)</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-text'>An intelligent system to evaluate your conceptual clarity and speech fluency using AI and DSP features.</p>", unsafe_allow_html=True)

# Main Dashboard Pages tabs
tab1, tab2, tab3 = st.tabs([
    "📊 Scenario 1: Conceptual Understanding",
    "📈 Scenario 2: Speech Fluency & DSP Visuals",
    "📜 Scenario 3: Performance History & Reports"
])

# Perform evaluation
if evaluate_clicked and uploaded_audio and selected_concept:
    with st.spinner("Processing audio, transcribing, and running AI evaluation..."):
        try:
            files = {"file": (uploaded_audio.name, uploaded_audio.read(), uploaded_audio.type)}
            data = {"concept_id": selected_concept["id"]}
            response = requests.post(f"{API_BASE_URL}/api/evaluate", files=files, data=data)
            
            if response.status_code == 200:
                st.session_state["results"] = response.json()
                st.success("Analysis complete!")
            else:
                st.error(f"Error evaluating audio: {response.text}")
        except Exception as e:
            st.error(f"Failed to communicate with backend evaluation service: {e}")

# Get state results
results = st.session_state.get("results", None)

with tab1:
    if not results:
        st.info("👈 Select a concept, record or upload your audio in the sidebar, and click 'Analyze Explanation' to start!")
    else:
        st.markdown(f"### Evaluation for Concept: **{results['concept_name']}**")
        st.caption(f"Completed at: {results['timestamp']}")
        
        # Metric Cards Layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card info'>
                <div class='metric-title'>Overall Score</div>
                <div class='metric-value'>{results['overall_score']:.1f}</div>
                <div class='metric-desc'>Composite concept & delivery index</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='metric-card success'>
                <div class='metric-title'>Semantic Score</div>
                <div class='metric-value'>{results['semantic_score']:.1f}%</div>
                <div class='metric-desc'>Accuracy compared to reference text</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class='metric-card success'>
                <div class='metric-title'>Completeness</div>
                <div class='metric-value'>{results['completeness_score']:.1f}%</div>
                <div class='metric-desc'>Key details & keywords matching</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class='metric-card warning'>
                <div class='metric-title'>Fluency Score</div>
                <div class='metric-value'>{results['fluency_score']:.1f}%</div>
                <div class='metric-desc'>Speech delivery pacing & quality</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Transcript & Feedback
        st.markdown("### Speech Transcript")
        st.info(results["transcript"])
        
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1:
            st.markdown("#### ✅ Strengths")
            for strength in results["feedback"].get("strengths", []):
                st.markdown(f"- {strength}")
                
        with col_fb2:
            st.markdown("#### 🔍 Knowledge Gaps & Improvements")
            for gap in results["feedback"].get("gaps", []):
                st.markdown(f"- {gap}")
            for sug in results["feedback"].get("suggestions", []):
                st.markdown(f"- *Suggestion:* {sug}")

with tab2:
    if not results:
        st.info("👈 Analyze an audio explanation first to view speech signals and DSP visualizations.")
    else:
        st.markdown("### Speech Signal Feature Extraction")
        
        # Audio Player
        # Try to locate the file in uploads folder
        audio_filename = f"upload_{selected_concept['id']}"
        matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(audio_filename)]
        
        if matching_files:
            latest_file = max([os.path.join(UPLOADS_DIR, f) for f in matching_files], key=os.path.getmtime)
            st.audio(latest_file)
            
            # Extract waveform for visualization
            with st.spinner("Generating signal visualizations..."):
                y, sr = librosa.load(latest_file, sr=None)
                
                # DSP stats row
                col_dsp1, col_dsp2, col_dsp3, col_dsp4 = st.columns(4)
                col_dsp1.metric("Speech Rate", f"{results['speech_rate']:.1f} WPM", help="Ideal is 130-160 Words Per Minute")
                col_dsp2.metric("Filler Words", f"{results['filler_words_count']}", help="Um, uh, like, etc.")
                col_dsp3.metric("Pause Ratio", f"{results['pause_rate'] * 100:.1f}%", help="Percentage of silence frames detected")
                
                # 1. Waveform Plot
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
                
                librosa.display.waveshow(y, sr=sr, ax=ax1, color="#1E3A8A")
                ax1.set_title("Audio Waveform (Amplitude vs. Time)")
                ax1.set_ylabel("Amplitude")
                
                # 2. Mel-Spectrogram
                S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
                S_dB = librosa.power_to_db(S, ref=np.max)
                img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax2, cmap='viridis')
                ax2.set_title("Mel-Spectrogram (Frequency vs. Time)")
                ax2.set_ylabel("Frequency (Hz)")
                fig.colorbar(img, ax=ax2, format='%+2.0f dB')
                
                st.pyplot(fig)
        else:
            st.warning("Audio file could not be retrieved locally for visualization.")

with tab3:
    st.markdown("### Performance & Session History")
    history_data = get_history()
    
    if not history_data:
        st.write("No session records found.")
    else:
        df = pd.DataFrame(history_data)
        
        # Format Date columns
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # History Table
        st.dataframe(
            df[['timestamp', 'concept_name', 'overall_score', 'semantic_score', 'completeness_score', 'fluency_score', 'speech_rate', 'filler_words_count']],
            column_config={
                "timestamp": "Timestamp",
                "concept_name": "Concept",
                "overall_score": "Overall Score",
                "semantic_score": "Semantic (%)",
                "completeness_score": "Completeness (%)",
                "fluency_score": "Fluency (%)",
                "speech_rate": "Speech Rate (WPM)",
                "filler_words_count": "Filler Words"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # PDF Report Downloads
        st.markdown("### Download PDF Reports")
        for h in history_data:
            col_h1, col_h2 = st.columns([4, 1])
            col_h1.write(f"📄 Session: **{h['concept_name']}** at {h['timestamp'][:19]} — Score: **{h['overall_score']:.1f}**")
            
            report_url = f"{API_BASE_URL}/api/report/{h['id']}"
            col_h2.markdown(f"[📥 Download PDF]({report_url})")
            
        # Progress Chart over time
        st.markdown("### Concept Mastery Timeline")
        chart_df = df.sort_values(by='timestamp')
        fig_timeline = px.line(
            chart_df,
            x='timestamp',
            y='overall_score',
            color='concept_name',
            title='Learning Curve (Overall Score over Time)',
            markers=True,
            labels={'overall_score': 'Overall Score', 'timestamp': 'Session Time'}
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
