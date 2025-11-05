param()
Remove-Item artifacts,scratch,reports,.pytest_cache,.mypy_cache,.ruff_cache,htmlcov
  -Recurse -Force -ErrorAction SilentlyContinue
