#!/usr/bin/env python3
"""Simple test for Heidelberg vendor detection."""

import pandas as pd


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
            matches = [
                m.strip().lower() for m in str(matches_str).split(",") if m.strip()
            ]
        excludes_str = row.get("vendor_excludes", "")
        if pd.isna(excludes_str):
            excludes = []
        else:
            excludes = [
                e.strip().lower() for e in str(excludes_str).split(",") if e.strip()
            ]
        vendor_rules.append(
            {
                "vendor_name": name,
                "display_name": display,
                "vendor_type": vtype,
                "match_terms": matches,
                "exclude_terms": excludes,
            }
        )
    return vendor_rules


def find_vendor(page_text: str, vendor_rules):
    """Return the vendor details that match page_text."""
    page_text_lower = page_text.lower()
    for rule in vendor_rules:
        matched_terms = [
            term for term in rule["match_terms"] if term in page_text_lower
        ]
        found_exclude = any(
            exclude in page_text_lower for exclude in rule["exclude_terms"]
        )
        if matched_terms and not found_exclude:
            return (
                rule["vendor_name"],
                rule["vendor_type"],
                matched_terms[0],
                rule.get("display_name", rule["vendor_name"]),
            )
    return ("", "", "", "")


def test_heidelberg_detection():
    """Test Heidelberg detection with sample ticket text."""

    # Load vendor rules
    vendor_rules = load_vendor_rules_from_csv(
        "src/doctr_process/configs/ocr_keywords.csv"
    )

    # Sample Heidelberg ticket text
    sample_texts = [
        # Test 1: Contains "heidelberg"
        "This is a Heidelberg Materials ticket with BOL: 123456",
        # Test 2: Contains "bridgeport"
        "Bridgeport Materials BOL: 789012 Date: 12/15/2023",
        # Test 3: Contains "BOL:" pattern
        "Material Delivery BOL: 456789 Time In: 08:30 Time Out: 16:45",
        # Test 4: Contains "Time In:" pattern
        "Delivery Receipt Time In: 09:15 Time Out: 17:30 Product: Concrete",
        # Test 5: Contains "Time Out:" pattern
        "Ticket #123 Time Out: 15:45 Job: 24-105 Tons: 25.50",
        # Test 6: Typical Heidelberg ticket
        """
        Date: 12/15/2023
        BOL: 123456
        Product: Concrete Mix
        Time In: 08:30
        Time Out: 16:45
        P.O.: 24-105
        25.50 Tons
        """,
        # Test 7: Non-Heidelberg ticket (should not match)
        "Lindamood Demolition Ticket #789 Material: Dirt",
    ]

    print("Testing Heidelberg vendor detection...")
    print("=" * 50)

    for i, text in enumerate(sample_texts, 1):
        vendor_name, vendor_type, matched_term, display_name = find_vendor(
            text, vendor_rules
        )

        print(f"Test {i}:")
        print(f"  Text: {text[:50]}...")
        print(f"  Detected: {vendor_name} ({vendor_type}) - matched: '{matched_term}'")
        print(f"  Display: {display_name}")
        print()


if __name__ == "__main__":
    test_heidelberg_detection()
