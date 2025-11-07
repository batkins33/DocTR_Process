@echo off
REM Build documentation for DocTR Process API

echo Installing documentation dependencies...
pip install sphinx sphinx-rtd-theme sphinx-autobuild

echo Cleaning previous build...
if exist _build rmdir /s /q _build

echo Building HTML documentation...
sphinx-build -M html . _build

echo.
echo Documentation built successfully!
echo Open: _build\html\index.html
echo.
pause
