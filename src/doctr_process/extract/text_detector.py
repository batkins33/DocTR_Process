"""Text detection in documents to avoid unnecessary OCR."""

import logging
from pathlib import Path
from typing import Optional, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class TextDetector:
    """Detects existing text in documents to avoid unnecessary OCR."""
    
    def __init__(self, min_text_length: int = 50):
        self.min_text_length = min_text_length
    
    def has_extractable_text(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if document has extractable text.
        
        Returns:
            Tuple of (has_text, extracted_text)
        """
        if file_path.suffix.lower() != ".pdf":
            return False, None
        
        # Try PyMuPDF first
        if fitz:
            try:
                doc = fitz.open(str(file_path))
                full_text = ""
                for page in doc:
                    text = page.get_text()
                    if text:
                        full_text += text + "\n"
                doc.close()
                
                if len(full_text.strip()) >= self.min_text_length:
                    logging.info(f"Found {len(full_text)} chars of text in {file_path.name}")
                    return True, full_text
            except Exception as e:
                logging.warning(f"PyMuPDF text extraction failed for {file_path.name}: {e}")
        
        # Fallback to pdfplumber
        if pdfplumber:
            try:
                with pdfplumber.open(file_path) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                
                if len(full_text.strip()) >= self.min_text_length:
                    logging.info(f"Found {len(full_text)} chars of text in {file_path.name}")
                    return True, full_text
            except Exception as e:
                logging.warning(f"pdfplumber text extraction failed for {file_path.name}: {e}")
        
        return False, None