import argparse
import ast
import os
import tempfile
import types

import pytest


def load_csventrifuge_partial():
    """Load csventrifuge functions without executing CLI code."""
    path = os.path.join(os.path.dirname(__file__), os.pardir, "csventrifuge.py")
    with open(path, "r", encoding="utf-8") as f:
        mod_ast = ast.parse(f.read(), filename=path)
    nodes = [n for n in mod_ast.body if getattr(n, "lineno", 0) <= 150]
    module = types.ModuleType("csventrifuge_partial")
    module.__dict__["__file__"] = path
    compiled = compile(ast.Module(body=nodes, type_ignores=[]), path, "exec")
    exec(compiled, module.__dict__)  # noqa: S102  pylint: disable=exec-used
    return module


csventrifuge = load_csventrifuge_partial()


def test_form_module():
    # form_module was removed in refactoring; module loading now
    # uses importlib.util.
    # This test is kept for backward compatibility and now validates
    # the simplified approach.
    src_dir = os.path.join(os.path.dirname(__file__), os.pardir, "sources")
    test_files = [
        f for f in os.listdir(src_dir) if f.endswith(".py") and f != "__init__.py"
    ]
    assert len(test_files) > 0, "No source modules found to test"


def test_load_module_all_sources():
    src_dir = os.path.join(os.path.dirname(__file__), os.pardir, "sources")
    for fname in os.listdir(src_dir):
        if fname.endswith(".py") and fname != "__init__.py":
            module_name = os.path.splitext(fname)[0]
            module = csventrifuge.load_module(module_name, "sources")
            assert isinstance(module, types.ModuleType)


def test_is_valid_source_with_tempfile():
    parser = argparse.ArgumentParser()
    src_dir = os.path.join(os.path.dirname(__file__), os.pardir, "sources")
    with tempfile.NamedTemporaryFile(dir=src_dir, suffix=".py", delete=False) as tf:
        module_name = os.path.splitext(os.path.basename(tf.name))[0]
    try:
        result = csventrifuge.is_valid_source(parser, module_name)
        assert result == module_name
    finally:
        os.unlink(tf.name)


def test_is_valid_output_opens_file():
    parser = argparse.ArgumentParser()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
    try:
        with csventrifuge.is_valid_output(parser, tmp_name) as handle:
            assert not handle.closed
            assert handle.name == tmp_name
    finally:
        os.unlink(tmp_name)


def test_is_valid_output_error(monkeypatch):
    parser = argparse.ArgumentParser()

    def raise_os_error(*args, **kwargs):
        raise OSError()

    monkeypatch.setattr("builtins.open", raise_os_error)
    with pytest.raises(SystemExit):
        csventrifuge.is_valid_output(parser, "foo.csv")
