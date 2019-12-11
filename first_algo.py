import acct
import trade
from market_data.market_data import MarketData
from market_data.combine_data import CombineData
from fut_price import get_price
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

# random.seed(11)
WK52_REDUCE = 1 #10 # No longer needed

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
		# cur = ledger.conn.cursor()
		# self.min_qty = cur.execute('SELECT min_qty FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		# self.max_qty = cur.execute('SELECT max_qty FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		# self.liquidate_chance = cur.execute('SELECT liquidate_chance FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		# self.ticker_source = cur.execute('SELECT ticker_source FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
		# cur.close()
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

	def check_weekend(self, date=None, v=True):
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
			if v: print(time_stamp() + 'Today is a weekend. ({})'.format(date))
			return weekday

	def check_holiday(self, date=None, v=True):
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
				if v: print(time_stamp() + 'Today is a trade holiday. ({})'.format(date))
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

	def get_prior_day(self, date=None):
		if date is not None:
			# print('date: {} | Type: {}'.format(date, type(date)))
			if isinstance(date, str):
				current_date = datetime.datetime.strptime(date, '%Y-%m-%d')
			else:
				current_date = date
		else:
			current_date = datetime.datetime.today()
		# print('current_date: {} | Type: {}'.format(current_date, type(current_date)))
		prior_day = (current_date - datetime.timedelta(days=1))#.date()
		if isinstance(prior_day, datetime.datetime):
			prior_day = prior_day.date()
		if self.check_weekend(prior_day) is not None:
			return self.get_prior_day(prior_day)
		if self.check_holiday(prior_day) is not None:
			return self.get_prior_day(prior_day)
		return prior_day

	def get_symbols(self, flag, date=None):
		if '.csv' in flag:
			symbols = pd.read_csv('/Users/Robbie/Documents/Development/Python/acct/data/' + flag)
			symbols = symbols.values.tolist()
			symbols = [item for sublist in symbols for item in sublist]

		elif flag == 'iex' and date is None:
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

		elif flag == 'sp500':
			sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
			symbols = pd.read_html(sp500_url, header=0)
			symbols = symbols[0]
			symbols.columns = ['symbol','security','sec_filings','sector','sub_sector','address','date_added','cik','founded']
			#print(symbols['symbols'])
			# return symbols

		else:
			if not isinstance(flag, (list, tuple)):
				flag = [x.strip() for x in flag.split(',')]
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
		# print('capital_bal:', capital_bal)
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

	def rank_combined(self, assets, norm=False, date=None, tickers=None, v=False):
		print('\nRunning test algo.')
		rank_wk52 = self.rank_wk52high(assets, norm, date)
		rank_wk52 = rank_wk52.rank()
		rank_wk52 = rank_wk52 / WK52_REDUCE # Now just a 1
		if v: print('\nrank_wk52: {}\n{}'.format(date, rank_wk52.head(30)))
		rank_day50 = self.rank_day50avg(assets, norm, date)
		rank_day50 = rank_day50.rank()
		if v: print('\nrank_day50: {}\n{}'.format(date, rank_day50.head(30)))
		rank = rank_wk52.add(rank_day50, fill_value=0)
		rank.sort_values(ascending=False, inplace=True)
		if tickers is not None:
			if not isinstance(tickers, (list, tuple)):
				tickers = [tickers]
			rank = rank.loc[rank.index.isin(tickers)]
		print('\nRank: {}\n{}'.format(date, rank.head()))
		return rank

	def rank_change_percent(self, assets, date=None, tickers=None, predict=False):
		if predict:
			print('\nRunning predict future direction algo.')
		else:
			print('\nRunning known future direction algo.')
		fut_date = self.get_next_day(date)
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(fut_date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(fut_date)+'.csv'
			# print('Path: {}'.format(path))
		if os.path.exists(path) and not predict and tickers is None:
			quote_df = combine_data.load_file(path)
		if tickers is not None:
			if not isinstance(tickers, (list, tuple)):
				tickers = [tickers]
			quote_dfs = []
			if not os.path.exists(path) or predict:
				for ticker in tickers:
					quote_df = self.future_data(ticker, date=date)
					if quote_df is None:
						continue
					quote_dfs.append(quote_df)
					print('quote_df:\n', quote_df)
				quote_df = pd.concat(quote_dfs)#, sort=True) # Sort to suppress warning
			else:
				for ticker in tickers:
					quote_df = combine_data.comp_filter(ticker, combine_data.date_filter(fut_date))
					quote_dfs.append(quote_df)
				quote_df = pd.concat(quote_dfs).reset_index().set_index('symbol')
				# quote_df = quote_df.loc[quote_df.index.isin(tickers)]
		else:
			print('Requires at least one ticker provided to predict the price.')
		# Filter as per available WealthSimple listing criteria
		try:
			quote_df_tmp = quote_df.loc[(quote_df['primaryExchange'].isin(['New York Stock Exchange','Nasdaq Global Select'])) & (quote_df['week52High'] > 0.5) & (quote_df['avgTotalVolume'] > 50000)]
			quote_df_tmp = quote_df[(quote_df.latestPrice <= assets)]
		except KeyError:
			quote_df_tmp = quote_df
		if not quote_df_tmp.empty:
			quote_df = quote_df_tmp	
		quote_df.sort_values(by='changePercent', ascending=False, inplace=True)
		change = quote_df['changePercent'].iloc[0]
		print('changePercent: {}'.format(change))
		if change <= 0:
			print('Rank: \n{}'.format(quote_df.head()))
			quote_df = quote_df.iloc[0:0]
			return quote_df
		return quote_df

	def future_data(self, ticker, date=None):
		if date is None:
			date = datetime.datetime.today()
			date = datetime.datetime.strftime('%Y-%m-%d', date)
		else:
			# print('date: {} | {}'.format(date, type(date)))
			if isinstance(date, datetime.datetime):
				date = datetime.datetime.strftime('%Y-%m-%d', date)
		dates = []
		dates.append(date)
		days = 2
		date_prior = date
		while len(dates) < days:
			if isinstance(date_prior, str):
				date_prior = datetime.datetime.strptime(date_prior, '%Y-%m-%d').date()
			date_prior = date_prior - datetime.timedelta(days=1)
			# date_prior = self.get_prior_day(date_prior)
			# TODO Clean up file location logic
			end_point = 'quote'
			path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_' + end_point + '_' + str(date_prior) + '.csv'
			if not os.path.exists(path):
				path = trade.data_location + end_point + '/iex_' + end_point + '_' + str(date_prior) + '.csv'
			print('path:', path)
			if not os.path.exists(path):
				print('File does not exist for: {}'.format(path))
				continue
			dates.append(date_prior)
		dates = [str(dt) for dt in dates]
		print('dates:', dates)
		try:
			df = combine_data.comp_filter(ticker, combine_data.date_filter(dates))
		except KeyError as e:
			print('No data for {} on: {}'.format(ticker, dates))
			return
		# print('Future Data Date: {} | {}'.format(date, type(date)))
		# pred = 300.0
		pred_price = get_price(df, ticker)
		# print('pred_price:', pred_price)
		prior = df.loc[str(date), 'latestPrice']
		# print('prior:', prior)
		change = (pred_price-prior)/prior
		pred_quote_df = pd.DataFrame(data={'symbol':[ticker], 'prediction':[pred_price], 'prior':[prior], 'changePercent':[(pred_price-prior)/prior]}, index=None).set_index('symbol')
		# print('pred_quote_df:\n', pred_quote_df)
		print('changePercent:', change)
		return pred_quote_df

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

	def rand_algo(self, tickers):
		print('\nRunning random buy sell algo.')
		if not isinstance(tickers, (list, tuple)):
			tickers = [tickers]
		rank = pd.DataFrame(columns=['symbol','chance'], index=None)
		print('tickers:', tickers)
		choice = 0
		for ticker in tickers:
			chance = random.randint(0, 1)
			if chance:
				# TODO Better handle multiple tickers
				choice = random.randint(0, len(tickers)-1)
				rank = rank.append({'symbol':tickers[choice], 'chance':chance}, ignore_index=True)
				rank = rank.set_index('symbol')
				return rank
			else:
				return pd.DataFrame()

	def buy_hold(self, tickers):
		print('\nRunning buy and hold algo.')
		if not isinstance(tickers, (list, tuple)):
			tickers = [tickers]
		rank = pd.DataFrame(columns=['symbol','alloc'], index=None)
		# print('tickers:', tickers)
		for i, ticker in enumerate(tickers, 1):
			rank = rank.append({'symbol':ticker, 'alloc':i}, ignore_index=True)
			# rank = rank.sample(frac=1)
			rank = rank.set_index('symbol')
			return rank

	def main(self, norm=False, date=None, dates=None, n=1, adv=False):
		t4_start = time.perf_counter()
		print('=' * DISPLAY_WIDTH)
		print(time_stamp() + 'Sim date: {}'.format(date))
		print ('-' * DISPLAY_WIDTH)

		if adv:
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

		for e in range(1, n+1):
			if n > 1:
				print('\nAlgo Entity:', e)
				self.ledger.default = e
				self.ledger.reset()

			capital = self.check_capital()
			assets = self.ledger.balance_sheet(['Cash','Investments'])
			portfolio = self.ledger.get_qty(accounts=['Investments'])
			# print('Portfolio: \n{}'.format(portfolio))

			# Trading Algos
			if args.tickers:
				tickers = args.tickers
			else:
				tickers = ['tsla'] + ['aapl'] #+ ['voo'] + ['ivv']
			if args.mode == '1' or (e == 1 and args.mode == 'all') or args.mode == 'hold':
				rank = self.buy_hold(tickers)
			if args.mode == '2' or e == 2 or args.mode == 'rand':
				rank = self.rand_algo(tickers)
			if args.mode == '3' or e == 3 or args.mode == 'pred_dir':
				rank = self.rank_change_percent(assets, date, tickers=tickers, predict=True)
			if args.mode == '4' or e == 4 or args.mode == 'perf_dir':
				rank = self.rank_change_percent(assets, date, tickers=tickers, predict=False)
			# if args.mode == '5' or e == 5 or args.mode == 'test':
			# 	rank = self.rank_combined(assets, norm, date, tickers=tickers)
		
			if not rank.empty:
				try:
					print('Rank: \n{}'.format(rank[['changePercent','companyName','sector','primaryExchange','week52High','avgTotalVolume','date']].head()))
				except KeyError:
					print('Rank: \n{}'.format(rank.head()))
				ticker = rank.index[0]
				print('Ticker: {}'.format(ticker))
				if not portfolio.empty:
					if ticker == portfolio['item_id'].iloc[0]:
						print('No change from {}.'.format(ticker))
						self.trade.unrealized(date=date)
						# self.ledger.print_bs()
						# return
					else:
						self.trade.unrealized(rvsl=True, date=date)
						self.liquidate(portfolio, date)
						capital = self.check_capital()
						capital_remain, qty = self.buy_max(capital, ticker, date)
				else:
					print('Setup initial portfolio.')
					capital = self.check_capital()
					capital_remain, qty = self.buy_max(capital, ticker, date)
			else:
				print('No securities have positive change. Will go cash only.')
				if not portfolio.empty:
					self.trade.unrealized(rvsl=True, date=date)
					self.liquidate(portfolio, date)

			print('-' * DISPLAY_WIDTH)
			self.ledger.print_bs()
			nav = self.ledger.balance_sheet()
			portfolio = self.ledger.get_qty(accounts=['Investments'])
			print('Portfolio at End of Day: \n{}'.format(portfolio))
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
	parser.add_argument('-m', '--mode', type=str, help='The name or number of the algo to run.')
	parser.add_argument('-norm', '--norm', action="store_true", help='Normalize stock prices in algo rankings.')
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-r', '--reset', action='store_true', help='Reset the trading sim!')
	parser.add_argument('-t', '--tickers', type=str, help='A list of tickers to consider.')
	args = parser.parse_args()
	if args.reset:
		delete_db(args.database)
	if args.seed:
		random.seed(args.seed)
	else:
		random.seed()

	accts = acct.Accounts(conn=args.database, standard_accts=trade_accts)
	ledger = acct.Ledger(accts, ledger_name=args.ledger, entity=args.entity)
	trade = trade.Trading(ledger, sim=args.simulation)
	data = MarketData()
	combine_data = CombineData(trade.data_location)
	algo = TradingAlgo(ledger, trade, combine_data)

	if args.entity:
		ledger.default = args.entity
	if args.tickers:
		if '.csv' not in args.tickers:
			args.tickers = [x.strip() for x in tickers.split(',')]
		else:
			args.tickers = algo.get_symbols(args.tickers)

	# pred = algo.future_data('tsla', date='2018-09-21')
	# print('pred:', pred)
	# exit()

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
			n = 1
			if args.mode == 'all':
				n = 5
			for entity in range(1, n+1):
				deposit_capital = [ [ledger.get_event(), entity, '', trade.trade_date(dates[0]), '', 'Deposit capital', '', '', '', 'Cash', 'Equity', cap] ]
				ledger.journal_entry(deposit_capital)
				#print(deposit_capital)
		for date in dates[1:]:
			try:
				algo.main(args.norm, date, dates, n=n)
			except FileNotFoundError as e:
				print(time_stamp() + 'No data for prior date: {}'.format(date))
				# print(time_stamp() + 'Error: {}'.format(repr(e)))
		print('-' * DISPLAY_WIDTH)
		ledger.print_bs() # Display final bs
		t0_end = time.perf_counter()
		print(time_stamp() + 'End of Simulation! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
	else:
		algo.main(args.norm)

# 2019-05-07