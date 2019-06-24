import os
import subprocess
import sqlite3

import pytest

import pandas as pd


class TestEcon:
    @pytest.mark.slow
    def test_full_iteration(self, request, db_econ01):

        # Path to econ executable
        econ = os.path.join(os.path.dirname(os.path.dirname(__file__)), "econ.py")

        # I'd rather call this directly, but a fair bit of logic is baked into the CLI
        # econ.py -s 11 -p 4 -r -t 1
        subprocess.call(
            [
                "python",
                econ,
                "-s",
                "11",
                "-p",
                "4",
                "-r",
                "-t",
                "1",
                "-db",
                db_econ01.path,
            ]
        )

        # TODO come up with a coherent way to find/link reference databases to the tests
        # could write a helper function that uses inspect.getframeinfo to generate a path
        db_path_ref = os.path.join(
            request.config.rootdir,
            "acct_test_reference",
            "econ",
            "full_iteration",
            "reference.db",
        )

        assert_db_equal(db_econ01.path, db_path_ref)

        assert 1


## Helpers for comparing simulation results. Should move into a module
# (https://stackoverflow.com/a/33515264/512652) for improved organization
# and reusability
def db_get_tables(conn):
    """Get list of tables from the given sqlite3 connection"""

    cursor = conn.cursor()
    res = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [x[0] for x in res.fetchall()]
    return tables


def assert_db_equal(path_got, path_expected):
    """Assert equality on sqlite databases"""

    # this raises an assertion on the first discrepancy.. in practice, it may be useful
    # to write a comprehensive comparator function (or generalize this one, to emit a
    # logging message on discrepancy, instead of raising an AssertionError)

    with sqlite3.connect(path_got) as got, sqlite3.connect(path_expected) as expected:
        tables_got = set(db_get_tables(got))
        tables_expected = set(db_get_tables(expected))
        assert tables_got == tables_expected, "Got unexpected set of database tables"

        for table in tables_got:
            SELECT = f"SELECT * FROM {table}"
            df_got = pd.read_sql_query(SELECT, got)
            df_expected = pd.read_sql_query(SELECT, expected)

            # The docs claim that setting obj= will affect the assertion message,
            # but I can't seem to get that working..
            pd.testing.assert_frame_equal(df_got, df_expected, obj=table)
