import pandas as pd
import glob, os
import datetime
import argparse

DISPLAY_WIDTH = 97
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 20)

def time_stamp(offset=0):
	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
		offset = 4
	time_stamp = (datetime.datetime.now() + datetime.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

class CombineData(object):
	def __init__(self, data_location=None, date=None):
		self.current_date = datetime.datetime.today().strftime('%Y-%m-%d')
		self.date = date
		self.data_location = data_location
		if self.data_location is None:
			if os.path.exists('/home/robale5/becauseinterfaces.com/acct/market_data/data/'):
				print('Server')
				self.data_location = '/home/robale5/becauseinterfaces.com/acct/market_data/data/'
			else:
				# self.data_location = '../market_data/data/'
				# self.data_location = '../market_data/test_data/'
				self.data_location = '/Users/Robbie/Public/market_data/data/'

	def load_file(self, infile):
		with open(infile, 'r') as f:
			try:
				df = pd.read_csv(f, index_col='symbol', encoding='utf-8')
				# df = pd.read_csv(f, header=None, index_col=None, skiprows=1)
				# df = df.drop(labels=0, axis=1)
			except pd.errors.EmptyDataError:
				print('Empty file:', infile)
				return
			fname_date = os.path.basename(infile)[-14:-4]
			# print('fname_date:', fname_date)
			df = df.assign(date=fname_date)
			df = df.drop(['ZEXIT','ZIEXT','ZXIET','ZVZZT','ZWZZT','ZXZZT','NONE','NAN','TRUE','FALSE'], errors='ignore')
			# print(df.head())
			#print('-' * DISPLAY_WIDTH)
			return df

	def load_data(self, end_point, dates=None):
		date = ''
		if dates:
			if not isinstance(dates, (list, tuple)):
				dates = [x.strip() for x in dates.split(',')]
			if len(dates) == 1:
				date = dates[0]
		path = self.data_location + end_point + '/*' + str(date) + '.csv'
		if not os.path.exists(path):
			# print('Not Server')
			path = self.data_location + end_point + '/*' + str(date) + '.csv'
		# print('Path:', path)
		files = glob.glob(path)
		if dates:
			files = [[file for file in files if date in file] for date in dates]
			files = [val for sublist in files for val in sublist]
		# print('date:', dates)
		files.sort()
		# print('files:', files)
		dfs = []
		for fname in files:
			load_df = self.load_file(fname)
			# if 'stats' in fname:
			# 	load_df = load_df[~load_df['avg10Volume'].str.contains(':', na=False)]
			# 	print('cleaned:', load_df)
			# 	exit()
			if load_df is None:
				continue
			dfs.append(load_df)
		df = pd.concat(dfs, sort=True) # Sort to suppress warning
		df = df.set_index('date', append=True)
		return df

	def merge_data(self, quote_df=None, stats_df=None, dates=None, save=False):
		if quote_df is None:
			quote_df = self.load_data('quote', dates=dates)
		if stats_df is None:
			stats_df = self.load_data('stats', dates=dates)
		merged = pd.merge(quote_df, stats_df, how='outer', left_index=True, right_index=True, sort=False)
		if save:
			merged.to_csv(self.data_location + 'merged.csv')
			print(time_stamp() + 'Saved merged data!\n{}'.format(merged.head()))
		return merged

	def date_filter(self, dates=None, merged=None, save=False, v=False):
		if dates is None:
			dates = str(self.current_date)
		if merged is None:
			# quote_df = self.load_data('quote', dates=dates)
			# stats_df = self.load_data('stats', dates=dates)
			merged = self.merge_data(dates=dates)
		if v: print('Data filtered for dates:\n{}'.format(merged))
		if save:
			if len(dates) == 1:
				filename = self.data_location + 'merged_' + str(dates) + '.csv'
			else:
				filename = self.data_location + 'merged_' + str(dates[0]) + '_to_' + str(dates[-1]) + '.csv'
			merged.to_csv(filename)
			print(time_stamp() + 'Saved data filtered for dates: {}\nTo: {}'.format(dates, filename))
		return merged

	def comp_filter(self, symbol, merged=None, flatten=False, save=False, v=False):
		if merged is None:
			merged = self.merge_data()
		if not isinstance(symbol, (list, tuple)):
			symbol = [x.strip().upper() for x in symbol.split(',')]
		else:
			if isinstance(symbol[-1], float): # xlsx causes last ticker to be nan
				symbol = symbol[:-2]
			symbol = list(map(str.upper, symbol))
		merged = merged.reset_index(level='symbol')
		merged = merged.loc[merged['symbol'].isin(symbol)]
		if flatten:
			merged = merged.set_index('symbol', append=True)
			# merged.columns = merged.columns.swaplevel(0, 1)
			merged = merged.unstack(level='symbol')
			# merged.columns = ['_'.join(c) for c in merged.columns]
			merged.columns = ['_'.join(reversed(c)) for c in merged.columns]
		if v: print('Data filtered for symbols:\n{}'.format(merged))
		if save:
			if len(symbol) == 1:
				filename = self.data_location + 'merged_' + str(symbol) + '.csv'
			else:
				filename = self.data_location + 'merged_' + str(symbol[0]) + '_to_' + str(symbol[-1]) + '.csv'
			merged.to_csv(filename)
			print(time_stamp() + 'Saved data filtered for symbols: {}\nTo: {}'.format(symbol, filename))
		return merged

	def data_point(self, fields, merged=None, v=False):
		if merged is None:
			# quote_df = self.load_data('quote')
			# stats_df = self.load_data('stats')
			merged = self.merge_data()#quote_df, stats_df)
		if not isinstance(fields, (list, tuple)):
			fields = [x.strip() for x in fields.split(',')]
		merged = merged[fields]
		if v: print('Data filtered for fields:\n{}'.format(merged))
		if save:
			if len(fields) == 1:
				filename = self.data_location + 'merged_' + str(fields) + '.csv'
			else:
				filename = self.data_location + 'merged_' + str(fields[0]) + '_to_' + str(fields[-1]) + '.csv'
			merged.to_csv(filename)
			print(time_stamp() + 'Saved data filtered for fields: {}\nTo: {}'.format(fields, filename))
		return merged#[fields]

	def value(self, date, symbol, field, merged=None):
		if merged is None:
			# quote_df = self.load_data('quote')
			# stats_df = self.load_data('stats')
			merged = self.merge_data()#quote_df, stats_df)
		return merged.xs((symbol.upper(), date))[field]

	def front(self, n):
		return self.iloc[:, :n]

	def back(self, n):
		return self.iloc[:, -n:]

	def fill_missing(self, missing, merged=None, save=False, v=False):
		if isinstance(missing, str):
			if '.csv' in missing:
				print(time_stamp() + 'Loading missing data from:', missing)
				missing = pd.read_csv(missing)
		merged_file = 'merged.csv' #'aapl_tsla_quote.csv'
		if merged is None and os.path.exists(self.data_location + merged_file):
			print(time_stamp() + 'Merged data exists at:', self.data_location)
			merged = pd.read_csv(self.data_location + merged_file)
			merged = merged.set_index(['symbol','date'])
		missing = missing.set_index(['symbol','date'])
		merged = merged.join(missing, how='outer')
		mask = merged.index.duplicated(keep='first')
		# print('mask:\n', mask)
		merged = merged[~mask]
		if v: print(time_stamp() + 'Step 1')
		merged.loc[merged['close'].isna(),'close'] = merged['hist_close']
		if v: print(time_stamp() + 'Step 2')
		# merged.loc[merged['day50MovingAvg'].isna(),'day50MovingAvg'] = merged['close'].rolling(50, min_periods=1).mean() # Not working
		# merged.loc[merged['day50MovingAvg'].isna(),'day50MovingAvg'] = ((merged['day50MovingAvg'].shift(1, fill_value=0) * 49) + merged['close']) / 50 # Not used
		# merged['day50MovingAvg'] = merged['day50MovingAvg'].astype(float)
		merged['day50MovingAvg'].fillna((((merged['day50MovingAvg'].shift(1, fill_value=0) * 49) + merged['close']) / 50), inplace=True)
		if v: print(time_stamp() + 'Step 3')
		merged.loc[merged['changePercent'].isna(),'changePercent'] = merged['close'].pct_change()
		if v: print(time_stamp() + 'Step 4')
		merged = merged.drop('hist_close', axis=1)
		if v: print(time_stamp() + 'Step 5')
		merged.dropna(subset=['close'], inplace=True)
		if v: print(time_stamp() + 'Step 6')
		while merged['day50MovingAvg'].isnull().values.any():
			merged['day50MovingAvg'].fillna((((merged['day50MovingAvg'].shift(1) * 49) + merged['close']) / 50), inplace=True)
		if v: print(time_stamp() + 'Step 7')
		# with pd.option_context('display.max_rows', None):
			# print(merged[['day50MovingAvg','changePercent','close',]])#.head(20))
		print('Missing data filled:\n{}'.format(merged[['day50MovingAvg','changePercent','close',]]))
		if save:
			filename = '/data/' + 'all_hist_prices' + '_merged.csv'
			merged.to_csv(filename, date_format='%Y-%m-%d', index=True)
			print(time_stamp() + 'Saved merged missing data to: {}'.format(filename))
		return merged

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--dates', type=str, help='A list of dates to combine data for.')
	parser.add_argument('-t', '--tickers', type=str, help='A list of tickers to filter data for.')
	parser.add_argument('-f', '--fields', type=str, help='The fields to filter data for.')
	parser.add_argument('-m', '--mode', type=str, help='The mode to run: merged, missing, value, tickers.')
	parser.add_argument('-s', '--save', action='store_true', help='Save the results to csv.')
	args = parser.parse_args()

	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/market_data/data/'):
		data_location = '/home/robale5/becauseinterfaces.com/acct/market_data/data/'
	else:
		# data_location = '../../market_data/test_data/'
		data_location = '/Users/Robbie/Public/market_data/new/data/'
	combine_data = CombineData(data_location=data_location)

	if args.mode == 'missing':
		df = combine_data.fill_missing(data_location + 'hist_prices/all_hist_prices.csv', save=args.save)
		exit()

	if args.mode == 'merged':
		print('Save: ', args.save)
		# quote_df = combine_data.load_data('quote', dates=args.dates)
		# stats_df = combine_data.load_data('stats', dates=args.dates)
		df = combine_data.merge_data(dates=args.dates, save=args.save)
		# Filter as per available WealthSimple listing criteria
		# df = df.loc[(df['primaryExchange'].isin(['New York Stock Exchange','Nasdaq Global Select'])) & (df['week52High'] > 0.5) & (df['avgTotalVolume'] > 50000)]
		print('Merged data:')
		print(df.head())
		exit()

	if args.mode == 'tickers':
		df = combine_data.merge_data(dates=args.dates)
		df.reset_index(inplace=True)
		tickers = pd.Series(df.symbol.unique())
		if args.save:
			tickers.to_csv('../data/' + 'all_tickers.csv', date_format='%Y-%m-%d', index=True)
		print(tickers.head())
		exit()

	if args.mode == 'value':
		if not isinstance(args.fields, (list, tuple)):
			args.fields = [x.strip() for x in args.fields.split(',')]
		if not isinstance(args.dates, (list, tuple)):
			args.dates = [x.strip() for x in args.dates.split(',')]
		if not isinstance(args.tickers, (list, tuple)):
			args.tickers = [x.strip() for x in args.tickers.split(',')]
		if len(args.fields) == 1 and len(args.dates) == 1 and len(args.tickers) == 1:
			print('{} value for {} on {}:'.format(args.fields[0], args.tickers[0], dates[0]))
			result = combine_data.value(args.dates, args.tickers, args.fields)
			print(result)
			print('-' * DISPLAY_WIDTH)
			exit()
		else:
			print('Value option only works when one field, date, and ticker are provided.')

	if args.dates and args.tickers and args.fields:
		df = combine_data.data_point(args.fields, combine_data.comp_filter(args.tickers, combine_data.date_filter(args.dates)), save=args.save)
	if args.dates and args.tickers and args.fields is None:
		df = combine_data.comp_filter(args.tickers, combine_data.date_filter(args.dates), save=args.save)
	if args.dates and args.tickers is None and args.fields:
		df = combine_data.data_point(args.fields, combine_data.date_filter(args.dates), save=args.save)
	if args.dates is None and args.tickers and args.fields:
		df = combine_data.data_point(args.fields, combine_data.comp_filter(args.tickers), save=args.save)
	if args.dates and args.tickers is None and args.fields is None:
		df = combine_data.date_filter(args.dates, save=args.save)
	if args.dates is None and args.tickers and args.fields is None:
		df = combine_data.comp_filter(args.tickers, save=args.save)
	if args.dates is None and args.tickers is None and args.fields:
		df = combine_data.data_point(args.fields, save=args.save)

	# print('Date Filter:')
	# print(combine_data.date_filter('2018-05-11'))
	# print('-' * DISPLAY_WIDTH)
	# print('Company Filter:')
	# print(combine_data.comp_filter('tsla'))
	# print('-' * DISPLAY_WIDTH)
	# print('Data Point Filter:')
	# print(combine_data.data_point('close'))
	# print('-' * DISPLAY_WIDTH)

	# print(combine_data.data_point('close', combine_data.comp_filter('tsla', combine_data.date_filter('2018-05-11')))) # Has to be in this specific order
	# rank_df = combine_data.data_point('week52high', combine_data.date_filter('2018-05-11'))
	# print(rank_df)
	# print('=' * DISPLAY_WIDTH)

	#result.to_csv('data/combined_' + combine_data.current_date + '.csv')

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/combine_data.py >> /home/robale5/becauseinterfaces.com/acct/logs/combine01.log 2>&1 &