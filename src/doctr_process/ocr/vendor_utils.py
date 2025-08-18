"""Vendor rule utilities and field extraction helpers."""

import re
import json
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd

__all__ = [
    "load_vendor_rules_from_csv",
    "find_vendor",
    "extract_field",
    "extract_vendor_fields",
    "detect_table_lines",
    "parse_line_items",
    "calculate_totals",
    "FIELDS",
]

FIELDS = ["ticket_number", "manifest_number", "material_type", "truck_number", "date", "line_items"]


def load_vendor_rules_from_csv(path: str):
    """Read vendor matching rules from a CSV file."""
    df = pd.read_csv(path)
    vendor_rules = []
    for _, row in df.iterrows():
        name = str(row["vendor_name"]).strip()
        display = str(row.get("display_name", "")).strip() or name
        vtype = str(row.get("vendor_type", "")).strip()
        matches_str = row.get("vendor_match", "")
        if pd.isna(matches_str):
            matches = []
        else:
            matches = [m.strip().lower() for m in str(matches_str).split(",") if m.strip()]
        excludes_str = row.get("vendor_excludes", "")
        if pd.isna(excludes_str):
            excludes = []
        else:
            excludes = [e.strip().lower() for e in str(excludes_str).split(",") if e.strip()]
        
        # Check for line items opt-in
        line_items_enabled = row.get("line_items_enabled", False)
        if pd.isna(line_items_enabled):
            line_items_enabled = False
        else:
            line_items_enabled = str(line_items_enabled).lower() in ['true', '1', 'yes', 'on']
        
        vendor_rules.append(
            {
                "vendor_name": name,
                "display_name": display,
                "vendor_type": vtype,
                "match_terms": matches,
                "exclude_terms": excludes,
                "line_items_enabled": line_items_enabled,
            }
        )
    return vendor_rules


def find_vendor(page_text: str, vendor_rules):
    """Return the vendor details that match ``page_text``."""
    page_text_lower = page_text.lower()
    for rule in vendor_rules:
        matched_terms = [term for term in rule["match_terms"] if term in page_text_lower]
        found_exclude = any(exclude in page_text_lower for exclude in rule["exclude_terms"])
        if matched_terms and not found_exclude:
            return (
                rule["vendor_name"],
                rule["vendor_type"],
                matched_terms[0],
                rule.get("display_name", rule["vendor_name"]),
            )
    return "", "", "", ""


def detect_table_lines(result_page, table_roi: Optional[List[float]] = None) -> List[Tuple[float, str]]:
    """Detect table lines in OCR result using Y-coordinate binning.
    
    Args:
        result_page: DocTR page result with blocks/lines/words
        table_roi: Optional ROI [x1, y1, x2, y2] to limit table detection area
        
    Returns:
        List of (y_coordinate, line_text) tuples sorted by Y position
    """
    lines_with_y = []
    
    for block in result_page.blocks:
        for line in block.lines:
            (lx_min, ly_min), (lx_max, ly_max) = line.geometry
            
            # Check if line is within table ROI if specified
            if table_roi:
                if not (lx_min >= table_roi[0] and ly_min >= table_roi[1] and 
                       lx_max <= table_roi[2] and ly_max <= table_roi[3]):
                    continue
            
            # Get line text
            line_text = " ".join(word.value for word in line.words)
            
            # Skip empty lines
            if not line_text.strip():
                continue
                
            # Use middle Y coordinate for binning
            y_coord = (ly_min + ly_max) / 2
            lines_with_y.append((y_coord, line_text.strip()))
    
    # Sort by Y coordinate (top to bottom)
    lines_with_y.sort(key=lambda x: x[0])
    return lines_with_y


