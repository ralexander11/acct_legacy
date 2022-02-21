# Preamble
This is a hobby project created for personal use. I am an accountant by profession, but started this project to teach myself programming skills. As such, the project grew organically over time and needs cleaning up, which is on my todo list but it has been more fun to add new features. :)

## Program Structure
This repo is actually three projects that have grown over time. The first is a general purpose accounting system. This is contained in the file acct.py.

The next is a trading platform and related tools for simulated stock trading where the transactions are recorded in the above accounting system. This is the file trade.py. There are also related data collection and aggregation tools in the market_data directory.

The file fut_price.py contains tools to create and use machine learning models on the collected stock market data. While trade_algo.py allows these ML models and other defined trading strategies to be run and recorded in a simulated manner over long periods of time on real stock market data.

The third is an economic simulator in the econ.py file. This is sort of like a economic game that can be run in automatic mode or user mode. The economic conditions can be configured with a simple .csv file for experimentation.

# Accounting and Trading System

This is a simple general purpose accounting system that can interface with other python applications.

An example of the web based display interfaces (WIP):
http://becauseinterfaces.com/

## Instructions

The below instructions are just the bare minimum example. It will allow you to get started using the accounting system with the trading platform to make some simulated stock trades with real market data.

### Part I - Setup the accounts and capital

1. Run acct.py
2. Type "gl" command. This displays the General Ledger
3. Type "bs" command. This displays the Balance Sheet
4. Type "accts" command. This displays the Chart of Accounts
5. Type "je" command. This allows you to enter a Journal Entry
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
3. Type "exit"
4. Run acct.py
5. Type "gl" command
6. This is a list of all the trades and transactions you have made
7. Type "bs" command
8. The Net Asset Value is your current portfolio worth
9. The Balance Check should always be zero
10. Type "qty" command, press enter when it asks for a ticker to see for all

## Econ Sim Instructions
To get started with the econ sim, run the following command:  
econ.py -u

To use a custom save file name use the command:  
econ.py -u -db my_econ.db

Where "my_econ" can be whatever you like. Note, if you do not complete at least one full day the save file needs to be removed before loading again.

1. Type "needs" command. This will list the current status of your person's need levels. These go down by 1 each day, and if any of them reach 0 then your person dies.
2. Type "hours" command. This will show you how many hours your person has left for the day.
3. Type "items" then type "Berries". This first shows you all the items available. Then typing Berries shows you details on the Berries item. The main thing to note is the requirements, and the amounts below that. The values for the amounts are in order of the list of requirements.
4. Type "claim" command. This lets you claim land for free, but it takes hours. Follow the prompts to claim some land.
5. Type "produce" command. This lets you produce an item. Try to produce some berries on the land you just claimed.
6. Type "help" command. This lists more commands, explore around and see what is possible!

## Dependencies


* Python >= 3.5
* Pandas >= 0.22


Data provided by [IEX Cloud](https://iexcloud.io).