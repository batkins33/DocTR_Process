"""Tests for synonym normalization functionality.

Tests cover:
1. SynonymNormalizer class initialization and loading
2. Vendor normalization with various synonyms
3. Material normalization with various synonyms
4. Source normalization with various synonyms
5. Destination normalization with various synonyms
6. Edge cases and error handling
7. Case sensitivity and whitespace handling
8. Unknown inputs (returns original text)
"""

import json

from src.truck_tickets.utils import SynonymNormalizer


class TestSynonymNormalizer:
    """Test SynonymNormalizer class functionality."""

    def test_init_default_path(self):
        """Test initialization with default synonyms path."""
        normalizer = SynonymNormalizer()

        # Should load default synonyms
        assert normalizer.synonyms is not None
        assert "vendors" in normalizer.synonyms
        assert "materials" in normalizer.synonyms
        assert "sources" in normalizer.synonyms
        assert "destinations" in normalizer.synonyms

    def test_init_custom_path(self, tmp_path):
        """Test initialization with custom synonyms path."""
        # Create custom synonyms file
        custom_synonyms = {
            "vendors": {"Custom Vendor": "CUSTOM_VENDOR"},
            "materials": {"Custom Material": "CUSTOM_MATERIAL"},
        }

        synonyms_file = tmp_path / "custom_synonyms.json"
        synonyms_file.write_text(json.dumps(custom_synonyms))

        normalizer = SynonymNormalizer(str(synonyms_file))

        assert normalizer.synonyms == custom_synonyms

    def test_init_nonexistent_path(self):
        """Test initialization with nonexistent path."""
        normalizer = SynonymNormalizer("nonexistent.json")

        # Should have empty synonyms
        assert normalizer.synonyms == {}

    def test_load_synonyms_valid_file(self, tmp_path):
        """Test loading synonyms from valid JSON file."""
        synonyms_data = {
            "vendors": {"Test Vendor": "TEST_VENDOR"},
            "materials": {"Test Material": "TEST_MATERIAL"},
        }

        synonyms_file = tmp_path / "test_synonyms.json"
        synonyms_file.write_text(json.dumps(synonyms_data))

        normalizer = SynonymNormalizer()
        normalizer.load_synonyms(str(synonyms_file))

        assert normalizer.synonyms == synonyms_data

    def test_load_synonyms_invalid_json(self, tmp_path):
        """Test loading synonyms from invalid JSON file."""
        synonyms_file = tmp_path / "invalid.json"
        synonyms_file.write_text("invalid json content")

        normalizer = SynonymNormalizer()
        normalizer.load_synonyms(str(synonyms_file))

        # Should have empty synonyms on error
        assert normalizer.synonyms == {}

    def test_load_synonyms_missing_file(self):
        """Test loading synonyms from missing file."""
        normalizer = SynonymNormalizer()
        normalizer.load_synonyms("missing_file.json")

        # Should have empty synonyms on error
        assert normalizer.synonyms == {}


