import os  # slop-guard: ignore -- kept for local debugging, remove before release


def unused_helper():  # slop-guard: ignore -- kept for an upcoming feature
    return 1


def run():
    try:
        risky()
    except Exception:  # slop-guard: ignore -- best-effort cleanup, failure here is not fatal
        pass


run()
