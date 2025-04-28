"""
Report generation service for CourtCaseVibe
Provides functionality to create PDF and JSON reports from transcription data
"""
import json
import os
import datetime
from typing import Dict, List, Any
from pathlib import Path

# For PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

class ReportGenerator:
    """
    Service for generating reports from CourtCaseVibe transcription data
    """
    
    def __init__(self):
        """Initialize the report generator"""
        # Create reports directory if it doesn't exist
        self.reports_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def generate_json_report(self, transcription_data: List[Dict[str, Any]], 
                            metadata: Dict[str, Any] = None) -> str:
        """
        Generate a JSON report from transcription data
        
        Args:
            transcription_data: List of transcription response objects
            metadata: Additional metadata to include in the report
            
        Returns:
            File path of the generated JSON report
        """
        # Create report data structure
        report = {
            "report_type": "CourtCaseVibe Transcription & Statute Analysis",
            "generated_at": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
            "transcriptions": []
        }
        
        # Process each transcription
        for item in transcription_data:
            # For each transcription, create a summary of statutes and comparisons
            statute_refs = []
            if hasattr(item, "statutes") and item.statutes:
                for statute in item.statutes:
                    # Convert Pydantic model to dict if needed
                    if hasattr(statute, "dict"):
                        statute_refs.append(statute.dict())
                    else:
                        statute_refs.append(statute)
            
            # Process statute comparisons
            comparisons = []
            if hasattr(item, "statute_comparisons") and item.statute_comparisons:
                for comp in item.statute_comparisons:
                    # Convert Pydantic model to dict if needed
                    if hasattr(comp, "dict"):
                        comparisons.append(comp.dict())
                    else:
                        comparisons.append(comp)
            
            # Add transcription data
            transcription_entry = {
                "file_id": item.file_id,
                "hearing_date": item.hearing_date,
                "transcription": item.transcription,
                "statute_references": statute_refs,
                "statute_comparisons": comparisons
            }
            
            report["transcriptions"].append(transcription_entry)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"courtcasevibe_report_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        # Write to file
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        
        return str(filepath)
    
    def generate_pdf_report(self, transcription_data: List[Dict[str, Any]],
                          metadata: Dict[str, Any] = None) -> str:
        """
        Generate a PDF report from transcription data
        
        Args:
            transcription_data: List of transcription response objects
            metadata: Additional metadata to include in the report
            
        Returns:
            File path of the generated PDF report
        """
        if not HAS_REPORTLAB:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"courtcasevibe_report_{timestamp}.pdf"
        filepath = self.reports_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading1"]
        subheading_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        # Custom styles
        statute_style = ParagraphStyle(
            "StatuteStyle",
            parent=normal_style,
            backColor=colors.lightblue,
            borderPadding=5,
            borderColor=colors.blue,
            borderWidth=1,
            borderRadius=5
        )
        
        discrepancy_style = ParagraphStyle(
            "DiscrepancyStyle",
            parent=normal_style,
            textColor=colors.red,
            backColor=colors.lightpink,
            borderPadding=5
        )
        
        # Build document content
        content = []
        
        # Title
        content.append(Paragraph("CourtCaseVibe Transcription & Statute Analysis Report", title_style))
        content.append(Spacer(1, 0.25 * inch))
        
        # Metadata
        if metadata:
            content.append(Paragraph("Report Metadata", heading_style))
            for key, value in metadata.items():
                content.append(Paragraph(f"<b>{key}:</b> {value}", normal_style))
            content.append(Spacer(1, 0.25 * inch))
        
        # Date & Time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"Generated: {current_time}", normal_style))
        content.append(Spacer(1, 0.5 * inch))
        
        # Process each transcription
        for i, item in enumerate(transcription_data):
            # Transcription section
            content.append(Paragraph(f"Transcription #{i+1}", heading_style))
            content.append(Paragraph(f"<b>File ID:</b> {item.file_id[:8]}...", normal_style))
            content.append(Paragraph(f"<b>Hearing Date:</b> {item.hearing_date}", normal_style))
            content.append(Spacer(1, 0.25 * inch))
            
            # Transcription text
            content.append(Paragraph("Full Transcription:", subheading_style))
            content.append(Paragraph(item.transcription, normal_style))
            content.append(Spacer(1, 0.25 * inch))
            
            # Statutes section
            if hasattr(item, "statutes") and item.statutes:
                content.append(Paragraph(f"Statute References Found ({len(item.statutes)})", subheading_style))
                
                # Create table of statute references
                statute_data = [["Statute ID", "Referenced Text", "Match Type"]]
                for statute in item.statutes:
                    statute_data.append([
                        statute.statute_id,
                        statute.text,
                        statute.match_type
                    ])
                
                statute_table = Table(statute_data, colWidths=[1.5*inch, 3*inch, 1*inch])
                statute_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                content.append(statute_table)
                content.append(Spacer(1, 0.25 * inch))
            
            # Comparisons section
            if hasattr(item, "statute_comparisons") and item.statute_comparisons:
                content.append(Paragraph("Statute Verification Results", subheading_style))
                
                for comp in item.statute_comparisons:
                    # Comparison header
                    score_percent = f"{comp.similarity_score * 100:.1f}%"
                    if comp.is_discrepancy:
                        content.append(Paragraph(
                            f"<b>Statute {comp.statute_id}</b> - Similarity: {score_percent} "
                            f"⚠️ <i>Potential Discrepancy</i>", 
                            discrepancy_style
                        ))
                    else:
                        content.append(Paragraph(
                            f"<b>Statute {comp.statute_id}</b> - Similarity: {score_percent} ✓ Verified", 
                            normal_style
                        ))
                    
                    # From hearing text
                    content.append(Paragraph("<b>From Hearing:</b>", normal_style))
                    content.append(Paragraph(f'"{comp.transcript_text}"', normal_style))
                    
                    # From Florida Statutes
                    content.append(Paragraph("<b>From Florida Statutes:</b>", normal_style))
                    if hasattr(comp, "error") and comp.error:
                        content.append(Paragraph(comp.error, discrepancy_style))
                    else:
                        if hasattr(comp, "title") and comp.title:
                            content.append(Paragraph(comp.title, normal_style))
                        
                        # Truncate statute text if too long
                        statute_text = comp.statute_text
                        if len(statute_text) > 500:
                            statute_text = statute_text[:500] + "..."
                        
                        content.append(Paragraph(statute_text, normal_style))
                        content.append(Paragraph(
                            f'<link href="{comp.url}">View on Official Florida Statutes Website</link>',
                            normal_style
                        ))
                    
                    content.append(Spacer(1, 0.25 * inch))
            
            # Add a page break between transcriptions (except for the last one)
            if i < len(transcription_data) - 1:
                content.append(Spacer(1, 0.5 * inch))
                content.append(Paragraph("", normal_style))
                content.append(Spacer(1, 0.5 * inch))
        
        # Build PDF
        doc.build(content)
        return str(filepath)
