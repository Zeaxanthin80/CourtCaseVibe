"""
Sample data generator for testing CourtCaseVibe
"""
import os
import time
import json
from pathlib import Path

# Sample transcription with Florida statute references
SAMPLE_TRANSCRIPTION = """
In today's hearing regarding case number 2025-CV-12345, we'll be discussing the defendant's compliance with Section 316.193 of Florida Statutes.

As stated in s. 316.193, F.S., driving under the influence is prohibited. The law clearly defines this as:
1. The person is driving or in actual physical control of a vehicle; and
2. The person is under the influence of alcoholic beverages, any chemical substance, or any controlled substance to the extent that the person's normal faculties are impaired.

Additionally, Chapter 322 outlines the requirements for driver licenses, and specifically Section 322.2615 covers the suspension of licenses for DUI offenses.

The defendant is also required to comply with Section 775.089 regarding restitution to victims.

During the previous hearing on April 15, the court referenced 948.03 F.S. concerning probation conditions.
"""

# Sample statute data
SAMPLE_STATUTES = [
    {
        "statute_id": "316.193",
        "title": "Driving under the influence; penalties",
        "text": "(1) A person is guilty of the offense of driving under the influence and is subject to punishment as provided in subsection (2) if the person is driving or in actual physical control of a vehicle within this state and:\n(a) The person is under the influence of alcoholic beverages, any chemical substance set forth in s. 877.111, or any substance controlled under chapter 893, when affected to the extent that the person's normal faculties are impaired;\n(b) The person has a blood-alcohol level of 0.08 or more grams of alcohol per 100 milliliters of blood; or\n(c) The person has a breath-alcohol level of 0.08 or more grams of alcohol per 210 liters of breath.",
        "url": "http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0300-0399/0316/Sections/0316.193.html",
        "cached": True,
        "last_updated": "2025-04-23T10:15:30"
    },
    {
        "statute_id": "322.2615",
        "title": "Suspension of license; right to review",
        "text": "(1)(a) A law enforcement officer or correctional officer shall, on behalf of the department, suspend the driving privilege of a person who is driving or in actual physical control of a motor vehicle and who has an unlawful blood-alcohol level or breath-alcohol level of 0.08 or higher, or of a person who has refused to submit to a urine test or a test of his or her breath-alcohol or blood-alcohol level.",
        "url": "http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0300-0399/0322/Sections/0322.2615.html",
        "cached": True,
        "last_updated": "2025-04-23T10:16:45"
    },
    {
        "statute_id": "775.089",
        "title": "Restitution",
        "text": "(1)(a) In addition to any punishment, the court shall order the defendant to make restitution to the victim for:\n1. Damage or loss caused directly or indirectly by the defendant's offense; and\n2. Damage or loss related to the defendant's criminal episode, unless it finds clear and compelling reasons not to order such restitution.",
        "url": "http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0700-0799/0775/Sections/0775.089.html",
        "cached": False,
        "last_updated": None
    },
    {
        "statute_id": "948.03",
        "title": "Terms and conditions of probation",
        "text": "(1) The court shall determine the terms and conditions of probation. Conditions specified in this section do not require oral pronouncement at the time of sentencing and may be considered standard conditions of probation. These conditions may include among them the following, that the probationer or offender in community control shall:",
        "url": "http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0900-0999/0948/Sections/0948.03.html",
        "cached": True,
        "last_updated": "2025-04-25T09:30:15"
    },
]

def generate_sample_audio_file(output_path, duration_seconds=5):
    """
    Generate a sample WAV file for testing
    
    Args:
        output_path: Path to save the generated audio file
        duration_seconds: Duration of the audio in seconds
        
    Returns:
        Path to the generated file
    """
    try:
        import numpy as np
        from scipy.io import wavfile
        
        # Generate a simple sine wave
        sample_rate = 44100
        t = np.linspace(0, duration_seconds, duration_seconds * sample_rate, False)
        tone = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        # Normalize and convert to 16-bit PCM
        tone = tone * 32767 / np.max(np.abs(tone))
        tone = tone.astype(np.int16)
        
        # Save the WAV file
        wavfile.write(output_path, sample_rate, tone)
        return output_path
    except ImportError:
        # Fallback if scipy is not available - create an empty file
        with open(output_path, 'wb') as f:
            f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
        return output_path

