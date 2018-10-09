import pandas as pd
import glob, os
import datetime

DISPLAY_WIDTH = 97
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 20)

class MarketData(object):
	def __init__(self, date=None):
		self.current_date = datetime.datetime.today().strftime('%Y-%m-%d')
		self.date = date

	def load_file(self, infile):
		with open(infile, 'r') as f:
			df = pd.read_csv(f, index_col='symbol')
			fname_date = os.path.basename(infile)[-14:-4]
			#print(fname_date)
			df = df.assign(date=fname_date)
			#print (df)
			#print ('-' * DISPLAY_WIDTH)
			return df

	def load_data(self, end_point):
		path = '/home/robale5/becauseinterfaces.com/acct/trading/market_data/' + end_point + '/*.csv'
		if not os.path.exists(path): # TODO Test this
			print('Not Server')
			path = 'market_data/' + end_point + '/*.csv'
		#print(path)
		dfs = []
		for fname in glob.glob(path):
			#print (fname)
			load_df = self.load_file(fname)
			dfs.append(load_df)
		df = pd.concat(dfs)
		df = df.set_index('date', append=True)
		return df

	def merge_data(self, quote_df, stats_df):
		result = pd.merge(quote_df, stats_df, how='outer', left_index=True, right_index=True, sort=False)
		return result

	def date_filter(self, date=None, merged=None):
		if date is None:
			date = self.current_date
		if merged is None:
			quote_df = self.load_data('quote')
			stats_df = self.load_data('stats')
			merged = self.merge_data(quote_df, stats_df)
		return merged.xs(date, level='date')

	def comp_filter(self, symbol, merged=None):
		if merged is None:
			quote_df = self.load_data('quote')
			stats_df = self.load_data('stats')
			merged = self.merge_data(quote_df, stats_df)
		return merged.xs(symbol.upper())#, level='symbol')

	def data_point(self, field, merged=None):
		if merged is None:
			quote_df = self.load_data('quote')
			stats_df = self.load_data('stats')
			merged = self.merge_data(quote_df, stats_df)
		return merged[field]

	def value(self, date, symbol, field, merged=None):
		if merged is None:
			quote_df = self.load_data('quote')
			stats_df = self.load_data('stats')
			merged = self.merge_data(quote_df, stats_df)
		return merged.xs((symbol.upper(), date))[field]

	# TODO Add save data function

	def front(self, n):
		return self.iloc[:, :n]

	def back(self, n):
		return self.iloc[:, -n:]

if __name__ == '__main__':
	data = MarketData()
	quote_df = data.load_data('quote')
	stats_df = data.load_data('stats')

	#pd.DataFrame.front = front
	#pd.DataFrame.back = back
	
	# TODO Add command line functions

	result = data.merge_data(quote_df, stats_df)
	print('Full:')
	print(result)
	print('-' * DISPLAY_WIDTH)

	print('Date Filter:')
	print(data.date_filter('2018-05-11'))
	print('-' * DISPLAY_WIDTH)
	print('Company Filter:')
	print(data.comp_filter('tsla'))
	print('-' * DISPLAY_WIDTH)
	print('Data Point Filter:')
	print(data.data_point('close'))
	print('-' * DISPLAY_WIDTH)
	print('Value:')
	print(data.value('2018-05-11','tsla','close'))
	print('-' * DISPLAY_WIDTH)

	print(data.data_point('close', data.comp_filter('tsla', data.date_filter('2018-05-11')))) # Has to be in this specific order
	rank_df = data.data_point('week52high', data.date_filter('2018-05-11'))
	print(rank_df)
	print('=' * DISPLAY_WIDTH)

	#result.to_csv('market_data/combined_' + data.current_date + '.csv')
