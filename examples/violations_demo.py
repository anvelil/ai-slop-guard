import os
import sys
import json

def get_user(uid):
    try:
        return db.fetch(uid)
    except Exception:
        pass

def unused_helper():
    return 42

def main():
    data = json.dumps({"a": 1})
    print(data)

main()
