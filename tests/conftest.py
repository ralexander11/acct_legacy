import pytest

import acct


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