def generate_sample_transcription_result(hearing_date="2025-04-27"):
    """
    Generate a sample transcription result
    
    Args:
        hearing_date: The hearing date to use in the result
        
    Returns:
        A dictionary with sample transcription data
    """
    from app.services.statute_extractor import StatuteExtractor
    
    extractor = StatuteExtractor()
    statutes, highlighted_text = extractor.get_highlighted_json(SAMPLE_TRANSCRIPTION)
    
    # Convert statute dicts to match the expected format
    statute_references = []
    for statute in statutes:
        statute_references.append({
            "statute_id": statute["statute_id"],
            "start_idx": statute["start_idx"],
            "end_idx": statute["end_idx"],
            "text": statute["text"],
            "match_type": statute["match_type"]
        })
    
    # Generate sample statute comparisons
    statute_comparisons = []
    for statute in statutes:
        # Find matching sample statute data or generate placeholders
        sample_data = next((s for s in SAMPLE_STATUTES if s["statute_id"] == statute["statute_id"]), None)
        
        if sample_data:
            statute_text = sample_data["text"]
            title = sample_data["title"]
            url = sample_data["url"]
        else:
            statute_text = f"Sample text for statute {statute['statute_id']}"
            title = f"Sample Title for {statute['statute_id']}"
            url = f"http://www.leg.state.fl.us/statutes/index.cfm?Statute={statute['statute_id']}"
        
        # Create a sample comparison
        statute_comparisons.append({
            "statute_id": statute["statute_id"],
            "transcript_text": statute["text"],
            "statute_text": statute_text[:200] + ("..." if len(statute_text) > 200 else ""),
            "similarity_score": 0.85,  # Sample score
            "is_discrepancy": False,
            "url": url,
            "title": title
        })
    
    return {
        "transcription": SAMPLE_TRANSCRIPTION,
        "highlighted_transcription": highlighted_text,
        "file_id": "sample_" + str(int(time.time())),
        "hearing_date": hearing_date,
        "statutes": statute_references,
        "statute_comparisons": statute_comparisons
    }

def generate_sample_report(format="json"):
    """
    Generate a sample report file
    
    Args:
        format: The report format ('json' or 'pdf')
        
    Returns:
        Path to the generated report file
    """
    from app.services.report_generator import ReportGenerator
    
    # Generate a sample transcription result
    transcription = generate_sample_transcription_result()
    
    # Create sample metadata
    metadata = {
        "generated_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "report_type": "Sample Test Report",
        "user_agent": "CourtCaseVibe Testing Suite"
    }
    
    # Generate the report
    report_generator = ReportGenerator()
    
    if format.lower() == "json":
        report_path = report_generator.generate_json_report([transcription], metadata)
    else:
        report_path = report_generator.generate_pdf_report([transcription], metadata)
    
    return report_path

def main():
    """
    Generate sample files for testing
    """
    print("Generating sample test data for CourtCaseVibe")
    
    # Create paths
    base_dir = Path(__file__).parent.parent
    uploads_dir = base_dir / "uploads"
    reports_dir = base_dir / "reports"
    
    # Ensure directories exist
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate a sample audio file
    audio_path = uploads_dir / "sample_audio.wav"
    generate_sample_audio_file(audio_path)
    print(f"Generated sample audio: {audio_path}")
    
    # Generate sample reports
    json_report = generate_sample_report("json")
    print(f"Generated sample JSON report: {json_report}")
    
    pdf_report = generate_sample_report("pdf")
    print(f"Generated sample PDF report: {pdf_report}")
    
    print("Sample data generation complete!")

if __name__ == "__main__":
    main()
