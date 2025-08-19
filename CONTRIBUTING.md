# Contributing

Thank you for your interest in improving DocTR_Process!

## Development Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
2. Install system packages `tesseract-ocr` and `poppler-utils` for OCR and PDF support.

## Testing

Run the test suite with:

```bash
pytest -vv
```

## Guidelines

- Use feature branches and submit pull requests against `main`.
- Ensure new code includes tests and docstrings.
- Format code with `black` and run `pytest` before submitting.
- For major changes, update `CHANGELOG.md`.

## Working with Amazon Q

- To route an issue to Amazon Q, add the `amazon-q` label.
- You can also comment `/q dev` on the issue to trigger Q to implement a fix or feature.
- Q will respond with a pull request linked to the issue.

