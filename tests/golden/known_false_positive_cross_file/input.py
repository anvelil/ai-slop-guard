# Simplified from pallets/flask, examples/tutorial/flaskr/db.py.
# This is still a false positive today -- documented here on purpose.

import click


def init_app(app):
    app.cli.add_command(init_db_command)


@click.command("init-db")
def init_db_command():
    print("Initialized the database.")  # slop-guard: ignore -- CLI user feedback
