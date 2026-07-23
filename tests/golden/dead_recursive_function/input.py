def unused_recursive(n):
    if n <= 0:
        return 0
    return unused_recursive(n - 1)
