# Real-world examples

Snippets taken from actually running `check.py` against independently
written code (not written to be a fixture for this project), with the real
finding attached. See `benchmarks/README.md` for the full methodology and
numbers these came from.

## flask_route_handler.py

```bash
slop-guard examples/real-world/flask_route_handler.py
# -> no findings
```

`index()` is never called by name anywhere in this file — it's registered
with `@bp.route("/")` and invoked by Flask's routing machinery. Before the
fix described in `benchmarks/README.md`, this was flagged as ASG002 dead
code. It no longer is, because `check.py` now excludes decorated
module-level functions from that check.
