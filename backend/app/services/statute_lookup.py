import os
import re
import json
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np

# Base URL for Florida Statutes
FL_STATUTES_BASE_URL = "http://www.leg.state.fl.us/statutes"
CACHE_EXPIRY = 30  # Cache expiry in days

class StatuteLookupService:
    def __init__(self, db_path=None):
        """
        Initialize the Statute Lookup Service with a cache database
        
        Args:
            db_path: Path to the SQLite database file for caching. If None, uses in-memory DB.
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "statute_cache.db"
        )
        
        # Initialize the database
        self._init_database()
        
        # Initialize the sentence transformer model
        self.model = None
    
    def _get_embedding_model(self):
        """Lazy-load the sentence embedding model"""
        if self.model is None:
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        return self.model

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two text strings
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        model = self._get_embedding_model()
        embedding1 = model.encode(text1)
        embedding2 = model.encode(text2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        
        return float(similarity)

    def _init_database(self):
        """Initialize the SQLite database with the necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS statutes (
            id TEXT PRIMARY KEY,
            title TEXT,
            full_text TEXT,
            url TEXT,
            last_updated TIMESTAMP,
            embedding BLOB
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def build_statute_url(self, statute_id: str) -> str:
        """
        Build a URL to access the Florida Statutes website for a given statute ID
        
        Args:
            statute_id: The statute identifier (e.g., "456.013" or "32B")
            
        Returns:
            URL string for the statute
        """
        # Clean up the statute ID
        statute_id = statute_id.strip().replace(' ', '')
        
        # Check if the ID has a chapter and section
        if '.' in statute_id:
            parts = statute_id.split('.')
            chapter = parts[0]
            section = parts[1]
            
            # Format: http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&Search_String=&URL=0400-0499/0456/Sections/0456.013.html
            # Determine the chapter range (e.g., 0400-0499 for chapter 456)
            chapter_num = int(chapter)
            range_base = (chapter_num // 100) * 100
            range_top = range_base + 99
            range_str = f"{range_base:04d}-{range_top:04d}"
            
            return f"{FL_STATUTES_BASE_URL}/index.cfm?App_mode=Display_Statute&Search_String=&URL={range_str}/{chapter}/Sections/{chapter}.{section}.html"
        else:
            # Just chapter, like "32B"
            # Extract number part
            chapter_match = re.match(r'(\d+)', statute_id)
            if chapter_match:
                chapter_num = int(chapter_match.group(1))
                range_base = (chapter_num // 100) * 100
                range_top = range_base + 99
                range_str = f"{range_base:04d}-{range_top:04d}"
                
                return f"{FL_STATUTES_BASE_URL}/index.cfm?App_mode=Display_Statute&Search_String=&URL={range_str}/{statute_id}/0{statute_id}.html"
            else:
                # Fallback to search
                return f"{FL_STATUTES_BASE_URL}/index.cfm?App_mode=Display_Statute&Search_String={statute_id}"
    
    def fetch_statute(self, statute_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch statute information from the cache or live website
        
        Args:
            statute_id: The statute identifier (e.g., "456.013")
            force_refresh: Whether to bypass the cache and fetch from the website
            
        Returns:
            Dictionary containing statute information
        """
        # First check the cache
        if not force_refresh:
            cached_result = self._get_from_cache(statute_id)
            if cached_result:
                return cached_result
        
        # If not in cache or forced refresh, fetch from the website
        try:
            result = self._fetch_from_website(statute_id)
            if result:
                # Update the cache with the result
                self._update_cache(statute_id, result)
                return result
            else:
                # If no result from website, return a placeholder
                return {
                    "statute_id": statute_id,
                    "title": f"Statute {statute_id}",
                    "text": f"Statute text for {statute_id} could not be retrieved.",
                    "url": self.build_statute_url(statute_id),
                    "found": False,
                    "cached": False
                }
        except Exception as e:
            # Return a placeholder with the error
            return {
                "statute_id": statute_id,
                "title": f"Statute {statute_id}",
                "text": f"Error retrieving statute: {str(e)}",
                "url": self.build_statute_url(statute_id),
                "found": False,
                "cached": False,
                "error": str(e)
            }
    
    def _fetch_from_website(self, statute_id: str) -> Dict[str, Any]:
        """
        Fetch statute information from the Florida Statutes website
        
        Args:
            statute_id: The statute identifier (e.g., "456.013")
            
        Returns:
            Dictionary containing statute information
        """
        url = self.build_statute_url(statute_id)
        
        # Fetch the webpage
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch statute from website: HTTP {response.status_code}")
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the statute title and text
        # Look for statute title in multiple possible locations
        title = f"Statute {statute_id}"
        title_element = soup.find('span', class_='StatuteTitle')
        if title_element:
            title = title_element.text.strip()
        else:
            # Try alternative locations
            title_element = soup.find('h1') or soup.find('h2') or soup.find('title')
            if title_element:
                title = title_element.text.strip()
        
        # Try to find the main statute text container
        # This may vary based on the actual website structure
        statute_text_element = soup.find('div', class_='Statute') or soup.find('div', id='content')
        
        if statute_text_element:
            # Clean up the text
            text = statute_text_element.get_text(separator="\n", strip=True)
        else:
            # Fallback to the main content area
            body = soup.find('body')
            if body:
                text = body.get_text(separator="\n", strip=True)
            else:
                text = "Statute text not found."
                
        # Check if we found meaningful statute content
        # If the response doesn't contain expected elements, mark it as not found
        found = bool(statute_text_element)
        
        return {
            "statute_id": statute_id,
            "title": title,
            "text": text,
            "url": url,
            "found": found,
            "cached": False
        }
    
    def _get_from_cache(self, statute_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statute information from the cache
        
        Args:
            statute_id: The statute identifier
            
        Returns:
            Dictionary containing statute information, or None if not in cache
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the statute information
        cursor.execute(
            "SELECT id, title, full_text, url, last_updated FROM statutes WHERE id = ?",
            (statute_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Check if the cache is expired
            last_updated = datetime.fromisoformat(result[4])
            if datetime.now() - last_updated > timedelta(days=CACHE_EXPIRY):
                return None
            
            # Return the cached result
            return {
                "statute_id": result[0],
                "title": result[1],
                "text": result[2],
                "url": result[3],
                "found": True,
                "cached": True,
                "last_updated": result[4]
            }
        
        return None
    
    def _update_cache(self, statute_id: str, data: Dict[str, Any]) -> None:
        """
        Update the cache with statute information
        
        Args:
            statute_id: The statute identifier
            data: Dictionary containing statute information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate embedding for the text if we have the model loaded
        embedding_bytes = None
        if self.model is not None and data.get("text"):
            embedding = self._get_embedding_model().encode(data["text"])
            embedding_bytes = embedding.tobytes()
        
        # Insert or update the statute information
        cursor.execute(
            """
            INSERT OR REPLACE INTO statutes (id, title, full_text, url, last_updated, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                statute_id,
                data.get("title", f"Statute {statute_id}"),
                data.get("text", ""),
                data.get("url", self.build_statute_url(statute_id)),
                datetime.now().isoformat(),
                embedding_bytes
            )
        )
        
        conn.commit()
        conn.close()
    
    def compare_transcript_to_statute(self, transcript_text: str, statute_id: str, 
                                      threshold: float = 0.6) -> Dict[str, Any]:
        """
        Compare a transcript mention to the actual statute text
        
        Args:
            transcript_text: The text from the transcript mentioning the statute
            statute_id: The statute identifier
            threshold: Similarity threshold for flagging discrepancies
            
        Returns:
            Dictionary with comparison results
        """
        # Fetch the statute
        statute_data = self.fetch_statute(statute_id)
        
        # If statute not found or has an error, return with low similarity
        if not statute_data.get("found", False) or "error" in statute_data:
            return {
                "statute_id": statute_id,
                "transcript_text": transcript_text,
                "statute_text": statute_data.get("text", ""),
                "similarity_score": 0.0,
                "is_discrepancy": True,
                "url": statute_data.get("url", ""),
                "error": statute_data.get("error", "Statute not found")
            }
        
        # Calculate semantic similarity
        model = self._get_embedding_model()
        transcript_embedding = model.encode(transcript_text)
        
        # Check if we already have the statute embedding in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT embedding FROM statutes WHERE id = ?", (statute_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # Use the cached embedding
            statute_embedding = np.frombuffer(result[0], dtype=np.float32)
        else:
            # Generate a new embedding
            statute_embedding = model.encode(statute_data["text"])
            
            # Update the cache with the embedding
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE statutes SET embedding = ? WHERE id = ?",
                (statute_embedding.tobytes(), statute_id)
            )
            conn.commit()
            conn.close()
        
        # Calculate cosine similarity
        similarity = np.dot(transcript_embedding, statute_embedding) / (
            np.linalg.norm(transcript_embedding) * np.linalg.norm(statute_embedding)
        )
        
        # Check if similarity is below threshold
        is_discrepancy = similarity < threshold
        
        return {
            "statute_id": statute_id,
            "transcript_text": transcript_text,
            "statute_text": statute_data["text"],
            "similarity_score": float(similarity),
            "is_discrepancy": is_discrepancy,
            "url": statute_data["url"],
            "title": statute_data.get("title", f"Statute {statute_id}")
        }
    
    def batch_process_statutes(self, statutes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple statute references from a transcript
        
        Args:
            statutes: List of statute references with statute_id and text
            
        Returns:
            List of dictionaries with comparison results
        """
        results = []
        
        for statute in statutes:
            statute_id = statute.get("statute_id")
            text = statute.get("text", "")
            
            if statute_id:
                comparison = self.compare_transcript_to_statute(text, statute_id)
                results.append(comparison)
        
        return results

if __name__ == "__main__":
    # Example usage
    service = StatuteLookupService()
    result = service.fetch_statute("456.013")
    print(f"Fetched statute: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Found: {result['found']}")
    print(f"Text excerpt: {result['text'][:100]}...")
