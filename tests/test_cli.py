"""Unit tests for CLI interface (Issue #19)."""
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.truck_tickets.cli.main import create_parser, main, setup_logging, validate_args


class TestCLIParser:
    """Test suite for CLI argument parser."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "ticketiq"

    def test_version_argument(self, capsys):
        """Test --version flag."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        result = main([])
        assert result == 0

    def test_process_command_required_args(self):
        """Test process command requires input and job."""
        parser = create_parser()
        
        # Missing both
        with pytest.raises(SystemExit):
            parser.parse_args(["process"])

    def test_process_command_with_required_args(self):
        """Test process command with required arguments."""
        parser = create_parser()
        args = parser.parse_args(["process", "--input", "test/path", "--job", "24-105"])
        
        assert args.command == "process"
        assert args.input == "test/path"
        assert args.job == "24-105"

    def test_process_command_with_all_exports(self):
        """Test process command with all export options."""
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", "test/path",
            "--job", "24-105",
            "--export-xlsx", "tracking.xlsx",
            "--export-invoice", "invoice.csv",
            "--export-manifest", "manifest.csv",
            "--export-review", "review.csv"
        ])
        
        assert args.export_xlsx == "tracking.xlsx"
        assert args.export_invoice == "invoice.csv"
        assert args.export_manifest == "manifest.csv"
        assert args.export_review == "review.csv"

    def test_process_command_with_processing_options(self):
        """Test process command with processing options."""
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", "test/path",
            "--job", "24-105",
            "--threads", "4",
            "--config", "./custom_config",
            "--vendor-template", "WM_LEWISVILLE",
            "--reprocess",
            "--dry-run"
        ])
        
        assert args.threads == 4
        assert args.config == "./custom_config"
        assert args.vendor_template == "WM_LEWISVILLE"
        assert args.reprocess is True
        assert args.dry_run is True

    def test_process_command_with_output_options(self):
        """Test process command with output options."""
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", "test/path",
            "--job", "24-105",
            "--verbose",
            "--log-file", "process.log"
        ])
        
        assert args.verbose is True
        assert args.log_file == "process.log"

    def test_process_command_quiet_flag(self):
        """Test process command with quiet flag."""
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", "test/path",
            "--job", "24-105",
            "--quiet"
        ])
        
        assert args.quiet is True

    def test_export_command_required_args(self):
        """Test export command requires job."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["export"])

    def test_export_command_with_all_options(self):
        """Test export command with all export options."""
        parser = create_parser()
        args = parser.parse_args([
            "export",
            "--job", "24-105",
            "--xlsx", "tracking.xlsx",
            "--invoice", "invoice.csv",
            "--manifest", "manifest.csv",
            "--review", "review.csv",
            "--verbose"
        ])
        
        assert args.command == "export"
        assert args.job == "24-105"
        assert args.xlsx == "tracking.xlsx"
        assert args.invoice == "invoice.csv"
        assert args.manifest == "manifest.csv"
        assert args.review == "review.csv"
        assert args.verbose is True


class TestLoggingSetup:
    """Test suite for logging configuration."""

    @pytest.fixture(autouse=True)
    def reset_logging(self):
        """Reset logging configuration before each test."""
        import logging
        # Remove all handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # Reset level
        logger.setLevel(logging.WARNING)
        yield
        # Cleanup after test
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def test_default_logging_level(self):
        """Test default logging level is INFO."""
        import logging
        setup_logging()
        logger = logging.getLogger()
        assert logger.level == logging.INFO

    def test_verbose_logging_level(self):
        """Test verbose flag sets DEBUG level."""
        import logging
        setup_logging(verbose=True)
        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_quiet_logging_level(self):
        """Test quiet flag sets ERROR level."""
        import logging
        setup_logging(quiet=True)
        logger = logging.getLogger()
        assert logger.level == logging.ERROR


class TestArgumentValidation:
    """Test suite for argument validation."""

    def test_validate_nonexistent_input_path(self, tmp_path):
        """Test validation fails for nonexistent input path."""
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", str(tmp_path / "nonexistent"),
            "--job", "24-105"
        ])
        
        assert validate_args(args) is False

    def test_validate_existing_input_path(self, tmp_path):
        """Test validation succeeds for existing input path."""
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", str(tmp_path),
            "--job", "24-105"
        ])
        
        assert validate_args(args) is True

    def test_validate_input_must_be_directory(self, tmp_path):
        """Test validation fails if input is a file."""
        test_file = tmp_path / "test.pdf"
        test_file.touch()
        
        parser = create_parser()
        args = parser.parse_args([
            "process",
            "--input", str(test_file),
            "--job", "24-105"
        ])
        
        assert validate_args(args) is False

    def test_validate_export_requires_at_least_one_option(self):
        """Test export command requires at least one export option."""
        parser = create_parser()
        args = parser.parse_args([
            "export",
            "--job", "24-105"
        ])
        
        assert validate_args(args) is False

    def test_validate_export_with_option_succeeds(self):
        """Test export command with at least one option succeeds."""
        parser = create_parser()
        args = parser.parse_args([
            "export",
            "--job", "24-105",
            "--xlsx", "output.xlsx"
        ])
        
        assert validate_args(args) is True


class TestProcessCommand:
    """Test suite for process command execution."""

    @patch("src.truck_tickets.cli.commands.process.logger")
    def test_process_command_dry_run(self, mock_logger, tmp_path):
        """Test process command in dry-run mode."""
        # Create test PDF
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()
        
        result = main([
            "process",
            "--input", str(tmp_path),
            "--job", "24-105",
            "--dry-run"
        ])
        
        assert result == 0

    @patch("src.truck_tickets.cli.commands.process.logger")
    def test_process_command_no_pdfs_found(self, mock_logger, tmp_path):
        """Test process command when no PDFs found."""
        result = main([
            "process",
            "--input", str(tmp_path),
            "--job", "24-105"
        ])
        
        assert result == 0

    @patch("src.truck_tickets.cli.commands.process.logger")
    def test_process_command_with_exports(self, mock_logger, tmp_path):
        """Test process command with export options."""
        # Create test PDF
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()
        
        result = main([
            "process",
            "--input", str(tmp_path),
            "--job", "24-105",
            "--export-xlsx", str(tmp_path / "tracking.xlsx"),
            "--export-invoice", str(tmp_path / "invoice.csv")
        ])
        
        assert result == 0


class TestExportCommand:
    """Test suite for export command execution."""

    @patch("src.truck_tickets.cli.commands.export.logger")
    def test_export_command_single_export(self, mock_logger):
        """Test export command with single export option."""
        result = main([
            "export",
            "--job", "24-105",
            "--xlsx", "tracking.xlsx"
        ])
        
        assert result == 0

    @patch("src.truck_tickets.cli.commands.export.logger")
    def test_export_command_multiple_exports(self, mock_logger):
        """Test export command with multiple export options."""
        result = main([
            "export",
            "--job", "24-105",
            "--xlsx", "tracking.xlsx",
            "--invoice", "invoice.csv",
            "--manifest", "manifest.csv"
        ])
        
        assert result == 0


class TestMainFunction:
    """Test suite for main entry point."""

    def test_main_with_no_args_shows_help(self, capsys):
        """Test main with no arguments shows help."""
        result = main([])
        assert result == 0

    def test_main_with_invalid_command(self):
        """Test main with invalid command returns error."""
        # This will fail at parse_args level
        with pytest.raises(SystemExit):
            main(["invalid_command"])

    def test_main_keyboard_interrupt(self, tmp_path):
        """Test main handles KeyboardInterrupt gracefully."""
        with patch("src.truck_tickets.cli.commands.process.process_command") as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            
            result = main([
                "process",
                "--input", str(tmp_path),
                "--job", "24-105"
            ])
            
            assert result == 130  # SIGINT exit code

    def test_main_unexpected_exception(self, tmp_path):
        """Test main handles unexpected exceptions."""
        with patch("src.truck_tickets.cli.commands.process.process_command") as mock_process:
            mock_process.side_effect = RuntimeError("Test error")
            
            result = main([
                "process",
                "--input", str(tmp_path),
                "--job", "24-105"
            ])
            
            assert result == 1
