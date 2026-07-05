import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:////Users/harsha/projects/vbcua/vbcua.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    reference_text = Column(Text, nullable=False)
    keywords = Column(Text, nullable=True)  # JSON list of keywords

class SessionAttempt(Base):
    __tablename__ = "session_attempts"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    audio_path = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    
    # Similarity and Scoring
    semantic_score = Column(Float, default=0.0)      # 0 to 100
    completeness_score = Column(Float, default=0.0)  # 0 to 100
    fluency_score = Column(Float, default=0.0)       # 0 to 100
    overall_score = Column(Float, default=0.0)       # 0 to 100
    
    # Audio Feature Metrics
    speech_rate = Column(Float, default=0.0)         # Words per minute
    filler_words_count = Column(Integer, default=0)
    pause_rate = Column(Float, default=0.0)          # Pauses per minute or percentage of silence
    average_pitch = Column(Float, default=0.0)       # Hz
    pitch_variance = Column(Float, default=0.0)
    average_energy = Column(Float, default=0.0)
    
    # Detailed feedback in JSON format
    feedback = Column(Text, nullable=True)

    concept = relationship("Concept")

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed concepts if database is empty
        if db.query(Concept).count() == 0:
            seed_concepts = [
                Concept(
                    name="Machine Learning",
                    reference_text="Machine learning is a subfield of artificial intelligence focused on building systems that learn from data, identify patterns, and make decisions with minimal human intervention. It involves algorithms, training datasets, and features to train predictive models.",
                    keywords=json.dumps(["artificial intelligence", "data", "patterns", "decisions", "algorithms", "predictive models"])
                ),
                Concept(
                    name="Cloud Computing",
                    reference_text="Cloud computing is the delivery of on-demand computing services over the internet on a pay-as-you-go basis. These services include servers, storage, databases, networking, software, and analytics, offering flexible resources and economies of scale.",
                    keywords=json.dumps(["on-demand", "internet", "servers", "storage", "databases", "networking", "pay-as-you-go"])
                ),
                Concept(
                    name="Database Indexing",
                    reference_text="Database indexing is a data structure technique used to quickly locate and access data in a database table without scanning the entire table. It improves query performance and retrieval speeds, typically using structures like B-Trees or Hash tables, at the cost of write speed and storage.",
                    keywords=json.dumps(["data structure", "query performance", "retrieval", "B-Tree", "scanning", "write speed"])
                )
            ]
            db.add_all(seed_concepts)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
