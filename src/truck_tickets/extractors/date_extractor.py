"""Date extraction and parsing."""

from datetime import datetime
from typing import Optional, Tuple

from .base_extractor import BaseExtractor


class DateExtractor(BaseExtractor):
    """Extracts dates from OCR text with multiple format support."""
    
    SUPPORTED_FORMATS = [
        "%m/%d/%Y",      # 10/17/2024
        "%m-%d-%Y",      # 10-17-2024
        "%Y-%m-%d",      # 2024-10-17
        "%m/%d/%y",      # 10/17/24
        "%d-%b-%Y",      # 17-OCT-2024
        "%d-%B-%Y",      # 17-October-2024
    ]
    
    def extract(self, text: str, **kwargs) -> Tuple[Optional[str], float]:
        """Extract date using vendor template or fallback patterns.
        
        Args:
            text: Full OCR text from page
            **kwargs: Additional context (may include filename_date)
        
        Returns:
            (date_string in YYYY-MM-DD format, confidence_score)
        """
        # Priority 1: Filename date (highest confidence)
        filename_date = kwargs.get('filename_date')
        if filename_date:
            parsed_date = self._parse_date_str(filename_date)
            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d"), 1.0
        
        # Priority 2: Vendor template with ROI
        if self.vendor_template:
            date_config = self.vendor_template.get('date', {})
            
            # Extract from ROI if specified
            if 'roi' in date_config:
                roi_text = self.extract_from_roi(text, date_config['roi'])
                text = roi_text or text
            
            # Try vendor-specific regex patterns
            if 'regex' in date_config:
                patterns = date_config['regex']
                if isinstance(patterns, dict):
                    patterns = [patterns]
                
                value, confidence = self.extract_with_regex(text, patterns)
                
                if value:
                    parsed_date = self._parse_date_str(value)
                    if parsed_date:
                        return parsed_date.strftime("%Y-%m-%d"), confidence
        
        # Priority 3: Generic date patterns
        fallback_patterns = [
            {
                'pattern': r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
                'priority': 1,
                'capture_group': 1
            },
            {
                'pattern': r'\b(\d{4}-\d{2}-\d{2})\b',
                'priority': 2,
                'capture_group': 1
            },
            {
                'pattern': r'\b(\d{1,2}-\d{1,2}-\d{4})\b',
                'priority': 3,
                'capture_group': 1
            }
        ]
        
        value, confidence = self.extract_with_regex(text, fallback_patterns)
        
        if value:
            parsed_date = self._parse_date_str(value)
            if parsed_date:
                # Validate date is reasonable
                if self._is_reasonable_date(parsed_date):
                    return parsed_date.strftime("%Y-%m-%d"), confidence * 0.9
        
        return None, 0.0
    
    def _parse_date_str(self, date_str: str) -> Optional[datetime]:
        """Parse date string using multiple formats.
        
        Args:
            date_str: Date string to parse
        
        Returns:
            Parsed datetime object or None
        """
        for date_format in self.SUPPORTED_FORMATS:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
        return None
    
    def _is_reasonable_date(self, dt: datetime) -> bool:
        """Check if date is within reasonable range.
        
        Args:
            dt: Datetime to validate
        
        Returns:
            True if date is reasonable
        """
        # Date should be between 2020 and 2030
        if dt.year < 2020 or dt.year > 2030:
            return False
        
        # Date should not be > 7 days in future
        from datetime import timedelta
        now = datetime.now()
        if dt > now + timedelta(days=7):
            return False
        
        # Date should not be > 180 days in past
        if dt < now - timedelta(days=180):
            return False
        
        return True
