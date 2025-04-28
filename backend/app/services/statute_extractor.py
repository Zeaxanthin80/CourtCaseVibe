import re
import spacy
from typing import List, Dict, Any, Tuple

# Pattern to match statute references like "Section 32B" or "s. 123.45"
STATUTE_PATTERNS = [
    r'\bsection\s+(\d+[A-Za-z]?(?:\.\d+)?(?:-\d+)?)',  # "section 123" or "section 123.45" or "section 123-45"
    r'\bs\.\s+(\d+[A-Za-z]?(?:\.\d+)?(?:-\d+)?)',      # "s. 123" or "s. 123.45"
    r'\b(\d+[A-Za-z]?(?:\.\d+)?(?:-\d+)?)\s+F\.S\.',   # "123 F.S." or "123.45 F.S."
    r'\bchapter\s+(\d+[A-Za-z]?)',                     # "chapter 123"
    r'\bflorida\s+statute\s+(\d+[A-Za-z]?(?:\.\d+)?)', # "florida statute 123" or "florida statute 123.45"
    r'\bfla\.\s+stat\.\s+[§]?\s*(\d+[A-Za-z]?(?:\.\d+)?)', # "fla. stat. § 123" or "fla. stat. 123.45"
    r'\bF\.S\.\s+[§]?\s*(\d+[A-Za-z]?(?:\.\d+)?)'      # "F.S. § 123" or "F.S. 123.45"
]

class StatuteExtractor:
    def __init__(self):
        """Initialize the StatuteExtractor with a SpaCy NER model"""
        # Load SpaCy model - we'll use the English model and extend it with custom rules
        # For production use, a custom-trained legal NER model would be better
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model isn't installed, download it
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            
        # Compile the regex patterns for faster matching
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in STATUTE_PATTERNS]
        
    def extract_statutes(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract statute references from the given text
        
        Args:
            text: The transcription text to analyze
            
        Returns:
            A list of dictionaries with statute information, including:
            - statute_id: The extracted statute number
            - start_idx: Start position in the text
            - end_idx: End position in the text
            - text: The original text matched
        """
        statutes = []
        
        # Use regex patterns to find statute mentions
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                statute_id = match.group(1)
                
                statutes.append({
                    "statute_id": statute_id,
                    "start_idx": match.start(),
                    "end_idx": match.end(),
                    "text": match.group(0),
                    "match_type": "regex"
                })
        
        # Use SpaCy for additional entity extraction
        doc = self.nlp(text)
        
        # Look for specific entity types that might indicate legal references
        for ent in doc.ents:
            if ent.label_ in ["LAW", "ORG", "CARDINAL"] and self._looks_like_statute(ent.text):
                # Check if this entity overlaps with any regex matches
                if not any(self._overlaps(ent.start_char, ent.end_char, s["start_idx"], s["end_idx"]) for s in statutes):
                    # Extract the statute number if possible
                    statute_id = self._extract_statute_id(ent.text)
                    if statute_id:
                        statutes.append({
                            "statute_id": statute_id,
                            "start_idx": ent.start_char,
                            "end_idx": ent.end_char,
                            "text": ent.text,
                            "match_type": "spacy"
                        })
        
        # Sort by position in text
        statutes.sort(key=lambda x: x["start_idx"])
        
        return statutes
    
    def _looks_like_statute(self, text: str) -> bool:
        """Check if the text looks like it might contain a statute reference"""
        lower_text = text.lower()
        keywords = ["section", "statute", "chapter", "code", "title", "law", "act"]
        return any(keyword in lower_text for keyword in keywords) or re.search(r'\d+\.\d+', text) is not None
    
    def _extract_statute_id(self, text: str) -> str:
        """Try to extract a statute ID from text that might contain one"""
        # Look for number patterns that might be statute IDs
        match = re.search(r'(\d+[A-Za-z]?(?:\.\d+)?(?:-\d+)?)', text)
        if match:
            return match.group(1)
        return ""
    
    def _overlaps(self, start1: int, end1: int, start2: int, end2: int) -> bool:
        """Check if two spans (start,end) overlap"""
        return max(start1, start2) < min(end1, end2)
    
    def get_highlighted_text(self, text: str, statutes: List[Dict[str, Any]]) -> str:
        """
        Create HTML with highlighted statute references
        
        Args:
            text: Original transcription text
            statutes: List of extracted statutes with positions
            
        Returns:
            HTML string with statute references wrapped in highlight spans
        """
        # Sort statutes by position in reverse order (to avoid index shifting)
        sorted_statutes = sorted(statutes, key=lambda x: x["start_idx"], reverse=True)
        
        # Create a copy of the text that we'll modify
        highlighted_text = text
        
        # Insert highlight tags around each statute mention
        for statute in sorted_statutes:
            start, end = statute["start_idx"], statute["end_idx"]
            statute_id = statute["statute_id"]
            
            # Create the highlighted span with data attribute for the statute ID
            highlight_open = f'<span class="statute-reference" data-statute-id="{statute_id}">'
            highlight_close = '</span>'
            
            # Insert the highlight tags
            highlighted_text = (
                highlighted_text[:start] + 
                highlight_open + 
                highlighted_text[start:end] + 
                highlight_close + 
                highlighted_text[end:]
            )
        
        return highlighted_text
    
    def get_highlighted_json(self, text: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process text and return both extracted statutes and highlighted text
        
        Args:
            text: The transcription text to analyze
            
        Returns:
            Tuple of (statutes, highlighted_text)
        """
        statutes = self.extract_statutes(text)
        highlighted_text = self.get_highlighted_text(text, statutes)
        return statutes, highlighted_text
