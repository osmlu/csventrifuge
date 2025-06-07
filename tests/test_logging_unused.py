import sys
import runpy
import logging
import shutil
from pathlib import Path


def test_logging_unused(monkeypatch, caplog, tmp_path):
    source_name = "temp_unused"
    src_path = Path("sources") / f"{source_name}.py"
    src_path.write_text(
        "import polars as pl\n\n" "def get():\n" "    return pl.DataFrame({'foo': ['val']})\n"
    )

    rules_dir = Path("rules") / source_name
    filters_dir = Path("filters") / source_name
    enhance_dir = Path("enhance") / source_name / "foo"
    rules_dir.mkdir(parents=True)
    filters_dir.mkdir(parents=True)
    enhance_dir.mkdir(parents=True)

    (rules_dir / "foo.csv").write_text("unused\tnew\n")
    (filters_dir / "foo.csv").write_text("something\twhy\n")
    (enhance_dir / "foo.csv").write_text("another\tbar\n")

    orig_basic = logging.basicConfig

    def patched_basic(*args, **kwargs):
        kwargs["level"] = logging.INFO
        orig_basic(*args, **kwargs)

    monkeypatch.setattr(logging, "basicConfig", patched_basic)

    out_file = tmp_path / "out.csv"
    argv = ["csventrifuge.py", source_name, str(out_file)]
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", argv)
        with caplog.at_level(logging.INFO):
            runpy.run_module("csventrifuge", run_name="__main__")

    log_text = "\n".join(caplog.messages)
    assert 'Did not use [foo] rule "unused" -> "new"' in log_text
    assert 'Did not use enhancement [foo] "another" -> [foo] "bar"' in log_text
    assert 'Did not use filter [foo] something' in log_text

    src_path.unlink()
    shutil.rmtree(rules_dir)
    shutil.rmtree(filters_dir)
    shutil.rmtree(Path("enhance") / source_name)
