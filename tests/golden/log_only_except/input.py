def process():
    try:
        risky()
    except Exception:
        rollback_transaction()


process()
