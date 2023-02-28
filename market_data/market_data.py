import numpy as np
import pandas as pd
import datetime
import argparse
import time
import os, sys
import urllib
import yaml
# import combine_data
#import urllib.request
#from tqdm import tqdm

DISPLAY_WIDTH = 98
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 20)

class MarketData(object):
	def __init__(self):
		self.config = self.load_config()
		self.token = self.config['api_token']
		self.save_location = '/home/robale5/becauseinterfaces.com/acct/market_data/data/'
		if not os.path.isdir(self.save_location):
			print('Not Server')
			self.save_location = 'data/'

	def time_stamp(self, offset=0):
		if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
			offset = 4
		time_stamp = (datetime.datetime.now() + datetime.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
		return time_stamp

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
			weekday = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
		else:
			weekday = datetime.datetime.today().weekday()
		# Don't do anything on weekends
		if weekday == 5 or weekday == 6:
			if v: print(self.time_stamp() + 'Today is a weekend.')
			return weekday

	def get_symbols(self, flag='iex', exchanges=None):
		if exchanges is None:
			exchanges = ['iex']
		if flag == 'iex':
			symbols_array = []
			exchanges += ['xtse','xtsx']
			for exchange in exchanges:
				print('Getting data from exchange: {}'.format(exchange))
				if exchange == 'iex':
					exchange_url = ''
				else:
					exchange_url = 'exchange/'
				base_url = 'https://cloud.iexapis.com/stable/ref-data/'
				symbols_url = base_url + exchange_url + exchange + '/symbols'
				symbols_url = symbols_url + '?token=' + self.token
				symbols = pd.read_json(symbols_url, typ='frame', orient='records')
				# symbols.to_csv(exchange + '.csv') # Temp
				# symbols = symbols.drop_duplicates(subset='symbol', keep='first')
				symbols_array.append(symbols)
				symbols_list = []
				# symbols_list = symbols['symbol'].tolist()
				#print(len(symbols_list))
				# symbols_list = ','.join(symbols_list)
				symbols_dict = {}
				# symbols_dict['symbols'] = symbols_list
				#print(symbols_list)
				#print(len(symbols_list))
				#print(symbols)
			symbols = pd.concat(symbols_array, sort=True) # Sort to suppress warning
			outfile = flag + '_tickers' + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv.gz'
			symbols.to_csv(self.save_location + 'tickers/' + outfile, compression='gzip')
			return symbols, symbols_list, symbols_dict
		
		if flag == 'sp500':
			sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
			symbols = pd.read_html(sp500_url, header=0)
			symbols = symbols[0]
			symbols.columns = ['symbol','security','sec_filings','sector','sub_sector','address','date_added','cik','founded']
			symbols_list = symbols['symbol'].tolist()
			#print(len(symbols_list))
			symbols_list = ','.join(symbols_list)
			symbols_dict = {}
			symbols_dict['symbols'] = symbols_list
			#print(symbols_list)
			#print(len(symbols_list))
			#print(symbols['symbols'])
			return symbols, symbols_list, symbols_dict
			
		if flag == 'test':
			symbols = pd.DataFrame(['tsla','afk','aapl','goog','trp','spot'], columns = ['symbol'])
			#print(symbols)
			symbols_list = symbols['symbol'].tolist()
			symbols_list = ','.join(symbols_list)
			#print(symbols_list)
			symbols_dict = {}
			symbols_dict['symbols'] = symbols_list
			#print(symbols_dict)
			#print(len(symbols_list))
			return symbols, symbols_list, symbols_dict

		base_dir = '../data/'
		if os.path.exists('/home/robale5/becauseinterfaces.com/acct/data/'):
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
		else:
			if not isinstance(flag, (list, tuple)):
				flag = [x.strip() for x in flag.split(',')]
			symbols = flag
			print('Number of tickers: {}'.format(len(symbols)))
			return symbols

	# /stock/market/batch?symbols=
	# TODO Load as plain json then make df in one shot
	def get_data(self, symbols, end_point='quote', v=True):
		# url = 'https://api.iextrading.com/1.0/stock/' # New url
		if isinstance(symbols, str):
			symbols = [x.strip() for x in symbols.split(',')]
			symbols = pd.DataFrame(symbols, columns=['symbol'])
		url = 'https://cloud.iexapis.com/stable/stock/'
		dfs = []
		invalid_tickers = []
		if v: print('Number of symbols:', len(symbols['symbol']))
		# print('symbols:\n', symbols)
		for symbol in symbols['symbol']: #tqdm(symbols['symbol']):
			try:
				s = pd.read_json(url + symbol + '/' + end_point + '?token=' + self.token, typ='series', orient='index')
				df = s.to_frame().T
				if 'symbol' not in df.columns:
					df['symbol'] = symbol
				df = df.set_index('symbol')
				if pd.isna(df.iloc[0,0]):
					raise ValueError('{} giving null response.'.format(symbol))
				dfs.append(df)
			except Exception as e:
				# print('Error: {}'.format(repr(e)))
				invalid_tickers.append(symbol)
		if dfs:
			data_feed = pd.concat(dfs, sort=True)#, verify_integrity=True)
		else:
			data_feed = pd.DataFrame()
		#print(data_feed)
		#print('-' * DISPLAY_WIDTH)
		return data_feed, invalid_tickers

	def get_batch(self, symbols_list, end_points='price'):
		# url = 'https://api.iextrading.com/1.0/stock/market/batch?symbols='
		url = 'https://cloud.iexapis.com/stable/stock/market/batch?symbols='
		# url_batch = 'https://api.iextrading.com/1.0/stock/market/batch?'
		url_batch = 'https://cloud.iexapis.com/stable/stock/market/batch?'
		url_batch = url_batch + urllib.parse.urlencode(symbols_list)
		print('Batch URL Len: {}'.format(len(url_batch)))
		batch_data = pd.read_json(url_batch + '&types=' + end_points, typ='frame', orient='index')
		#batch_data = pd.read_json(url + symbols_list + '&types=' + end_points, typ='frame', orient='index')
		# print(batch_data)
		return batch_data

	def get_prices(self, symbols):
		t1_start = time.perf_counter()
		# url = 'https://api.iextrading.com/1.0/stock/' # Old url
		url = 'https://cloud.iexapis.com/stable/stock/'
		prices = {}
		invalid_tickers = []
		print('Getting prices for all tickers from ' + source + '.')
		for symbol in symbols['symbol']:
			#print('Symbol: {}'.format(symbol))
			try:
				price = float(urllib.request.urlopen(url + symbol + '/price' + '?token=' + self.token).read())
				prices[symbol] = price
				#print('Price: {}'.format(price))
			except Exception as e:
				print('Error getting price from: ' + url + symbol + '/price\n')
				print('Error: {}'.format(repr(e)))
				invalid_tickers.append(symbol)
		#print(prices)
		prices = pd.DataFrame.from_dict(prices, orient='index')
		prices.columns = ['price']
		print (prices)
		t1_end = time.perf_counter()
		print(time.ctime() + 'Finished getting prices! It took {:,.2f} min.'.format((t1_end - t1_start) / 60))
		print('-' * DISPLAY_WIDTH)
		return prices, invalid_tickers

	def dividends(self, symbols, end_point='dividends'):
		# url = 'https://api.iextrading.com/1.0/stock/' # Old url
		url = 'https://cloud.iexapis.com/stable/stock/'
		dividends = []
		invalid_tickers_divs = []
		print(end_point)
		for symbol in symbols['symbol']:
			print('Getting divs for: {}'.format(symbol))
			try:
				div = pd.read_json(url + symbol + '/' + end_point + self.token, typ='frame', orient='records')
				#print(div)
				if not div.empty:
					div['symbol'] = symbol.upper()
					div['divID'] = div['symbol'] + "|" + div['exDate']
					div = div.set_index('divID')
					#print(div)
					dividends.append(div)
					#print(dividends)
			except:
				print('No divs for ' + symbol)
				invalid_tickers_divs.append(symbol)
		divs = pd.concat(dividends)
		print('Divs:')
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(divs)
		print('-' * DISPLAY_WIDTH)
		return divs, invalid_tickers_divs

	def save_data(self, data_feed, end_point='quote'):
		if '/' in end_point:
			end_point = end_point.replace('/','_')
		if end_point in ['quote', 'stats']:
			extension = '.csv.gz'
		else:
			extension = '.csv'
		outfile = source + '_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + extension
		path = self.save_location + end_point + '/' + outfile
		if end_point in ['quote', 'stats']:
			data_feed.to_csv(path, compression='gzip')
		else:
			data_feed.to_csv(path)
		print(self.time_stamp() + 'Data file saved to: {}'.format(path))

	def save_errors(self, invalid_tickers, end_point='quote'):
		if '/' in end_point:
			end_point = end_point.replace('/','_')
		error_df = pd.DataFrame(np.array(invalid_tickers))
		#print(error_df)
		path = self.save_location + 'invalid_tickers/' + 'invalid_tickers_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
		error_df.to_csv(path)
		print(self.time_stamp() + 'Invalid tickers file saved to: {}'.format(path))

	def get_hist_prices2(self, dates, tickers=None, save=False, v=True):
		if tickers is None:
			tickers = 'ws_tickers.csv'
		if '.csv' in tickers:
			tickers = self.get_symbols(tickers)
		if isinstance(tickers, str):
			tickers = [x.strip() for x in tickers.split(',')]
		if not '.csv' in dates:
			if not isinstance(dates, (list, tuple)):
				dates = [x.strip() for x in dates.split(',')]
		else:
			dates = pd.read_csv('../data/' + dates, header=None)
			dates = dates.iloc[:,0].tolist()
		if v: print('Number of dates:', len(dates))
		base_url = 'https://cloud.iexapis.com/stable/stock/'
		prices = []
		# if v: print('Number of tickers:', len(tickers))
		for ticker in tickers:
			for date in dates:
				if isinstance(date, str):
					date = time.strptime(date, '%Y-%m-%d')
				date = time.strftime('%Y%m%d', date)
				if v: print(self.time_stamp() + base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=TOKEN')
				try:
					result = pd.read_json(base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=' + self.token)
				except:
					try:
						result = pd.read_json(base_url + ticker + '-ct' + '/chart/date/' + date + '?chartByDay=true&token=' + self.token)
					except:
						try:
							result = pd.read_json(base_url + ticker + '-cv' + '/chart/date/' + date + '?chartByDay=true&token=' + self.token)
						except:
							print(self.time_stamp() + 'Error: ' + base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=TOKEN')
							continue
				# if v: print('Result:\n', result)
				if result.empty:
					continue
				if isinstance(date, str):
					date = time.strptime(date, '%Y%m%d')
				date = time.strftime('%Y-%m-%d', date)
				result['symbol'] = ticker.upper()
				prices.append(result)
		prices_save = pd.concat(prices, sort=True)
		# prices_save = prices_save[['symbol', 'date', 'close', 'changePercent', 'change', 'changeOverTime', 'high', 'low', 'open', 'volume', 'uClose', 'uHigh', 'uLow', 'uOpen', 'uVolume', 'label']]
		# if v: print(self.time_stamp() + 'Historical Prices:\n', prices_save)
		if save:
			if len(tickers) == 1 and len(dates) == 1:
				path = self.save_location + 'hist_prices/' + str(tickers[0]) + '_hist_prices_' + str(dates) + '.csv'
			else:
				path = self.save_location + 'hist_prices/' + str(tickers[0]) + '_to_' + str(tickers[-1]) + '_hist_prices_' + str(dates[0]) + '_to_' + str(dates[-1]) + '.csv'
			print(self.time_stamp() + 'Saved: ', path)
			prices_save.to_csv(path, index=False)
		return prices_save

	def get_hist_price(self, data=None, save=False, v=True):
		if data is None:
			data = 'miss_merged.csv' # 'ws_new_miss_fields.csv'
		if '.csv' in data:
			print(self.time_stamp() + 'Reading data from: data/{}'.format(data))
			data = pd.read_csv('data/' + data)
		base_url = 'https://cloud.iexapis.com/stable/stock/'
		prices = []
		if v: print('Number of ticker-dates:', len(data))
		for i, row in data.iterrows():
			ticker = row['symbol']
			date = row['date']
			if isinstance(date, str):
				date = time.strptime(date, '%Y-%m-%d')
			date = time.strftime('%Y%m%d', date)
			if v: print(self.time_stamp() + '[' + str(i) + '] ' + base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=TOKEN')
			# https://cloud.iexapis.com/stable/stock/aapl/chart/date/20201001?chartByDay=true&token=TOKEN
			try:
				result = pd.read_json(base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=' + self.token)
			except:
				try:
					result = pd.read_json(base_url + ticker + '-ct' + '/chart/date/' + date + '?chartByDay=true&token=' + self.token)
				except:
					try:
						result = pd.read_json(base_url + ticker + '-cv' + '/chart/date/' + date + '?chartByDay=true&token=' + self.token)
					except:
						print(self.time_stamp() + 'Error: ' + base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=TOKEN')
						continue
			# if v: print('Result:\n', result)
			if result.empty:
				print(self.time_stamp() + '[' + str(i) + '] ' + 'Empty: ' + base_url + ticker + '/chart/date/' + date + '?chartByDay=true&token=TOKEN')
				continue
			if isinstance(date, str):
				date = time.strptime(date, '%Y%m%d')
			date = time.strftime('%Y-%m-%d', date)
			result['symbol'] = ticker.upper()
			prices.append(result)
			if i % 10000 == 0:
				prices_save = pd.concat(prices, sort=True)
				# prices_save = prices_save[['symbol', 'date', 'close', 'changePercent', 'change', 'changeOverTime', 'high', 'low', 'open', 'volume', 'uClose', 'uHigh', 'uLow', 'uOpen', 'uVolume', 'label']]
				# if v: print(self.time_stamp() + 'Historical Prices:\n', prices_save)
				if save:
					tickers = data['symbol'].values.tolist()
					dates = data['date'].values.tolist()
					if len(tickers) == 1 and len(dates) == 1:
						path = self.save_location + 'hist_prices/' + str(tickers[0]) + '_hist_prices_' + str(dates) + '.csv'
					else:
						path = self.save_location + 'hist_prices/' + str(tickers[0]) + '_to_' + str(tickers[-1]) + '_hist_prices_' + str(dates[0]) + '_to_' + str(dates[-1]) + '.csv'
					# path = self.save_location + 'hist_prices2.csv'
					print(self.time_stamp() + 'Saved: ', path)
					prices_save.to_csv(path, index=False)
		prices_save = pd.concat(prices, sort=True)
		# prices_save = prices_save[['symbol', 'date', 'close', 'changePercent', 'change', 'changeOverTime', 'high', 'low', 'open', 'volume', 'uClose', 'uHigh', 'uLow', 'uOpen', 'uVolume', 'label']]
		# if v: print(self.time_stamp() + 'Historical Prices:\n', prices_save)
		if save:
			tickers = data['symbol'].values.tolist()
			dates = data['date'].values.tolist()
			if len(tickers) == 1 and len(dates) == 1:
				path = self.save_location + 'hist_prices/' + str(tickers[0]) + '_hist_prices_' + str(dates) + '.csv'
			else:
				path = self.save_location + 'hist_prices/' + str(tickers[0]) + '_to_' + str(tickers[-1]) + '_hist_prices_' + str(dates[0]) + '_to_' + str(dates[-1]) + '.csv'
			# path = self.save_location + 'hist_prices2.csv'
			print(self.time_stamp() + 'Saved: ', path)
			prices_save.to_csv(path, index=False)
		return prices_save

	def get_financials(self, tickers=None, transpose=True, save=False, v=False):
		# WARNING! Data weight is 1000 per call
		if tickers is None:
			# tickers = 'ws_tickers.csv'
			tickers = ['tsla']
		if '.csv' in tickers:
			tickers = self.get_symbols(tickers)
		if isinstance(tickers, str):
			tickers = [x.strip() for x in tickers.split(',')]
		base_url = 'https://cloud.iexapis.com/stable/time-series/reported_financials/'
		financials = []
		financials_save = None
		if v: print('tickers:', tickers)
		for ticker in tickers:
			try:
				result = pd.read_json(base_url + ticker + '?token=' + self.token, orient='records')
				if transpose:
					print(result)
					result = result.T
					print('after:')
					print(result)
			except Exception as e:
				print(self.time_stamp() + 'Error: ' + base_url + ticker + '?token=TOKEN')
				print('Error Msg: {}'.format(repr(e)))
				continue
			if result.empty:
				print(self.time_stamp() + 'Empty: ' + base_url + ticker + '?token=TOKEN')
				continue
			if not transpose:
				result.reset_index(inplace=True)
			result['symbol'] = ticker.upper()
			try:
				if transpose:
					year = result.loc['DocumentFiscalYearFocus'].values[0]
					quarter = result.loc['DocumentFiscalPeriodFocus'].values[0]
				else:
					year = result['DocumentFiscalYearFocus'].values[0]
					quarter = result['DocumentFiscalPeriodFocus'].values[0]
				if v: print(year)
				if v: print(quarter)
			except KeyError as e:
				print('Error Msg: {}'.format(repr(e)))
				year = ''
				quarter = ''
			# if v: print('result:\n', result)
			financials.append(result)
			financials_save = pd.concat(financials, sort=True)
			if v: print('financials_save:\n', financials_save)
			if save:
				if len(tickers) == 1:
					path = self.save_location + 'financials/' + str(tickers[0]) + '_financials_' + str(year) + str(quarter) + '.csv'
				else:
					path = self.save_location + 'financials/' + str(tickers[0]) + '_to_' + str(tickers[-1]) + '_financials_' + str(year) + str(quarter) + '.csv'
				print(self.time_stamp() + 'Saved: ', path)
				financials_save.to_csv(path)#, index=False)
		return financials_save

	def get_splits(self, tickers=None, range='1y', save=False, v=False):
		if tickers is None:
			# tickers = '../data/ws_tickers.csv'
			tickers = ['tsla', 'aapl']
		if '.csv' in tickers:
			# print('Splits tickers loaded from:', tickers)
			symbols = self.get_symbols(tickers)
		if '.csv' not in tickers and isinstance(tickers, str):
			symbols = [x.strip() for x in tickers.split(',')]
		base_url = 'https://cloud.iexapis.com/stable/stock/'
		# https://cloud.iexapis.com/stable/stock/tsla/splits/1y?token=TOKEN
		splits = []
		for ticker in symbols:
			try:
				result = pd.read_json(base_url + ticker + '/splits/' + range + '?token=' + self.token, orient='records')
			except:
				print(self.time_stamp() + 'Error: ' + base_url + ticker + '/splits/' + range + '?token=TOKEN')
				continue
			if result.empty:
				print(self.time_stamp() + 'Empty: ' + base_url + ticker + '/splits/' + range + '?token=TOKEN')
				continue
			# result.reset_index(inplace=True)
			result['symbol'] = ticker.upper()
			# if v: print('result:\n', result)
			splits.append(result)
		splits_save = pd.concat(splits, sort=True)
		splits_save.dropna(subset=['ratio'], inplace=True)
		splits_save.drop_duplicates(['symbol', 'exDate', 'ratio'], inplace=True)
		if v: print('splits_save:\n', splits_save)
		if save:
			if '.csv' in tickers:
				path = self.save_location + 'splits/splits_data.csv'
			elif len(symbols) == 1:
				path = self.save_location + 'splits/' + str(symbols[0]) + '_splits_data.csv'
			else:
				path = self.save_location + 'splits/' + str(symbols[0]) + '_to_' + str(symbols[-1]) + '_splits_data.csv'
			print(self.time_stamp() + 'Saved: ', path)
			splits_save.to_csv(path, index=False)
		return splits_save

	def get_holidays(self, days=365, save=False, v=False):
		base_url = 'https://cloud.iexapis.com/stable/ref-data/us/dates/holiday/'
		# https://sandbox.iexapis.com/stable/ref-data/us/dates/holiday/last/365?token=TOKEN
		df_past = pd.read_json(base_url + 'last/' + str(days) + '?token=' + self.token, orient='records')
		df_fut = pd.read_json(base_url + 'next/' + str(days) + '?token=' + self.token, orient='records')
		df = pd.concat([df_past, df_fut])
		if v: print('US Holidays:\n', df)
		if save:
			path = self.save_location + 'holidays.csv'
			print(self.time_stamp() + 'Saved: ', path)
			df.to_csv(path, index=False)
		return df


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--tickers', type=str, help='The flag or tickers for which data to pull.')
	parser.add_argument('-d', '--dates', type=str, help='The dates for when to pull data.')
	parser.add_argument('-e', '--end_points', type=str, help='The end points to pull data.')
	parser.add_argument('-m', '--mode', type=str, help='The name of the mode to pull data: missing, financials, divs, symbols, batch')
	parser.add_argument('-v', '--verbose', action='store_true', help='Display the results on the screen.')
	parser.add_argument('-s', '--save', action='store_true', help='Save the results to csv.')
	args = parser.parse_args()
	t0_start = time.perf_counter()
	data = MarketData()
	print(data.time_stamp() + str(sys.argv))
	if args.tickers is None:
		source = 'iex' # input('Which ticker source? ').lower()
	else:
		source = args.tickers
	if args.dates is not None and not '.csv' in args.dates:
		dates = args.dates
		if not isinstance(dates, (list, tuple)):
			dates = [x.strip() for x in dates.split(',')]
	else:
		dates = args.dates
	if args.end_points:
		args.end_points = [x.strip() for x in args.end_points.split(',')]
		end_points = args.end_points
	print('=' * DISPLAY_WIDTH)
	print(data.time_stamp() + 'Getting data from: {}'.format(source))
	if args.mode is not None:
		print(data.time_stamp() + 'Under mode: {}'.format(args.mode))
	print('-' * DISPLAY_WIDTH)

	if args.mode == 'missing':
		data.get_hist_price(save=args.save)
		exit()

	if args.mode == 'missing2':
		# args.tickers = None #['aapl']
		# dates = ['2020-01-22']#, '2020-01-23']
		if args.dates is None:
			dates = '../data/missing_dates.csv'
		else:
			dates = args.dates
		data.get_hist_prices2(dates, args.tickers, save=args.save)
		exit()

	if args.mode == 'financials':
		# args.tickers = ['aapl']
		data.get_financials(args.tickers, save=args.save, v=args.verbose)
		exit()

	if args.mode == 'splits':
		data.get_splits(args.tickers, save=args.save)
		exit()

	if args.mode == 'holidays':
		data.get_holidays(save=args.save, v=True)
		exit()

	if args.mode == 'symbols':
		symbols = data.get_symbols(source)[0]
		print('Number of Symbols: {}'.format(len(symbols)))
		exit()

	if args.mode == 'batch':
		t0_start = time.perf_counter()
		symbols_list = data.get_symbols(source)[2]
		batch_data = data.get_batch(symbols_list)
		t0_end = time.perf_counter()
		print(data.time_stamp() + 'Finished getting batch prices! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
		exit()

	if args.mode == 'divs':
		end_points = ['dividends/5y']
		for end_point in end_points: 
			div_data, div_invalid_tickers = data.dividends(symbols, end_point)
			data.save_data(div_data)
			data.save_errors(div_invalid_tickers)
		exit()

	# Didn't do anything on weekends previously
	if data.check_weekend() is not None:
		pass
		# exit()

	symbols = data.get_symbols(source)[0]
	if args.end_points is None:
		end_points = ['quote', 'stats'] #['company','financials','earnings','peers']
	for end_point in end_points:
		try:
			print(data.time_stamp() + 'Getting data from ' + source + ' for end point: ' + end_point)
			data_feed, invalid_tickers = data.get_data(symbols, end_point)
			data.save_data(data_feed, end_point)
			data.save_errors(invalid_tickers, end_point)
			print('-' * DISPLAY_WIDTH)
		except Exception as e:
			print(data.time_stamp() + 'Error: {}'.format(repr(e)))
			print('-' * DISPLAY_WIDTH)
			continue
	t0_end = time.perf_counter()
	print(data.time_stamp() + 'Finished getting market data! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))

# crontab schedule
# 20 18 * * *

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py >> /home/robale5/becauseinterfaces.com/acct/logs/missing01.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py -m missing -t cdn_tickers.csv -d all_dates.csv -s >> /home/robale5/becauseinterfaces.com/acct/logs/missing05.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py -m missing -s >> /home/robale5/becauseinterfaces.com/acct/logs/missing12.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py -m splits -t 'all_tickers.csv' -s >> /home/robale5/becauseinterfaces.com/acct/logs/splits02.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py >> /home/robale5/becauseinterfaces.com/acct/logs/market_data.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py -e stats >> /home/robale5/becauseinterfaces.com/acct/logs/market_data_tmp.log 2>&1 &