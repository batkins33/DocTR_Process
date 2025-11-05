@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===========================
REM Simplified OCR Force Clean Then Embed
REM ===========================
REM Uses the specific conda environment that has DocTR installed

set "PYTHON_CMD=U:\Dev\envs\doctr_env_py310\python.exe"
set "OCREMBED=%~dp0ocr_embed_pdf.py"

REM Check if Python and OCR script exist
if not exist "%PYTHON_CMD%" (
    echo [ERROR] Python not found at: %PYTHON_CMD%
    echo Please check your conda environment path.
    pause
    exit /b 1
)

if not exist "%OCREMBED%" (
    echo [ERROR] OCR script not found at: %OCREMBED%
    echo Please ensure ocr_embed_pdf.py is in the same folder as this batch file.
    pause
    exit /b 1
)

REM Try to find Ghostscript
set "GSCMD="
for %%G in (gswin64c.exe gswin32c.exe gs.exe) do (
  where %%G >nul 2>&1 && set "GSCMD=%%G"
)
if not defined GSCMD (
  echo [WARN] Ghostscript not found on PATH. Will proceed WITHOUT stripping existing text layers.
  echo        Install from https://ghostscript.com/ and ensure gswin64c.exe is on PATH.
)

echo [DEBUG] Script started with %0 arguments
echo [DEBUG] First argument: %~1
echo [DEBUG] Python path: %PYTHON_CMD%
echo [DEBUG] OCR script: %OCREMBED%

REM If no args, show usage; else process args
if "%~1"=="" (
  echo.
  echo [INFO] Usage: Drag and drop PDF files onto this batch file
  echo        Or run: %0 "file1.pdf" "file2.pdf"
  echo.
  echo [DEBUG] No arguments provided - waiting for user input
  pause
  exit /b 0
)

echo [DEBUG] Processing arguments...
:loop_args
  if "%~1"=="" goto :done
  echo [DEBUG] Processing argument: %~1
  call :process_one "%~1"
  shift
  goto :loop_args

:done
echo.
echo [DONE] All tasks complete.
pause
exit /b 0

REM ===========================
REM Subroutine: process_one
REM ===========================
:process_one
set "IN=%~1"
if not exist "%IN%" (
  echo [SKIP] File not found: %IN%
  goto :eof
)

REM Skip non-PDFs safely
if /I not "%~x1"==".pdf" (
  echo [SKIP] Not a PDF: %IN%
  goto :eof
)

set "DRIVE=%~d1"
set "DIR=%~p1"
set "NAME=%~n1"
set "BASE=%DRIVE%%DIR%%NAME%"
set "OUT_FINAL=%BASE%_searchable.pdf"
set "CLEAN=%BASE%_clean.pdf"
set "OUT_FROM_CLEAN=%BASE%_clean_ocr.pdf"
set "OUT_FROM_ORIG=%BASE%_ocr.pdf"

echo.
echo ==========================================================
echo [FILE] %IN%
echo ==========================================================

REM -------- Detect existing text layer --------
echo [STEP] Checking for existing text layer...
set "HAS_TEXT=0"

"%PYTHON_CMD%" -c "import pdfplumber; pdf=pdfplumber.open(r'%IN%'); print('1' if any((page.extract_text() or '').strip() for page in pdf.pages) else '0')" 2>nul > temp_hastext.txt
if exist temp_hastext.txt (
    for /f %%V in (temp_hastext.txt) do set "HAS_TEXT=%%V"
    del temp_hastext.txt
)

if "%HAS_TEXT%"=="1" (
  echo [INFO] Existing text/OCR layer detected.
  if defined GSCMD (
    echo [STEP] Stripping text layer with Ghostscript...
    "%GSCMD%" -q -o "%CLEAN%" -sDEVICE=pdfwrite -dFILTERTEXT "%IN%"
    if errorlevel 1 (
      echo [WARN] Ghostscript failed; continuing with original (may cause duplicate text layer).
      set "CANDIDATE=%IN%"
    ) else (
      echo [INFO] Text layer stripped successfully.
      set "CANDIDATE=%CLEAN%"
    )
  ) else (
    echo [WARN] Ghostscript unavailable; proceeding with original (may cause duplicate text layer).
    set "CANDIDATE=%IN%"
  )
) else (
  echo [INFO] No text layer found; using original as input to OCR.
  set "CANDIDATE=%IN%"
)

REM -------- Run OCR embedding --------
echo [STEP] Embedding fresh OCR layer via DocTR...
"%PYTHON_CMD%" "%OCREMBED%" "!CANDIDATE!" --force
if errorlevel 1 (
  echo [ERROR] OCR embedding failed for: %IN%
  goto :cleanup
)

REM -------- Normalize output name --------
set "ACTUAL_OUTPUT="
if exist "%OUT_FROM_CLEAN%" set "ACTUAL_OUTPUT=%OUT_FROM_CLEAN%"
if exist "%OUT_FROM_ORIG%" set "ACTUAL_OUTPUT=%OUT_FROM_ORIG%"

if defined ACTUAL_OUTPUT (
  if exist "%OUT_FINAL%" (
    echo [INFO] Backing up existing searchable PDF...
    set "TIMESTAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
    set "TIMESTAMP=!TIMESTAMP: =0!"
    ren "%OUT_FINAL%" "%NAME%_searchable_backup_!TIMESTAMP!.pdf" >nul 2>&1
  )
  move /y "!ACTUAL_OUTPUT!" "%OUT_FINAL%" >nul
)

if exist "%OUT_FINAL%" (
  echo [SUCCESS] Output created: "%OUT_FINAL%"

  REM Quick verification that it's searchable
  echo [STEP] Verifying searchable PDF...
  "%PYTHON_CMD%" -c "import pdfplumber; pdf=pdfplumber.open(r'%OUT_FINAL%'); print('SUCCESS: PDF is searchable!' if any((page.extract_text() or '').strip() for page in pdf.pages) else 'WARNING: PDF may not be searchable')" 2>nul
) else (
  echo [WARN] Expected output not found; check logs above.
)

:cleanup
REM Cleanup intermediate files
if exist "%CLEAN%" (
    echo [INFO] Cleaning up intermediate file...
    del /q "%CLEAN%" >nul 2>&1
)

goto :eof
