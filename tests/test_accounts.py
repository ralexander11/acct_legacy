import logging
import sqlite3

import pytest
import pandas as pd

from .. import acct


class TestAccounts:

    # TODO figure this out dynamically
    IS_WEBSITE = False

    def test_constructor_logs_website(self, caplog):
        """Account constructor emits a debug logging of website status"""

        with caplog.at_level(logging.DEBUG):
            A = acct.Accounts()

        assert caplog.record_tuples == [
            ("root", logging.DEBUG, f"Website: {self.IS_WEBSITE}")
        ]

    def test_attributes(self, accounts):
        """Check expected Accounts attributes"""

        assert type(accounts.coa) is pd.DataFrame, "Accounts has a .coa DataFrame"
        assert (
            type(accounts.conn) is sqlite3.Connection
        ), "Accounts has a .conn database connection"


class TestLedger:
    def test_attributes(self, ledger):
        """Check expected Ledger attributes"""

        assert type(ledger.bs) is pd.DataFrame
        assert type(ledger.conn) is sqlite3.Connection
        assert type(ledger.ledger_name) is str

    @pytest.mark.parametrize("date", (["2019-06-22"]))
    def test_set_date(self, ledger, date):
        """Set and retrieve a date"""

        # Set it directly
        ledger.set_date(date)
        assert ledger.date == date
        ledger.date = None

    @pytest.mark.parametrize("date", (None, "20190622", "22-06-2019", "2019-13-13"))
    def test_set_date_malformed(self, ledger, date):
        """Set a malformed date"""

        # Set it directly
        with pytest.raises(ValueError):
            ledger.set_date(date)
