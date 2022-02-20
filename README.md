# Preamble
This is a hobby project created for personal use. I am an accountant by profession, but started this project to team myself programming skills. As such, the project grew organically over time and needs cleaning up, which is on my todo list but it has been more fun to add new features. :)

## Program Structure
This repo is actually three projects that have grown over time. The first is a general purpose accounting system. This is contained in the file acct.py.

The next is a trading platform and related tools for simulated stock trading where the transactions are recorded in the above accounting system. This is the file trade.py. There are also related data collection and aggregation tools in the market_data directory.

The file fut_price.py contains tools to create and use machine learning models on the collected stock market data. While trade_algo.py allows these ML models and other defined trading strategies to be run and recorded in a simulated manner over long periods of time on real stock market data.

The third is an economic simulator in the econ.py file. This is sort of like a economic game that can be run in automatic mode or user mode. The economic conditions can be configured with a simple .csv file for experimentation.

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
10. Type "Equity" for the credit account and hit enter
11. Enter a number for the capital such as 100000 or any amount you wish
12. Type "gl" command
13. Type "bs" command
14. Type "help" for more commands

### Part II - Make trades
IEX requires users to register and get a free token to pull stock data:

1. Register for a free token from [IEX](https://iexcloud.io/s/635ab634)
2. Create a file in the main dir called: config.yaml
3. In the file put the following, and replace __TOKEN__ with your token:  
`# Trade Config`  
`    api_token: TOKEN`  

Once the above config file is created, perform the below:

1. Run trade.py
2. Type "buy" command
3. Enter a ticker such as "aapl"
4. Enter a number for the shares such as 10
5. Repeat similar steps for "sell" or "buy" as you wish

### Part III - Check performance
After some time has passed for the market to change, do the following:
1. Run trade.py
2. Type "trueup" command

3. Run acct.py
4. Type "gl" command
5. This is a list of all the trades and transactions you have made
6. Type "bs" command
7. The Net Asset Value is your current portfolio worth
8. The Balance Check should always be zero
9. Type "qty" command, press enter when it asks for a ticker to see for all

## Dependencies


* Python >= 3.5
* Pandas >= 0.22


Data provided by [IEX Cloud](https://iexcloud.io).