import os
from shutil import copyfile
import tempfile
from collections import namedtuple

import pytest

from .. import acct


@pytest.fixture
def accounts():
    """An simple Accounts instance"""

    # Would be nice if the caller (us) could specify a DB
    # location, rather than being force by Accounts to use
    # a specific directory. Ideally, these fixture instances
    # are completely indepentent, so side-effects from the
    # individual tests don't interfere with each other.
    return acct.Accounts()


@pytest.fixture
def ledger(accounts):
    """A simple Ledger instance"""
    return acct.Ledger(accounts)


## Template databases ##
# Each fixture should return a TemplateDB. The .temp database path is
# for use in the test. The .reference database is provided in case you
# need to compare the modified database to its original state. This
# might be unnecessarily complicated.. maybe better to only return the
# temp path, and let the caller make a copy if needed.
TemplateDB = namedtuple("TemplateDB", ["path", "orig"])


def generate_db_fixtures(bases):
    """
    Generate database fixtures for the given template bases.

    Fixtures named by stripping the base's extension and prefixing 'db_'
    """
    # Pattern lifted from https://github.com/pytest-dev/pytest/issues/2424

    # All of the bases should live in this directory
    # There's probably a better way to find the rootdir; maybe using the
    # built-in request fixture (request.rootdir)
    dbdir = os.path.join(os.path.dirname(__file__), "..", "db")
    assert os.path.exists(dbdir), f"db dir {dbdir} doesn't exist!"

    for base in bases:

        @pytest.fixture
        def _fixture():

            # locate the template
            original = os.path.join(dbdir, base)
            assert os.path.exists(original)

            # create a temp path to which we'll copy
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                temp_path = f.name

            # Copy the database
            copyfile(original, temp_path)

            # Return the TemplateDB
            return TemplateDB(temp_path, original)

        # Insert into the global namespace
        name, _ = os.path.splitext(os.path.basename(base))
        globals()["db_" + name] = _fixture


generate_db_fixtures(["acct.db", "econ01.db"])
