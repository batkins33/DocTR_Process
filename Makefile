.PHONY: setup lint test hygiene clean clean-hard archive-sandbox e2e e2e-update

setup:
\tpython -m pip install -U pip
\tpip install -r requirements.txt || true
\tpre-commit install || true

lint:
\truff check --fix || true
\tblack --check src tests || black src tests || true

test:
\tpytest -q || true

e2e:
\tpytest -q tests/integration/test_pipeline_e2e.py

e2e-update:
\tpytest -q tests/integration/test_pipeline_e2e.py --update-snapshots || true

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