class TestVendorNormalization:
    """Test vendor name normalization."""

    def test_normalize_vendor_exact_match(self):
        """Test vendor normalization with exact matches."""
        normalizer = SynonymNormalizer()

        # Exact matches should return canonical form
        assert normalizer.normalize_vendor("WM") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_vendor("Republic Services") == "REPUBLIC_SERVICES"
        assert normalizer.normalize_vendor("Skyline") == "WASTE_MANAGEMENT_SKYLINE_RDF"

    def test_normalize_vendor_case_insensitive(self):
        """Test vendor normalization is case insensitive."""
        normalizer = SynonymNormalizer()

        # Various cases should work
        assert normalizer.normalize_vendor("wm") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_vendor("Wm") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_vendor("WM") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_vendor("republic services") == "REPUBLIC_SERVICES"
        assert normalizer.normalize_vendor("REPUBLIC SERVICES") == "REPUBLIC_SERVICES"

    def test_normalize_vendor_whitespace_handling(self):
        """Test vendor normalization handles whitespace."""
        normalizer = SynonymNormalizer()

        # Leading/trailing whitespace should be stripped
        assert normalizer.normalize_vendor("  WM  ") == "WASTE_MANAGEMENT_DFW_RDF"
        assert (
            normalizer.normalize_vendor("\tRepublic Services\n") == "REPUBLIC_SERVICES"
        )

    def test_normalize_vendor_partial_match(self):
        """Test vendor normalization with partial matching."""
        normalizer = SynonymNormalizer()

        # Vendor normalization supports partial matching
        assert (
            normalizer.normalize_vendor("Waste Management")
            == "WASTE_MANAGEMENT_DFW_RDF"
        )
        assert normalizer.normalize_vendor("WM DFW") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_vendor("DFW RDF") == "WASTE_MANAGEMENT_DFW_RDF"

    def test_normalize_vendor_unknown(self):
        """Test vendor normalization with unknown vendor."""
        normalizer = SynonymNormalizer()

        # Unknown vendor should return stripped original
        assert normalizer.normalize_vendor("Unknown Vendor") == "Unknown Vendor"
        assert normalizer.normalize_vendor("  Unknown Vendor  ") == "Unknown Vendor"

    def test_normalize_vendor_empty_input(self):
        """Test vendor normalization with empty input."""
        normalizer = SynonymNormalizer()

        # Empty input should return empty
        assert normalizer.normalize_vendor("") == ""
        assert normalizer.normalize_vendor(None) is None
        assert normalizer.normalize_vendor("   ") == ""

    def test_normalize_vendor_all_waste_management_variants(self):
        """Test all Waste Management vendor variants."""
        normalizer = SynonymNormalizer()

        wm_variants = [
            "Waste Management",
            "WM",
            "WM Lewisville",
            "WM-Lewisville",
            "Waste Mgmt",
            "Waste Management Lewisville",
            "DFW",
            "WM DFW",
            "DFW RDF",
            "WM DFW RDF",
            "Waste Management DFW",
        ]

        for variant in wm_variants:
            result = normalizer.normalize_vendor(variant)
            assert result == "WASTE_MANAGEMENT_DFW_RDF", f"Failed for: {variant}"

    def test_normalize_vendor_all_skyline_variants(self):
        """Test all Skyline vendor variants."""
        normalizer = SynonymNormalizer()

        skyline_variants = [
            "Skyline",
            "WM Skyline",
            "Skyline RDF",
            "WM Skyline RDF",
            "Waste Management Skyline",
        ]

        for variant in skyline_variants:
            result = normalizer.normalize_vendor(variant)
            assert result == "WASTE_MANAGEMENT_SKYLINE_RDF", f"Failed for: {variant}"

    def test_normalize_vendor_all_republic_variants(self):
        """Test all Republic Services vendor variants."""
        normalizer = SynonymNormalizer()

        republic_variants = ["Republic", "Republic Services"]

        for variant in republic_variants:
            result = normalizer.normalize_vendor(variant)
            assert result == "REPUBLIC_SERVICES", f"Failed for: {variant}"


class TestMaterialNormalization:
    """Test material name normalization."""

    def test_normalize_material_exact_match(self):
        """Test material normalization with exact matches."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_material("Class2") == "CLASS_2_CONTAMINATED"
        assert normalizer.normalize_material("Clean") == "NON_CONTAMINATED"
        assert normalizer.normalize_material("Spoils") == "SPOILS"
        assert normalizer.normalize_material("Rock") == "ROCK"

    def test_normalize_material_case_insensitive(self):
        """Test material normalization is case insensitive."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_material("class2") == "CLASS_2_CONTAMINATED"
        assert normalizer.normalize_material("CLASS2") == "CLASS_2_CONTAMINATED"
        assert normalizer.normalize_material("clean") == "NON_CONTAMINATED"
        assert normalizer.normalize_material("CLEAN") == "NON_CONTAMINATED"

    def test_normalize_material_whitespace_handling(self):
        """Test material normalization handles whitespace."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_material("  Class2  ") == "CLASS_2_CONTAMINATED"
        assert normalizer.normalize_material("\tClean\n") == "NON_CONTAMINATED"

    def test_normalize_material_unknown(self):
        """Test material normalization with unknown material."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_material("Unknown Material") == "Unknown Material"
        assert (
            normalizer.normalize_material("  Unknown Material  ") == "Unknown Material"
        )

    def test_normalize_material_empty_input(self):
        """Test material normalization with empty input."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_material("") == ""
        assert normalizer.normalize_material(None) is None
        assert normalizer.normalize_material("   ") == ""

    def test_normalize_material_all_contaminated_variants(self):
        """Test all contaminated material variants."""
        normalizer = SynonymNormalizer()

        contaminated_variants = [
            "Class2",
            "Class 2",
            "Contaminated",
            "Class 2 Contaminated",
        ]

        for variant in contaminated_variants:
            result = normalizer.normalize_material(variant)
            assert result == "CLASS_2_CONTAMINATED", f"Failed for: {variant}"

    def test_normalize_material_all_clean_variants(self):
        """Test all clean material variants."""
        normalizer = SynonymNormalizer()

        clean_variants = ["Clean", "Clean Fill", "Non-Contaminated", "Non Contaminated"]

        for variant in clean_variants:
            result = normalizer.normalize_material(variant)
            assert result == "NON_CONTAMINATED", f"Failed for: {variant}"


class TestSourceNormalization:
    """Test source location normalization."""

    def test_normalize_source_exact_match(self):
        """Test source normalization with exact matches."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_source("SPG") == "SPG"
        assert normalizer.normalize_source("Pier Ex") == "PIER_EX"
        assert normalizer.normalize_source("MSE Wall") == "MSE_WALL"
        assert normalizer.normalize_source("Beck") == "BECK_SPOILS"

    def test_normalize_source_case_insensitive(self):
        """Test source normalization is case insensitive."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_source("spg") == "SPG"
        assert normalizer.normalize_source("SPG") == "SPG"
        assert normalizer.normalize_source("pier ex") == "PIER_EX"
        assert normalizer.normalize_source("PIER EX") == "PIER_EX"

    def test_normalize_source_whitespace_handling(self):
        """Test source normalization handles whitespace."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_source("  SPG  ") == "SPG"
        assert normalizer.normalize_source("\tPier Ex\n") == "PIER_EX"

    def test_normalize_source_unknown(self):
        """Test source normalization with unknown source."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_source("Unknown Source") == "Unknown Source"
        assert normalizer.normalize_source("  Unknown Source  ") == "Unknown Source"

    def test_normalize_source_empty_input(self):
        """Test source normalization with empty input."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_source("") == ""
        assert normalizer.normalize_source(None) is None
        assert normalizer.normalize_source("   ") == ""


