"""Manifest number extraction - CRITICAL for contaminated material compliance."""

import re
from typing import Dict, Optional, Tuple

from .base_extractor import BaseExtractor


class ManifestNumberExtractor(BaseExtractor):
    """Extracts manifest numbers from contaminated material tickets.
    
    This is CRITICAL for regulatory compliance. Must achieve 100% recall.
    """
    
    def extract(self, text: str, **kwargs) -> Tuple[Optional[str], float]:
        """Extract manifest number using vendor template or fallback patterns.
        
        Args:
            text: Full OCR text from page
            **kwargs: Additional context
        
        Returns:
            (manifest_number, confidence_score)
        """
        # Try vendor-specific patterns first
        if self.vendor_template:
            manifest_config = self.vendor_template.get('manifest_number', {})
            
            # Extract from ROI if specified
            if 'roi' in manifest_config:
                roi_text = self.extract_from_roi(text, manifest_config['roi'])
                text = roi_text or text
            
            # Try vendor-specific regex patterns
            if 'regex' in manifest_config:
                patterns = manifest_config['regex']
                if isinstance(patterns, dict):
                    patterns = [patterns]
                
                value, confidence = self.extract_with_regex(text, patterns)
                
                if value:
                    # Apply validation if specified
                    if 'validation' in manifest_config:
                        is_valid, error = self.apply_validation(
                            value, 
                            manifest_config['validation']
                        )
                        if not is_valid:
                            self.logger.warning(
                                f"Manifest number '{value}' failed validation: {error}"
                            )
                        else:
                            return value, confidence
                    else:
                        return value, confidence
        
        # Fallback: Generic manifest number patterns
        fallback_patterns = [
            {
                'pattern': r'\bMANIFEST\s*#?\s*:?\s*(WM-MAN-\d{4}-\d{6})\b',
                'priority': 1,
                'capture_group': 1
            },
            {
                'pattern': r'\bMAN\s*#?\s*:?\s*([A-Z0-9-]{10,})\b',
                'priority': 2,
                'capture_group': 1
            },
            {
                'pattern': r'\bMANIFEST[:\s]+([A-Z0-9-]{6,20})\b',
                'priority': 3,
                'capture_group': 1
            },
            {
                'pattern': r'\bMFST[:\s]+([A-Z0-9-]{6,20})\b',
                'priority': 4,
                'capture_group': 1
            }
        ]
        
        value, confidence = self.extract_with_regex(text, fallback_patterns)
        
        if value:
            # Confidence penalty for fallback
            confidence *= 0.8
            return value, confidence
        
        # CRITICAL: No manifest found
        # This should trigger review queue for contaminated material
        self.logger.warning("No manifest number found - may require manual review")
        return None, 0.0
    
    def is_required(self, material_type: Optional[str] = None) -> bool:
        """Check if manifest is required for this material type.
        
        Args:
            material_type: Canonical material type name
        
        Returns:
            True if manifest required (contaminated material)
        """
        # Manifest required for contaminated material
        contaminated_materials = [
            'CLASS_2_CONTAMINATED',
            'CONTAMINATED',
            'REGULATED'
        ]
        
        if material_type:
            return material_type.upper() in contaminated_materials
        
        # If material type unknown, check vendor template
        if self.vendor_template:
            material_config = self.vendor_template.get('material', {})
            if material_config.get('assume_contaminated'):
                return True
        
        return False
