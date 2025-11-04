"""Text normalization utilities using synonym maps."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional


class SynonymNormalizer:
    """Normalizes extracted text using synonym mappings."""
    
    def __init__(self, synonyms_path: Optional[str] = None):
        """Initialize normalizer with synonym mappings.
        
        Args:
            synonyms_path: Path to synonyms.json file
        """
        self.synonyms: Dict[str, Dict[str, str]] = {}
        
        if synonyms_path:
            self.load_synonyms(synonyms_path)
        else:
            # Try to load from default location
            default_path = Path(__file__).parent.parent / "config" / "synonyms.json"
            if default_path.exists():
                self.load_synonyms(str(default_path))
    
    def load_synonyms(self, path: str):
        """Load synonym mappings from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.synonyms = json.load(f)
            logging.info(f"Loaded synonyms from {path}")
        except Exception as e:
            logging.error(f"Failed to load synonyms from {path}: {e}")
            self.synonyms = {}
    
    def normalize_vendor(self, vendor_text: str) -> str:
        """Normalize vendor name to canonical form."""
        if not vendor_text:
            return vendor_text
        
        vendor_map = self.synonyms.get("vendors", {})
        for key, canonical in vendor_map.items():
            if vendor_text.strip().lower() == key.lower():
                return canonical
        
        vendor_lower = vendor_text.strip().lower()
        for key, canonical in vendor_map.items():
            if key.lower() in vendor_lower or vendor_lower in key.lower():
                return canonical
        
        return vendor_text.strip()
    
    def normalize_source(self, source_text: str) -> str:
        """Normalize source location to canonical form."""
        if not source_text:
            return source_text
        
        source_map = self.synonyms.get("sources", {})
        for key, canonical in source_map.items():
            if source_text.strip().lower() == key.lower():
                return canonical
        
        return source_text.strip()
    
    def normalize_destination(self, dest_text: str) -> str:
        """Normalize destination to canonical form."""
        if not dest_text:
            return dest_text
        
        dest_map = self.synonyms.get("destinations", {})
        for key, canonical in dest_map.items():
            if dest_text.strip().lower() == key.lower():
                return canonical
        
        return dest_text.strip()
    
    def normalize_material(self, material_text: str) -> str:
        """Normalize material type to canonical form."""
        if not material_text:
            return material_text
        
        material_map = self.synonyms.get("materials", {})
        for key, canonical in material_map.items():
            if material_text.strip().lower() == key.lower():
                return canonical
        
        return material_text.strip()