class TestDestinationNormalization:
    """Test destination normalization."""

    def test_normalize_destination_exact_match(self):
        """Test destination normalization with exact matches."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_destination("LDI") == "LDI_YARD"
        assert normalizer.normalize_destination("WM") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_destination("Republic") == "REPUBLIC_SERVICES"
        assert (
            normalizer.normalize_destination("Skyline")
            == "WASTE_MANAGEMENT_SKYLINE_RDF"
        )

    def test_normalize_destination_case_insensitive(self):
        """Test destination normalization is case insensitive."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_destination("ldi") == "LDI_YARD"
        assert normalizer.normalize_destination("LDI") == "LDI_YARD"
        assert normalizer.normalize_destination("wm") == "WASTE_MANAGEMENT_DFW_RDF"
        assert normalizer.normalize_destination("WM") == "WASTE_MANAGEMENT_DFW_RDF"

    def test_normalize_destination_whitespace_handling(self):
        """Test destination normalization handles whitespace."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_destination("  LDI  ") == "LDI_YARD"
        assert normalizer.normalize_destination("\tWM\n") == "WASTE_MANAGEMENT_DFW_RDF"

    def test_normalize_destination_unknown(self):
        """Test destination normalization with unknown destination."""
        normalizer = SynonymNormalizer()

        assert (
            normalizer.normalize_destination("Unknown Destination")
            == "Unknown Destination"
        )
        assert (
            normalizer.normalize_destination("  Unknown Destination  ")
            == "Unknown Destination"
        )

    def test_normalize_destination_empty_input(self):
        """Test destination normalization with empty input."""
        normalizer = SynonymNormalizer()

        assert normalizer.normalize_destination("") == ""
        assert normalizer.normalize_destination(None) is None
        assert normalizer.normalize_destination("   ") == ""


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_normalize_with_empty_synonyms(self):
        """Test normalization with empty synonyms."""
        normalizer = SynonymNormalizer()
        normalizer.synonyms = {}

        # Should return stripped original for all
        assert normalizer.normalize_vendor("Test Vendor") == "Test Vendor"
        assert normalizer.normalize_material("Test Material") == "Test Material"
        assert normalizer.normalize_source("Test Source") == "Test Source"
        assert (
            normalizer.normalize_destination("Test Destination") == "Test Destination"
        )

    def test_normalize_with_missing_category(self):
        """Test normalization with missing category in synonyms."""
        normalizer = SynonymNormalizer()
        normalizer.synonyms = {"vendors": {"Test": "TEST"}}  # No other categories

        # Vendor should work, others should return stripped original
        assert normalizer.normalize_vendor("Test") == "TEST"
        assert normalizer.normalize_material("Test Material") == "Test Material"
        assert normalizer.normalize_source("Test Source") == "Test Source"
        assert (
            normalizer.normalize_destination("Test Destination") == "Test Destination"
        )

    def test_normalize_unicode_characters(self):
        """Test normalization with unicode characters."""
        normalizer = SynonymNormalizer()

        # Unicode should be preserved
        assert normalizer.normalize_vendor("Test Vendor™") == "Test Vendor™"
        assert normalizer.normalize_material("Test Material®") == "Test Material®"

    def test_normalize_special_characters(self):
        """Test normalization with special characters."""
        normalizer = SynonymNormalizer()

        # Special characters should be preserved
        assert normalizer.normalize_vendor("Test-Vendor") == "Test-Vendor"
        assert normalizer.normalize_material("Test_Material") == "Test_Material"
        assert normalizer.normalize_source("Test.Source") == "Test.Source"

    def test_normalize_very_long_strings(self):
        """Test normalization with very long strings."""
        normalizer = SynonymNormalizer()

        long_string = "A" * 1000
        result = normalizer.normalize_vendor(long_string)

        assert result == long_string

    def test_normalize_with_different_line_endings(self):
        """Test normalization with different line endings."""
        normalizer = SynonymNormalizer()

        # Should handle different line endings
        assert normalizer.normalize_vendor("WM\r\n") == "WM"
        assert normalizer.normalize_vendor("WM\r") == "WM"
        assert normalizer.normalize_vendor("WM\n") == "WM"


class TestIntegration:
    """Test integration scenarios."""

    def test_normalize_real_world_examples(self):
        """Test normalization with real-world examples."""
        normalizer = SynonymNormalizer()

        # Real OCR examples
        examples = [
            ("Waste Management", "WASTE_MANAGEMENT_DFW_RDF"),
            ("WM DFW RDF", "WASTE_MANAGEMENT_DFW_RDF"),
            ("Republic Services", "REPUBLIC_SERVICES"),
            ("Class 2", "CLASS_2_CONTAMINATED"),
            ("Clean Fill", "NON_CONTAMINATED"),
            ("South Parking Garage", "SPG"),
            ("LDI Yard", "LDI_YARD"),
        ]

        for input_text, expected in examples:
            # Test with each normalization method
            if (
                "Management" in input_text
                or "Republic" in input_text
                or "Skyline" in input_text
            ):
                result = normalizer.normalize_vendor(input_text)
            elif (
                "Class" in input_text or "Clean" in input_text or "Spoils" in input_text
            ):
                result = normalizer.normalize_material(input_text)
            elif "Garage" in input_text or "Pier" in input_text or "MSE" in input_text:
                result = normalizer.normalize_source(input_text)
            else:
                result = normalizer.normalize_destination(input_text)

            assert (
                result == expected
            ), f"Failed: {input_text} -> {result}, expected {expected}"

    def test_synonym_file_changes_are_reflected(self, tmp_path):
        """Test that changes to synonym file are reflected."""
        # Create initial synonyms file
        initial_synonyms = {"vendors": {"Initial": "INITIAL_VENDOR"}}
        synonyms_file = tmp_path / "synonyms.json"
        synonyms_file.write_text(json.dumps(initial_synonyms))

        normalizer = SynonymNormalizer(str(synonyms_file))
        assert normalizer.normalize_vendor("Initial") == "INITIAL_VENDOR"

        # Update synonyms file
        updated_synonyms = {"vendors": {"Updated": "UPDATED_VENDOR"}}
        synonyms_file.write_text(json.dumps(updated_synonyms))

        # Reload synonyms
        normalizer.load_synonyms(str(synonyms_file))

        # Should reflect changes
        assert normalizer.normalize_vendor("Updated") == "UPDATED_VENDOR"
        assert normalizer.normalize_vendor("Initial") == "Initial"  # No longer mapped


# Performance Tests


class TestPerformance:
    """Test performance of normalization functions."""

    def test_normalize_performance(self):
        """Test that normalization is performant."""
        import time

        normalizer = SynonymNormalizer()

        # Test with 1000 normalizations
        start_time = time.time()

        for _ in range(1000):
            normalizer.normalize_vendor("Waste Management")
            normalizer.normalize_material("Class 2")
            normalizer.normalize_source("SPG")
            normalizer.normalize_destination("LDI")

        elapsed_time = time.time() - start_time

        # Should complete 4000 normalizations in under 1 second
        assert (
            elapsed_time < 1.0
        ), f"Too slow: {elapsed_time:.3f}s for 4000 normalizations"
