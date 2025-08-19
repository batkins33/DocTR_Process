#!/usr/bin/env python3
"""Audit repository for stale/legacy imports after package reorganization.

This script walks a repository, parses Python files using ``ast`` and reports
imports that refer to the old layout (``pipeline``, ``ocr``, ``preflight`` …).
It can optionally rewrite simple cases in-place when ``--fix`` is supplied.

The canonical package prefix is ``doctr_process``.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

CANONICAL = "doctr_process"
OCR_SUBMODULES = {
    "config_utils",
    "input_picker",
    "ocr_engine",
    "ocr_utils",
    "preflight",
    "reporting_utils",
    "vendor_utils",
}
LEGACY_TOPLEVEL = {"pipeline", "ocr", "output"}.union(OCR_SUBMODULES)
EXCLUDE_DIRS = {
    "venv",
    ".venv",
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".pytest_cache",
}


@dataclass
class Finding:
    file: str
    lineno: int
    col: int
    line: str
    classification: str
    suggestion: Optional[str]
    new_stmt: Optional[str] = None
    fixed: bool = False

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        return d


def discover_py_files(root: str) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")
        ]
        for f in filenames:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def get_package_parts(path: str, root: str) -> List[str]:
    parts: List[str] = []
    dir_path = os.path.dirname(os.path.abspath(path))
    root = os.path.abspath(root)
    while dir_path.startswith(root):
        if os.path.exists(os.path.join(dir_path, "__init__.py")):
            parts.insert(0, os.path.basename(dir_path))
            dir_path = os.path.dirname(dir_path)
        else:
            break
    return parts


def resolve_from(module: Optional[str], level: int, package_parts: List[str]) -> str:
    """Resolve an ImportFrom target to an absolute module path."""

    parts: List[str] = []
    if level > 0:
        parts = package_parts[: len(package_parts) - level]
    if module:
        parts.extend(module.split("."))
    return ".".join(parts)


def map_module(name: str) -> Optional[str]:
    """Return suggested canonical path for legacy module ``name``.

    If ``name`` is already canonical, ``None`` is returned.
    """

    if name.startswith("src."):
        stripped = name[4:]
        mapped = map_module(stripped)
        return mapped if mapped else stripped

    parts = name.split(".")
    head, tail = parts[0], parts[1:]

    if head == CANONICAL:
        return None
    if head == "pipeline":
        new_head = f"{CANONICAL}.pipeline"
    elif head == "ocr":
        new_head = f"{CANONICAL}.ocr"
    elif head == "output":
        new_head = f"{CANONICAL}.output"
    elif head in OCR_SUBMODULES:
        new_head = f"{CANONICAL}.ocr.{head}"
        if tail:
            new_head += "." + ".".join(tail)
        return new_head
    else:
        return None

    if tail:
        new_head += "." + ".".join(tail)
    return new_head


def classify_module(module: str) -> Tuple[str, Optional[str]]:
    """Classify a module path.

    Returns a tuple ``(classification, suggestion)`` where classification is
    ``"OK"`` or ``"VIOLATION"``.
    """

    if module.startswith(CANONICAL):
        return "OK", None

    head = module.split(".")[0]
    if module.startswith("src.") or head in LEGACY_TOPLEVEL:
        suggestion = map_module(module)
        return "VIOLATION", suggestion

    return "OK", None


def is_inside_pkg(path: str, pkg_root: str) -> bool:
    abs_path = os.path.abspath(path)
    return abs_path.startswith(pkg_root)


def analyze_file(path: str, root: str, pkg_root: str) -> Tuple[List[Finding], int]:
    rel = os.path.relpath(path, root)
    findings: List[Finding] = []
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return findings, 0

    lines = src.splitlines(keepends=True)
    package_parts = get_package_parts(path, root)
    import_count = 0

    # Warn about conftest shims
    if os.path.basename(path) == "conftest.py":
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Subscript):
                        if (
                                isinstance(tgt.value, ast.Attribute)
                                and isinstance(tgt.value.value, ast.Name)
                                and tgt.value.value.id == "sys"
                                and tgt.value.attr == "modules"
                        ):
                            key = None
                            if isinstance(tgt.slice, ast.Constant):
                                key = tgt.slice.value
                            elif isinstance(tgt.slice, ast.Index) and isinstance(
                                    tgt.slice.value, ast.Constant
                            ):
                                key = tgt.slice.value.value
                            if isinstance(key, str) and key in LEGACY_TOPLEVEL:
                                line = lines[node.lineno - 1].strip()
                                findings.append(
                                    Finding(
                                        rel,
                                        node.lineno,
                                        node.col_offset,
                                        line,
                                        "WARN",
                                        f"conftest shim for '{key}'",
                                    )
                                )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_count += 1
                module = alias.name
                line = lines[node.lineno - 1].strip()
                classification, suggestion = classify_module(module)
                if classification == "OK":
                    continue
                new_stmt = None
                if (
                        suggestion
                        and len(node.names) == 1
                        and getattr(node, "end_lineno", node.lineno) == node.lineno
                ):
                    new_stmt = f"import {suggestion}"
                    if alias.asname:
                        new_stmt += f" as {alias.asname}"
                findings.append(
                    Finding(
                        rel,
                        node.lineno,
                        node.col_offset,
                        line,
                        classification,
                        suggestion,
                        new_stmt,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            base = resolve_from(node.module, node.level, package_parts)
            for alias in node.names:
                import_count += 1
                module_for_check = base if base else alias.name
                line = lines[node.lineno - 1].strip()
                classification, suggestion = classify_module(module_for_check)
                # Warn if relative import to doctr_process from outside
                if (
                        classification == "OK"
                        and node.level > 0
                        and base.startswith(CANONICAL)
                        and not is_inside_pkg(path, pkg_root)
                ):
                    findings.append(
                        Finding(
                            rel,
                            node.lineno,
                            node.col_offset,
                            line,
                            "WARN",
                            "relative import to doctr_process outside package",
                        )
                    )
                    continue
                if classification == "OK":
                    continue
                new_stmt = None
                if (
                        suggestion
                        and len(node.names) == 1
                        and getattr(node, "end_lineno", node.lineno) == node.lineno
                        and node.module
                ):
                    new_stmt = f"from {suggestion} import {alias.name}"
                    if alias.asname:
                        new_stmt += f" as {alias.asname}"
                findings.append(
                    Finding(
                        rel,
                        node.lineno,
                        node.col_offset,
                        line,
                        classification,
                        suggestion,
                        new_stmt,
                    )
                )
    return findings, import_count


def apply_fixes(root: str, findings: Iterable[Finding]) -> int:
    mods: Dict[str, List[Finding]] = {}
    for f in findings:
        if f.new_stmt:
            mods.setdefault(f.file, []).append(f)
    count = 0
    for relpath, flist in mods.items():
        # Validate relpath to prevent path traversal
        if os.path.isabs(relpath) or '..' in relpath:
            continue
        path = os.path.normpath(os.path.join(root, relpath))
        if not path.startswith(os.path.abspath(root)):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        backup = path + ".bak"
        # Validate backup path to prevent traversal attacks
        if not os.path.abspath(backup).startswith(os.path.abspath(root)):
            continue
        shutil.copyfile(path, backup)
        for f in flist:
            orig = lines[f.lineno - 1]
            newline = build_new_line(orig, f.new_stmt)
            lines[f.lineno - 1] = newline
            f.fixed = True
            f.classification = "FIXED"
            count += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
    return count


def build_new_line(orig: str, new_stmt: str) -> str:
    newline = "\n" if orig.endswith("\n") else ""
    line = orig.rstrip("\n")
    comment = ""
    if "#" in line:
        code, comment = line.split("#", 1)
        comment = "#" + comment.strip()
    else:
        code = line
    indent = re.match(r"\s*", code).group(0)
    new_line = indent + new_stmt
    if comment:
        new_line += " " + comment
    return new_line + newline


def summarize(findings: List[Finding]) -> Tuple[int, int]:
    violations = sum(1 for f in findings if f.classification in {"VIOLATION", "FIXED"})
    warnings = sum(1 for f in findings if f.classification == "WARN")
    return violations, warnings


def find_pkg_root(root: str) -> str:
    candidates = [os.path.join(root, CANONICAL), os.path.join(root, "src", CANONICAL)]
    for c in candidates:
        if os.path.isdir(c):
            return os.path.abspath(c)
    candidate = os.path.abspath(os.path.join(root, CANONICAL))
    if candidate.startswith(os.path.abspath(root) + os.sep):
        return candidate
    raise ValueError("Resolved package root is outside the specified root directory.")


def _test_map_module() -> None:
    cases = {
        "pipeline": f"{CANONICAL}.pipeline",
        "ocr.preflight": f"{CANONICAL}.ocr.preflight",
        "preflight": f"{CANONICAL}.ocr.preflight",
        "src.ocr.ocr_utils": f"{CANONICAL}.ocr.ocr_utils",
        "src.doctr_process.ocr": f"{CANONICAL}.ocr",
    }
    for old, expected in cases.items():
        assert map_module(old) == expected, (old, map_module(old), expected)
    assert map_module(f"{CANONICAL}.ocr") is None


def main() -> None:
    _test_map_module()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=os.getcwd())
    p.add_argument("--fix", action="store_true", help="Apply safe rewrites")
    p.add_argument("--json", dest="json_out")
    args = p.parse_args()

    root = os.path.abspath(args.root)
    pkg_root = find_pkg_root(root)

    files = list(discover_py_files(root))
    findings: List[Finding] = []
    total_imports = 0
    for file in files:
        fnd, count = analyze_file(file, root, pkg_root)
        findings.extend(fnd)
        total_imports += count
    files_scanned = len(files)

    autofixed = 0
    if args.fix:
        autofixed = apply_fixes(root, findings)

    violations, _warnings = summarize(findings)

    for f in sorted(findings, key=lambda x: (x.file, x.lineno, x.col)):
        sugg = f.suggestion or ""
        print(f"{f.file}:{f.lineno}:{f.col} | {f.line} | {f.classification} | {sugg}")

    print(
        f"SUMMARY: files={files_scanned}, imports={total_imports}, violations={violations}, autofixed={autofixed}"
    )

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "files_scanned": files_scanned,
                    "imports_scanned": total_imports,
                    "violations": violations,
                    "autofixed": autofixed,
                    "findings": [f.to_dict() for f in findings],
                },
                fh,
                indent=2,
            )

    if violations and not (args.fix and autofixed == violations):
        sys.exit(1)


if __name__ == "__main__":
    main()
