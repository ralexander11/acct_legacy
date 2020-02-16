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
			# Fix error due to past null values
			if 'sharesOutstanding' in df.columns.values:
				# print(df['sharesOutstanding'].dtype)
				if df['sharesOutstanding'].dtype == object:
					if df['sharesOutstanding'].str.contains(':').any():
						# print(time_stamp() + 'Error: colon infile:', infile)
						# print(df[df['sharesOutstanding'].str.contains(':', na=False)])
						df = df[~df['sharesOutstanding'].str.contains(':', na=False)]
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
				filename = self.data_location + 'merged_' + str(dates[0]) + '.csv'
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
				filename = self.data_location + 'merged_' + str(symbol[0]) + '.csv'
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
				filename = self.data_location + 'merged_' + str(fields[0]) + '.csv'
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

	def fill_missing(self, missing=None, merged=None, save=False, v=False):
		if v: print(time_stamp() + 'Missing File Save:', save)
		if isinstance(missing, str):
			if '.csv' in missing:
				print(time_stamp() + 'Loading missing data from:', missing)
				missing = pd.read_csv(data_location + 'hist_prices/' + missing)
				if 'close' in missing.columns.values:
					missing = missing.rename(columns={'close': 'hist_close', 'changePercent': 'hist_changePercent', 'change': 'hist_change', 'changeOverTime': 'hist_changeOverTime', 'high': 'hist_high', 'low': 'hist_low', 'open': 'hist_open', 'volume': 'hist_volume', 'label': 'hist_label'})
				missing['comment_miss'] = 'missing'
		if isinstance(merged, str):
			if '.csv' in merged:
				# if merged is None and os.path.exists(self.data_location + merged_file):
				print(time_stamp() + 'Merged data exists at:', self.data_location + merged)
				merged = pd.read_csv(self.data_location + merged)
		if merged is None:
			merged = self.merge_data()
		merged['date'] = pd.to_datetime(merged['date'])
		df = merged.set_index(['symbol','date'])
		df['sector'] = df['sector'].astype(str)
		df['latestEPSDate'] = df['latestEPSDate'].astype(str)
		df['nextEarningsDate'] = df['nextEarningsDate'].astype(str)
		# df = df.drop(['calculationPrice','companyName_x','latestSource','latestTime','primaryExchange','sector','companyName_y','latestEPSDate','comment_merg','isUSMarketOpen','nextEarningsDate','nextDividendDate','exDividendDate','shortDate'], axis=1, errors='ignore')
		# print(df)
		# with pd.option_context('display.max_rows', None):
		# 	print(df.dtypes)
		df['comment_merg'] = 'merged'

		# for i, row in df.iterrows():
		# i = 'sharesOutstanding'
		# row = df['sharesOutstanding']
		# for j, item in row.iteritems():
		# 	try:
		# 		float(item)
		# 	except Exception as e:
		# 		print('Error at row {} item {}:'.format(i, j, repr(e)))
		# bad = df[~df.applymap(lambda x: isinstance(x, (int, float))).all(1)]
		# bad = bad.applymap(lambda x: type(x))
		# with pd.option_context('display.max_columns', None):
		# 	print(time_stamp() + 'bad:\n', bad)
		# exit()

		if missing is not None:
			print(time_stamp() + 'Merging missing data.')
			missing['date'] = pd.to_datetime(missing['date'])
			missing = missing.set_index(['symbol','date'])
			# print(missing)
			# with pd.option_context('display.max_rows', None):
			# 	print(missing.dtypes)
			# df = df.join(missing, how='outer')
			df = df.merge(missing, how='outer', on=['symbol','date'])
		mask = df.index.duplicated(keep='first')
		# print('mask:\n', mask)
		df = df[~mask]
		# Remove any weekends
		df = df[df.index.get_level_values('date').weekday < 5]

		if v: print(time_stamp() + 'Step 1')
		if missing is not None:
			df['close'].fillna(df['hist_close'], inplace=True)
			df['latestPrice'].fillna(df['hist_close'], inplace=True)
			df['change'].fillna(df['hist_change'], inplace=True)
			df['changePercent'].fillna(df['hist_changePercent'], inplace=True)
			df['high'].fillna(df['hist_high'], inplace=True)
			df['low'].fillna(df['hist_low'], inplace=True)
			df['open'].fillna(df['hist_open'], inplace=True)
			df['volume'].fillna(df['hist_volume'], inplace=True)
			df['latestVolume'].fillna(df['hist_volume'], inplace=True)
			df['previousVolume'].fillna(df['hist_volume'].shift(1), inplace=True)
		df['comment'] = None
		df['comment'].fillna(df['comment_merg'], inplace=True)
		if missing is not None:
			df['comment'].fillna(df['comment_miss'], inplace=True)
		df.drop(['comment_merg'], axis=1, errors='ignore', inplace=True)
		df.drop(['comment_miss'], axis=1, errors='ignore', inplace=True)

		if v: print(time_stamp() + 'Step 2')
		df['close'].fillna(df['latestPrice'], inplace=True)
		df['delayedPrice'].fillna(df['latestPrice'], inplace=True)
		df['extendedPrice'].fillna(df['latestPrice'], inplace=True)
		df['extendedChange'].fillna(0, inplace=True)
		df['extendedChangePercent'].fillna(0, inplace=True)
		df['latestSource'].fillna('Close', inplace=True)
		df['latestVolume'].fillna(df['volume'], inplace=True)
		df['latestVolume'].fillna(df['previousVolume'].shift(-1), inplace=True)
		df['volume'].fillna(df['latestVolume'], inplace=True)
		# df.loc[df['latestVolume'].isna(), 'latestVolume'] = df['avgTotalVolume'] # Not yet
		# df['oddLotDelayedPrice'].fillna(df['latestPrice'], inplace=True) # Not in merged
		df['previousVolume'].fillna(df['latestVolume'].shift(1), inplace=True)

		df['sector'].fillna(method='ffill', inplace=True)
		df['avg30Volume'].fillna(df['avgTotalVolume'], inplace=True)
		df['beta'].fillna(method='ffill', inplace=True)
		df['companyName_x'].fillna(method='ffill', inplace=True)
		df['companyName_y'].fillna(method='ffill', inplace=True)
		df['employees'].fillna(method='ffill', inplace=True)
		df['employees'].fillna(method='bfill', inplace=True)
		df['float'].fillna(method='ffill', inplace=True)
		df['float'].fillna(method='bfill', inplace=True)
		
		if v: print(time_stamp() + 'Step 3')
		df['avgTotalVolume'].fillna(df['volume'].rolling(30, min_periods=1).mean(), inplace=True)
		df['avg10Volume'].fillna(df['volume'].rolling(10, min_periods=1).mean(), inplace=True)
		df['avg30Volume'].fillna(df['avgTotalVolume'], inplace=True)
		# df['avg30Volume'].fillna(df['volume'].rolling(30, min_periods=1).mean(), inplace=True)
		df['day200MovingAvg'].fillna(df['latestPrice'].rolling(200, min_periods=1).mean(), inplace=True)
		df['day30ChangePercent'].fillna(df['latestPrice'].pct_change(30), inplace=True)
		df['day50MovingAvg'].fillna(df['latestPrice'].rolling(50, min_periods=1).mean(), inplace=True)
		df['day5ChangePercent'].fillna(df['latestPrice'].pct_change(5), inplace=True)

		if v: print(time_stamp() + 'Step 4')
		df['month1ChangePercent'].fillna(df['latestPrice'].pct_change(30), inplace=True) # freq='M'
		df['month3ChangePercent'].fillna(df['latestPrice'].pct_change(90), inplace=True) # freq='M'
		df['month6ChangePercent'].fillna(df['latestPrice'].pct_change(180), inplace=True) # freq='M'
		df['sharesOutstanding'].fillna(df['marketCap'] / df['latestPrice'], inplace=True)
		df['sharesOutstanding'].fillna(method='ffill', inplace=True)
		df['week52change'].fillna(df['latestPrice'].pct_change(52*7), inplace=True) # freq='M'
		if v: print(time_stamp() + 'Step 5')
		df['week52High'].fillna(df['latestPrice'].rolling(window=52*7, min_periods=1).max(), inplace=True)
		df['week52Low'].fillna(df['latestPrice'].rolling(window=52*7, min_periods=1).min(), inplace=True)
		df['week52high'].fillna(df['week52High'], inplace=True)
		df['week52low'].fillna(df['week52Low'], inplace=True)
		df['calculationPrice'].fillna('close', inplace=True)
		df['previousClose'].fillna(df['close'].shift(1), inplace=True)
		df['change'].fillna(df['close'].diff(), inplace=True)
		df['change'].fillna(df['close'].pct_change(), inplace=True)
		df['marketCap'].fillna(df['sharesOutstanding'] * df['latestPrice'], inplace=True)
		df['marketcap'].fillna(df['marketCap'], inplace=True)
		df['primaryExchange'].fillna(method='ffill', inplace=True)
		df['primaryExchange'].fillna(method='bfill', inplace=True)
		df['dividendYield'].fillna(method='ffill', inplace=True)
		df['dividendYield'].fillna(method='bfill', inplace=True)

		df['peRatio_x'].fillna(df['latestPrice'] / (df['peRatio_x'].shift(1) * df['latestPrice'].shift(1)), inplace=True)
		df['peRatio_y'].fillna(df['peRatio_x'], inplace=True)

		# if v: print(time_stamp() + 'Step 4')
		# df['day50MovingAvg'].fillna((((df['day50MovingAvg'].shift(1) * 49) + df['latestPrice']) / 50), inplace=True) #, fill_value=0 # Test if only needed in while loop
		# if v: print(time_stamp() + 'Step 5')
		# df.loc[df['changePercent'].isna(),'changePercent'] = df['latestPrice'].pct_change() # Old
		# df.loc[df['changePercent'].isna(), 'changePercent'] = df['hist_changePercent'] # Not needed
		if v: print(time_stamp() + 'Step 6')
		# df.drop(['hist_close'], axis=1, errors='ignore', inplace=True)
		# df.drop(['hist_change'], axis=1, errors='ignore', inplace=True)
		# df.drop(['hist_changePercent'], axis=1, errors='ignore', inplace=True)
		# df.drop(['hist_high'], axis=1, errors='ignore', inplace=True)
		# df.drop(['hist_low'], axis=1, errors='ignore', inplace=True)
		# df.drop(['hist_open'], axis=1, errors='ignore', inplace=True)
		# df.drop(['hist_volume'], axis=1, errors='ignore', inplace=True)
		if v: print(time_stamp() + 'Step 7')
		df.dropna(subset=['latestPrice'], inplace=True)
		if v: print(time_stamp() + 'Step 8')
		# while df['day50MovingAvg'].isnull().values.any():
		# 	df['day50MovingAvg'].fillna((((df['day50MovingAvg'].shift(1) * 49) + df['latestPrice']) / 50), inplace=True) # Old
		while df['peRatio_x'].isnull().values.any():
			current = df['peRatio_x'].isnull().values.sum()
			if v: print(current)
			# if current < 800000:
			# 	break
			df['peRatio_x'].fillna(df['latestPrice'] / (df['peRatio_x'].shift(1) * df['latestPrice'].shift(1)), inplace=True)
		df['peRatio_y'].fillna(df['peRatio_x'], inplace=True)
		if v: print(time_stamp() + 'Step 9')
		# with pd.option_context('display.max_rows', None):
		# 	if v: print(time_stamp() + 'Missing data filled:\n', df[['day50MovingAvg','changePercent','close',]])#.head(20))
		# print(time_stamp() + 'Missing data filled:\n{}'.format(df[['day50MovingAvg','changePercent','close',]]))
		# df.reset_index(inplace=True)
		with pd.option_context('display.max_columns', None):
			# display_dates = ['2018-09-04','2018-09-05','2018-09-06']
			# display_dates = ['2019-09-04','2019-09-05','2019-09-06','2019-09-09']
			# display_dates = ['2019-05-28','2019-08-26','2019-08-27']
			display_dates = ['2019-09-13','2019-09-16','2019-10-01']
			# if v: print(time_stamp() + 'missing_merged:\n', df.loc[df.index.get_level_values('date').isin(display_dates)])
		if save:
			filename = 'all_hist_prices_new4'
			path = 'data/' + filename + '_merged.csv'
			df.to_csv(path, date_format='%Y-%m-%d', index=True)
			print(time_stamp() + 'Saved merged missing data to: {}'.format(path))
		return df

	def find_missing(self, data=None, dates_only=False, save=False, v=False):
		if data is None:
			missing = None
			merged = None #'merged.csv'
			data = self.fill_missing(missing, merged)
		if isinstance(data, str):
			if '.csv' in data:
				print(time_stamp() + 'Merged data exists at:', self.data_location + data)
				data = pd.read_csv(self.data_location + data)
		df = data[['symbol','date','close','high','low','open','latestVolume','change','changePercent']]
		df = df[df.isnull().values.any(axis=1)]
		if v: print('Number of missing ticker-dates:', len(df))
		if dates_only:
			df = df['date'].unique()
			df.sort()
		with pd.option_context('display.max_columns', None, 'display.max_rows', None):
			if v: print(time_stamp() + 'Found Missing Fields: {}\n{}'.format(len(df), df))
		if save:
			filename = 'all_miss_fields.csv'
			path = 'data/' + filename
			df.to_csv(path, date_format='%Y-%m-%d', index=True)
			print(time_stamp() + 'Saved found missing fields to: {}'.format(path))
		return df

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
		merged = 'merged.csv' #'merged_AAPl.csv' #'aapl_tsla_quote.csv'
		missing = 'a_to_zyne_hist_prices_2018-05-22_to_2020-01-22.csv'
		# 'aapl_to_aapl_hist_prices_2018-05-22_to_2020-01-22.csv'
		# 'a_to_zzz-ct_hist_prices_2018-05-22_to_2020-01-22' #'all_hist_prices'
		df = combine_data.fill_missing(missing, merged, save=args.save, v=True)
		exit()

	if args.mode == 'find':
		data = 'all_hist_prices_new4_merged.csv'
		df = combine_data.find_missing(data, save=args.save, v=False)
		exit()

	if args.mode == 'merged':
		print(time_stamp() + 'Merged Save: ', args.save)
		# quote_df = combine_data.load_data('quote', dates=args.dates)
		# stats_df = combine_data.load_data('stats', dates=args.dates)
		df = combine_data.merge_data(dates=args.dates, save=args.save)
		# Filter as per available WealthSimple listing criteria
		# df = df.loc[(df['primaryExchange'].isin(['New York Stock Exchange','Nasdaq Global Select'])) & (df['week52High'] > 0.5) & (df['avgTotalVolume'] > 50000)]
		print(time_stamp() + 'Merged data:')
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
		print('Merging all dates for:', args.tickers)
		print('Save: ', args.save)
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

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/combine_data.py -m missing -s >> /home/robale5/becauseinterfaces.com/acct/logs/fix01.log 2>&1 &