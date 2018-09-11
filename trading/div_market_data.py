import numpy as np
import pandas as pd
import time
from tqdm import tqdm

DISPLAY_WIDTH = 160
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 20)

class Feed(object):
	def __init__(self):
		#self.save_location = '/home/robale5/becauseinterfaces.com/acct/trading/market_data/'
		self.save_location = 'market_data/'
	
	def get_symbols(self, flag):
		if flag == 'iex':
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			#print (symbols)
			print(time.ctime())
			outfile = flag + '_tickers' + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
			symbols.to_csv(self.save_location + 'tickers/' + outfile)
			return symbols
		
		if flag == 'sp500':
			sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
			symbols = pd.read_html(sp500_url, header=0)
			print(symbols)
			symbols = symbols[0]
			symbols.columns = ['symbols','security','sec_filings','sector','sub_sector','location','date_added','cik','founded']
			print (symbols['symbols'])
			return symbols
			
		if flag == 'test':
			corps = ['aapl','kmb','ges','gm','cni','tu','unh','lzb','wm']
			#corps = ['tsla','afk','aapl','goog','trp','spot']
			symbols = pd.DataFrame(corps, columns = ['symbol'])
			#print (symbols)
			print(time.ctime())
			return symbols

	def get_data(self, symbols, end_point='quote'):
		url = 'https://api.iextrading.com/1.0/stock/'
		dfs = []
		invalid_tickers = []
		print('Getting data of ' + source + ' for end point: ' + end_point)
		for symbol in tqdm(symbols['symbol']):
			try:
				s = pd.read_json(url + symbol + '/' + end_point, typ='series', orient='index')
				df = s.to_frame().T
				df = df.set_index('symbol')
				dfs.append(df)
			except:
				invalid_tickers.append(symbol)
		data = pd.concat(dfs, verify_integrity=True)
		print (data)
		print ('-' * DISPLAY_WIDTH)
		return data, invalid_tickers

	def dividends(self, symbols, end_point='dividends/3m'):
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

	def save_data(self, data):
		end_point = 'dividends/5y'
		if '/' in end_point:
			end_point = end_point.replace('/','_')
		outfile = source + '_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
		data.to_csv(self.save_location + end_point + '/' + outfile)

	def save_errors(self, invalid_tickers):
		error_df = pd.DataFrame(np.array(invalid_tickers))
		print (error_df)
		error_df.to_csv(self.save_location + 'invalid_tickers/' + 'invalid_tickers_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv')

if __name__ == '__main__':
	feed = Feed()
	source = 'test' #'iex' # input("Which ticker source? ").lower()
	symbols = feed.get_symbols(source)
	
	end_points = ['dividends/5y']
	for end_point in end_points: 
		div_data, div_invalid_tickers = feed.dividends(symbols, end_point)
		feed.save_data(div_data)
		feed.save_errors(div_invalid_tickers)
	exit()

	end_points = ['quote', 'stats'] #['company','financials','earnings','peers']
	for end_point in end_points:
		try:
			data, invalid_tickers = feed.get_data(symbols, end_point)
			feed.save_data(data)
			feed.save_errors(invalid_tickers)
		except:
			continue
	print (time.ctime())
