from .conftest import run_source


def test_tuple_source(run_source):
    produced = run_source("test_tuple_source", "")
    assert produced == [{"foo": "bar"}]
