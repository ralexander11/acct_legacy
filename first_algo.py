import acct
import trade
# from acct import Accounts
# from acct import Ledger
# from trade import Trading
from market_data.market_data import MarketData
from market_data.combine_data import CombineData
import pandas as pd
import argparse
import logging
import datetime
import random
import time
import yaml
import glob, os

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 30)
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

random.seed()
WK52_REDUCE = 1 #10

def time_stamp(offset=0):
	time_stamp = (datetime.datetime.now() + datetime.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def delete_db(db_name=None):
	if db_name is None:
		db_name = 'first01.db'
	db_path = 'db/'
	if os.path.exists(db_path + db_name):
		os.remove(db_path + db_name)
		print(time_stamp() + 'Database file reset: {}'.format(db_path + db_name))
	else:
		print(time_stamp() + 'The database file does not exist to be reset at: {}.'.format(db_path + db_name))

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
		('Interest Income','Revenue'),
		('Dividend Receivable','Asset'),
		('Dividend Income','Revenue'),
	]

class TradingAlgo(object):
	def __init__(self, ledger, trade, combine_data):
		self.config = self.load_config()
		self.token = self.config['api_token']
		self.data_location = trade.data_location
		print('Data Location: {}'.format(self.data_location))
		self.ledger = ledger
		self.trade = trade
		self.ledger_name = trade.ledger_name
		self.entity = trade.entity
		self.date = trade.date
		self.start_date = trade.start_date
		self.txn = trade.txn
		self.combine_data = combine_data

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

	def load_config(self, file='config.yaml'):
		config = None
		if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
			file = '/home/robale5/becauseinterfaces.com/acct/config.yaml'
		with open(file, 'r') as stream:
			try:
				config = yaml.safe_load(stream)
				# print('Load config success: \n{}'.format(config))
			except yaml.YAMLError as e:
				print('Error loading yaml config: \n{}'.format(repr(e)))
		return config

	def check_weekend(self, date=None):
		# Get the day of the week (Monday is 0)
		if date is not None:
			if not isinstance(date, str):
				weekday = date.weekday()
			else:
				weekday = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
		else:
			weekday = datetime.datetime.today().weekday()

		# Don't do anything on weekends
		if weekday == 5 or weekday == 6:
			print(time_stamp() + 'Today is a weekend.')
			return weekday

	def check_holiday(self, date=None):
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
							'2018-05-26',
							'2019-01-01',
							'2019-01-21',
							'2019-02-18',
							'2019-04-19',
							'2019-05-27',
							'2019-07-04',
							'2019-09-02',
							'2019-11-28',
							'2019-12-25',
						]

		# Don't do anything on trade holidays
		if date is not None:
			if not isinstance(date, str):
				current_date = date.strftime('%Y-%m-%d')
			else:
				current_date = date
		else:
			current_date = datetime.datetime.today().strftime('%Y-%m-%d')
		for holiday in trade_holidays:
			if holiday == current_date:
				print(time_stamp() + 'Today is a trade holiday.')
				return holiday

	def check_hours(self, begin_time=None, end_time=None, check_time=None):
		if begin_time is None:
			begin_time = datetime.time(6, 30) # Market opens at 9:30 am EST
		if end_time is None:
			end_time = datetime.time(13) # Market closes at 4:00 pm EST
		# If check time is not given, default to current server (PST) time
		check_time = check_time or datetime.datetime.now().time()
		if begin_time < end_time:
			return check_time >= begin_time and check_time <= end_time
		else: # crosses midnight
			return check_time >= begin_time or check_time <= end_time

	def get_next_day(self, date=None):
		if date is not None:
			# print('date: {} | Type: {}'.format(date, type(date)))
			if isinstance(date, str):
				current_date = datetime.datetime.strptime(date, '%Y-%m-%d')
			else:
				current_date = date
		else:
			current_date = datetime.datetime.today()
		# print('current_date: {} | Type: {}'.format(current_date, type(current_date)))
		next_day = (current_date + datetime.timedelta(days=1))#.date()
		if isinstance(next_day, datetime.datetime):
			next_day = next_day.date()
		if self.check_weekend(next_day) is not None:
			return self.get_next_day(next_day)
		if self.check_holiday(next_day) is not None:
			return self.get_next_day(next_day)
		return next_day

	def get_symbols(self, flag, date=None):
		if flag == 'iex' and date is None:
			# symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols_url = 'https://cloud.iexapis.com/stable/ref-data/iex/symbols'
			symbols_url = symbols_url + '?token=' + self.token
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			symbols = symbols.sample(frac=1).reset_index(drop=True) #Randomize list

		elif flag == 'iex' and date is not None:
			path = self.data_location + 'tickers/iex_tickers_'
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
		logging.info(time_stamp() + 'Checking capital...')
		# self.gl = self.ledger.gl
		if capital_accts is None:
			capital_accts = ['Cash','Chequing']
		capital_bal = 0
		capital_bal = self.ledger.balance_sheet(capital_accts)
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
		portfolio = self.ledger.get_qty(accounts=['Investments'])
		portfolio.columns = ['symbol','qty']
		portfolio = portfolio[(portfolio.qty != 0)] # Filter out tickers with zero qty
		# portfolio = portfolio.sample(frac=1).reset_index(drop=True) #Randomize list
		logging.info(time_stamp() + 'Done getting fresh portfolio.')
		return portfolio

	# Buy shares until you run out of capital
	def random_buy(self, capital, symbols, date=None):
		logging.info('Randomly buying.')
		while capital > 1000: # TODO Make this an entity setting
			capital = self.trade.buy_shares(*self.get_trade(symbols), date)
			logging.debug(capital)
		logging.info('Out of capital.')

	# Sell randomly from a random subset of positions
	def random_sell(self, portfolio, date=None):
		print(time_stamp() + 'Randomly selling from {} securities.'.format(len(portfolio)))
		t1_start = time.perf_counter()
		for count, symbol in enumerate(portfolio['symbol'][:random.randint(1,len(portfolio))]):
			logging.debug('Selling shares of: {}'.format(symbol))
			self.trade.sell_shares(*self.get_trade(symbol, portfolio), date)
		t1_end = time.perf_counter()
		print(time_stamp() + 'Done randomly selling {} securities in: {:,.2f} min.'.format(count, (t1_end - t1_start) / 60))

	# First algo functions
	def rank_wk52high(self, assets, norm=False, date=None): # TODO Make this able to be a percentage change calc
		if date is not None:
			date = datetime.datetime.strptime(date, '%Y-%m-%d').date() - datetime.timedelta(days=1)
		if date is None:
			date = datetime.datetime.today().date() - datetime.timedelta(days=1)
		#print('Data Date: {}'.format(date))
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		quote_df = self.combine_data.load_file(path)
		end_point = 'stats'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		stats_df = self.combine_data.load_file(path)
		merged = self.combine_data.merge_data(quote_df, stats_df)
		merged = merged[(merged.close <= assets)]
		if not norm:
			auth_shares = 1
		else:
			auth_shares = merged['sharesOutstanding']

		wk52high = merged['week52high'] * auth_shares
		close = merged['close'] * auth_shares
		rank_wk52 = wk52high - close
		rank_wk52.sort_values(ascending=False, inplace=True)
		#print('rank_wk52: \n{}'.format(rank_wk52))
		return rank_wk52

	def rank_day50avg(self, assets, norm=False, date=None): # TODO Make this able to be a percentage change calc
		if date is not None:
			date = datetime.datetime.strptime(date, '%Y-%m-%d').date() - datetime.timedelta(days=1)
		if date is None:
			date = datetime.datetime.today().date() - datetime.timedelta(days=1)
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		quote_df = self.combine_data.load_file(path)
		end_point = 'stats'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		stats_df = self.combine_data.load_file(path)
		merged = self.combine_data.merge_data(quote_df, stats_df)
		merged = merged[(merged.close <= assets)]
		if not norm:
			auth_shares = 1
		else:
			auth_shares = merged['sharesOutstanding']

		day50avg = merged['day50MovingAvg'] * auth_shares
		close = merged['close'] * auth_shares
		rank_day50 = close - day50avg
		rank_day50.sort_values(ascending=False, inplace=True)
		#print('rank_day50: \n{}'.format(rank_day50))
		return rank_day50

	def rank_combined(self, assets, norm=False, date=None, v=False):
		rank_wk52 = self.rank_wk52high(assets, norm, date)
		rank_wk52 = rank_wk52.rank()
		rank_wk52 = rank_wk52 / WK52_REDUCE # Now just a 1
		if v: print('\nrank_wk52: {}\n{}'.format(date, rank_wk52.head(30)))
		rank_day50 = self.rank_day50avg(assets, norm, date)
		rank_day50 = rank_day50.rank()
		if v: print('\nrank_day50: {}\n{}'.format(date, rank_day50.head(30)))
		rank = rank_wk52.add(rank_day50, fill_value=0)
		rank.sort_values(ascending=False, inplace=True)
		if v: print('\nRank: {}\n{}'.format(date, rank.head(30)))
		return rank

	def rank_change_percent(self, assets, date=None):
		if date is not None:
			date = self.get_next_day(date=date)
		if date is None:
			date = self.get_next_day()
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
			# print('Path: {}'.format(path))
		quote_df = self.combine_data.load_file(path)
		# Filter as per available WealthSimple listing criteria
		quote_df = quote_df.loc[(quote_df['primaryExchange'].isin(['New York Stock Exchange','Nasdaq Global Select'])) & (quote_df['week52High'] > 0.5) & (quote_df['avgTotalVolume'] > 50000)]
		quote_df = quote_df[(quote_df.close <= assets)]
		quote_df.sort_values(by='changePercent', ascending=False, inplace=True)
		return quote_df

	def buy_single(self, symbol, date=None):
		print(symbol)
		capital = self.trade.buy_shares(symbol, 1, date)
		return capital

	def buy_max(self, capital, symbol, date=None):
		price = self.trade.get_price(symbol, date=date)
		qty = capital // price
		if qty == 0:
			return capital, qty
		capital = self.trade.buy_shares(symbol, qty, date)
		print('Purchased {} shares of {} for {} each.'.format(qty, symbol, price))
		return capital, qty

	def liquidate(self, portfolio, date=None):
		for symbol, qty in portfolio.itertuples(index=False):
			self.trade.sell_shares(symbol, qty, date)
			print('Liquidated {} shares of {}.'.format(qty, symbol))

	def main(self, norm=False, date=None):
		t4_start = time.perf_counter()
		print('=' * DISPLAY_WIDTH)
		print(time_stamp() + 'Sim date: {}'.format(date))
		print ('-' * DISPLAY_WIDTH)

		self.trade.int_exp(date=date) # TODO ensure this only runs daily
		if not trade.sim: # TODO Temp restriction while historical CA data is missing
			self.trade.dividends() # TODO Add perf timers
			self.trade.div_accr()
			self.trade.splits()
		logging.info('-' * (DISPLAY_WIDTH - 32))
		
		# Don't do anything on weekends
		if self.check_weekend(date) is not None:
			return
		# Don't do anything on trade holidays
		if self.check_holiday(date) is not None:
			return

		# if not self.trade.sim:
		# 	if not algo.check_hours():
		# 		print(time_stamp() + 'Not within trading hours.')
		# 		return

		capital = self.check_capital()
		assets = self.ledger.balance_sheet(['Cash','Investments'])

		# Trading Algo
		# rank = self.rank_combined(assets, norm, date)
		rank = self.rank_change_percent(assets, date)
		print('Rank: \n{}'.format(rank[['changePercent','companyName','sector','primaryExchange','week52High','avgTotalVolume','date']].head()))

		ticker = rank.index[0]
		print('Ticker: {}'.format(ticker))
		# portfolio = self.get_portfolio()
		portfolio = self.ledger.get_qty(accounts=['Investments'])
		# print('Portfolio: \n{}'.format(portfolio))
		if not portfolio.empty:
			if ticker == portfolio['item_id'].iloc[0]:#['symbol'][0]:
				print('No change from {}.'.format(ticker))
				self.trade.unrealized(date=date)
				return
			self.trade.unrealized(rvsl=True, date=date)
			self.liquidate(portfolio, date)
		capital = self.check_capital()
		capital_remain, qty = self.buy_max(capital, ticker, date)

		print('-' * DISPLAY_WIDTH)
		self.ledger.print_bs()
		nav = self.ledger.balance_sheet()
		portfolio = self.ledger.get_qty(accounts=['Investments'])
		print('Portfolio End: \n{}'.format(portfolio))
		#ledger.bs_hist()
		t4_end = time.perf_counter()
		print(time_stamp() + 'Done trading! It took {:,.2f} min.'.format((t4_end - t4_start) / 60))
		return nav

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-sim', '--simulation', action="store_true", help='Run on historical data.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital to start with.')
	parser.add_argument('-norm', '--norm', action="store_true", help='Normalize stock prices in algo rankings.')
	parser.add_argument('-r', '--reset', action='store_true', help='Reset the trading sim!')
	args = parser.parse_args()
	if args.reset:
		delete_db(args.database)

	accts = acct.Accounts(conn=args.database, standard_accts=trade_accts)
	ledger = acct.Ledger(accts, ledger_name=args.ledger, entity=args.entity)
	trade = trade.Trading(ledger, sim=args.simulation)
	data = MarketData()
	combine_data = CombineData()
	algo = TradingAlgo(ledger, trade, combine_data)

	if trade.sim:
		t0_start = time.perf_counter()
		cap = args.capital
		if cap is None:
			cap = float(10000)
		print(time_stamp() + 'Start Simulation with ${:,.2f} capital:'.format(cap))
		data_path = algo.data_location + 'quote/*.csv'
		dates = []
		for fname in glob.glob(data_path):
			fname_date = os.path.basename(fname)[-14:-4]
			dates.append(fname_date)
		dates.sort()
		print(dates)
		print(time_stamp() + 'Number of Days: {}'.format(len(dates)))
		# print(accts.coa)
		if algo.check_capital() == 0:
			deposit_capital = [ [ledger.get_event(), ledger.get_entity(), '', trade.trade_date(dates[0]), '', 'Deposit capital', '', '', '', 'Cash', 'Equity', cap] ]
			ledger.journal_entry(deposit_capital)
			#print(deposit_capital)
		for date in dates[1:]:
			try:
				algo.main(args.norm, date)
			except FileNotFoundError as e:
				print(time_stamp() + 'No data for prior date: {}'.format(date))
				# print(time_stamp() + 'Error: {}'.format(repr(e)))
		print('-' * DISPLAY_WIDTH)
		ledger.print_bs() # Display final bs
		t0_end = time.perf_counter()
		print(time_stamp() + 'End of Simulation! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
	else:
		algo.main(args.norm)
