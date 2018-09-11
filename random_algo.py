from acct import Accounts
from acct import Ledger
from trade_platform import Trading
import pandas as pd
import argparse
import logging
import datetime
import random
import time
import glob, os

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 20)
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

random.seed()

class RandomAlgo(Trading):
	def __init__(self, trade):
		self.df = trade.df
		self.ledger_name = trade.ledger_name
		self.entity = trade.entity
		self.date = trade.date
		self.start_date = trade.start_date
		self.txn = trade.txn

		# Get entity settings for random trading parameters
		if self.entity is None:
			self.entity = 1
		cur = ledger.conn.cursor()
		self.min_qty = cur.execute('SELECT min_qty FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		self.max_qty = cur.execute('SELECT max_qty FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		self.liquidate_chance = cur.execute('SELECT liquidate_chance FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		self.ticker_source = cur.execute('SELECT ticker_source FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		cur.close()
		self.sim = trade.sim
		self.date = trade.date

	def time(self):
		time = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
		return time

	def get_symbols(self, flag, date=None):
		if flag == 'iex' and not trade.sim:
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			symbols = symbols.sample(frac=1).reset_index(drop=True) #Randomize list

		elif flag == 'iex' and trade.sim:
			path = 'trading/market_data/tickers/iex_tickers_'
			infile = path + date + '.csv'
			with open(infile, 'r') as f:
				symbols = pd.read_csv(f)

		if flag == 'sp500':
			sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
			symbols = pd.read_html(sp500_url, header=0)
			symbols = symbols[0]
			symbols.columns = ['symbol','security','sec_filings','sector','sub_sector','address','date_added','cik','founded']
			#print (symbols['symbols'])
			return symbols

		else: # TODO Make into list
			symbols = flag
		return symbols

	# Check how much capital is available
	def check_capital(self, capital_accts=None):
		logging.info(algo.time() + 'Checking capital...')
		self.df = trade.df
		if capital_accts is None:
			capital_accts = ['Cash','Chequing']
		capital_bal = 0
		capital_bal = trade.balance_sheet(capital_accts)
		logging.info(capital_bal)
		return capital_bal
	
	 # Generates the trade details
	def get_trade(self, symbols, portfolio=None):
		# TODO Add case to handle lists
		if not isinstance(symbols, str): # Get random ticker from df
			symbol = symbols.iloc[random.randint(0, len(symbols))-1]['symbol'].lower()
			logging.debug('Using list of tickers')
		else: # If single ticker is provided
			symbol = symbols
			logging.debug('Using single ticker: {}'.format(symbol))
		if portfolio is not None: # If position is already held on ticker
			qty_held = portfolio.loc[portfolio['symbol'] == symbol]['qty'].values
			logging.debug('QTY Held: {}'.format(qty_held))
			if random.random() < self.liquidate_chance: # Chance to sell portion of existing position up to its max qty. Set by entity settings
				logging.debug('Not max QTY')
				qty = random.randint(1, qty_held)
			else: # Chance to liquidate position. Set by entity settings
				logging.debug('Max QTY')
				qty = int(qty_held)
		else: # Purchase random amount of shares on position not held
			logging.debug('Ticker not held')
			qty = random.randint(self.min_qty, self.max_qty) # Set by entity settings
		logging.debug( (symbol, qty) )
		return symbol, qty

	# Get list of currently held tickers
	def get_portfolio(self):
		portfolio = trade.get_qty()
		portfolio.columns = ['symbol','qty']
		portfolio = portfolio[(portfolio.qty != 0)] # Filter out tickers with zero qty
		portfolio = portfolio.sample(frac=1).reset_index(drop=True) #Randomize list
		logging.info(algo.time() + 'Done getting fresh portfolio.')
		return portfolio

	# Buy shares until you run out of capital
	def random_buy(self, capital, symbols, date=None):
		logging.info('Randomly buying.')
		while capital > 1000: # TODO Make this an entity setting
			capital = trade.buy_shares(*algo.get_trade(symbols), date)
			logging.debug(capital)
		logging.info('Out of capital.')

	# Sell randomly from a random subset of positions
	def random_sell(self, portfolio, date=None):
		print(algo.time() + 'Randomly selling from {} securities.'.format(len(portfolio)))
		t1_start = time.perf_counter()
		for count, symbol in enumerate(portfolio['symbol'][:random.randint(1,len(portfolio))]):
			logging.debug('Selling shares of: {}'.format(symbol))
			trade.sell_shares(*algo.get_trade(symbol, portfolio), date)
		t1_end = time.perf_counter()
		print(algo.time() + 'Done randomly selling {} securities in: {:,.2f} min.'.format(count, (t1_end - t1_start) / 60))

	def main(self, date=None):
		t4_start = time.perf_counter()
		print('=' * DISPLAY_WIDTH)
		print(algo.time() + 'Sim date: {}'.format(date))
		print(algo.time() + 'Entity: {} \nCommission: {}, Min QTY: {}, Max QTY: {}, Liquidate Chance: {}, Ticker Source: {}'.format(ledger.entity, trade.com(), algo.min_qty, algo.max_qty, algo.liquidate_chance, algo.ticker_source))
		print ('-' * DISPLAY_WIDTH)

		trade.int_exp(ledger, date=date)
		if not trade.sim: # TODO Temp restriction while historical CA data is missing
			trade.dividends()
			trade.div_accr()
			trade.splits()
		logging.info('-' * (DISPLAY_WIDTH - 32))

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
		if trade.sim:
			weekday = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
		else:
			weekday = datetime.datetime.today().weekday()

		# Don't do anything on weekends
		if weekday == 5 or weekday == 6:
			print (algo.time() + 'Today is a weekend.')
			return

		# Don't do anything on trade holidays
		if trade.sim:
			current_date = date
		else:
			current_date = datetime.datetime.today().strftime('%Y-%m-%d')
		for holiday in trade_holidays:
			if holiday == current_date:
				print (algo.time() + 'Today is a trade holiday.')
				return

		# Get list of all the tickers
		symbols = algo.get_symbols(algo.ticker_source, date)
		logging.debug(symbols)

		# Check how much capital is available
		capital = algo.check_capital()
		logging.debug(capital)
		logging.info('-' * (DISPLAY_WIDTH - 32))

		# Inital day of portfolio setup
		try:
			portfolio = algo.get_portfolio()
		except:
			print(algo.time() + 'Initial porfolio setup.')
			algo.random_buy(capital, symbols, date)
			print('-' * DISPLAY_WIDTH)
			trade.print_bs()
			nav = trade.balance_sheet()
			logging.info(algo.time() + 'Net Asset Value: ${:,.2f}'.format(nav))
			print(algo.time() + 'Done initial porfolio setup.')
			return nav

		# Sell random amounts of currently held shares from a random subset of positions currently held
		algo.random_sell(portfolio, date)
		logging.info('-' * (DISPLAY_WIDTH - 32))

		# Buy shares until you run out of capital again
		logging.debug(capital)
		capital = algo.check_capital()
		logging.debug(capital)
		logging.info('-' * (DISPLAY_WIDTH - 32))
		print(algo.time() + 'Randomly buying. With ${:,.2f} of capital'.format(capital))
		t2_start = time.perf_counter()
		algo.random_buy(capital, symbols, date)
		t2_end = time.perf_counter()
		print(algo.time() + 'Done randomly buying in: {:,.2f} min.'.format((t2_end - t2_start) / 60))

		# True up positions to market value
		logging.info('-' * (DISPLAY_WIDTH - 32))
		print(algo.time() + 'Booking unrealized gains and losses for {} positions.'.format(len(trade.get_qty())))
		t3_start = time.perf_counter()
		trade.unrealized(date)
		t3_end = time.perf_counter()
		print(algo.time() + 'Done booking unrealized gains and losses in: {:,.2f} min.'.format((t3_end - t3_start) / 60))

		# Dislay balance sheet
		print('-' * DISPLAY_WIDTH)
		trade.print_bs()
		nav = trade.balance_sheet()
		logging.info(algo.time() + 'Net Asset Value: ${:,.2f}'.format(nav))
		t4_end = time.perf_counter()
		print(algo.time() + 'Done randomly trading! It took {:,.2f} min.'.format((t4_end - t4_start) / 60))
		return nav

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-sim', '--simulation', action="store_true", help='Run on historical data.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital to start with.')
	args = parser.parse_args()

	accts = Accounts(conn=args.database)
	ledger = Ledger(ledger_name=args.ledger, entity=args.entity)
	trade = Trading(ledger, sim=args.simulation)
	algo = RandomAlgo(trade)

	if trade.sim:
		print(algo.time() + 'Setup default accounts:')
		t0_start = time.perf_counter()
		trade_accts = [
			('Cash','Asset'),
			('Chequing','Asset'),
			('Savings','Asset'),
			('Investments','Asset'),
			('Visa','Liability'),
			('Student Credit','Liability'),
			('Credit Line','Liability'),
			('Uncategorized','Admin'),
			('Info','Admin'),
			('Commission Expense','Expense'),
			('Investment Gain','Revenue'),
			('Investment Loss','Expense'),
			('Unrealized Gain','Revenue'),
			('Unrealized Loss','Expense'),
			('Interest Expense','Expense'),
			('Dividend Receivable','Asset'),
			('Dividend Income','Revenue'),
			('Interest Income','Revenue')
		]
		accts.add_acct(trade_accts)
		#accts.load_accts('accounts.csv')
		cap = args.capital
		if cap is None:
			cap = float(10000)#(input('How much capital? '))
		print(algo.time() + 'Start Simulation with ${:,.2f} capital:'.format(cap))
		path = 'trading/market_data/quote/*.csv'
		dates = []
		for fname in glob.glob(path):
			fname_date = os.path.basename(fname)[-14:-4]
			dates.append(fname_date)
		dates.sort()
		#print(dates)
		print(algo.time() + 'Number of Days: {}'.format(len(dates)))
		if algo.check_capital() == 0:
			deposit_capital = [ [ledger.get_event(), ledger.get_entity(), trade.trade_date(dates[0]), 'Deposit capital', 'credit_line_01', '', '', 'Cash', 'Credit Line', cap] ]
			trade.journal_entry(deposit_capital)
		for date in dates:
			algo.main(date)
		print('-' * DISPLAY_WIDTH)
		trade.print_bs() # Display final bs
		t0_end = time.perf_counter()
		print(algo.time() + 'End of Simulation! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
	else:
		algo.main()
