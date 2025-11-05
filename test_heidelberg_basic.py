#!/usr/bin/env python3
"""Basic test for Heidelberg vendor detection."""


def test_heidelberg_detection():
    """Test Heidelberg detection with pattern-based approach."""

    import re

    # Heidelberg patterns
    heidelberg_patterns = [
        r"\bBOL\b.*\d{6,}",  # BOL with 6+ digits
        r"Time\s*In.*\d{1,2}:\d{2}",  # Time In pattern
        r"Time\s*Out.*\d{1,2}:\d{2}",  # Time Out pattern
        r"P\.?\s*O\.?.*\d{2}[\-\s]\d{3}",  # P.O. pattern
        r"\d+\.\d{2}\s*Ton",  # Tons pattern
    ]

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

    print("Testing Heidelberg pattern-based detection...")
    print("=" * 50)

    for i, text in enumerate(sample_texts, 1):
        matches = []
        for j, pattern in enumerate(heidelberg_patterns):
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(f"Pattern{j+1}")

        heidelberg_score = len(matches)
        is_heidelberg = heidelberg_score >= 3

        print(f"Test {i}:")
        print(f"  Text: {text[:50]}...")
        print(f"  Patterns matched: {matches} (score: {heidelberg_score})")
        if is_heidelberg:
            print("  HEIDELBERG DETECTED")
        else:
            print("  Not Heidelberg (score < 3)")
        print()


if __name__ == "__main__":
    test_heidelberg_detection()
