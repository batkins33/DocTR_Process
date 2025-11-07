# Activate DocTR Python 3.10 Environment
# Usage: .\activate_env.ps1

Write-Host "Activating doctr_env_py310 (Python 3.10.18)..." -ForegroundColor Green

# Activate conda environment
& C:\ProgramData\miniconda3\Scripts\conda.exe activate doctr_env_py310

Write-Host "✅ Environment activated!" -ForegroundColor Green
Write-Host ""
Write-Host "Verify Python version:" -ForegroundColor Yellow
python --version
Write-Host ""
Write-Host "To run E2E tests:" -ForegroundColor Yellow
Write-Host "  pytest tests/integration/test_pipeline_e2e.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "To deactivate:" -ForegroundColor Yellow
Write-Host "  conda deactivate" -ForegroundColor Cyan
