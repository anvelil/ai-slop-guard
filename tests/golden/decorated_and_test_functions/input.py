def route_registry(fn):
    return fn


@route_registry
def index():
    return "ok"


def test_index():
    assert index() == "ok"
