import acct
import trade
from market_data.market_data import MarketData
from market_data.combine_data import CombineData
from fut_price import get_fut_price
import pandas as pd
import argparse
import datetime as dt
import logging
import random
import time
import yaml
import glob, os
import itertools

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 30)
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

# random.seed(11)
WK52_REDUCE = 1 #10 # No longer needed

def time_stamp(offset=0):
	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
		offset = 4
	time_stamp = (dt.datetime.now() + dt.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
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
		# print('New db: {}'.format(new_db))
		self.ledger = ledger
		self.trade = trade
		self.combine_data = combine_data
		self.entity = trade.entity
		if self.entity is None:
			self.entity = 1
		self.sim = trade.sim
		if new_db or args.reset:
			self.quote_df = None
			self.ledger_name = trade.ledger_name # TODO Not used
			self.date = trade.date # TODO Not used
			self.start_date = trade.start_date # TODO Not used
			self.txn = trade.txn # TODO Not used

			# Get entity settings for random trading parameters
			# cur = ledger.conn.cursor()
			# self.min_qty = cur.execute('SELECT min_qty FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
			# self.max_qty = cur.execute('SELECT max_qty FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
			# self.liquidate_chance = cur.execute('SELECT liquidate_chance FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
			# self.ticker_source = cur.execute('SELECT ticker_source FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
			# cur.close()
		else:
			print(time_stamp() + 'Resuming from: {}'.format(args.database))
			try:
				self.quote_df = self.get_table('quote_df')
			except Exception as e:
				print(time_stamp() + 'Less than one full day completed.')
				self.quote_df = pd.DataFrame()

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

	def set_table(self, table, table_name, v=False):
		if v: print('Orig set table: {}\n{}'.format(table_name, table))
		if not isinstance(table, (pd.DataFrame, pd.Series)):
			if not isinstance(table, (list, tuple)):
				table = [table]
			table = pd.DataFrame(data=table, index=None)
			if v: print('Singleton set table: {}\n{}'.format(table_name, table))
		try:
			table = table.reset_index()
			if v: print('Reset Index - set table: {}\n{}'.format(table_name, table))
		except ValueError as e:
			print('Set table error: {}'.format(repr(e)))
		table.to_sql(table_name, ledger.conn, if_exists='replace', index=False)
		if v: print('Final set table: {}\n{}'.format(table_name, table))
		return table

	def get_table(self, table_name, v=False):
		tmp = pd.read_sql_query('SELECT * FROM ' + table_name + ';', ledger.conn)
		if v: print('Get table tmp: \n{}'.format(tmp))
		index = tmp.columns[0]
		if v: print('Index: {}'.format(index))
		table = pd.read_sql_query('SELECT * FROM ' + table_name + ';', ledger.conn, index_col=index)
		table.index.name = None
		if v: print('Get table: {}\n{}'.format(table_name, table))
		return table

	def check_weekend(self, date=None, v=True):
		# Get the day of the week (Monday is 0)
		if date is not None:
			if not isinstance(date, str):
				weekday = date.weekday()
			else:
				weekday = dt.datetime.strptime(date, '%Y-%m-%d').weekday()
		else:
			weekday = dt.datetime.today().weekday()

		# Don't do anything on weekends
		if weekday == 5 or weekday == 6:
			if v: print(time_stamp() + 'Today is a weekend. ({})'.format(date))
			return weekday

	def check_holiday(self, date=None, v=True):
		# TODO Pull this data from IEX
		us_trade_holidays = [
							'2018-01-01',
							'2018-01-15',
							'2018-02-19',
							'2018-03-30',
							'2018-05-28',
							'2018-07-04',
							'2018-09-03',
							'2018-11-22',
							'2018-12-25',
							'2019-01-01',
							'2019-01-21',
							'2019-02-18',
							'2019-04-19',
							'2019-05-27',
							'2019-07-04',
							'2019-09-02',
							'2019-11-28',
							'2019-12-25',

							'2020-01-01',
							'2020-01-20',
							'2020-02-17',
							'2020-04-10',
							'2020-05-25',
							'2020-07-03',
							'2020-09-07',
							'2020-11-26',
							'2020-12-25',

							'2021-01-01',
							'2021-01-18',
							'2021-02-15',
							'2021-04-02',
							'2021-05-31',
							'2021-07-05',
							'2021-09-06',
							'2021-11-25',
							'2021-12-24',
						]

		# Don't do anything on trade holidays
		if date is not None:
			if not isinstance(date, str):
				current_date = date.strftime('%Y-%m-%d')
			else:
				current_date = date
		else:
			current_date = dt.datetime.today().strftime('%Y-%m-%d')
		for holiday in us_trade_holidays:
			if holiday == current_date:
				if v: print(time_stamp() + 'Today is a trade holiday. ({})'.format(date))
				return holiday

	def check_hours(self, begin_time=None, end_time=None, check_time=None):
		if begin_time is None:
			begin_time = dt.time(6, 30) # Market opens at 9:30 am EST
		if end_time is None:
			end_time = dt.time(13) # Market closes at 4:00 pm EST
		# If check time is not given, default to current server (PST) time
		check_time = check_time or dt.datetime.now().time()
		if begin_time < end_time:
			return check_time >= begin_time and check_time <= end_time
		else: # crosses midnight
			return check_time >= begin_time or check_time <= end_time

	def get_next_day(self, date=None):
		if date is not None:
			# print('date: {} | Type: {}'.format(date, type(date)))
			if isinstance(date, str):
				current_date = dt.datetime.strptime(date, '%Y-%m-%d')
			else:
				current_date = date
		else:
			current_date = dt.datetime.today()
		# print('current_date: {} | Type: {}'.format(current_date, type(current_date)))
		next_day = (current_date + dt.timedelta(days=1))#.date()
		if isinstance(next_day, dt.datetime):
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
				current_date = dt.datetime.strptime(date, '%Y-%m-%d')
			else:
				current_date = date
		else:
			current_date = dt.datetime.today()
		# print('current_date: {} | Type: {}'.format(current_date, type(current_date)))
		prior_day = (current_date - dt.timedelta(days=1))#.date()
		if isinstance(prior_day, dt.datetime):
			prior_day = prior_day.date()
		if self.check_weekend(prior_day) is not None:
			return self.get_prior_day(prior_day)
		if self.check_holiday(prior_day) is not None:
			return self.get_prior_day(prior_day)
		return prior_day

	def get_symbols(self, flag, date=None):
		base_dir = '/Users/Robbie/Documents/Development/Python/acct/data/'
		if not os.path.exists(base_dir):
			base_dir = '/home/robale5/becauseinterfaces.com/acct/data/'
		if '.csv' in flag:
			symbols = pd.read_csv(base_dir + flag, header=None)
			if 'symbol' in symbols.columns.values.tolist(): # TODO This is not possible with header=None
				symbols = symbols['symbol'].unique().tolist()
			else:
				symbols = symbols.iloc[:,0].unique().tolist()
			print('Number of tickers: {}'.format(len(symbols)))
			return symbols
		elif '.xls' in flag:
			symbols = pd.read_excel(base_dir + flag, index_col=None)
			if 'symbol' in symbols.columns.values.tolist():
				symbols = symbols['symbol'].unique().tolist()
			else:
				symbols = symbols.iloc[:,0].unique().tolist()
			print('Number of tickers: {}'.format(len(symbols)))
			return symbols
		elif flag == 'iex' and date is None:
			# symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols_url = 'https://cloud.iexapis.com/stable/ref-data/iex/symbols'
			symbols_url = symbols_url + '?token=' + self.token
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			symbols = symbols.sample(frac=1).reset_index(drop=True) #Randomize list
			print('Number of tickers: {}'.format(len(symbols)))
			return symbols
		elif flag == 'iex' and date is not None:
			path = self.data_location + 'tickers/iex_tickers_'
			infile = path + date + '.csv'
			# with open(infile, 'r') as f:
			symbols = pd.read_csv(f)
			print('Number of tickers: {}'.format(len(symbols)))
			return symbols
		elif flag == 'sp500':
			sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
			symbols = pd.read_html(sp500_url, header=0)
			symbols = symbols[0]
			symbols.columns = ['symbol','security','sec_filings','sector','sub_sector','address','date_added','cik','founded']
			#print(symbols['symbols'])
			print('Number of tickers: {}'.format(len(symbols)))
			return symbols
		else:
			if not isinstance(flag, (list, tuple)):
				flag = [x.strip() for x in flag.split(',')]
			symbols = flag
			print('Number of tickers: {}'.format(len(symbols)))
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
		t1a_start = time.perf_counter()
		for count, symbol in enumerate(portfolio['symbol'][:random.randint(1,len(portfolio))]):
			logging.debug('Selling shares of: {}'.format(symbol))
			self.trade.sell_shares(*self.get_trade(symbol, portfolio), date)
		t1a_end = time.perf_counter()
		print(time_stamp() + 'Done randomly selling {} securities in: {:,.2f} min.'.format(count, (t1a_end - t1a_start) / 60))

	# First algo functions
	def rank_wk52high(self, assets, norm=False, date=None): # TODO Make this able to be a percentage change calc
		if date is not None:
			date = dt.datetime.strptime(date, '%Y-%m-%d').date() - dt.timedelta(days=1)
		if date is None:
			date = dt.datetime.today().date() - dt.timedelta(days=1)
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
			date = dt.datetime.strptime(date, '%Y-%m-%d').date() - dt.timedelta(days=1)
		if date is None:
			date = dt.datetime.today().date() - dt.timedelta(days=1)
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

	def rank_change_percent(self, assets, date=None, tickers=None, predict=False, train=False):
		t1_start = time.perf_counter()
		if predict:
			print('\n' + time_stamp() + 'Running predict future direction algo.')
		else:
			print('\n' + time_stamp() + 'Running known future direction algo.')
		fut_date = self.get_next_day(date)
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(fut_date)+'.csv'
		if not os.path.exists(path):
			path = self.data_location + end_point + '/iex_'+end_point+'_'+str(fut_date)+'.csv'
			# print('Path: {}'.format(path))
		if os.path.exists(path) and not predict and tickers is None:
			quote_df = combine_data.load_file(path) # TODO Cache data
		elif not os.path.exists(path) and not predict:
			print(time_stamp() + 'Cannot get known future price.')
			return pd.DataFrame()
		if tickers is not None:
			if not isinstance(tickers, (list, tuple)):
				tickers = [tickers]
			quote_dfs = []
			if not os.path.exists(path) or predict:
				if train:
					merged = 'merged_final.csv'
					if os.path.exists(combine_data.data_location + merged):
						print(time_stamp() + 'Merged data exists outer.')
						merged_data = pd.read_csv(combine_data.data_location + merged)
						merged_data = merged_data.set_index(['symbol','date'])
				else:
					merged_data = None
				if algo.quote_df is not None:
					quote_df = algo.quote_df.copy(deep=True)
					quote_dfs.append(algo.quote_df)
					try:
						k = tickers.index(algo.quote_df.index[-1])
					except (IndexError, ValueError) as e:
						k = -1
					tickers = tickers[k+1:]
				for i, ticker in enumerate(tickers, 1):
					time.sleep(args.delay/6)
					# print('ticker:', ticker)
					if isinstance(ticker, float): # xlsx causes last ticker to be nan
						continue
					# quote_df = self.future_data(ticker, date=date, merged_data=merged_data, train=train)
					quote_df = self.future_price(ticker, date=date, v=True)
					print(time_stamp() + 'Done predicting price for: {} ({} / {}) {:.0f}%'.format(ticker, i, len(tickers), (i/len(tickers)*100)))
					if quote_df is None:
						continue
					quote_dfs.append(quote_df)
					print(time_stamp() + 'Prediction:\n', quote_df)
					quote_df = pd.concat(quote_dfs)#, sort=True) # Sort to suppress warning
					self.set_table(quote_df, 'quote_df')
					# quote_df.to_csv('data/result.csv') # For testing, tabbed above line
				if not quote_dfs:
					return pd.DataFrame()
				quote_df = pd.concat(quote_dfs)#, sort=True) # Sort to suppress warning
				self.set_table(quote_df, 'quote_df')
				algo.quote_df = None
			else:
				# for ticker in tickers:
					# quote_df = combine_data.comp_filter(ticker, combine_data.date_filter(fut_date))
					# quote_dfs.append(quote_df)
				quote_df = combine_data.comp_filter(tickers, combine_data.date_filter(str(fut_date))).set_index('symbol')
				# quote_df = pd.concat(quote_dfs).reset_index().set_index('symbol')
				# print('quote_df known:\n', quote_df)
				# quote_df = quote_df.loc[quote_df.index.isin(tickers)]
		else:
			print(time_stamp() + 'Requires at least one ticker provided to predict the price.')
		# Filter as per available WealthSimple listing criteria
		# try:
		# 	quote_df_tmp = quote_df.loc[(quote_df['primaryExchange'].isin(['New York Stock Exchange','Nasdaq Global Select'])) & (quote_df['week52High'] > 0.5) & (quote_df['avgTotalVolume'] > 50000)]
		# 	quote_df_tmp = quote_df[(quote_df.latestPrice <= assets)]
		# except KeyError:
		# 	quote_df_tmp = quote_df
		# if not quote_df_tmp.empty:
		# 	quote_df = quote_df_tmp
		if quote_df.empty:
			return pd.DataFrame()
		quote_df.sort_values(by='changePercent', ascending=False, inplace=True)
		if predict:
			self.set_table(quote_df, 'quote_df')
		change = quote_df['changePercent'].iloc[0]
		print('greatest_changePercent: {}'.format(change))
		t1_end = time.perf_counter()
		print(time_stamp() + 'Done ranking {} securities by change percentage in: {:,.2f} min.'.format(quote_df.shape[0], (t1_end - t1_start) / 60))
		if change <= 0:
			print('No Positive Change Rank: \n{}'.format(quote_df.head()))
			quote_df = quote_df.iloc[0:0]
			return quote_df
		return quote_df

	def future_price(self, ticker, date, v=False):
		pred_price = get_fut_price(ticker, date)
		if v: print('pred_price:\n', pred_price)
		pred_quote_df = pred_price.rename(columns={'latestPrice': 'prior'}, errors='ignore')
		pred_quote_df['changePercent'] = (pred_quote_df['prediction'] - pred_quote_df['prior']) / pred_quote_df['prior']
		pred_quote_df = pred_quote_df[['symbol', 'prediction', 'prior', 'changePercent']]
		pred_quote_df.set_index('symbol', inplace=True)
		# pred_quote_df = pd.DataFrame(data={'symbol':[ticker], 'prediction':[pred_price], 'prior':[prior], 'changePercent':[(pred_price-prior)/prior]}, index=None).set_index('symbol')
		if v: print('pred_quote_df:\n', pred_quote_df)
		return pred_quote_df

	def future_data(self, ticker, date=None, merged_data=None, train=False):
		t2_start = time.perf_counter()
		if date is None:
			date = dt.datetime.today()
			if date.weekday() == 0:
				delta = 3
			# elif date.weekday() == 1:
			# 	delta = 1#2
			else:
				delta = 0#1
			date = date - dt.timedelta(days=delta) # TODO Test support for Mondays and Tuesdays
			date = date.date()
			if isinstance(date, dt.datetime):
				date = dt.datetime.strftime('%Y-%m-%d', date)
			print(time_stamp() + 'Date Inner 1: {}'.format(date))
			self.set_table(date, 'date')
		else:
			# print('date: {} | {}'.format(date, type(date)))
			if isinstance(date, dt.datetime):
				date = dt.datetime.strftime('%Y-%m-%d', date)
		dates = []
		dates.append(date)
		days = 2
		date_prior = date
		while len(dates) < days:
			if isinstance(date_prior, str):
				date_prior = dt.datetime.strptime(date_prior, '%Y-%m-%d').date()
			date_prior = date_prior - dt.timedelta(days=1)
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
			if not trade.sim:
				df1 = combine_data.comp_filter(ticker, combine_data.date_filter(dates[1:]))
				if df1.empty:
					print(time_stamp() + 'No data for {} on: {}'.format(ticker, dates))
					return
				ticker_df = pd.DataFrame([ticker], columns=['symbol'])
				df2 = data.get_data(ticker_df, 'quote', v=False)[0]
				if df2.empty:
					print(time_stamp() + 'No data for {} on: {}'.format(ticker, dates))
					return
				df2['symbol'] = ticker.upper()
				# cols = df2.columns.values.tolist()
				# cols.insert(0, cols.pop(cols.index('symbol')))
				# df2 = df2[cols]
				df2['day50MovingAvg'] = ((df1['day50MovingAvg'].values[0] * 49) + df2['latestPrice']) / 50
				df2['date'] = dates[0]
				df2.set_index('date', inplace=True)
				df = pd.concat([df1, df2], sort=True)
				# print('df:\n', df[['symbol','day50MovingAvg','changePercent','latestPrice']])
			else:
				df = combine_data.comp_filter(ticker, combine_data.date_filter(dates))
		except KeyError as e:
			print(time_stamp() + 'No data for {} on: {}'.format(ticker, dates))
			return
		if df.empty:
			print(time_stamp() + 'No data for {} on: {}'.format(ticker, dates))
			return
		# print('Future Data Date: {} | {}'.format(date, type(date)))
		# pred = 300.0
		try:
			pred_price = get_price(df, ticker, merged_data=merged_data, train=train)
			# pred_price = get_fut_price(ticker, dates)
		except Exception as e:
			print(time_stamp() + 'Error getting price for {}: {}\n{}'.format(ticker, repr(e), df))
			return
		if pred_price is None:
			return
		# print('pred_price:', pred_price)
		prior = df.loc[str(date), 'latestPrice']
		# print('prior:', prior)
		change = (pred_price-prior)/prior
		pred_quote_df = pd.DataFrame(data={'symbol':[ticker], 'prediction':[pred_price], 'prior':[prior], 'changePercent':[(pred_price-prior)/prior]}, index=None).set_index('symbol')
		# print('pred_quote_df:\n', pred_quote_df)
		print('changePercent {}: {}'.format(ticker, change))
		t2_end = time.perf_counter()
		print(time_stamp() + 'Done predicting price for: {} in: {:,.0f} sec'.format(ticker, (t2_end - t2_start))) # {:,.2f}
		return pred_quote_df

	def buy_single(self, symbol, date=None):
		print(symbol)
		capital = self.trade.buy_shares(symbol, 1, date)
		return capital

	def buy_max(self, capital, symbol, date=None):
		price = self.trade.get_price(symbol, date=date)
		if not price:
			return None, None
		qty = capital // price
		if qty == 0:
			return capital, qty
		capital = self.trade.buy_shares(symbol, qty, price, date)
		print('Purchased {} shares of {} for {} each.'.format(qty, symbol, price))
		return capital, qty

	def liquidate(self, portfolio, date=None):
		for symbol, account, qty in portfolio.itertuples(index=False):
			self.trade.sell_shares(symbol, qty, date)
			print('Liquidated {} shares of {}.'.format(qty, symbol))

	def rand_algo(self, tickers):
		print('\nRunning random buy sell algo.')
		if not isinstance(tickers, (list, tuple)):
			tickers = [tickers]
		rank = pd.DataFrame(columns=['symbol','chance'], index=None)
		# print('tickers:', tickers)
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
			if len(tickers) > 1000:
				ticker = 'spy'
			rank = rank.append({'symbol':ticker, 'alloc':i}, ignore_index=True)
			# rank = rank.sample(frac=1)
			rank = rank.set_index('symbol')
			return rank

	def main(self, date=None, dates=None, norm=False, n=1, first=False, adv=False, tmp_n=None):
		t3_start = time.perf_counter()
		if date is None:
			date = dt.datetime.today()
			date = date.date()
			if isinstance(date, dt.datetime):
				date = dt.datetime.strftime('%Y-%m-%d', date)
		self.set_table(date, 'date')
		print('=' * DISPLAY_WIDTH)
		if trade.sim:
			print(time_stamp() + 'Sim Date: {}'.format(date))
		else:
			print(time_stamp() + 'Date: {}'.format(date))
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

		# Trading Algos
		if args.tickers:
			tickers = args.tickers
		else:
			tickers = ['tsla'] + ['aapl'] #+ ['voo'] + ['ivv']
		if args.mode == 'each':
			tickers_repeated = list(itertools.chain.from_iterable([ticker, ticker, ticker, ticker] for ticker in args.tickers))
		else:
			tickers_repeated = [tickers]

		for e in range(1, n+1):
			if tmp_n is not None and first:
				e = e + tmp_n-1
				if e > len(tickers_repeated):
					break
			count = e % 4
			if count == 0:
				count = 4
			time.sleep(args.delay)
			if n > 1:
				print('\nAlgo Entity:', e)
				self.ledger.default = e
				self.ledger.reset()

			capital = self.check_capital()
			print('Capital for entity {}: {}'.format(e, capital))
			assets = self.ledger.balance_sheet(['Cash','Investments'])
			portfolio = self.ledger.get_qty(accounts=['Investments'])
			# print('Portfolio: \n{}'.format(portfolio))
			if args.mode == 'each':
				tickers = tickers_repeated[e-1]
				# print('Tickers: {} | count: {}'.format(tickers, count))

			if args.mode == '1' or (e == 1 and (args.mode == 'all' or args.mode == 'each')) or args.mode == 'hold' or count == 1:
				rank = self.buy_hold(tickers)
				algo_type = 'hold'
			if args.mode == '2' or e == 2 or args.mode == 'rand' or count == 2:
				rank = self.rand_algo(tickers)
				algo_type = 'rand'
			if args.mode == '3' or e == 3 or args.mode == 'perf_dir' or count == 3:
				rank = self.rank_change_percent(assets, date, tickers=tickers, predict=False)
				algo_type = 'perf'
			if args.mode == '4' or e == 4 or args.mode == 'pred_dir' or count == 4:
				rank = self.rank_change_percent(assets, date, tickers=tickers, predict=True, train=args.train)
				algo_type = 'pred'
			# if args.mode == '5' or e == 5 or args.mode == 'test':
			# 	rank = self.rank_combined(assets, norm, date, tickers=tickers)

			self.entities = accts.get_entities()
			if e not in self.entities.index:
				if isinstance(tickers, (list, tuple)):
					name = tickers[0] + '-' + algo_type
				else:
					name = tickers + '-' + algo_type
				entity_data = [[name, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]] # Note: The 2nd to 5th values are for another program as well as the 6th to 19th values
				accts.add_entity(entity_data)#, v=True)
		
			if not rank.empty:
				try:
					print('Rank: \n{}'.format(rank[['changePercent','sector','primaryExchange','week52High','avgTotalVolume']].head()))#,'companyName','date'
				except KeyError as e:
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

		t3_end = time.perf_counter()
		print(time_stamp() + 'Done trading for {}. It took {:,.2f} min.'.format(date, (t3_end - t3_start) / 60))
		first = False
		return nav

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, default='trade01.db', help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-sim', '--simulation', action="store_true", help='Run on historical data.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital to start with.')
	parser.add_argument('-m', '--mode', type=str, default='all', help='The name or number of the algo to run. Or each to run each ticker separately')
	parser.add_argument('-norm', '--norm', action="store_true", help='Normalize stock prices in algo rankings.')
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-r', '--reset', action='store_true', help='Reset the trading sim!')
	parser.add_argument('-t', '--tickers', type=str, default='ws_tickers.csv', help='A list of tickers to consider.')
	parser.add_argument('-n', '--train_new', action='store_false', help='Train a new model if existing model is not found.')
	parser.add_argument('-a', '--train', action='store_true', help='Train all new models.')
	parser.add_argument('-since', '--since', action='store_false', help='Use all dates since a given date. On by default.')
	args = parser.parse_args()
	new_db = True
	# print('Existing DB Check: {}'.format(os.path.exists('db/' + args.database)))
	if os.path.exists('db/' + args.database):
		new_db = False
	if args.reset:
		delete_db(args.database)
		new_db = True
	# print('New DB:', new_db)
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

	if new_db:
		accts.clear_tables(v=True)
	if args.entity:
		ledger.default = args.entity
	if args.train_new:
		print(time_stamp() + 'Will train new models if they don\'t already exist.')
	if args.train:
		print(time_stamp() + 'Will train all new models.')
	if args.tickers:
		if '.csv' not in args.tickers and '.xls' not in args.tickers:
			args.tickers = [x.strip() for x in args.tickers.split(',')]
		else:
			args.tickers = algo.get_symbols(args.tickers)
	# print('args.tickers:', args.tickers)
	# result = algo.future_data('scor', '2018-05-09')
	# convert_lite(args.tickers)
	# exit()

	if trade.sim:
		t0_start = time.perf_counter()
		cap = args.capital
		if cap is None:
			cap = float(1000)
		print(time_stamp() + 'Start Simulation with ${:,.2f} capital:'.format(cap))
		if (args.delay is not None) and (args.delay != 0):
			print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))
		data_path = algo.data_location + 'quote/*.csv'
		dates = []
		for fname in glob.glob(data_path):
			fname_date = os.path.basename(fname)[-14:-4]
			dates.append(fname_date)
		print('dates len1:', len(dates))
		if args.since:
			# TODO Add option to provide since date
			since = '2020-01-24'
			dates = [date for date in dates if date > since]
		dates.sort()
		# print(dates)
		print(time_stamp() + 'Number of Days: {}'.format(len(dates)))
		# print(accts.coa)
		n = 1
		if args.mode == 'all':
			n = 4
		elif args.mode == 'each':
			n = len(args.tickers) * 4
			print('Mode: {} | Number of entities: {}'.format(args.mode, n))
		# print('Capital: {}'.format(algo.check_capital(['Cash','Chequing','Investments'])))
		if algo.check_capital(['Cash','Chequing','Investments']) == 0:
			for entity in range(1, n+1):
				deposit_capital = [ [ledger.get_event(), entity, '', trade.trade_date(dates[0]), '', 'Deposit capital', '', '', '', 'Cash', 'Equity', cap] ]
				ledger.journal_entry(deposit_capital)
				#print(deposit_capital)
		if not new_db and not args.reset:
			if not algo.quote_df.empty:
				ticker = algo.quote_df.index[0]#['symbol']
				if args.mode == 'each':
					tickers_repeated = list(itertools.chain.from_iterable([ticker, ticker, ticker, ticker] for ticker in args.tickers))
				# TODO Only assumes it stopped during the 4th algo
				tmp_n = tickers_repeated.index(ticker)+1 + 3 + 4
			else:
				tmp_n = 4
			date = algo.get_table('date').values[0][0]
			date_index = dates.index(date)
			dates = dates[date_index-1:]
		else:
			tmp_n = None
		first = True
		for date in dates[1:]: # TODO Data window is 2 days back, but this should be general
			algo.set_table(date, 'date')
			try:
				algo.main(date, dates, args.norm, n=n, first=first, tmp_n=tmp_n)
			except FileNotFoundError as e:
				print(time_stamp() + 'No data for prior date: {}'.format(date))
				# print(time_stamp() + 'Error: {}'.format(repr(e)))
		print('-' * DISPLAY_WIDTH)
		ledger.print_bs() # Display final bs
		t0_end = time.perf_counter()
		print(time_stamp() + 'End of Simulation! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
	else:
		date = None # '2019-12-26' # 
		cap = args.capital
		if cap is None:
			cap = float(1000)
		n = 1
		if args.mode == 'all':
			n = 4
		elif args.mode == 'each':
			n = len(args.tickers) * 4
			print('Mode: {} | Number of entities: {}'.format(args.mode, n))
		if algo.check_capital(['Cash','Chequing','Investments']) == 0:
			for entity in range(1, n+1):
				deposit_capital = [ [ledger.get_event(), entity, '', trade.trade_date(date), '', 'Deposit capital', '', '', '', 'Cash', 'Equity', cap] ]
				ledger.journal_entry(deposit_capital)
		if not new_db and not args.reset:
			date = algo.get_table('date').values[0][0]
		algo.main(norm=args.norm, date=date, n=n, first=new_db)

# python first_algo.py -db first36.db -s 11 -sim -t ws_tickers.xlsx

# python first_algo.py -db trade02.db -s 11 -t ws_tickers.csv -r
# python first_algo.py -db first01.db -s 11 -t ws_tickers.csv -r

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/trade_algo.py -db first01.db -s 11 -t tsla -sim >> /home/robale5/becauseinterfaces.com/acct/logs/first01.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/trade_algo.py -db trade01.db -s 11 -a >> /home/robale5/becauseinterfaces.com/acct/logs/trade01.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/trade_algo.py -db test01.db -s 11 -m each -sim -t us_tickers.csv >> /home/robale5/becauseinterfaces.com/acct/logs/test01.log 2>&1 &

# crontab schedule
# 00 07 * * *

# nohup python first_algo.py -db test01.db -s 11 -m each -sim -t us_tickers.csv