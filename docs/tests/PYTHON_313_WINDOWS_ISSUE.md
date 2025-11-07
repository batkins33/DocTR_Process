# Python 3.13 + Windows + SQLAlchemy Compatibility Issue

## Problem

Python 3.13 on Windows has a known issue with asyncio and the `_overlapped` module that affects SQLAlchemy:

```
OSError: [WinError 10106] The requested service provider could not be loaded or initialized
```

This occurs when SQLAlchemy tries to import asyncio utilities, even though we're using sync-only database operations.

## Impact

- E2E tests that invoke the CLI fail
- Direct Python imports work fine (tests pass)
- Only affects `python -m truck_tickets` CLI invocation

## Workarounds

### Option 1: Downgrade Python (Recommended)
```bash
# Use Python 3.11 or 3.12
pyenv install 3.12.0
pyenv local 3.12.0
```

### Option 2: Set Environment Variable
```bash
# Before running tests
set PYTHONASYNCIODEBUG=0
pytest tests/integration/
```

### Option 3: Use Direct Imports
Instead of CLI subprocess calls, import and call functions directly in tests.

## Current Status

- ✅ Test framework implemented
- ✅ Test fixtures copied
- ✅ Database utilities working
- ❌ CLI subprocess tests blocked by Python 3.13 issue
- ✅ Direct import tests passing (2/4 tests)

## Resolution

This is a known Python 3.13.0-3.13.5 issue on Windows. Options:
1. Wait for Python 3.13.6 fix
2. Downgrade to Python 3.12
3. Modify tests to use direct imports instead of subprocess CLI calls

## References

- https://github.com/python/cpython/issues/115874
- https://github.com/sqlalchemy/sqlalchemy/issues/10241
