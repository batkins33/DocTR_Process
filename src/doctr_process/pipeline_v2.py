"""Refactored OCR pipeline with modular structure."""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any

from tqdm import tqdm

from .io import InputHandler, OutputManager
from .extract import ImageExtractor, OCRProcessor
from .parse import FieldExtractor, VendorDetector
from .ocr.config_utils import load_config, load_extraction_rules
from .ocr.vendor_utils import load_vendor_rules_from_csv
from .output.factory import create_handlers
from .resources import get_config_path


class RefactoredPipeline:
    """Refactored OCR pipeline with modular components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_components()
    
    def setup_components(self):
        """Initialize pipeline components."""
        # Load rules and configurations
        extraction_rules_path = self.config.get("extraction_rules_yaml")
        if extraction_rules_path:
            self.extraction_rules = load_extraction_rules(extraction_rules_path)
        else:
            self.extraction_rules = load_extraction_rules()
        
        vendor_csv_path = self.config.get("vendor_keywords_csv")
        if vendor_csv_path:
            self.vendor_rules = load_vendor_rules_from_csv(vendor_csv_path)
        else:
            try:
                self.vendor_rules = load_vendor_rules_from_csv(str(get_config_path("ocr_keywords.csv")))
            except FileNotFoundError:
                from .pipeline import CONFIG_DIR
                self.vendor_rules = load_vendor_rules_from_csv(str(CONFIG_DIR / "ocr_keywords.csv"))
        
        # Initialize components
        self.input_handler = InputHandler(self.config.get("input_pdf") or self.config.get("input_dir"))
        self.output_manager = OutputManager(
            self.config.get("output_dir", "./outputs"),
            prefer_timestamp=self.config.get("prefer_timestamp", False)
        )
        self.image_extractor = ImageExtractor(
            dpi=self.config.get("dpi", 300),
            poppler_path=self.config.get("poppler_path")
        )
        self.ocr_processor = OCRProcessor(
            engine_name=self.config.get("ocr_engine", "doctr"),
            orientation_method=self.config.get("orientation_check", "tesseract")
        )
        self.field_extractor = FieldExtractor(self.extraction_rules)
        self.vendor_detector = VendorDetector(self.vendor_rules)
        
        # Output handlers
        output_format = self.config.get("output_format", ["csv"])
        self.output_handlers = create_handlers(output_format, self.config)
    
    def process_file(self, file_name: str, file_path: Path, file_data: bytes) -> List[Dict[str, Any]]:
        """Process a single file and return extracted data."""
        logging.info(f"Processing: {file_name}")
        
        # Create per-input subdirectory
        input_subdir = self.output_manager.get_input_subdir(file_name)
        
        # Extract images
        try:
            if file_data:
                images = list(self.image_extractor.extract_from_bytes(file_data, file_name))
            else:
                images = list(self.image_extractor.extract_from_file(file_path))
        except Exception as e:
            logging.error(f"Failed to extract images from {file_name}: {e}")
            return []
        
        if not images:
            logging.warning(f"No images extracted from {file_name}")
            return []
        
        # Process OCR in batches for efficiency
        batch_size = self.config.get("batch_size", 5)
        all_results = []
        
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_results = self.ocr_processor.process_batch(batch_images)
            
            # Process each page result
            for j, ocr_result in enumerate(batch_results):
                page_num = i + j + 1
                
                # Detect vendor
                vendor_name, vendor_type, confidence, display_name = self.vendor_detector.detect_vendor(
                    ocr_result["text"]
                )
                
                # Extract fields
                fields = self.field_extractor.extract_fields(
                    ocr_result["result_page"], vendor_name
                )
                
                # Validate fields
                field_issues = self.field_extractor.validate_fields(fields)
                
                # Build result record
                result = {
                    "file": file_name,
                    "page": page_num,
                    "vendor": display_name,
                    **fields,
                    "ocr_text": ocr_result["text"],
                    "page_hash": ocr_result["page_hash"],
                    "orientation": ocr_result["orientation"],
                    "field_issues": field_issues,
                    **ocr_result["timings"]
                }
                
                all_results.append(result)
        
        # Clean up images
        for img in images:
            if hasattr(img, 'close'):
                img.close()
        
        return all_results
    
    def run(self) -> None:
        """Execute the pipeline."""
        start_time = time.perf_counter()
        all_results = []
        
        # Process all input files
        files_processed = 0
        
        if self.config.get("batch_mode"):
            # Process multiple files
            for file_name, file_path, file_data in tqdm(
                self.input_handler.iter_file_contents(),
                desc="Processing files"
            ):
                try:
                    results = self.process_file(file_name, file_path, file_data)
                    all_results.extend(results)
                    files_processed += 1
                except Exception as e:
                    logging.error(f"Failed to process {file_name}: {e}")
                    # Add error record
                    all_results.append({
                        "file": file_name,
                        "page": 1,
                        "vendor": None,
                        "error": str(e)
                    })
        else:
            # Process single file
            input_path = Path(self.config.get("input_pdf"))
            try:
                results = self.process_file(input_path.name, input_path, None)
                all_results.extend(results)
                files_processed = 1
            except Exception as e:
                logging.error(f"Failed to process {input_path}: {e}")
                all_results.append({
                    "file": input_path.name,
                    "page": 1,
                    "vendor": None,
                    "error": str(e)
                })
        
        # Write outputs
        for handler in self.output_handlers:
            handler.write(all_results, self.config)
        
        # Log statistics
        total_time = time.perf_counter() - start_time
        ocr_stats = self.ocr_processor.get_stats()
        
        logging.info(f"Pipeline completed:")
        logging.info(f"  Files processed: {files_processed}")
        logging.info(f"  Pages processed: {len(all_results)}")
        logging.info(f"  Total time: {total_time:.2f}s")
        logging.info(f"  OCR stats: {ocr_stats}")


def run_refactored_pipeline(config_path: str = None) -> None:
    """Run the refactored pipeline."""
    # Load configuration
    if config_path:
        config = load_config(config_path)
    else:
        config = load_config()
    
    # Resolve input configuration
    from .ocr.input_picker import resolve_input
    config = resolve_input(config)
    
    # Create and run pipeline
    pipeline = RefactoredPipeline(config)
    pipeline.run()