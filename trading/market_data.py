import numpy as np
import pandas as pd
import datetime
import time
import os
import urllib
#import urllib.request
#from tqdm import tqdm

DISPLAY_WIDTH = 98
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 20)

class Feed(object):
	save_location = '/home/robale5/becauseinterfaces.com/acct/trading/market_data/'
	if not os.path.isdir(save_location):
		print('Not Server')
		save_location = 'market_data/'
	
	def time(self):
		time = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
		return time

	def get_symbols(self, flag):
		if flag == 'iex':
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
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
		url = 'https://api.iextrading.com/1.0/stock/'
		dfs = []
		invalid_tickers = []
		for symbol in symbols['symbol']: #tqdm(symbols['symbol']):
			try:
				s = pd.read_json(url + symbol + '/' + end_point, typ='series', orient='index')
				df = s.to_frame().T
				df = df.set_index('symbol')
				dfs.append(df)
			except:
				invalid_tickers.append(symbol)
			
		data = pd.concat(dfs, verify_integrity=True)
		#print(data)
		#print('-' * DISPLAY_WIDTH)
		return data, invalid_tickers

	def get_batch(self, symbols_list, end_points='price'):
		url = 'https://api.iextrading.com/1.0/stock/market/batch?symbols='
		url_batch = 'https://api.iextrading.com/1.0/stock/market/batch?'
		url_batch = url_batch + urllib.parse.urlencode(symbols_list)
		print('URL: {}'.format(url_batch))
		batch_data = pd.read_json(url_batch + '&types=' + end_points, typ='frame', orient='index')
		#batch_data = pd.read_json(url + symbols_list + '&types=' + end_points, typ='frame', orient='index')
		print(batch_data)
		return batch_data

	def get_prices(self, symbols):
		t1_start = time.perf_counter()
		url = 'https://api.iextrading.com/1.0/stock/'
		prices = {}
		invalid_tickers = []
		print('Getting prices for all tickers from ' + source + '.')
		for symbol in symbols['symbol']:
			#print('Symbol: {}'.format(symbol))
			try:
				price = float(urllib.request.urlopen(url + symbol + '/price').read())
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
		url = 'https://api.iextrading.com/1.0/stock/'
		dividends = []
		invalid_tickers_divs = []
		print(end_point)
		for symbol in symbols['symbol']:
			print('Getting divs for: {}'.format(symbol))
			try:
				div = pd.read_json(url + symbol + '/' + end_point, typ='frame', orient='records')
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

	def save_data(self, data, end_point='quote'):
		if '/' in end_point:
			end_point = end_point.replace('/','_')
		outfile = source + '_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
		path = self.save_location + end_point + '/' + outfile
		data.to_csv(path)
		print(feed.time() + 'Data file saved to: {}'.format(path))

	def save_errors(self, invalid_tickers, end_point='quote'):
		if '/' in end_point:
			end_point = end_point.replace('/','_')
		error_df = pd.DataFrame(np.array(invalid_tickers))
		#print(error_df)
		path = self.save_location + 'invalid_tickers/' + 'invalid_tickers_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
		error_df.to_csv(path)
		print(feed.time() + 'Invalid tickers file saved to: {}'.format(path))

if __name__ == '__main__':
	feed = Feed()
	t0_start = time.perf_counter()
	source = 'iex' # input('Which ticker source? ').lower() # TODO Add support for argparse
	print('=' * DISPLAY_WIDTH)
	print(feed.time() + 'Getting data from: {}'.format(source))

	batch_test = False
	if batch_test:
		t0_start = time.perf_counter()
		symbols_list = feed.get_symbols(source)[2]
		data = feed.get_batch(symbols_list)
		t0_end = time.perf_counter()
		print(feed.time() + 'Finished getting batch prices! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
		exit()

	dividends_test = False
	if dividends_test:
		end_points = ['dividends/5y']
		for end_point in end_points: 
			div_data, div_invalid_tickers = feed.dividends(symbols, end_point)
			feed.save_data(div_data)
			feed.save_errors(div_invalid_tickers)
		exit()

	symbols = feed.get_symbols(source)[0]
	end_points = ['quote', 'stats'] #['company','financials','earnings','peers']
	for end_point in end_points:
		try:
			print(feed.time() + 'Getting data from ' + source + ' for end point: ' + end_point)
			data, invalid_tickers = feed.get_data(symbols, end_point)
			feed.save_data(data, end_point)
			feed.save_errors(invalid_tickers, end_point)
			print('-' * DISPLAY_WIDTH)
		except Exception as e:
			print(feed.time() + 'Error: {}'.format(e))
			print('-' * DISPLAY_WIDTH)
			continue
	t0_end = time.perf_counter()
	print(feed.time() + 'Finished getting market data! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))
