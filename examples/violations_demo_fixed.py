import json


def get_user(uid, db):
    try:
        return db.fetch(uid)
    except LookupError:
        return None


def main():
    data = json.dumps({"a": 1})
    return data


main()
get_user(1, db=None)
