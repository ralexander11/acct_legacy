import numpy as np
import pandas as pd
import datetime
import time
import os
import urllib
import yaml
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
	
	def time_stamp(self):
		time_stamp = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
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

	def check_weekend(self, date=None):
		# Get the day of the week (Monday is 0)
		if date is not None:
			weekday = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
		else:
			weekday = datetime.datetime.today().weekday()
		# Don't do anything on weekends
		if weekday == 5 or weekday == 6:
			print(self.time_stamp() + 'Today is a weekend.')
			return weekday

	def get_symbols(self, flag):
		if flag == 'iex':
			# 'https://api.iextrading.com/1.0/ref-data/symbols' # Old url
			symbols_url = 'https://cloud.iexapis.com/stable/ref-data/iex/symbols'
			symbols_url = symbols_url + '?token=' + self.token
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			symbols_list = symbols['symbol'].tolist()
			#print(len(symbols_list))
			symbols_list = ','.join(symbols_list)
			symbols_dict = {}
			symbols_dict['symbols'] = symbols_list
			#print(symbols_list)
			#print(len(symbols_list))
			#print(symbols)
			outfile = flag + '_tickers' + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
			symbols.to_csv(self.save_location + 'tickers/' + outfile)
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

	# /stock/market/batch?symbols=

	def get_data(self, symbols, end_point='quote'):
		# url = 'https://api.iextrading.com/1.0/stock/' # New url
		url = 'https://cloud.iexapis.com/stable/stock/'
		dfs = []
		invalid_tickers = []
		for symbol in symbols['symbol']: #tqdm(symbols['symbol']):
			try:
				s = pd.read_json(url + symbol + '/' + end_point + '?token=' + self.token, typ='series', orient='index')
				df = s.to_frame().T
				if 'symbol' not in df.columns:
					df['symbol'] = symbol
				df = df.set_index('symbol')
				dfs.append(df)
			except Exception as e:
				# print('Error: {}'.format(repr(e)))
				invalid_tickers.append(symbol)
		data_feed = pd.concat(dfs, verify_integrity=True, sort=True)
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
		outfile = source + '_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
		path = self.save_location + end_point + '/' + outfile
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

if __name__ == '__main__':
	t0_start = time.perf_counter()
	data = MarketData()
	source = 'iex' # input('Which ticker source? ').lower() # TODO Add support for argparse
	print('=' * DISPLAY_WIDTH)
	print(data.time_stamp() + 'Getting data from: {}'.format(source))
	print('-' * DISPLAY_WIDTH)

	symbols_test = False
	if symbols_test:
		symbols = data.get_symbols(source)[0]
		print('Number of Symbols: {}'.format(len(symbols)))
		exit()

	batch_test = False
	if batch_test:
		t0_start = time.perf_counter()
		symbols_list = data.get_symbols(source)[2]
		batch_data = data.get_batch(symbols_list)
		t0_end = time.perf_counter()
		print(data.time_stamp() + 'Finished getting batch prices! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
		exit()

	dividends_test = False
	if dividends_test:
		end_points = ['dividends/5y']
		for end_point in end_points: 
			div_data, div_invalid_tickers = data.dividends(symbols, end_point)
			data.save_data(div_data)
			data.save_errors(div_invalid_tickers)
		exit()

	# Don't do anything on weekends
	if data.check_weekend() is not None:
		exit()

	symbols = data.get_symbols(source)[0]
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
