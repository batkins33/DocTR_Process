"""Enhanced field extraction with fuzzy matching, proximity detection, and confidence scoring.

This module provides improved field extraction capabilities that reduce dependency on brittle
regex patterns by adding fuzzy string matching, proximity-based detection, and confidence scoring.
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from rapidfuzz import fuzz, process
import dateparser


logger = logging.getLogger(__name__)


@dataclass
class FieldResult:
    """Result of field extraction with confidence and method tracking."""
    value: Optional[str]
    confidence: float  # 0.0 to 1.0
    method: str  # extraction method used
    source_text: str  # original text that was matched
    position: Optional[Tuple[float, float, float, float]] = None  # bounding box if available


class FuzzyExtractor:
    """Enhanced field extraction with fuzzy matching capabilities."""
    
    def __init__(self, confidence_threshold: float = 0.6):
        """Initialize with minimum confidence threshold for accepting results."""
        self.confidence_threshold = confidence_threshold
        
    def extract_field_with_confidence(
        self, 
        result_page, 
        field_rules: Dict[str, Any], 
        pil_img=None, 
        cfg=None
    ) -> FieldResult:
        """Extract field with confidence scoring and method tracking."""
        method = field_rules.get("method")
        
        if not method or method == "null":
            return FieldResult(None, 0.0, "null", "")
            
        # Try primary method first
        result = self._extract_by_method(result_page, field_rules, method, pil_img, cfg)
        
        # If primary method fails and fallback is available, try fallback
        if result.confidence < self.confidence_threshold:
            fallback_method = field_rules.get("fallback_method")
            fallback_regex = field_rules.get("fallback_regex")
            
            if fallback_method and fallback_regex:
                # Create fallback rules
                fallback_rules = field_rules.copy()
                fallback_rules["method"] = fallback_method
                fallback_rules["regex"] = fallback_regex
                
                fallback_result = self._extract_by_method(
                    result_page, fallback_rules, fallback_method, pil_img, cfg
                )
                
                if fallback_result.confidence > result.confidence:
                    fallback_result.method = f"{method}_fallback_to_{fallback_method}"
                    result = fallback_result
                    
        return result
    
    def _extract_by_method(
        self, 
        result_page, 
        field_rules: Dict[str, Any], 
        method: str,
        pil_img=None, 
        cfg=None
    ) -> FieldResult:
        """Extract field using specified method."""
        
        if method in ["roi", "box"]:
            return self._extract_roi_fuzzy(result_page, field_rules, cfg)
        elif method == "below_label":
            return self._extract_below_label_fuzzy(result_page, field_rules)
        elif method == "label_right":
            return self._extract_label_right_fuzzy(result_page, field_rules)
        elif method == "proximity":
            return self._extract_proximity(result_page, field_rules)
        else:
            logger.warning(f"Unknown extraction method: {method}")
            return FieldResult(None, 0.0, f"unknown_{method}", "")
    
    def _extract_roi_fuzzy(self, result_page, field_rules: Dict[str, Any], cfg=None) -> FieldResult:
        """Extract from ROI with fuzzy label filtering."""
        roi = field_rules.get("roi") or field_rules.get("box")
        regex = field_rules.get("regex")
        DEBUG = cfg.get("DEBUG", False) if cfg else False
        
        candidates = []
        for block in result_page.blocks:
            for line in block.lines:
                (lx_min, ly_min), (lx_max, ly_max) = line.geometry
                if lx_min >= roi[0] and ly_min >= roi[1] and lx_max <= roi[2] and ly_max <= roi[3]:
                    text = " ".join(word.value for word in line.words)
                    candidates.append((text, line.geometry))
        
        # Filter out label text using fuzzy matching
        labels = self._normalize_labels(field_rules.get("label", ""))
        filtered_candidates = []
        
        for text, geometry in candidates:
            is_label = False
            for label in labels:
                if self._is_fuzzy_match(text.lower(), label, threshold=0.8):
                    is_label = True
                    break
            if not is_label:
                filtered_candidates.append((text, geometry))
        
        if DEBUG:
            logger.debug(f"ROI candidates after label filtering: {[c[0] for c in filtered_candidates]}")
        
        # Extract values using regex with confidence scoring
        for text, geometry in filtered_candidates:
            if regex:
                match = re.search(regex, text)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    
                    # Calculate confidence based on regex match quality
                    confidence = self._calculate_regex_confidence(value, text, field_rules)
                    
                    return FieldResult(
                        value=value,
                        confidence=confidence,
                        method="roi_fuzzy",
                        source_text=text,
                        position=geometry
                    )
        
        # Return best candidate even without regex match
        if filtered_candidates:
            text, geometry = filtered_candidates[0]
            return FieldResult(
                value=text.strip(),
                confidence=0.3,  # Low confidence for non-regex match
                method="roi_fuzzy_no_regex",
                source_text=text,
                position=geometry
            )
            
        return FieldResult(None, 0.0, "roi_fuzzy_failed", "")
    
    def _extract_below_label_fuzzy(self, result_page, field_rules: Dict[str, Any]) -> FieldResult:
        """Extract field below label using fuzzy label matching."""
        target_label = field_rules.get("label", "").lower()
        regex = field_rules.get("regex")
        
        lines = []
        for block in result_page.blocks:
            for line in block.lines:
                text = " ".join(word.value for word in line.words)
                lines.append((text, line.geometry))
        
        # Find label using fuzzy matching
        label_idx = None
        best_label_score = 0
        
        for i, (line_text, _) in enumerate(lines):
            score = fuzz.partial_ratio(target_label, line_text.lower())
            if score > 70 and score > best_label_score:  # 70% similarity threshold
                label_idx = i
                best_label_score = score
        
        if label_idx is not None and label_idx + 1 < len(lines):
            target_text, geometry = lines[label_idx + 1]
            
            if regex:
                match = re.search(regex, target_text)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    confidence = self._calculate_regex_confidence(value, target_text, field_rules)
                    confidence *= (best_label_score / 100.0)  # Adjust by label match quality
                    
                    return FieldResult(
                        value=value,
                        confidence=confidence,
                        method="below_label_fuzzy",
                        source_text=target_text,
                        position=geometry
                    )
            
            return FieldResult(
                value=target_text.strip(),
                confidence=(best_label_score / 100.0) * 0.5,  # Lower confidence without regex
                method="below_label_fuzzy_no_regex", 
                source_text=target_text,
                position=geometry
            )
            
        return FieldResult(None, 0.0, "below_label_fuzzy_failed", "")
    
    def _extract_label_right_fuzzy(self, result_page, field_rules: Dict[str, Any]) -> FieldResult:
        """Extract field to the right of label using fuzzy matching."""
        target_label = field_rules.get("label", "").lower()
        regex = field_rules.get("regex")
        
        for block in result_page.blocks:
            for line in block.lines:
                line_text = " ".join(word.value for word in line.words)
                
                # Use fuzzy matching to find label
                if fuzz.partial_ratio(target_label, line_text.lower()) > 70:
                    # Find best position to split on
                    best_idx = self._find_label_split_position(line_text.lower(), target_label)
                    if best_idx != -1:
                        after_label = line_text[best_idx:].strip()
                        
                        if regex:
                            match = re.search(regex, after_label)
                            if match:
                                value = match.group(1) if match.lastindex else match.group(0)
                                confidence = self._calculate_regex_confidence(value, after_label, field_rules)
                                
                                return FieldResult(
                                    value=value,
                                    confidence=confidence,
                                    method="label_right_fuzzy",
                                    source_text=after_label,
                                    position=line.geometry
                                )
                        
                        return FieldResult(
                            value=after_label,
                            confidence=0.4,
                            method="label_right_fuzzy_no_regex",
                            source_text=after_label,
                            position=line.geometry
                        )
                        
        return FieldResult(None, 0.0, "label_right_fuzzy_failed", "")
    
    def _extract_proximity(self, result_page, field_rules: Dict[str, Any]) -> FieldResult:
        """Extract field based on proximity to labels."""
        labels = self._normalize_labels(field_rules.get("label", ""))
        regex = field_rules.get("regex")
        max_distance = field_rules.get("max_distance", 0.3)  # Max distance in normalized coordinates
        
        if not labels:
            return FieldResult(None, 0.0, "proximity_no_labels", "")
        
        # Get all text elements with positions
        text_elements = []
        for block in result_page.blocks:
            for line in block.lines:
                text = " ".join(word.value for word in line.words)
                (x1, y1), (x2, y2) = line.geometry
                center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
                text_elements.append((text, center_x, center_y, line.geometry))
        
        # Find label positions using fuzzy matching
        label_positions = []
        for text, x, y, geometry in text_elements:
            text_lower = text.lower()
            for label in labels:
                # Use more lenient fuzzy matching for labels
                if (label in text_lower or 
                    fuzz.partial_ratio(label, text_lower) > 60 or
                    any(label_word in text_lower for label_word in label.split())):
                    label_positions.append((x, y, text, geometry))
                    break
        
        if not label_positions:
            return FieldResult(None, 0.0, "proximity_no_labels_found", "")
        
        # Find candidates near labels
        candidates = []
        for text, x, y, geometry in text_elements:
            # Skip if this text is a label itself
            text_lower = text.lower()
            is_label = False
            for label in labels:
                if (label in text_lower or 
                    fuzz.partial_ratio(label, text_lower) > 60 or
                    any(label_word in text_lower for label_word in label.split())):
                    is_label = True
                    break
                    
            if is_label:
                continue
                
            # Find distance to nearest label
            min_distance = float('inf')
            for lx, ly, _, _ in label_positions:
                distance = ((x - lx) ** 2 + (y - ly) ** 2) ** 0.5
                min_distance = min(min_distance, distance)
            
            if min_distance <= max_distance:
                candidates.append((text, min_distance, geometry))
        
        # Sort by distance (closest first)
        candidates.sort(key=lambda x: x[1])
        
        # Try regex on candidates
        for text, distance, geometry in candidates:
            if regex:
                match = re.search(regex, text)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    # Confidence decreases with distance
                    distance_factor = max(0.1, 1 - (distance / max_distance))
                    confidence = self._calculate_regex_confidence(value, text, field_rules) * distance_factor
                    
                    return FieldResult(
                        value=value,
                        confidence=confidence,
                        method="proximity",
                        source_text=text,
                        position=geometry
                    )
        
        # Return closest candidate even without regex match
        if candidates:
            text, distance, geometry = candidates[0]
            distance_factor = max(0.1, 1 - (distance / max_distance))
            
            return FieldResult(
                value=text.strip(),
                confidence=0.3 * distance_factor,
                method="proximity_no_regex",
                source_text=text,
                position=geometry
            )
            
        return FieldResult(None, 0.0, "proximity_failed", "")
    
    def _normalize_labels(self, labels) -> List[str]:
        """Normalize label input to list of lowercase strings."""
        if isinstance(labels, str):
            if not labels:
                return []
            return [l.strip().lower() for l in labels.split(",") if l.strip()]
        elif isinstance(labels, list):
            return [str(l).strip().lower() for l in labels if str(l).strip()]
        else:
            return []
    
    def _is_fuzzy_match(self, text: str, target: str, threshold: float = 0.7) -> bool:
        """Check if text matches target with fuzzy matching."""
        score = fuzz.partial_ratio(target, text)
        return score >= (threshold * 100)
    
    def _find_label_split_position(self, text: str, label: str) -> int:
        """Find best position to split text after label."""
        # Try exact match first
        if label in text:
            return text.index(label) + len(label)
        
        # Try fuzzy matching with different positions
        best_score = 0
        best_pos = -1
        
        for i in range(len(text) - len(label) + 1):
            substring = text[i:i + len(label)]
            score = fuzz.ratio(label, substring)
            if score > best_score and score > 70:
                best_score = score
                best_pos = i + len(label)
                
        return best_pos
    
    def _calculate_regex_confidence(self, value: str, source_text: str, field_rules: Dict[str, Any]) -> float:
        """Calculate confidence score for regex match."""
        base_confidence = 0.8
        
        # Check validation regex if available
        validation_regex = field_rules.get("validation_regex")
        if validation_regex:
            if re.match(validation_regex, value):
                base_confidence = 0.95
            else:
                base_confidence = 0.4  # Lower confidence if validation fails
        
        # Adjust confidence based on how much of source text was matched
        value_length = len(value.strip())
        source_length = len(source_text.strip())
        if source_length > 0:
            coverage = min(1.0, value_length / source_length)
            base_confidence *= (0.5 + 0.5 * coverage)  # Boost for better coverage
        
        return min(1.0, base_confidence)
    
    def _enhanced_date_parsing(self, text: str) -> Tuple[Optional[str], float]:
        """Enhanced date parsing with confidence scoring."""
        try:
            # Use dateparser for fuzzy date parsing
            parsed_date = dateparser.parse(text)
            if parsed_date:
                # Format as standard date string
                formatted_date = parsed_date.strftime('%Y-%m-%d')
                
                # Calculate confidence based on how much of the text was likely a date
                confidence = 0.9 if len(text.strip()) < 20 else 0.7
                return formatted_date, confidence
        except Exception as e:
            logger.debug(f"Date parsing failed for '{text}': {e}")
            
        return None, 0.0


def extract_field_with_confidence(
    result_page, 
    field_rules: Dict[str, Any], 
    pil_img=None, 
    cfg=None
) -> FieldResult:
    """Extract field with confidence scoring - convenience function."""
    extractor = FuzzyExtractor()
    return extractor.extract_field_with_confidence(result_page, field_rules, pil_img, cfg)


def extract_vendor_fields_enhanced(
    result_page, 
    vendor_name: str, 
    extraction_rules, 
    pil_img=None, 
    cfg=None
) -> Dict[str, FieldResult]:
    """Extract all vendor fields with confidence scoring and method tracking."""
    from src.doctr_process.ocr.vendor_utils import FIELDS
    
    vendor_rule = extraction_rules.get(vendor_name, extraction_rules.get("DEFAULT"))
    extractor = FuzzyExtractor()
    results = {}
    
    for field in FIELDS:
        field_rules = vendor_rule.get(field)
        if not field_rules:
            results[field] = FieldResult(None, 0.0, "no_rules", "")
            continue
            
        # Special handling for date fields
        if field == "date" and field_rules.get("method") != "null":
            result = extractor.extract_field_with_confidence(result_page, field_rules, pil_img, cfg)
            if result.value:
                # Try enhanced date parsing
                parsed_date, date_confidence = extractor._enhanced_date_parsing(result.value)
                if parsed_date and date_confidence > 0.5:
                    result.value = parsed_date
                    result.confidence = min(1.0, result.confidence + date_confidence * 0.2)
                    result.method += "_date_enhanced"
            results[field] = result
        else:
            results[field] = extractor.extract_field_with_confidence(result_page, field_rules, pil_img, cfg)
    
    return results