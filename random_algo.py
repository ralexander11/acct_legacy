from acct import Accounts
from acct import Ledger
from trade_platform import Trading
import pandas as pd
import random
import datetime
import argparse

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 20)

random.seed()
timestamp = datetime.datetime.now().strftime('[%Y-%b-%d %H:%M:%S] ')

class RandomAlgo(Trading):
	def __init__(self, trade):
		self.df = trade.df
		self.ledger_name = trade.ledger_name

	def get_symbols(self, flag):
		if flag == 'iex':
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			#symbols.set_index('symbol', inplace=True)
			symbols = symbols.sample(frac=1).reset_index(drop=True) #Randomize list
			#outfile = flag + '_tickers' + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
			#symbols.to_csv(self.save_location + 'tickers/' + outfile)
			return symbols

	# Check how much capital is available
	def check_capital(self, capital_accts=None):
		print (timestamp + 'Checking capital...')
		self.df = trade.df
		if capital_accts == None:
			capital_accts = ['Cash','Chequing']
		capital_bal = 0
		capital_bal = trade.balance_sheet(capital_accts)
		return capital_bal
	
	 # Generates the trade details
	def get_trade(self, symbols):
		try: # Get random ticker from df
			symbol = symbols.iloc[random.randint(0, len(symbols))-1]['symbol'].lower()
			print ('Using list of tickers')
		except: # If single ticker is provided
			print ('Using single ticker')
			symbol = symbols
		try: # If position is already held on ticker
			max_qty = portfolio.loc[portfolio['symbol'] == symbol]['qty'].values
			if (random.randint(1, 2) % 2 == 0): # 50% chance to sell portion of existing position up to its max qty
				print ('Not max QTY')
				qty = random.randint(2, max_qty)
			else: # 50% chance to liquidate position
				print ('Max QTY')
				qty = int(max_qty)
		except: # Purchase random amount of shares on position not held
			print ('Ticker not held')
			max_qty = 100
			qty = random.randint(2, max_qty)
			
		#print (qty)
		return symbol, qty

	# Get list of currently held tickers
	def get_portfolio(self):
		portfolio = trade.get_qty()
		portfolio.columns = ['symbol','qty']
		portfolio = portfolio[(portfolio.qty != 0)] # Filter out tickers with zero qty
		portfolio = portfolio.sample(frac=1).reset_index(drop=True) #Randomize list
		print (timestamp + 'Got fresh portfolio.')
		return portfolio

	# Buy shares until you run out of capital
	def random_buy(self, capital):
		print (timestamp + 'Randomly buying.')
		while capital > 1000:
			capital = trade.buy_shares(*algo.get_trade(symbols))
			print (capital)
		print (timestamp + 'Out of capital.')

	# Sell randomly from a random subset of positions
	def random_sell(self, portfolio):
		print (timestamp + 'Randomly selling.')
		for symbol in portfolio['symbol'][:random.randint(1,len(portfolio))]:
			#print (symbol) # Debug
			trade.sell_shares(*algo.get_trade(symbol))
		print (timestamp + 'Done randomly selling.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-entity', type=int, help='A number for the entity.')
	args = parser.parse_args()

	accts = Accounts()
	ledger = Ledger('random_1', args.entity)
	trade = Trading(ledger)
	algo = RandomAlgo(trade)

	print ('=' * DISPLAY_WIDTH)
	print (timestamp + 'Entity: ' + str(ledger.entity))

	# TODO Use pandas to generate this list automatically from this source: https://www.nyse.com/markets/hours-calendars
	trade_holidays = [
						'2018-01-01',
						'2018-01-15',
						'2018-02-19',
						'2018-03-30',
						'2018-05-28',
						'2018-07-04',
						'2018-09-03',
						'2018-11-22',
						'2018-12-25',
						'2018-05-26'
						]

	# Get the day of the week (Monday is 0)
	weekday = datetime.datetime.today().weekday()

	# Don't do anything on weekends
	if weekday == 5 or weekday == 6:
		print (timestamp + 'Today is a weekend.')
		exit()

	# Don't do anything on trade holidays
	day_of_year = datetime.datetime.today().timetuple().tm_yday
	for holiday in trade_holidays:
		datetime_object = datetime.datetime.strptime(holiday, '%Y-%m-%d')
		holiday_day_of_year = datetime_object.timetuple().tm_yday
		if holiday_day_of_year == day_of_year:
			print (timestamp + 'Today is a trade holiday.')
			exit()

	source = 'iex' # input("Which ticker source? ").lower()
	symbols = algo.get_symbols(source) # Get list of all the tickers

	# Check how much capital is available
	capital = algo.check_capital()
	print (capital)
	print ('-' * DISPLAY_WIDTH)

	# Inital day of portfolio setup
	try:
		portfolio = algo.get_portfolio()
	except:
		print (timestamp + 'Initial porfolio setup.')
		algo.random_buy(capital)
		exit()

	# Buy shares until you run out of capital
	algo.random_buy(capital)
	print ('-' * DISPLAY_WIDTH)
	
	# Get fresh list of currently held tickers
	portfolio = algo.get_portfolio()
	print (portfolio)
	print ('-' * DISPLAY_WIDTH)

	# Sell random amounts of currently held shares from a random subset of positions currently held
	algo.random_sell(portfolio)
	print ('-' * DISPLAY_WIDTH)

	# Buy shares until you run out of capital again
	print (capital)
	capital = algo.check_capital()
	print (capital)
	print ('-' * DISPLAY_WIDTH)
	algo.random_buy(capital)#(algo.check_capital())

	print ('-' * DISPLAY_WIDTH)
	nav = trade.balance_sheet()
	print (nav)
	print (timestamp + 'Done randomly trading!')
