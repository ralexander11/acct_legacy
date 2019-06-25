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
            _ = acct.Accounts()

        assert caplog.record_tuples == [
            ("root", logging.DEBUG, f"Website: {self.IS_WEBSITE}")
        ]

    def test_attributes(self, accounts):
        """Check expected Accounts attributes"""

        # This is kind of bad practice.. I guess it's entirely up to us what
        # qualities we feel is valuable to test/enforce, but e.g., if we wanted
        # to swap out sqlite3 for a different db engine, we maybe shouldn't care
        # as long as all of the Accounts behaviours still work.
        assert type(accounts.coa) is pd.DataFrame, "Accounts has a .coa DataFrame"
        assert (
            type(accounts.conn) is sqlite3.Connection
        ), "Accounts has a .conn database connection"
