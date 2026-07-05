import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(session_attempt, concept, output_path):
    """
    Generates a beautifully styled PDF report for a session attempt using ReportLab.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Brand Colors
    PRIMARY_COLOR = colors.HexColor("#1E3A8A")  # Deep Blue
    SECONDARY_COLOR = colors.HexColor("#0D9488") # Teal
    TEXT_COLOR = colors.HexColor("#1F2937")      # Dark Grey
    BG_LIGHT = colors.HexColor("#F9FAFB")        # Off-white
    ACCENT_COLOR = colors.HexColor("#F59E0B")    # Amber
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=SECONDARY_COLOR,
        spaceAfter=25
    )
    
    heading1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=SECONDARY_COLOR,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_COLOR,
        leading=14,
        spaceAfter=8
    )
    
    body_bold_style = ParagraphStyle(
        'BodyTextBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []
    
    # Header Section
    story.append(Paragraph("Voice-Based Concept Understanding Analyser", title_style))
    story.append(Paragraph(f"Session Report - Concept: {concept.name}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Metadata Table
    meta_data = [
        [Paragraph("<b>Date & Time:</b>", body_style), Paragraph(session_attempt.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style),
         Paragraph("<b>Overall Score:</b>", body_style), Paragraph(f"<b>{session_attempt.overall_score:.1f} / 100</b>", body_style)],
        [Paragraph("<b>Audio File:</b>", body_style), Paragraph(os.path.basename(session_attempt.audio_path), body_style),
         Paragraph("<b>Speech Rate:</b>", body_style), Paragraph(f"{session_attempt.speech_rate:.1f} WPM", body_style)],
        [Paragraph("<b>Filler Words:</b>", body_style), Paragraph(str(session_attempt.filler_words_count), body_style),
         Paragraph("<b>Pause Rate:</b>", body_style), Paragraph(f"{session_attempt.pause_rate * 100:.1f}%", body_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[100, 160, 100, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E5E7EB"))
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Evaluation Scores Table
    story.append(Paragraph("Evaluation Summary", heading1_style))
    score_data = [
        ["Metric", "Score", "Rating"],
        ["Semantic Similarity", f"{session_attempt.semantic_score:.1f}%", get_rating(session_attempt.semantic_score)],
        ["Concept Completeness", f"{session_attempt.completeness_score:.1f}%", get_rating(session_attempt.completeness_score)],
        ["Fluency & Delivery", f"{session_attempt.fluency_score:.1f}%", get_rating(session_attempt.fluency_score)],
        ["Overall Evaluation", f"{session_attempt.overall_score:.1f}%", get_rating(session_attempt.overall_score)]
    ]
    score_table = Table(score_data, colWidths=[180, 120, 200])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))
    
    # Transcript Section
    story.append(Paragraph("Speech Transcript", heading1_style))
    transcript_p = Paragraph(session_attempt.transcript or "[No transcription available]", body_style)
    transcript_box = Table([[transcript_p]], colWidths=[500])
    transcript_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E5E7EB"))
    ]))
    story.append(transcript_box)
    story.append(Spacer(1, 20))
    
    # AI Qualitative Feedback
    story.append(Paragraph("Concept Understanding Feedback", heading1_style))
    try:
        feedback_dict = json.loads(session_attempt.feedback) if session_attempt.feedback else {}
    except Exception:
        feedback_dict = {}
        
    strengths = feedback_dict.get("strengths", [])
    gaps = feedback_dict.get("gaps", [])
    suggestions = feedback_dict.get("suggestions", [])
    
    story.append(Paragraph("Strengths Identified:", heading2_style))
    if strengths:
        for s in strengths:
            story.append(Paragraph(f"• {s}", body_style))
    else:
        story.append(Paragraph("None specified.", body_style))
        
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Knowledge Gaps / Missed Details:", heading2_style))
    if gaps:
        for g in gaps:
            story.append(Paragraph(f"• {g}", body_style))
    else:
        story.append(Paragraph("No major gaps found. Excellent coverage!", body_style))
        
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Suggestions for Improvement:", heading2_style))
    if suggestions:
        for sug in suggestions:
            story.append(Paragraph(f"• {sug}", body_style))
    else:
        story.append(Paragraph("Keep practicing and refining your explanation pace.", body_style))
        
    story.append(Spacer(1, 20))
    
    # Build Document
    doc.build(story)
    return output_path

def get_rating(score):
    if score >= 85:
        return "Strong Understanding"
    elif score >= 60:
        return "Moderate Understanding"
    else:
        return "Poor Understanding"
