@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo OCR Batch File Debug Test
echo ========================================

set "PYTHON_CMD=U:\Dev\envs\doctr_env_py310\python.exe"
set "OCR_SCRIPT=%~dp0ocr_embed_pdf.py"

echo [TEST 1] Checking Python...
if exist "%PYTHON_CMD%" (
    echo ✅ Python found: %PYTHON_CMD%
) else (
    echo ❌ Python NOT found: %PYTHON_CMD%
    pause & exit /b 1
)

echo [TEST 2] Checking OCR script...
if exist "%OCR_SCRIPT%" (
    echo ✅ OCR script found: %OCR_SCRIPT%
) else (
    echo ❌ OCR script NOT found: %OCR_SCRIPT%
    pause & exit /b 1
)

echo [TEST 3] Testing Python imports...
"%PYTHON_CMD%" -c "import pdfplumber, fitz, doctr; print('✅ All imports work')"
if errorlevel 1 (
    echo ❌ Python imports failed
    pause & exit /b 1
)

echo [TEST 4] Testing OCR script help...
"%PYTHON_CMD%" "%OCR_SCRIPT%" --help
if errorlevel 1 (
    echo ❌ OCR script failed
    pause & exit /b 1
)

if "%~1"=="" (
    echo.
    echo ✅ All tests passed! 
    echo [USAGE] Now drag a PDF file onto this batch file to test OCR
) else (
    echo.
    echo [PROCESSING] Running OCR on: %~1
    echo ========================================
    "%PYTHON_CMD%" "%OCR_SCRIPT%" "%~1" --force
    echo ========================================
    echo [COMPLETE] Check output above for results
)

pause