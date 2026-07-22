# A decorator applied without call syntax (@foo, not @foo()) is still a
# use of `foo` -- an earlier version of check.py missed this because it
# only tracked ast.Call nodes; a bare decorator reference is an
# ast.Name instead. See docs/known-limitations.md.

def route_registry(fn):
    return fn


@route_registry
def index():
    return "ok"
