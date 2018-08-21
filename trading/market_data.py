import numpy as np
import pandas as pd
import time
from tqdm import tqdm

DISPLAY_WIDTH = 98
pd.set_option('display.width',DISPLAY_WIDTH)

class Feed(object):
	save_location = 'data/'
	#save_location = '/home/robale5/becauseinterfaces.com/acct/trading/market_data/'
	
	def get_symbols(self, flag):
		if flag == 'iex':
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			#print (symbols)
			print(time.ctime())
			outfile = flag + '_tickers' + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
			symbols.to_csv(self.save_location + 'tickers/' + outfile)
			return symbols
		
		# if flag == 'sp500':
			# sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
			# symbols = pd.read_html(sp500_url, header=0)
			# symbols = symbols[0]
			# symbols.columns = ['symbols','security','sec_filings','sector','sub_sector','address','date_added','cik']
			# print (symbols['symbols'])
			# return symbols
			
		if flag == 'test':
			symbols = pd.DataFrame(['tsla','afk','aapl','goog','trp','spot'], columns = ['symbol'])
			#print (symbols)
			print (time.ctime())
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

	def save_data(self, data):
		outfile = source + '_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
		data.to_csv(self.save_location + end_point + '/' + outfile)

	def save_errors(self, invalid_tickers):
		error_df = pd.DataFrame(np.array(invalid_tickers))
		print (error_df)
		error_df.to_csv(self.save_location + 'invalid_tickers/' + 'invalid_tickers_' + end_point + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv')

if __name__ == '__main__':
	feed = Feed()
	source = 'iex' # input("Which ticker source? ").lower()
	symbols = feed.get_symbols(source)
	end_points = ['quote', 'stats'] #['company','financials','earnings','peers']
	for end_point in end_points:
		try:
			data, invalid_tickers = feed.get_data(symbols, end_point)
			feed.save_data(data)
			feed.save_errors(invalid_tickers)
		except:
			continue
	print (time.ctime())
