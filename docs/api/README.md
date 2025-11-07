# DocTR Process API Documentation

This directory contains the Sphinx configuration and source files for generating the DocTR Process API documentation.

## Building the Documentation

### Prerequisites

- Python 3.10+
- The DocTR Process package installed

### Quick Start

1. **Install documentation dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the HTML documentation:**
   ```bash
   # Using make (Unix/Linux/macOS)
   make html

   # Or using sphinx-build directly
   sphinx-build -M html . _build
   ```

3. **View the documentation:**
   Open `_build/html/index.html` in your browser

### Windows Users

Use the provided batch file:
```cmd
build_docs.bat
```

## Development

### Live Reload

For development with live reload:
```bash
make livehtml
# or
sphinx-autobuild . _build/html
```

### Clean Build

Remove all generated files:
```bash
make clean
```

### Check Links

Validate external links:
```bash
make linkcheck
```

### Coverage Report

Generate documentation coverage report:
```bash
make coverage
```

## Documentation Structure

```
docs/api/
├── conf.py                 # Sphinx configuration
├── index.rst               # Main documentation page
├── introduction.rst        # Architecture overview
├── quickstart.rst          # Getting started guide
├── api_reference.rst       # API reference index
├── api/                    # Detailed API documentation
│   ├── processing.rst     # Processing pipeline modules
│   ├── database.rst       # Database layer
│   ├── extractors.rst     # Field extraction modules
│   ├── models.rst         # Data models
│   ├── exporters.rst      # Export generation
│   ├── utils.rst          # Utility functions
│   └── cli.rst            # Command-line interface
├── _static/               # Custom static files
├── _templates/            # Custom templates
├── Makefile              # Build commands
├── build_docs.bat        # Windows build script
└── requirements.txt      # Documentation dependencies
```

## Configuration

The documentation is configured in `conf.py` with the following key settings:

- **Extensions:** autodoc, autosummary, napoleon, viewcode, intersphinx
- **Theme:** Read the Docs theme
- **Source Path:** Points to `../../src` for the truck_tickets package
- **Autodoc:** Automatically generates docs from docstrings

## Features

- **Auto-generated from source code** using Sphinx autodoc
- **Google/NumPy style docstrings** supported via Napoleon extension
- **Cross-references** between modules and classes
- **Source code links** for easy navigation
- **Search functionality** across all documentation
- **Responsive design** for mobile and desktop

## Updating Documentation

The documentation is automatically generated from the source code docstrings. To update:

1. **Update docstrings** in the source code
2. **Add new modules** to the appropriate `.rst` files
3. **Rebuild** the documentation

### Adding New Modules

When adding a new module, include it in the appropriate API section file:

```rst
.. automodule:: truck_tickets.new_module
   :members:
   :undoc-members:
   :show-inheritance:
```

Then add it to the main `api_reference.rst` TOC.

## Deployment

The built documentation in `_build/html/` can be deployed to any static web server or hosted on GitHub Pages, Netlify, or similar platforms.

## Troubleshooting

### Import Errors

If you get import errors, ensure:
1. The source path is correct in `conf.py`
2. The truck_tickets package is installed
3. All dependencies are installed

### Missing Documentation

If classes or functions are missing:
1. Check they have proper docstrings
2. Verify they're imported in the module's `__all__` list
3. Ensure the module is included in the appropriate `.rst` file

### Build Errors

Common build errors and solutions:
- **"autodoc failed to import"**: Check Python path and package installation
- **"Theme not found"**: Install sphinx-rtd-theme
- **"Extension not found"**: Install missing extensions from requirements.txt
