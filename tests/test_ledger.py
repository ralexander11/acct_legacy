import pytest
import sqlite3

import pandas as pd


class TestLedger:
    def test_attributes(self, ledger):
        """Check expected Ledger attributes"""

        # See comment in TestAccounts.test_attributes
        assert type(ledger.bs) is pd.DataFrame
        assert type(ledger.conn) is sqlite3.Connection
        assert type(ledger.ledger_name) is str

    @pytest.mark.parametrize("date", ["2019-06-22"])
    def test_set_date(self, ledger, date):
        """Set and retrieve a date"""

        assert ledger.date != date, "ledger default value conflict with test scenario"
        ledger.set_date(date)
        assert ledger.date == date

    @pytest.mark.parametrize(
        "date",
        [
            "20190622",
            "22-06-2019",
            "2019-13-13",
            pytest.param(
                None, marks=pytest.mark.xfail(reason="None param triggers user input")
            ),
        ],
    )
    def test_set_date_malformed(self, ledger, date):
        """Set a malformed date"""

        with pytest.raises(ValueError):
            ledger.set_date(date)