def parse_line_items(lines_with_y: List[Tuple[float, str]], 
                    vendor_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse line items from detected table lines.
    
    Args:
        lines_with_y: List of (y_coordinate, line_text) tuples
        vendor_rules: Optional vendor-specific parsing rules
        
    Returns:
        Dictionary containing parsed line items and metadata
    """
    items = []
    total_amount = 0.0
    parsing_status = "success"
    
    # Default patterns for quantity, unit, amount
    qty_pattern = r'\b(\d+(?:\.\d+)?)\s+(tons?|cubic\s*yards?|cy|each|ea)\b'  # Quantity followed by unit
    unit_pattern = r'\b(tons?|cubic\s*yards?|cy|tons|each|ea)\b'
    amount_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
    
    # Override with vendor-specific patterns if available
    if vendor_rules:
        qty_pattern = vendor_rules.get('quantity_pattern', qty_pattern)
        unit_pattern = vendor_rules.get('unit_pattern', unit_pattern)
        amount_pattern = vendor_rules.get('amount_pattern', amount_pattern)
    
    for y_coord, line_text in lines_with_y:
        # Skip header lines or non-data lines
        line_lower = line_text.lower()
        if any(header in line_lower for header in ['qty', 'quantity', 'description', 'total', 'subtotal', 'header']):
            continue
            
        # Look for patterns indicating this is a line item
        qty_match = re.search(qty_pattern, line_text, re.IGNORECASE)
        unit_match = re.search(unit_pattern, line_text, re.IGNORECASE)
        amount_match = re.search(amount_pattern, line_text, re.IGNORECASE)
        
        # If we have quantity and amount, consider it a line item
        if qty_match and amount_match:
            try:
                quantity = float(qty_match.group(1))
                amount_str = amount_match.group(1).replace(',', '')
                amount = float(amount_str)
                unit = unit_match.group(1) if unit_match else "unknown"
                
                # Extract description (text before amount)
                description_end = amount_match.start()
                description = line_text[:description_end].strip()
                
                item = {
                    "description": description,
                    "quantity": quantity,
                    "unit": unit,
                    "amount": amount,
                    "line_text": line_text,
                    "y_coordinate": y_coord
                }
                items.append(item)
                total_amount += amount
                
            except (ValueError, IndexError) as e:
                parsing_status = "partial_error"
                continue
    
    # Look for document total in remaining lines
    document_total = None
    for y_coord, line_text in lines_with_y:
        line_lower = line_text.lower()
        if any(total_keyword in line_lower for total_keyword in ['total', 'grand total', 'amount due']):
            total_match = re.search(amount_pattern, line_text, re.IGNORECASE)
            if total_match:
                try:
                    document_total = float(total_match.group(1).replace(',', ''))
                    break
                except ValueError:
                    continue
    
    # Calculate reconciliation
    reconciliation = {
        "calculated_total": round(total_amount, 2),
        "document_total": document_total,
        "difference": None,
        "reconciled": False
    }
    
    if document_total is not None:
        difference = abs(total_amount - document_total)
        reconciliation["difference"] = round(difference, 2)
        reconciliation["reconciled"] = difference < 0.01  # Within penny tolerance
    
    return {
        "items": items,
        "item_count": len(items),
        "reconciliation": reconciliation,
        "parsing_status": parsing_status
    }


def calculate_totals(line_items_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate and validate totals from line items data.
    
    Args:
        line_items_data: Dictionary from parse_line_items()
        
    Returns:
        Dictionary with total calculations and validation status
    """
    if not line_items_data or not line_items_data.get("items"):
        return {
            "status": "no_items",
            "calculated_total": 0.0,
            "document_total": None,
            "reconciled": False
        }
    
    reconciliation = line_items_data.get("reconciliation", {})
    
    return {
        "status": "calculated",
        "calculated_total": reconciliation.get("calculated_total", 0.0),
        "document_total": reconciliation.get("document_total"),
        "difference": reconciliation.get("difference"),
        "reconciled": reconciliation.get("reconciled", False),
        "item_count": line_items_data.get("item_count", 0)
    }


def extract_field(result_page, field_rules: Dict[str, Any], pil_img=None, cfg=None):
    """Extract a single field from the OCR result page."""
    method = field_rules.get("method")
    regex = field_rules.get("regex")
    label = str(field_rules.get("label") or "").lower()
    DEBUG = cfg.get("DEBUG", False) if cfg else False

    # Handle line items extraction
    if method == "line_items":
        table_roi = field_rules.get("table_roi")
        vendor_rules = field_rules.get("parsing_rules")
        
        # Detect table lines
        lines_with_y = detect_table_lines(result_page, table_roi)
        
        # Parse line items
        line_items_data = parse_line_items(lines_with_y, vendor_rules)
        
        # Return as JSON string for storage in existing CSV structure
        return json.dumps(line_items_data) if line_items_data["items"] else None

    if method in ["roi", "box"]:
        roi = field_rules.get("roi") or field_rules.get("box")
        candidates = []
        for block in result_page.blocks:
            for line in block.lines:
                (lx_min, ly_min), (lx_max, ly_max) = line.geometry
                if lx_min >= roi[0] and ly_min >= roi[1] and lx_max <= roi[2] and ly_max <= roi[3]:
                    text = " ".join(word.value for word in line.words)
                    candidates.append(text)

        labels = field_rules.get("label", "")
        if isinstance(labels, str):
            labels = [l.strip().lower() for l in labels.split(",") if l.strip()]
        elif isinstance(labels, list):
            labels = [l.lower() for l in labels]
        else:
            labels = []

        if labels:
            candidates = [c for c in candidates if not any(lbl in c.lower() for lbl in labels)]

        if DEBUG:
            print("CANDIDATES:", candidates)

        for text in candidates:
            if regex:
                m = re.search(regex, text)
                if DEBUG:
                    print(f"[DEBUG] Matching '{regex}' in '{text}' => {m.group(0) if m else None}")
                if m:
                    return m.group(1) if m.lastindex else m.group(0)
        return candidates[0] if candidates else None

    elif method == "below_label":
        label = field_rules.get("label", "").lower()
        lines = [" ".join(word.value for word in line.words) for block in result_page.blocks for line in block.lines]
        ticket_label_idx = None
        for i, line in enumerate(lines):
            if label in line.lower():
                ticket_label_idx = i
                break
        if ticket_label_idx is not None and ticket_label_idx + 1 < len(lines):
            target_line = lines[ticket_label_idx + 1]
            if regex:
                m = re.search(regex, target_line)
                if m:
                    return m.group(0)
            return target_line.strip()
        return None

    elif method == "label_right":
        label = field_rules.get("label", "").lower()
        for block in result_page.blocks:
            for line in block.lines:
                line_text = " ".join(word.value for word in line.words)
                if label in line_text.lower():
                    idx = line_text.lower().find(label)
                    after_label = line_text[idx + len(label):]
                    if regex:
                        m = re.search(regex, after_label)
                        if m:
                            return m.group(0)
                    return after_label.strip()
        return None

    return None


def extract_vendor_fields(result_page, vendor_name: str, extraction_rules, pil_img=None, cfg=None):
    """Extract all configured fields for ``vendor_name`` from ``result_page``."""
    vendor_rule = extraction_rules.get(vendor_name, extraction_rules.get("DEFAULT"))
    result = {}
    for field in FIELDS:
        field_rules = vendor_rule.get(field)
        if not field_rules:
            result[field] = None
            continue
        if field_rules.get("method") is None:
            result[field] = None
            continue
        result[field] = extract_field(result_page, field_rules, pil_img, cfg)
    
    # Add line items status for vendor
    result["line_items_status"] = "disabled"  # Default status
    
    return result
