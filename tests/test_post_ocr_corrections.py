import tempfile
from pathlib import Path

from src.doctr_process.post_ocr_corrections import (
    CorrectionContext,
    CorrectionsMemory,
    FuzzyDict,
    correct_record,
    id_for_record,
    normalize,
    normalize_money,
    validate_date,
    validate_money,
    validate_ticket_no,
)


class TestCorrectionsMemory:
    def test_memory_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrections.jsonl"
            memory = CorrectionsMemory(path)

            # Add correction
            memory.add(
                "vendor", "LINDAMOOD DEM0LITION", "Lindamood Demolition", {"score": 95}
            )

            # Lookup should find it
            result = memory.lookup("vendor", "LINDAMOOD DEM0LITION")
            assert result == "Lindamood Demolition"

            # New instance should load from file
            memory2 = CorrectionsMemory(path)
            result2 = memory2.lookup("vendor", "LINDAMOOD DEM0LITION")
            assert result2 == "Lindamood Demolition"

    def test_dry_run_prevents_writes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrections.jsonl"
            memory = CorrectionsMemory(path)
            ctx = CorrectionContext(memory, dry_run=True)

            rec = {"vendor": "BAD VENDOR"}

            # Simulate correction that would normally be saved
            def mock_callback(field, old, new, meta):
                return True  # Approve

            # Even with approval, dry_run should prevent saving
            corrected = correct_record(rec, ctx, mock_callback)

            # File should not exist
            assert not path.exists()


class TestNormalization:
    def test_normalize(self):
        assert normalize("  hello   world  ") == "hello world"
        assert normalize("hello\u2014world") == "hello-world"
        assert normalize("") == ""
        assert normalize(None) == ""

    def test_normalize_money(self):
        assert normalize_money("$ 1,2S8.4O") == "1258.40"
        assert normalize_money("$123") == "123"
        assert normalize_money("1,234.56") == "1234.56"
        assert normalize_money("") == ""


class TestValidators:
    def test_validate_ticket_no(self):
        # Valid cases
        fixed, ok = validate_ticket_no("LDI123456")
        assert ok and fixed == "LDI123456"

        fixed, ok = validate_ticket_no("LDI-123456")
        assert ok and fixed == "LDI-123456"

        # Confusion fix
        fixed, ok = validate_ticket_no("LDI1O234S")
        assert ok and fixed == "LDI102345"

        # Invalid
        fixed, ok = validate_ticket_no("INVALID")
        assert not ok

    def test_validate_money(self):
        # Valid cases
        fixed, ok = validate_money("123.45")
        assert ok and fixed == "123.45"

        # Confusion fixes
        fixed, ok = validate_money("12S.4O")
        assert ok and fixed == "125.40"

        # Invalid
        fixed, ok = validate_money("not-money")
        assert not ok

    def test_validate_date(self):
        # Valid cases
        fixed, ok = validate_date("07-10-25")
        assert ok and fixed == "2025-07-10"

        fixed, ok = validate_date("2025-07-10")
        assert ok and fixed == "2025-07-10"

        # With confusion chars
        fixed, ok = validate_date("O7-1O-25")
        assert ok  # Should parse despite O->0 confusion

        # Invalid
        fixed, ok = validate_date("not-a-date")
        assert not ok


class TestFuzzyDict:
    def test_fuzzy_matching(self):
        vendors = ["Lindamood Demolition", "Martin Marietta"]
        fdict = FuzzyDict(vendors, score_cutoff=80)

        # Exact match
        best, score = fdict.best("Lindamood Demolition")
        assert best == "Lindamood Demolition"
        assert score == 100

        # Fuzzy match
        best, score = fdict.best("LINDAMOOD DEM0LITION")
        assert best == "Lindamood Demolition"
        assert score >= 80

        # No match below cutoff
        best, score = fdict.best("Completely Different")
        assert best is None
        assert score == 0


class TestCorrectionOrchestrator:
    def test_correct_record_memory_lookup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrections.jsonl"
            memory = CorrectionsMemory(path)
            memory.add("vendor", "BAD VENDOR", "Good Vendor")

            ctx = CorrectionContext(memory)
            rec = {"vendor": "BAD VENDOR", "amount": "123"}

            corrected = correct_record(rec, ctx)
            assert corrected["vendor"] == "Good Vendor"
            assert corrected["amount"] == "123"  # Unchanged

    def test_correct_record_validators(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrections.jsonl"
            memory = CorrectionsMemory(path)
            ctx = CorrectionContext(memory)

            rec = {
                "ticket_no": "LDI1O2345",  # O->0 confusion
                "amount": "12S.4O",  # S->5, O->0 confusion
                "date": "O7-1O-25",  # O->0 confusion
            }

            corrected = correct_record(rec, ctx)

            assert corrected["ticket_no"] == "LDI102345"
            assert corrected["amount"] == "125.40"
            assert "2025-07-10" in corrected["date"]  # Flexible date parsing

    def test_correct_record_fuzzy_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrections.jsonl"
            memory = CorrectionsMemory(path)

            vendors = ["Lindamood Demolition"]
            vendor_dict = FuzzyDict(vendors, score_cutoff=80)
            ctx = CorrectionContext(memory, vendor_dict=vendor_dict)

            rec = {"vendor": "LINDAMOOD DEM0LITION"}  # Has confusable chars

            corrected = correct_record(rec, ctx)
            assert corrected["vendor"] == "Lindamood Demolition"

    def test_approve_callback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrections.jsonl"
            memory = CorrectionsMemory(path)
            ctx = CorrectionContext(memory)

            approvals = []

            def callback(field, old, new, meta):
                approvals.append((field, old, new))
                return field == "ticket_no"  # Only approve ticket_no

            rec = {"ticket_no": "LDI1O2345", "amount": "12S.4O"}

            corrected = correct_record(rec, ctx, callback)

            # Only ticket_no should be corrected
            assert corrected["ticket_no"] == "LDI102345"
            assert corrected["amount"] == "12S.4O"  # Unchanged
            assert len(approvals) == 2  # Both were proposed


class TestUtilities:
    def test_id_for_record(self):
        rec = {"ticket_no": "LDI123456", "date": "2025-01-01", "amount": "100.00"}
        record_id = id_for_record(rec)

        assert len(record_id) == 12
        assert record_id.isalnum()

        # Same record should produce same ID
        record_id2 = id_for_record(rec)
        assert record_id == record_id2

        # Different record should produce different ID
        rec2 = {"ticket_no": "LDI123457", "date": "2025-01-01", "amount": "100.00"}
        record_id3 = id_for_record(rec2)
        assert record_id != record_id3
