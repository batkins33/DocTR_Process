"""Quantity and units extraction."""

from typing import Optional, Tuple

from .base_extractor import BaseExtractor


class QuantityExtractor(BaseExtractor):
    """Extracts quantity and units from OCR text."""
    
    def extract(self, text: str, **kwargs) -> Tuple[Optional[float], Optional[str], float]:
        """Extract quantity and units.
        
        Args:
            text: Full OCR text from page
            **kwargs: Additional context
        
        Returns:
            (quantity_value, quantity_unit, confidence_score)
        """
        # Try vendor template first
        if self.vendor_template:
            quantity_config = self.vendor_template.get('quantity', {})
            
            # Extract from ROI if specified
            if 'roi' in quantity_config:
                roi_text = self.extract_from_roi(text, quantity_config['roi'])
                text = roi_text or text
            
            # Try vendor-specific regex patterns
            if 'regex' in quantity_config:
                patterns = quantity_config['regex']
                if isinstance(patterns, dict):
                    patterns = [patterns]
                
                result = self._extract_quantity_with_unit(text, patterns)
                if result[0] is not None:
                    return result
        
        # Fallback: Generic quantity patterns
        fallback_patterns = [
            {
                'pattern': r'(\d+(?:\.\d{1,2})?)\s*TONS?',
                'priority': 1,
                'capture_group': 1,
                'unit': 'TONS'
            },
            {
                'pattern': r'(\d+(?:\.\d{1,2})?)\s*(?:CY|CUBIC\s*YARDS?)',
                'priority': 2,
                'capture_group': 1,
                'unit': 'CY'
            },
            {
                'pattern': r'(\d+)\s*LOADS?',
                'priority': 3,
                'capture_group': 1,
                'unit': 'LOADS'
            }
        ]
        
        result = self._extract_quantity_with_unit(text, fallback_patterns)
        if result[0] is not None:
            # Apply confidence penalty for fallback
            return result[0], result[1], result[2] * 0.9
        
        # No quantity found - assume 1 load
        return 1.0, 'LOADS', 0.5
    
    def _extract_quantity_with_unit(
        self, 
        text: str, 
        patterns: list
    ) -> Tuple[Optional[float], Optional[str], float]:
        """Extract quantity with its unit.
        
        Args:
            text: Text to search
            patterns: List of pattern dicts
        
        Returns:
            (quantity, unit, confidence)
        """
        value_str, confidence = self.extract_with_regex(text, patterns)
        
        if value_str:
            try:
                quantity = float(value_str)
                
                # Get unit from matched pattern
                for pattern_config in sorted(patterns, key=lambda p: p.get('priority', 999)):
                    if pattern_config.get('unit'):
                        # Validate quantity range
                        if self._is_valid_quantity(quantity):
                            return quantity, pattern_config['unit'], confidence
                        else:
                            self.logger.warning(
                                f"Quantity {quantity} out of valid range"
                            )
            except ValueError:
                self.logger.error(f"Failed to parse quantity: {value_str}")
        
        return None, None, 0.0
    
    def _is_valid_quantity(self, quantity: float) -> bool:
        """Validate quantity is within reasonable range.
        
        Args:
            quantity: Quantity value to validate
        
        Returns:
            True if quantity is valid
        """
        # Quantity must be positive
        if quantity <= 0:
            return False
        
        # Typical truck capacity is 5-30 tons
        # Allow up to 50 as max
        if quantity > 50:
            return False
        
        return True
