# Accounting and Trading System

This is a simple general purpose accounting system that can interface with other python applications.

http://becauseinterfaces.com/

## Instructions If Using a Clean DB File

The below instructions apply when not using the acct.db file included in the repository.

### Part I - Setup the accounts and capital

0. Rename acct.db to acct_orig.db if it exists
1. Run acct.py
2. Type "gl" command
3. Type "bs" command
4. Type "accts" command
5. Type "JE" command
6. Press enter 3 times until it asks you for a description
7. Type "Deposit capital" for the description and hit enter
8. Press enter 3 times until it asks you for an account to debit
9. Type "Cash" for the debit account and hit enter
10. Type "Wealth" for the credit account and hit enter
11. Enter a number for the capital such as 100000 or any amount you wish
12. Type "gl" command
13. Type "bs" command

### Part II - Make trades
Unfortunately, IEX changed their policies and the below will not work currently.

1. Run trade_platform.py
2. Type "buy" command
3. Enter a ticker such as "aapl"
4. Enter a number for the shares such as 10
5. Repeat similar steps for "sell" or "buy" as you wish

### Part III - Check performance

1. Run acct.py
2. Type "gl" command
3. This is a list of all the trades and transactions you have made
4. Type "bs" command
5. The Net Asset Value is your current portfolio worth
6. The Balance Check should always be zero
7. Type "qty" command, press enter when it asks for a ticker to see for all

## Dependencies


* Python 3.5
* Pandas 0.22


Data provided for free by [IEX](https://iextrading.com/developer). View [IEX’s Terms of Use](https://iextrading.com/api-exhibit-a/).