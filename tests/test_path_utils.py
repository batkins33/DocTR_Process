import logging

import pytest

from doctr_process.path_utils import guard_call, normalize_single_path


def test_normalize_single_path_basic(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hi")
    assert normalize_single_path(str(f)) == f.resolve()


def test_normalize_single_path_list_and_semicolon(tmp_path, caplog):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a")
    f2.write_text("b")
    with caplog.at_level(logging.WARNING):
        p = normalize_single_path([str(f1), str(f2)])
    assert p == f1.resolve()
    with caplog.at_level(logging.WARNING):
        p2 = normalize_single_path(f"{f1};{f2}")
    assert p2 == f1.resolve()


def test_normalize_single_path_errors(tmp_path):
    with pytest.raises(TypeError):
        normalize_single_path([])
    with pytest.raises(FileNotFoundError):
        normalize_single_path(tmp_path / "missing.txt")
    d = tmp_path / "d"
    d.mkdir()
    with pytest.raises(TypeError):
        normalize_single_path(d)


def test_guard_call_logs(caplog):
    def add(a, b):
        return a + b

    with caplog.at_level(logging.DEBUG):
        res = guard_call("add", add, 1, 2)
    assert res == 3
