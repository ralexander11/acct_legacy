from acct import Accounts
from acct import Ledger
from trade_platform import Trading
from market_data.market_data import MarketData
from market_data.combine_data import CombineData
import pandas as pd
import argparse
import logging
import datetime
import random
import time
import glob, os

DISPLAY_WIDTH = 97
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 30)
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

random.seed()
WK52_REDUCE = 10

class TradingAlgo(object):
	def __init__(self, ledger, trade, combine_data):
		self.ledger = ledger
		self.trade = trade
		self.gl = trade.gl
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

	def time(self):
		time = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
		return time

	def check_weekend(self, date=None):
		# Get the day of the week (Monday is 0)
		if trade.sim:
			weekday = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
		else:
			weekday = datetime.datetime.today().weekday()

		# Don't do anything on weekends
		if weekday == 5 or weekday == 6:
			print(algo.time() + 'Today is a weekend.')
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
							'2018-05-26'
							]

		# Don't do anything on trade holidays
		if trade.sim:
			current_date = date
		else:
			current_date = datetime.datetime.today().strftime('%Y-%m-%d')
		for holiday in trade_holidays:
			if holiday == current_date:
				print(algo.time() + 'Today is a trade holiday.')
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

	def get_symbols(self, flag, date=None):
		if flag == 'iex' and not trade.sim:
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			symbols = symbols.sample(frac=1).reset_index(drop=True) #Randomize list

		elif flag == 'iex' and trade.sim:
			path = 'market_data/data/tickers/iex_tickers_'
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
		self.gl = self.ledger.gl
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
		portfolio = self.ledger.get_qty(acct='Investments')
		portfolio.columns = ['symbol','qty']
		portfolio = portfolio[(portfolio.qty != 0)] # Filter out tickers with zero qty
		portfolio = portfolio.sample(frac=1).reset_index(drop=True) #Randomize list
		logging.info(algo.time() + 'Done getting fresh portfolio.')
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
		print(algo.time() + 'Randomly selling from {} securities.'.format(len(portfolio)))
		t1_start = time.perf_counter()
		for count, symbol in enumerate(portfolio['symbol'][:random.randint(1,len(portfolio))]):
			logging.debug('Selling shares of: {}'.format(symbol))
			self.trade.sell_shares(*self.get_trade(symbol, portfolio), date)
		t1_end = time.perf_counter()
		print(algo.time() + 'Done randomly selling {} securities in: {:,.2f} min.'.format(count, (t1_end - t1_start) / 60))

	# First algo functions
	def rank_wk52high(self, assets, date=None): # TODO Make this able to be a percentage change calc
		if date is not None:
			date = datetime.datetime.strptime(date, '%Y-%m-%d').date() - datetime.timedelta(days=1)
		if date is None:
			date = datetime.datetime.today().date() - datetime.timedelta(days=1)
		#print('Data Date: {}'.format(date))
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = 'market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		quote_df = self.combine_data.load_file(path)
		end_point = 'stats'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = 'market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		stats_df = self.combine_data.load_file(path)
		merged = self.combine_data.merge_data(quote_df, stats_df)
		merged = merged[(merged.close <= assets)]

		wk52high = merged['week52high']
		close = merged['close']
		rank_wk52 = wk52high - close
		rank_wk52.sort_values(ascending=False, inplace=True)
		#print('rank_wk52: \n{}'.format(rank_wk52))
		return rank_wk52

	def rank_day50avg(self, assets, date=None): # TODO Make this able to be a percentage change calc
		if date is not None:
			date = datetime.datetime.strptime(date, '%Y-%m-%d').date() - datetime.timedelta(days=1)
		if date is None:
			date = datetime.datetime.today().date() - datetime.timedelta(days=1)
		end_point = 'quote'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = 'market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		quote_df = self.combine_data.load_file(path)
		end_point = 'stats'
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		if not os.path.exists(path):
			path = 'market_data/data/' + end_point + '/iex_'+end_point+'_'+str(date)+'.csv'
		stats_df = self.combine_data.load_file(path)
		merged = self.combine_data.merge_data(quote_df, stats_df)
		merged = merged[(merged.close <= assets)]

		day50avg = merged['day50MovingAvg']
		close = merged['close']
		rank_day50 = close - day50avg
		rank_day50.sort_values(ascending=False, inplace=True)
		#print('rank_day50: \n{}'.format(rank_day50))
		return rank_day50

	def rank(self, assets, date=None, v=False):
		rank_wk52 = self.rank_wk52high(assets, date)
		rank_wk52 = rank_wk52.rank()
		rank_wk52 = rank_wk52 / WK52_REDUCE
		if v:
			print('\nrank_wk52: {}\n{}'.format(date, rank_wk52.head(30)))
		rank_day50 = self.rank_day50avg(assets, date)
		rank_day50 = rank_day50.rank()
		if v:
			print('\nrank_day50: {}\n{}'.format(date, rank_day50.head(30)))
		rank = rank_wk52.add(rank_day50, fill_value=0)
		rank.sort_values(ascending=False, inplace=True)
		if v:
			print('\nRank: {}\n{}'.format(date, rank.head(30)))
		return rank

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

	def main(self, date=None):
		t4_start = time.perf_counter()
		print('=' * DISPLAY_WIDTH)
		print(self.time() + 'Sim date: {}'.format(date))
		#print(algo.time() + 'Entity: {} \nCommission: {}, Min QTY: {}, Max QTY: {}, Liquidate Chance: {}, Ticker Source: {}'.format(ledger.entity, trade.com(), algo.min_qty, algo.max_qty, algo.liquidate_chance, algo.ticker_source))
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

		if not self.trade.sim:
			if not algo.check_hours():
				print(self.time() + 'Not within trading hours.')
				return

		capital = self.check_capital()
		assets = self.ledger.balance_sheet(['Cash','Investments'])
		#print(assets)

		# Initial day of portfolio setup
		try: # TODO Move into own function maybe
			portfolio = self.get_portfolio()
		except:
			print(self.time() + 'Initial porfolio setup.')
			rank = self.rank(assets, date)
			#print(rank)
			ticker = rank.index[0]
			capital_remain, qty = self.buy_max(capital, ticker, date)
			print('-' * DISPLAY_WIDTH)
			self.ledger.print_bs()
			nav = self.ledger.balance_sheet()
			print(self.time() + 'Done initial porfolio setup.')
			return nav

		# Trading Algo
		rank = self.rank(assets, date)
		ticker = rank.index[0]
		portfolio = self.get_portfolio()
		if ticker == portfolio['symbol'][0]:
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
		self.ledger.get_qty(acct='Investments')
		#ledger.bs_hist()
		t4_end = time.perf_counter()
		print(self.time() + 'Done trading! It took {:,.2f} min.'.format((t4_end - t4_start) / 60))
		return nav

	def test1(self, date=None): # TODO Remove
		dates = ['2018-09-26','2018-09-27','2018-09-28','2018-10-01','2018-10-02']
		capital = self.check_capital()
		assets = self.ledger.balance_sheet(['Cash','Investments'])
		print('Assets: {}'.format(assets))
		for date in dates:
			#print(date)
			rank = self.rank(assets, date, v=True)
			#print(rank)
		exit()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-sim', '--simulation', action="store_true", help='Run on historical data.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital to start with.')
	args = parser.parse_args()

	accts = Accounts(conn=args.database)
	ledger = Ledger(accts, ledger_name=args.ledger,entity=args.entity)
	trade = Trading(ledger, sim=args.simulation)
	data = MarketData()
	combine_data = CombineData()
	algo = TradingAlgo(ledger, trade, combine_data)

	#algo.test1()

	if trade.sim:
		t0_start = time.perf_counter()
		print(algo.time() + 'Setup default accounts:')
		accts.load_accts('trading')
		cap = args.capital
		if cap is None:
			cap = float(10000)
		print(algo.time() + 'Start Simulation with ${:,.2f} capital:'.format(cap))
		path = 'market_data/data/quote/*.csv'
		dates = []
		for fname in glob.glob(path):
			fname_date = os.path.basename(fname)[-14:-4]
			dates.append(fname_date)
		dates.sort()
		#print(dates)
		print(algo.time() + 'Number of Days: {}'.format(len(dates)))
		print(accts.coa)
		if algo.check_capital() == 0:
			deposit_capital = [ [ledger.get_event(), ledger.get_entity(), trade.trade_date(dates[0]), 'Deposit capital', '', '', '', 'Cash', 'Wealth', cap] ]
			ledger.journal_entry(deposit_capital)
			#print(deposit_capital)
		for date in dates[1:]:
			algo.main(date)
		print('-' * DISPLAY_WIDTH)
		ledger.print_bs() # Display final bs
		t0_end = time.perf_counter()
		print(algo.time() + 'End of Simulation! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
	else:
		algo.main()
