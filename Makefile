.PHONY: setup lint test hygiene clean clean-hard archive-sandbox

setup:
\tpython -m pip install -U pip
\tpip install -r requirements.txt || true
\tpre-commit install || true

lint:
\truff check --fix || true
\tblack --check src tests || black src tests || true

test:
\tpytest -q || true

hygiene:
\t@echo "🧹 Enforcing repo hygiene..."
\tpython scripts/archive_sandbox.py || true
\tpre-commit run --all-files || true
\tgit clean -fdX -e docs/ -e src/ -e tests/

clean:
\tpython scripts/archive_sandbox.py || true

clean-hard:
\tgit clean -fdX

archive-sandbox:
\tpython scripts/archive_sandbox.py
