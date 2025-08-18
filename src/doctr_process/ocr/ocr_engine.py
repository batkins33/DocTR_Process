"""Wrapper for various OCR engines."""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
from PIL import Image


# Global cache for OCR results
_ocr_cache: Dict[str, Tuple[str, Any]] = {}


def _get_cache_key(img_hash: str, engine_name: str, params: Dict[str, Any]) -> str:
    """Generate a cache key from image hash, engine name, and parameters."""
    params_str = json.dumps(params, sort_keys=True)
    cache_data = f"{img_hash}:{engine_name}:{params_str}"
    return hashlib.md5(cache_data.encode()).hexdigest()


def _load_cache_from_disk(cache_dir: str) -> None:
    """Load OCR cache from disk if it exists."""
    global _ocr_cache
    cache_file = Path(cache_dir) / "ocr_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                _ocr_cache = json.load(f)
                logging.info(f"Loaded {len(_ocr_cache)} cached OCR results")
        except Exception as e:
            logging.warning(f"Failed to load OCR cache: {e}")
            _ocr_cache = {}


def _save_cache_to_disk(cache_dir: str) -> None:
    """Save OCR cache to disk."""
    global _ocr_cache
    if not _ocr_cache:
        return
    
    cache_file = Path(cache_dir) / "ocr_cache.json"
    os.makedirs(cache_dir, exist_ok=True)
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(_ocr_cache, f, indent=2)
            logging.info(f"Saved {len(_ocr_cache)} OCR results to cache")
    except Exception as e:
        logging.warning(f"Failed to save OCR cache: {e}")


def get_engine(name: str, params: Optional[Dict[str, Any]] = None, cache_dir: Optional[str] = None):
    """Get OCR engine with optional parameters and caching support.
    
    Args:
        name: Engine name ('tesseract', 'easyocr', 'doctr')
        params: Engine-specific parameters
        cache_dir: Directory for caching OCR results
    
    Returns:
        Callable OCR function
    """
    name = name.lower()
    if params is None:
        params = {}
    
    # Load cache if enabled
    if cache_dir:
        _load_cache_from_disk(cache_dir)
    
    def _get_image_hash(img):
        """Helper to get image hash for caching."""
        from io import BytesIO
        import hashlib
        if isinstance(img, Image.Image):
            with BytesIO() as buf:
                img.save(buf, format="PNG")
                return hashlib.sha256(buf.getvalue()).hexdigest()
        return None
    
    def _check_cache_and_run(img, engine_func):
        """Check cache before running OCR."""
        if not cache_dir:
            return engine_func(img)
        
        img_hash = _get_image_hash(img)
        if img_hash:
            cache_key = _get_cache_key(img_hash, name, params)
            if cache_key in _ocr_cache:
                logging.debug(f"Cache hit for {name} OCR")
                result = _ocr_cache[cache_key]
                return result[0], result[1] if len(result) > 1 else None
        
        # Run OCR and cache result
        result = engine_func(img)
        if img_hash and cache_dir:
            cache_key = _get_cache_key(img_hash, name, params)
            _ocr_cache[cache_key] = result
            # Periodically save cache
            if len(_ocr_cache) % 10 == 0:
                _save_cache_to_disk(cache_dir)
        
        return result
    
    if name == "tesseract":
        import pytesseract
        
        # Extract tesseract-specific parameters
        config = params.get("config", "")
        lang = params.get("lang", "eng")
        timeout = params.get("timeout", 0)

        def _run(img):
            def _ocr_single(single_img):
                kwargs = {}
                if lang != "eng":  # Only add if not default
                    kwargs["lang"] = lang
                if config:
                    kwargs["config"] = config
                if timeout > 0:
                    kwargs["timeout"] = timeout
                if kwargs:
                    return pytesseract.image_to_string(single_img, **kwargs)
                else:
                    return pytesseract.image_to_string(single_img)
            
            def _engine_func(image):
                imgs = [image] if not isinstance(image, list) else image
                texts = [_ocr_single(im) for im in imgs]
                return (texts[0], None) if len(texts) == 1 else (texts, None)
            
            return _check_cache_and_run(img, _engine_func)

        return _run
        
    elif name == "easyocr":
        from easyocr import Reader
        
        # Extract easyocr-specific parameters
        languages = params.get("languages", ["en"])
        gpu = params.get("gpu", False)
        
        reader = Reader(languages, gpu=gpu)

        def _run(img):
            def _engine_func(image):
                imgs = [image] if not isinstance(image, list) else image
                texts = []
                for im in imgs:
                    r = reader.readtext(im)
                    texts.append(" ".join(t for _, t, _ in r))
                return (texts[0], None) if len(texts) == 1 else (texts, None)
            
            return _check_cache_and_run(img, _engine_func)

        return _run
        
    else:  # doctr requested
        try:
            from doctr.models import ocr_predictor
            from doctr.io import DocumentFile
            import numpy as np
            from PIL import Image
            
            # Extract doctr-specific parameters
            pretrained = params.get("pretrained", True)
            assume_straight_pages = params.get("assume_straight_pages", True)
            
            predictor_kwargs = {"pretrained": pretrained}
            if "det_arch" in params:
                predictor_kwargs["det_arch"] = params["det_arch"]
            if "reco_arch" in params:
                predictor_kwargs["reco_arch"] = params["reco_arch"]
            
            predictor = ocr_predictor(**predictor_kwargs)

            def _run(img):
                def _engine_func(image):
                    imgs = [image] if not isinstance(image, list) else image
                    np_imgs = []
                    for im in imgs:
                        if isinstance(im, np.ndarray):
                            np_imgs.append(im)
                        elif isinstance(im, Image.Image):
                            np_imgs.append(np.array(im))
                        else:
                            np_imgs.append(im)
                    doc = DocumentFile.from_images(np_imgs)
                    res = predictor(doc)
                    pages = res.pages
                    texts = [page.render() for page in pages]
                    return (texts[0], pages[0]) if len(texts) == 1 else (texts, pages)
                
                return _check_cache_and_run(img, _engine_func)

            return _run
            
        except Exception:
            # fallback so tests/environments without doctr still pass
            import warnings, pytesseract

            warnings.warn("doctr not available; falling back to tesseract")
            
            # Use tesseract parameters for fallback
            config = params.get("config", "")
            lang = params.get("lang", "eng")
            timeout = params.get("timeout", 0)

            def _run(img):
                def _engine_func(image):
                    imgs = [image] if not isinstance(image, list) else image
                    kwargs = {}
                    if lang != "eng":  # Only add if not default
                        kwargs["lang"] = lang
                    if config:
                        kwargs["config"] = config
                    if timeout > 0:
                        kwargs["timeout"] = timeout
                    if kwargs:
                        texts = [pytesseract.image_to_string(im, **kwargs) for im in imgs]
                    else:
                        texts = [pytesseract.image_to_string(im) for im in imgs]
                    return (texts[0], None) if len(texts) == 1 else (texts, None)
                
                return _check_cache_and_run(img, _engine_func)

            return _run


def save_ocr_cache(cache_dir: str) -> None:
    """Explicitly save OCR cache to disk."""
    if cache_dir:
        _save_cache_to_disk(cache_dir)


def clear_ocr_cache() -> None:
    """Clear the in-memory OCR cache."""
    global _ocr_cache
    _ocr_cache = {}
