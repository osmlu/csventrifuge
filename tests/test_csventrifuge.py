import argparse
import ast
import os
import types
import tempfile


def load_csventrifuge_partial():
    """Load csventrifuge functions without executing CLI code."""
    path = os.path.join(os.path.dirname(__file__), os.pardir, "csventrifuge.py")
    with open(path, "r", encoding="utf-8") as f:
        mod_ast = ast.parse(f.read(), filename=path)
    nodes = [n for n in mod_ast.body if getattr(n, "lineno", 0) <= 100]
    module = types.ModuleType("csventrifuge_partial")
    module.__dict__["__file__"] = path
    compiled = compile(ast.Module(body=nodes, type_ignores=[]), path, "exec")
    exec(compiled, module.__dict__)
    return module


csventrifuge = load_csventrifuge_partial()


def test_form_module():
    assert csventrifuge.form_module("example.py") == ".example"
    assert csventrifuge.form_module("another.PY") == ".another"


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
