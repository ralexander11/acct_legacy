import pandas as pd
import glob, os
import datetime

DISPLAY_WIDTH = 97
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 20)

class CombineData(object):
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
		path = '/home/robale5/becauseinterfaces.com/acct/market_data/data/' + end_point + '/*.csv'
		if not os.path.exists(path): # TODO Test this
			print('Not Server')
			path = 'data/' + end_point + '/*.csv'
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
	combine_data = CombineData()
	quote_df = combine_data.load_data('quote')
	stats_df = combine_data.load_data('stats')

	#pd.DataFrame.front = front
	#pd.DataFrame.back = back
	
	# TODO Add command line functions

	result = combine_data.merge_data(quote_df, stats_df)
	print('Full:')
	print(result)
	print('-' * DISPLAY_WIDTH)

	print('Date Filter:')
	print(combine_data.date_filter('2018-05-11'))
	print('-' * DISPLAY_WIDTH)
	print('Company Filter:')
	print(combine_data.comp_filter('tsla'))
	print('-' * DISPLAY_WIDTH)
	print('Data Point Filter:')
	print(combine_data.data_point('close'))
	print('-' * DISPLAY_WIDTH)
	print('Value:')
	print(combine_data.value('2018-05-11','tsla','close'))
	print('-' * DISPLAY_WIDTH)

	print(combine_data.data_point('close', combine_data.comp_filter('tsla', combine_data.date_filter('2018-05-11')))) # Has to be in this specific order
	rank_df = combine_data.data_point('week52high', combine_data.date_filter('2018-05-11'))
	print(rank_df)
	print('=' * DISPLAY_WIDTH)

	#result.to_csv('data/combined_' + combine_data.current_date + '.csv')
