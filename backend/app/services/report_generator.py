"""
Report generation service for CourtCaseVibe
Provides functionality to create PDF and JSON reports from transcription data
"""
import json
import os
import datetime
import sys
from typing import Dict, List, Any
from pathlib import Path

# For PDF generation - moved inside functions to avoid module-level import errors
HAS_REPORTLAB = True
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
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
            "hearings": {}  # Group by hearing date
        }
        
        # Process each transcription and group by hearing date
        for item in transcription_data:
            # Get hearing date and ensure it's a string
            hearing_date = item.get("hearing_date", "unknown") if isinstance(item, dict) else getattr(item, "hearing_date", "unknown")
            
            # Initialize hearing entry if it doesn't exist
            if hearing_date not in report["hearings"]:
                report["hearings"][hearing_date] = []
            
            # For each transcription, create a summary of statutes and comparisons
            statute_refs = []
            if "statutes" in item or hasattr(item, "statutes"):
                statutes = item.get("statutes", []) if isinstance(item, dict) else getattr(item, "statutes", [])
                for statute in statutes:
                    # Convert Pydantic model to dict if needed
                    if hasattr(statute, "dict"):
                        statute_refs.append(statute.dict())
                    else:
                        statute_refs.append(statute)
            
            # Process statute comparisons
            comparisons = []
            if "statute_comparisons" in item or hasattr(item, "statute_comparisons"):
                comps = item.get("statute_comparisons", []) if isinstance(item, dict) else getattr(item, "statute_comparisons", [])
                for comp in comps:
                    # Convert Pydantic model to dict if needed
                    if hasattr(comp, "dict"):
                        comparisons.append(comp.dict())
                    else:
                        comparisons.append(comp)
            
            # Add transcription data
            transcription_entry = {
                "file_id": item.get("file_id", "unknown") if isinstance(item, dict) else getattr(item, "file_id", "unknown"),
                "transcription": item.get("transcription", "") if isinstance(item, dict) else getattr(item, "transcription", ""),
                "statute_references": statute_refs,
                "statute_comparisons": comparisons
            }
            
            report["hearings"][hearing_date].append(transcription_entry)
        
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
        # Double-check ReportLab is available at runtime
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
        except ImportError:
            error_msg = (
                "ReportLab is required for PDF generation but is not installed or properly configured.\n"
                "To fix this issue, please run the following command in your terminal:\n"
                "pip install reportlab\n\n"
                "If you're using a virtual environment, make sure to activate it first with:\n"
                "source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
            )
            print(error_msg, file=sys.stderr)
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
        date_heading_style = styles["Heading3"] 
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
        
        # Group transcriptions by hearing date
        hearing_dates = {}
        for item in transcription_data:
            # Get hearing date
            hearing_date = item.get("hearing_date", "unknown") if isinstance(item, dict) else getattr(item, "hearing_date", "unknown")
            
            if hearing_date not in hearing_dates:
                hearing_dates[hearing_date] = []
                
            hearing_dates[hearing_date].append(item)
        
        # Process each hearing date group
        for date, items in hearing_dates.items():
            # Hearing date section header
            content.append(Paragraph(f"Hearing Date: {date}", heading_style))
            content.append(Spacer(1, 0.25 * inch))
            
            # Process each transcription within this hearing date
            for i, item in enumerate(items):
                # Convert item to dict if it's not already
                item_dict = item if isinstance(item, dict) else item.__dict__ if hasattr(item, '__dict__') else {}
                
                # Transcription section
                content.append(Paragraph(f"Transcription #{i+1}", subheading_style))
                
                file_id = item_dict.get('file_id', 'unknown')
                if hasattr(item, 'file_id'):
                    file_id = item.file_id
                
                truncated_id = file_id[:8] if isinstance(file_id, str) and len(file_id) > 8 else file_id
                content.append(Paragraph(f"<b>File ID:</b> {truncated_id}...", normal_style))
                content.append(Spacer(1, 0.25 * inch))
                
                # Transcription text
                transcription = item_dict.get('transcription', '')
                if hasattr(item, 'transcription'):
                    transcription = item.transcription
                    
                content.append(Paragraph("Full Transcription:", subheading_style))
                content.append(Paragraph(transcription, normal_style))
                content.append(Spacer(1, 0.25 * inch))
                
                # Statutes section
                statutes = item_dict.get('statutes', [])
                if hasattr(item, 'statutes'):
                    statutes = item.statutes
                    
                if statutes:
                    content.append(Paragraph(f"Statute References Found ({len(statutes)})", subheading_style))
                    
                    # Create table of statute references
                    statute_data = [["Statute ID", "Referenced Text", "Match Type"]]
                    for statute in statutes:
                        statute_id = statute.get('statute_id', '') if isinstance(statute, dict) else getattr(statute, 'statute_id', '')
                        statute_text = statute.get('text', '') if isinstance(statute, dict) else getattr(statute, 'text', '')
                        match_type = statute.get('match_type', '') if isinstance(statute, dict) else getattr(statute, 'match_type', '')
                        
                        statute_data.append([
                            statute_id,
                            statute_text,
                            match_type
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
                comparisons = item_dict.get('statute_comparisons', [])
                if hasattr(item, 'statute_comparisons'):
                    comparisons = item.statute_comparisons
                    
                if comparisons:
                    content.append(Paragraph("Statute Verification Results", subheading_style))
                    
                    for comp in comparisons:
                        # Handle both dict and object cases
                        if isinstance(comp, dict):
                            statute_id = comp.get('statute_id', '')
                            similarity_score = comp.get('similarity_score', 0)
                            is_discrepancy = comp.get('is_discrepancy', False)
                            transcript_text = comp.get('transcript_text', '')
                            statute_text = comp.get('statute_text', '')
                            url = comp.get('url', '')
                            title = comp.get('title', '')
                            error = comp.get('error', '')
                        else:
                            statute_id = getattr(comp, 'statute_id', '')
                            similarity_score = getattr(comp, 'similarity_score', 0)
                            is_discrepancy = getattr(comp, 'is_discrepancy', False)
                            transcript_text = getattr(comp, 'transcript_text', '')
                            statute_text = getattr(comp, 'statute_text', '')
                            url = getattr(comp, 'url', '')
                            title = getattr(comp, 'title', '')
                            error = getattr(comp, 'error', '')
                        
                        # Comparison header
                        score_percent = f"{similarity_score * 100:.1f}%"
                        if is_discrepancy:
                            content.append(Paragraph(
                                f"<b>Statute {statute_id}</b> - Similarity: {score_percent} "
                                f"⚠️ <i>Potential Discrepancy</i>", 
                                discrepancy_style
                            ))
                        else:
                            content.append(Paragraph(
                                f"<b>Statute {statute_id}</b> - Similarity: {score_percent} ✓ Verified", 
                                normal_style
                            ))
                        
                        # From hearing text
                        content.append(Paragraph("<b>From Hearing:</b>", normal_style))
                        content.append(Paragraph(f'"{transcript_text}"', normal_style))
                        
                        # From Florida Statutes
                        content.append(Paragraph("<b>From Florida Statutes:</b>", normal_style))
                        if error:
                            content.append(Paragraph(error, discrepancy_style))
                        else:
                            if title:
                                content.append(Paragraph(title, normal_style))
                            
                            # Truncate statute text if too long
                            if len(statute_text) > 500:
                                statute_text = statute_text[:500] + "..."
                            
                            content.append(Paragraph(statute_text, normal_style))
                            content.append(Paragraph(
                                f'<link href="{url}">View on Official Florida Statutes Website</link>',
                                normal_style
                            ))
                        
                        content.append(Spacer(1, 0.25 * inch))
                
                # Add spacing between transcriptions within a hearing
                if i < len(items) - 1:
                    content.append(Spacer(1, 0.5 * inch))
            
            # Add a page break between hearing dates (except for the last one)
            dates = list(hearing_dates.keys())
            if date != dates[-1]:
                content.append(Spacer(1, 0.5 * inch))
                content.append(Paragraph("", normal_style))
                content.append(Spacer(1, 0.5 * inch))
        
        # Build PDF
        doc.build(content)
        return str(filepath)
