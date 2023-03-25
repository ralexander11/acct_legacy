import numpy as np
import pandas as pd
import glob, os
import datetime as dt
import argparse
import sys

DISPLAY_WIDTH = 97
pd.set_option('display.width',DISPLAY_WIDTH)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 20)

def time_stamp(offset=0):
	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
		offset = 4
	time_stamp = (dt.datetime.now() + dt.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

class CombineData(object):
	def __init__(self, data_location=None, date=None):
		self.current_date = dt.datetime.today().strftime('%Y-%m-%d')
		self.date = date
		self.data_location = data_location
		if self.data_location is None:
			if os.path.exists('/home/robale5/becauseinterfaces.com/acct/market_data/data/'):
				self.data_location = '/home/robale5/becauseinterfaces.com/acct/market_data/data/'
				print(time_stamp() + 'Combine Data: Server')
			elif os.path.exists('/Users/Robbie/Public/market_data/new/data/'):
				self.data_location = '/Users/Robbie/Public/market_data/new/data/'
				# self.data_location = '/Users/Robbie/Public/market_data/test_data/'
			else:
				if os.getcwd().split('/')[-1] != 'market_data':
					self.data_location = 'market_data/data/'
				else:
					self.data_location = '../market_data/data/'
					# self.data_location = '../market_data/test_data/'
		print('Data Location:', self.data_location)

	def load_file(self, infile, compress=None):
		if infile[-3:] == '.gz':
			compress = True
		if compress:
			open_mode = 'rb'
		else:
			open_mode = 'r'
		with open(infile, open_mode) as f:
			try:
				if compress:
					df = pd.read_csv(f, compression='gzip', na_filter = False)
				else:
					df = pd.read_csv(f, encoding='utf-8', na_filter = False)
			except pd.errors.EmptyDataError:
				print('Empty file:', infile)
				return
			df = df.set_index('symbol')
			if compress:
				fname_date = os.path.basename(infile)[-17:-7]
			else:
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
				if isinstance(dates, str):
					dates = [x.strip() for x in dates.split(',')]
				else:
					dates = [dt.datetime.strftime('%Y-%m-%d', dates)]
			if len(dates) == 1:
				date = dates[0]
				if not isinstance(date, str):
					date = dt.datetime.strftime('%Y-%m-%d', date)
		path = self.data_location + end_point + '/*' + str(date) + '.csv.gz'
		compress = True
		print('Path gz:', path)
		files = glob.glob(path)
		if not files:
			# print('Data not Compressed')
			path = self.data_location + end_point + '/*' + str(date) + '.csv'
			compress = False
			files = glob.glob(path)
		print('Path:', path)
		if dates:
			files = [[file for file in files if date in file] for date in dates]
			files = [val for sublist in files for val in sublist]
		# print('date:', dates)
		files.sort()
		# print('files:', files)
		dfs = []
		for fname in files:
			# print(time_stamp() + 'fname:', fname)
			load_df = self.load_file(fname, compress=compress)
			# if 'stats' in fname:
			# 	load_df = load_df[~load_df['avg10Volume'].str.contains(':', na=False)]
			# 	print('cleaned:', load_df)
			# 	exit()
			if load_df is None:
				continue
			dfs.append(load_df)
		if all(e is None for e in dfs):
			print(time_stamp() + f'No data for {end_point}.')
			return pd.DataFrame()
		df = pd.concat(dfs, sort=True) # Sort to suppress warning
		df = df.set_index('date', append=True)
		return df

	def merge_data(self, quote_df=None, stats_df=None, dates=None, save=False):
		if quote_df is None:
			quote_df = self.load_data('quote', dates=dates)
		if stats_df is None:
			stats_df = self.load_data('stats', dates=dates)
		merged = pd.merge(quote_df, stats_df, how='outer', left_index=True, right_index=True, suffixes=(None, '_y'), sort=False)
		if save:
			merged.to_csv(self.data_location + 'merged.csv', index=True)
			print(time_stamp() + 'Saved merged data!\n{}'.format(merged.head()))
		return merged

	def date_filter(self, dates=None, merged=None, since=False, until=False, data=None, filename=None, save=False, v=False):
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if dates is not None:
			if '.csv' in dates:
				dates = pd.read_csv(self.data_location + '../../data/' + dates, header=None, comment='#')
				if 'date' in dates.columns.values.tolist():
					dates = dates['date'].values.tolist()
				elif 'dates' in dates.columns.values.tolist():
					dates = dates['dates'].values.tolist()
				else:
					dates = dates.iloc[:,0].values.tolist()
		# since with no date: jan to now
		# since with date: date to now
		# until with no date: start of data ['2018-05-08'] to now
		# until with date: jan to date?
		# add start date (sd) arg?
		# until with sd: sd to date?
		# if sd == 'None' then = None
		if not since:
			try:
				since = args.since
			except NameError:
				pass
		if not until:
			try:
				until = args.until
			except NameError:
				pass
		if since or until:
			if dates:
				if not isinstance(dates, (list, tuple)):
					if isinstance(dates, str):
						dates = [x.strip() for x in dates.split(',')]
					else:
						dates = [dates]
			if len(dates) > 1:
				# TODO Raise an exception
				print('Must provide only 1 date with the "since" or "until" commands. Will use the max date.')
				dates = [max(dates)]
				print('Date:', dates)
				#return
			if until:
				if not dates:
					end_date = dt.datetime.today()
				else:
					end_date = dates[-1]
					end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
			else:
				end_date = dt.datetime.today()
			if since:
				if not dates:
					if args.start_date:
						start_date = args.start_date
					else:
						start_date = '2020-01-24'
				else:
					if args.start_date:
						start_date = args.start_date
					else:
						if isinstance(dates, (list, tuple)):
							start_date = dates[0]
						else:
							start_date = dates
			else:
				if args.start_date:
					start_date = args.start_date
				else:
					start_date = '2020-01-24'
			if v: print('start_date:', start_date)
			dates = pd.date_range(start=start_date, end=end_date, freq='D').to_pydatetime().tolist()
			dates = [date.strftime('%Y-%m-%d') for date in dates]
			print(time_stamp() + f'Number of Days since {dates[0]}: {len(dates)}')
		else:
			if dates is None:
				try:
					dates = args.dates
				except NameError:
					pass
				if dates is None:
					dates = [str(self.current_date)]
			else:
				if not isinstance(dates, (list, tuple)):
					if isinstance(dates, str):
						dates = [x.strip() for x in dates.split(',')]
					else:
						dates = [dates]
		if merged is None:
			merged = self.merge_data(dates=dates)
		elif '.csv' in merged:
			merged = pd.read_csv(self.data_location + merged)
		if merged.index.names[0] is not None:
			merged.reset_index(inplace=True)
		merged = merged.loc[merged['date'].isin(dates)]
		if data is not None:
			merged = pd.concat([data, merged])
		if v: print(time_stamp() + 'Data filtered for dates:\n{}'.format(merged))
		if save:
			if not pathname:
				if dates:
					if len(dates) == 1:
						pathname = self.data_location + filename + '_' + str(dates[0]) + '.csv'
					else:
						pathname = self.data_location + filename + '_' + str(dates[0]) + '_to_' + str(dates[-1]) + '.csv'
				else:
					pathname = self.data_location + filename + '.csv'
			merged.to_csv(pathname, index=True)
			print(time_stamp() + 'Saved data filtered for dates: {}\nTo: {}'.format(dates, pathname))
		return merged

	def comp_filter(self, symbol, merged=None, flatten=False, filename=None, save=False, v=False):
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if '.csv' in symbol:
			symbol = pd.read_csv(self.data_location + '../../data/' + symbol, header=None, comment='#')
			if 'symbol' in symbol.columns.values.tolist():
				symbol = symbol['symbol'].values.tolist()
			elif 'symbols' in symbol.columns.values.tolist():
				symbol = symbol['symbols'].values.tolist()
			elif 'ticker' in symbol.columns.values.tolist():
				symbol = symbol['ticker'].values.tolist()
			elif 'tickers' in symbol.columns.values.tolist():
				symbol = symbol['tickers'].values.tolist()
			else:
				symbol = symbol.iloc[:,0].values.tolist()
		if merged is None:
			# if os.path.exists('data/merged.csv'):
			# 	merged = pd.read_csv('data/merged.csv')
			# else:
			merged = self.merge_data()
		if symbol is None:
			symbol = []
		if not isinstance(symbol, (list, tuple)):
			symbol = [x.strip().upper() for x in symbol.split(',')]
		else:
			if isinstance(symbol[-1], float): # xlsx causes last ticker to be nan
				symbol = symbol[:-2]
			symbol = list(map(str.upper, symbol))
		if merged.index.names[0] is not None:
			merged = merged.reset_index()
		if symbol:
			merged = merged.loc[merged['symbol'].isin(symbol)]
		if flatten:
			merged = merged.set_index('symbol', append=True)
			# merged.columns = merged.columns.swaplevel(0, 1)
			merged = merged.unstack(level='symbol')
			# merged.columns = ['_'.join(c) for c in merged.columns]
			merged.columns = ['_'.join(reversed(c)) for c in merged.columns]
		if v: print('Data filtered for symbols:\n{}'.format(merged))
		if save:
			if not pathname:
				if len(symbol) == 1:
					pathname = self.data_location + filename + '_' + str(symbol[0]).lower() + '.csv'
				else:
					pathname = self.data_location + filename + '_' + str(symbol[0]).lower() + '_to_' + str(symbol[-1]).lower() + '.csv'
			merged.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved data filtered for symbols: {}\nTo: {}'.format(symbol, pathname))
		return merged

	def data_point(self, fields, merged=None, filename=None, save=False, v=False):
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if merged is None:
			# quote_df = self.load_data('quote')
			# stats_df = self.load_data('stats')
			merged = self.merge_data()#quote_df, stats_df)
		if '.csv' in fields:
			fields = pd.read_csv(self.data_location + fields, header=None, comment='#')
			if 'fields' in fields.columns.values.tolist():
				fields = fields['fields'].values.tolist()
			elif 'features' in fields.columns.values.tolist():
				fields = fields['features'].values.tolist()
			else:
				fields = fields.iloc[:,0].values.tolist()
		cols = merged.columns.values.tolist()
		if not isinstance(fields, (list, tuple)):
			fields = [x.strip() for x in fields.split(',') if x in cols]
		else:
			fields = [x for x in fields if x in cols]
		merged = merged[fields]
		if v: print('Data filtered for fields:\n{}'.format(merged))
		if save:
			if not pathname:
				if len(fields) == 1:
					pathname = self.data_location + filename + '_' + str(fields[0]) + '.csv'
				else:
					pathname = self.data_location + filename + '_' + str(fields[0]) + '_to_' + str(fields[-1]) + '.csv'
			merged.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved data filtered for fields: {}\nTo: {}'.format(fields, pathname))
		return merged#[fields]

	def value(self, date, symbol, field, merged=None):
		if merged is None:
			# quote_df = self.load_data('quote')
			# stats_df = self.load_data('stats')
			merged = self.merge_data()#quote_df, stats_df)
		return merged.xs((symbol.upper(), date))[field]

	def splits(self, merged=None, filename=None, splits=None, save=False, v=False):
		if v: print(time_stamp() + 'Running splits.')
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if merged is None:
			if os.path.exists(self.data_location + 'merged.csv'):
				df = pd.read_csv(self.data_location + 'merged.csv')
			else:
				# df = self.merge_data()
				df = self.date_filter()
		elif '.csv' in merged:
			df = pd.read_csv(self.data_location + merged)
		else:
			df = merged
		# print('splits df:\n', df)
		if splits is None:
			# splits = input('Enter csv file name with split data: ')
			if not splits:
				splits = 'splits_data.csv'
		if '.csv' in splits:
			splits_data = pd.read_csv(self.data_location + 'splits/' + splits, index_col='symbol', encoding='utf-8')
		if 'factor' not in df.columns.values:
			df['factor'] = 1
		else:
			df['factor'].fillna(1, inplace=True)
		df['cur_factor'] = 1
		for symbol, split_event in splits_data.iterrows():
			# print('symbol:', symbol)
			# if symbol == 'TSLA':
			# 	split_event['ratio'] = 0.2 # Fixed this in the raw data now
			# print(split_event)
			df.loc[(df['symbol'] == symbol) & (df['date'] < split_event['exDate']), 'cur_factor'] *= split_event['ratio']
		# Adjust data columns
		adj_cols = ['factor','close','delayedPrice','extendedPrice','high','iexClose','iexRealtimePrice','latestPrice','low','oddLotDelayedPrice','open','previousClose','week52High','week52Low','day200MovingAvg','day50MovingAvg','week52high','week52low']
		for col in adj_cols:
			if col in df.columns.values:
				# print(time_stamp() + 'splits column:', col)
				df[col] = pd.to_numeric(df[col], errors='coerce')
				df[col] *= df['cur_factor']
		df.reset_index(drop=True, inplace=True)
		if v: print('Data adjusted for stock splits:\n{}'.format(df))
		if save:
			if not pathname:
				pathname = self.data_location + 'merged.csv'
			df.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved data adjusted for stock splits to:\n{}'.format(pathname))
		return df

	def mark_miss(self, merged=None, filename=None, save=False, v=False):
		if v: print(time_stamp() + 'Running mark miss.')
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if merged is None:
			if os.path.exists(self.data_location + 'merged.csv'):
				df = pd.read_csv(self.data_location + 'merged.csv')
			else:
				# df = self.merge_data()
				df = self.date_filter()
		elif '.csv' in merged:
			df = pd.read_csv(self.data_location + merged)
		else:
			df = merged.copy(deep=True)
		# if args.tickers: # TODO Having .csv in tickers arg causes issues
		# 	if not isinstance(args.tickers, (list, tuple)):
		# 		args.tickers = [x.strip().upper() for x in args.tickers.split(',')]
		# 	df = df.loc[df['symbol'].isin(args.tickers)]
		if 'target' not in df.columns.values:
			df['target'] = None
		tickers = df['symbol'].unique().tolist()
		print(time_stamp() + f'Numbers of tickers: {len(tickers)}')
		dfs = []
		for ticker in tickers:
			tmp_df = df.loc[df['symbol'] == ticker]
			min_date = tmp_df['date'].min()
			max_date = tmp_df['date'].max()
			# if v: print('min_date:', min_date)
			# if v: print('max_date:', max_date)
			tmp_df.set_index(pd.DatetimeIndex(tmp_df['date']), inplace=True)
			miss_dates = pd.date_range(start=min_date, end=max_date).difference(tmp_df.index)
			miss_dates = [(date - pd.to_timedelta(1, unit='d')).strftime('%Y-%m-%d') for date in miss_dates]
			# if v: print('miss_dates:\n', miss_dates)
			tmp_df['target'] = tmp_df.apply(lambda x: 'miss' if x['date'] in miss_dates else x['target'], axis=1)
			dfs.append(tmp_df)
		df = pd.concat(dfs)
		if v: print(time_stamp() + 'Data marked for missing dates:\n{}'.format(df))
		if save:
			if not pathname:
				pathname = self.data_location + 'merged.csv'
			df.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved data marked for missing dates to:\n{}'.format(pathname))
		return df

	def scrub(self, df=None, filename=None, save=False, v=False):
		if v: print(time_stamp() + 'Running scrub.')
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if df is None:
			if os.path.exists(self.data_location + 'merged.csv'):
				df = pd.read_csv(self.data_location + 'merged.csv')
			else:
				# df = self.merge_data()
				df = self.date_filter()
		elif '.csv' in df:
			df = pd.read_csv(self.data_location + df)
		df['date'] = pd.to_datetime(df['date'])
		if v: print(df)
		if 'sector' not in df.columns.values:
			df['sector'] = None
		df = df.loc[(df['date'].dt.dayofweek < 5) | (df['sector'] == 'cryptocurrency')]
		if v: print(df)
		holidays = pd.read_csv(self.data_location + 'holidays.csv')
		# df = df[~df['date'].isin(holidays['date'])]
		df = df.loc[(~df['date'].isin(holidays['date'])) | (df['sector'] == 'cryptocurrency') | (df['primaryExchange'].isin(['Toronto Stock Exchange', 'TSX Venture Exchange']))]
		cdn_holidays = ['2019-01-01', '2019-02-18', '2019-04-19', '2019-05-20', '2019-07-01', '2019-08-05', '2019-09-02', '2019-10-14', '2019-12-25', '2019-12-26', '2020-01-01', '2020-02-17', '2020-04-10', '2020-05-18', '2020-07-1', '2020-08-03', '2020-09-07', '2020-10-12', '2020-12-25', '2020-12-28']
		df = df.loc[(~df['date'].isin(cdn_holidays)) | (df['sector'] == 'cryptocurrency') | (~df['primaryExchange'].isin(['Toronto Stock Exchange', 'TSX Venture Exchange']))]
		df.reset_index(drop=True, inplace=True)
		if v: print(df)
		if save:
			if not pathname:
				pathname = self.data_location + 'merged.csv'
			df.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved data with weekends and US holidays scrubbed out to:\n{}'.format(pathname))
		return df

	def target(self, df=None, filename=None, save=False, v=False):
		if v: print(time_stamp() + 'Running target.')
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if df is None:
			if os.path.exists(self.data_location + 'merged.csv'):
				df = pd.read_csv(self.data_location + 'merged.csv')
			else:
				# df = self.merge_data()
				df = self.date_filter()
		elif '.csv' in df:
			df = pd.read_csv(self.data_location + df)
		if 'target' not in df.columns.values:
			df['target'] = None
		tickers = df['symbol'].unique().tolist()
		dfs = []
		for ticker in tickers:
			tmp_df = df.loc[df['symbol'] == ticker]
			# tmp_df['target'] = tmp_df['latestPrice'].shift(-1)
			tmp_df['target'].fillna(tmp_df['latestPrice'].shift(-1), inplace=True) # TODO Test this
			dfs.append(tmp_df)
		df = pd.concat(dfs)
		df['target'] = df.apply(lambda x: None if x['target'] == 'miss' else x['target'], axis=1)
		df.reset_index(drop=True, inplace=True)
		if v: print('Target price added to data:\n{}'.format(df))
		if save:
			if not pathname:
				pathname = self.data_location + 'merged.csv'
			df.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved data with target price added to:\n{}'.format(pathname))
		return df

	def get(self, dates=None, tickers=None, merged=None, filename=None, save=False, v=False):
		if merged is None:
			merged = 'merged.csv'
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		print(f'Get new data and save as: {filename}.csv')
		if dates is not None:
			if not isinstance(dates, (list, tuple)):
				if isinstance(dates, str):
					if '.csv' in dates:
						dates = pd.read_csv(self.data_location + '../../data/' + dates, header=None, comment='#')
						if 'date' in dates.columns.values.tolist():
							dates = dates['date'].values.tolist()
						elif 'dates' in dates.columns.values.tolist():
							dates = dates['dates'].values.tolist()
						else:
							dates = dates.iloc[:,0].values.tolist()
					else:
						dates = [x.strip() for x in dates.split(',')]
				else:
					dates = [dates]
		if os.path.exists(self.data_location + merged):
			if v: print(time_stamp() + f'Merged data exists for get. Save: {args.save}')
			merged = pd.read_csv(self.data_location + merged)
			cols = merged.columns.values.tolist()
			if v: print('cols:', cols)
			if v: print('merged tail:\n', merged.tail())
			if v: print(time_stamp() + 'merged shape load:', merged.shape)
			if v: print('date type:', type(merged['date'].max()))
			if dates is None:
				dates = [dt.datetime.strptime(merged['date'].max(), '%Y-%m-%d').date() + dt.timedelta(days=1)]
				if v: print(time_stamp() + 'Merged Max Date:', dates)
			else:
				dates = max(dates)
			new_merged = combine_data.date_filter(dates, since=True)
			if v: print(time_stamp() + 'new_merged shape filter dates:', new_merged.shape)
			if tickers is not None:
				if isinstance(tickers, str):
					if '.csv' in tickers:
						tickers = pd.read_csv(self.data_location + '../../data/' + tickers, header=None, comment='#')
						if 'symbol' in tickers.columns.values.tolist():
							tickers = tickers['symbol'].values.tolist()
						elif 'symbols' in tickers.columns.values.tolist():
							tickers = tickers['symbols'].values.tolist()
						elif 'ticker' in tickers.columns.values.tolist():
							tickers = tickers['ticker'].values.tolist()
						elif 'tickers' in tickers.columns.values.tolist():
							tickers = tickers['tickers'].values.tolist()
						else:
							tickers = tickers.iloc[:,0].values.tolist()
					else:
						tickers = [x.strip() for x in tickers.split(',')]
				if v: print(time_stamp() + 'Tickers:', tickers)
				new_merged = combine_data.comp_filter(tickers, new_merged)
				merged = combine_data.comp_filter(tickers, merged)
				if v: print(time_stamp() + 'new_merged shape filter tickers:', merged.shape)
			mergeds = []
			new_mergeds = []
			for symbol in list(merged['symbol'].unique()):
				tmp_merged = merged.loc[merged['symbol'] == symbol]
				tmp_new_merged = new_merged.loc[new_merged['symbol'] == symbol]
				last_row = tmp_merged.tail(1)
				tmp_merged = tmp_merged[:-1]
				tmp_new_merged = pd.concat([last_row, tmp_new_merged], sort=True)
				mergeds.append(tmp_merged)
				new_mergeds.append(tmp_new_merged)
			merged = pd.concat(mergeds, sort=True)
			new_merged = pd.concat(new_mergeds, sort=True)
			new_merged = combine_data.splits(new_merged)
			if v: print(time_stamp() + 'new_merged shape splits:', new_merged.shape)
			new_merged = combine_data.mark_miss(new_merged)
			if v: print(time_stamp() + 'new_merged shape miss:', new_merged.shape)
			new_merged = combine_data.scrub(new_merged)
			if v: print(time_stamp() + 'new_merged shape scrub:', new_merged.shape)
			new_merged = combine_data.target(new_merged)
			new_merged['date'] = new_merged['date'].dt.date
			if v: print(time_stamp() + 'new_merged shape end:', new_merged.shape)
			merged = merged[cols]
			new_merged = new_merged[cols]
			# merged = pd.concat([merged, new_merged], sort=True)
			if v: print(time_stamp() + 'merged shape end:', merged.shape)
		else:
			if v: print(time_stamp() + f'Merged data does not exist for get. Save: {args.save}')
			# if dates is None:
				# dates = args.start_date
				# dates = ['2020-01-24']
			# if tickers is None:
			# 	tickers = pd.read_csv('../data/ws_tickers.csv', header=None)
			# tickers = tickers.iloc[:,0].unique().tolist()
			# new_merged = combine_data.comp_filter(tickers, combine_data.date_filter(dates, since=True))
			new_merged = combine_data.date_filter(dates, since=True)
			new_merged = combine_data.splits(new_merged)
			new_merged = combine_data.mark_miss(new_merged)
			new_merged = combine_data.scrub(new_merged)
			new_merged = combine_data.target(new_merged)
			merged = None
		if save:
			if not pathname:
				if tickers is not None:
					if len(tickers) == 1:
						pathname = self.data_location + filename + '_' + tickers[0] + '.csv'
					else:
						pathname = self.data_location + filename + '_' + tickers[0] + '_to_' + tickers[-1] + '.csv'
				else:
					pathname = self.data_location + filename + '.csv'
			header = True
			if merged is not None:
				header = False
				merged.to_csv(pathname, index=False)
			new_merged.to_csv(pathname, index=False, mode='a', header=header)
			# Fix sorting
			merged = pd.read_csv(pathname)
			# print(merged.head())
			merged = merged.sort_values(by=['symbol', 'date'])
			merged.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved merged data for {} to:\n{}'.format(dates[-1], pathname))
		return merged

	def crypto_data(self, merged=None, prep=False, filename=None, save=False, v=False):
		if merged is None:
			merged = 'merged.csv'
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if v: print(time_stamp() + 'Loading data from:', merged)
		df = pd.read_csv('data/' + merged)
		df = df.loc[df['sector'] == 'cryptocurrency']
		if v: print(time_stamp() + 'Prep:', prep)
		if prep:
			# Keep certain columns
			# df.dropna(axis=1, how='all', inplace=True)
			# cols = ['symbol','date','askPrice','askSize','bidPrice','bidSize','high','latestPrice','latestVolume','low','previousClose','target'] # After 2020-07-26
			cols = ['symbol','date','askPrice','askSize','bidPrice','bidSize','latestPrice','target']
			df = df[cols]
			df.dropna(inplace=True)
		if v: print(df)
		if args.save:
			if not pathname:
				if prep:
					pathname = self.data_location + 'crypto_prep_merged.csv'
				else:
					pathname = self.data_location + 'crypto_merged.csv'
			df.to_csv(pathname, date_format='%Y-%m-%d', index=False)
			print(time_stamp() + 'Saved crypto data to: {}'.format(pathname))
		return df

	def get_tickers(self, df=None, filename=None, save=False, v=False):
		if filename is None:
			filename = 'merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if df is None:
			if os.path.exists('data/merged.csv'):
				df = pd.read_csv('data/merged.csv')
		# TODO Add check to df to look for .csv in name and if so, then load that file
		df = pd.Series(df['symbol'].unique())
		if save:
			if not pathname:
				pathname = self.data_location + 'all_tickers.csv'
			df.to_csv(pathname, index=False)
			print(time_stamp() + 'Saved tickers to:\n{}'.format(pathname))
		return df

	def max_date(self, merged, v=True):
		if merged is None:
			merged = 'merged.csv'
		if '.csv' not in merged:
			print('Must be a .csv file name:', merged)
			return
		if v: print(time_stamp() + 'Loading data to check Max Date from:', merged)
		df = pd.read_csv(self.data_location + merged)
		max_date = df['date'].max()
		if v: print(time_stamp() + 'Max Date:', max_date)
		return max_date

	def min_date(self, merged, v=True):
		if merged is None:
			merged = 'merged.csv'
		if '.csv' not in merged:
			print('Must be a .csv file name:', merged)
			return
		if v: print(time_stamp() + 'Loading data to check Min Date from:', merged)
		df = pd.read_csv(self.data_location + merged)
		min_date = df['date'].min()
		if v: print(time_stamp() + 'Min Date:', min_date)
		return min_date

	def fill_missing(self, missing=None, filename=None, merged=None, save=False, v=False):
		if v: print(time_stamp() + 'Missing File Save:', save)
		if filename is None:
			filename = 'merged_filled'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if isinstance(missing, str):
			if '.csv' in missing:
				print(time_stamp() + 'Loading missing data from:', missing)
				missing = pd.read_csv(self.data_location + 'hist_prices/' + missing)
				if 'close' in missing.columns.values:
					missing = missing.rename(columns={'close': 'hist_close', 'changePercent': 'hist_changePercent', 'change': 'hist_change', 'changeOverTime': 'hist_changeOverTime', 'high': 'hist_high', 'low': 'hist_low', 'open': 'hist_open', 'volume': 'hist_volume', 'label': 'hist_label'})
				missing['comment_miss'] = 'missing'
		if isinstance(merged, str):
			if '.csv' in merged:
				# if merged is None and os.path.exists(self.data_location + merged_file):
				if os.path.exists(self.data_location + merged):
					print(time_stamp() + 'Merged data exists at:', self.data_location + merged)
					merged = pd.read_csv(self.data_location + merged)
				else:
					print(time_stamp() + 'Merged data does not exists at:', self.data_location + merged)
					merged = self.merge_data(save=save)
		if merged is None:
			print(time_stamp() + 'Creating merged data at:', self.data_location)
			merged = self.merge_data(save=save)
		merged.reset_index(inplace=True)
		merged['date'] = pd.to_datetime(merged['date'])
		df = merged.set_index(['symbol','date'])
		df = df.drop(['hist_close','hist_changePercent','hist_change','hist_changeOverTime','hist_high','hist_low','hist_open','hist_volume','hist_label','uClose','uHigh','uLow','uOpen'], axis=1, errors='ignore')
		df['sector'] = df['sector'].astype(str)
		if 'latestEPSDate' in df.columns.values:
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
			# with pd.option_context('display.max_rows', None):
			# 	print(missing)
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

		if 'factor' in df.columns.values:
			df['factor'].fillna(df['factor'].shift(1), inplace=True)
		if 'cur_factor' in df.columns.values:
			df['cur_factor'].fillna(df['cur_factor'].shift(1), inplace=True)
		# if 'target' in df.columns.values: # Rerun target() function instead
		# 	df['target'].fillna(df['latestPrice'].shift(-1), inplace=True)

		df['sector'].fillna(method='ffill', inplace=True)
		df['avg30Volume'].fillna(df['avgTotalVolume'], inplace=True)
		df['beta'].fillna(method='ffill', inplace=True)
		if 'companyName' in df.columns.values:
			df['companyName'].fillna(method='ffill', inplace=True)
		if 'companyName_x' in df.columns.values:
			df['companyName_x'].fillna(method='ffill', inplace=True)
		if 'companyName_y' in df.columns.values:
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

		if 'peRatio' in df.columns.values:
			df['peRatio'].fillna(df['latestPrice'] / (df['peRatio'].shift(1) * df['latestPrice'].shift(1)), inplace=True)
		if 'peRatio_x' in df.columns.values:
			df['peRatio_x'].fillna(df['latestPrice'] / (df['peRatio_x'].shift(1) * df['latestPrice'].shift(1)), inplace=True)
		if 'peRatio_y' in df.columns.values:
			if 'peRatio_x' in df.columns.values:
				df['peRatio_y'].fillna(df['peRatio_x'], inplace=True)
			else:
				df['peRatio_y'].fillna(df['peRatio'], inplace=True)

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
		while df['peRatio'].isnull().values.any():
			current = df['peRatio'].isnull().values.sum()
			# if v: print(current)
			if current % 10000 == 0:
				if v: print(current)
			df['peRatio'].fillna(df['latestPrice'] / (df['peRatio'].shift(1) * df['latestPrice'].shift(1)), inplace=True)
		df['peRatio_y'].fillna(df['peRatio'], inplace=True)
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
			if not pathname:
				pathname = self.data_location + 'merged_filled.csv'
			df.to_csv(pathname, date_format='%Y-%m-%d', index=True)
			print(time_stamp() + 'Saved merged missing data to: {}'.format(path))
		return df

	def find_missing(self, data=None, filename=None, dates_only=False, save=False, v=False):
		if filename is None:
			filename = 'miss_merged'
			pathname = None
		elif '.csv' == filename[-4:]:
			filename = filename[:-4]
			pathname = self.data_location + filename + '.csv'
		else:
			pathname = self.data_location + filename + '.csv'
		if data is None:
			missing = None
			merged = 'merged.csv' # None #
			data = self.fill_missing(missing, merged)
		if isinstance(data, str):
			if '.csv' in data:
				print(time_stamp() + 'Merged data exists at:', self.data_location + data)
				data = pd.read_csv(self.data_location + data)
		df = data[['symbol','date','close','high','low','open','latestVolume','change','changePercent']]
		df = df[df.isnull().values.any(axis=1)]
		df = df.loc[~(df['symbol'].str.contains('-CV') | df['symbol'].str.contains('-CT'))]
		print('Number of missing ticker-dates:', len(df))
		if dates_only:
			df = df['date'].unique()
			df.sort()
		with pd.option_context('display.max_columns', None, 'display.max_rows', None):
			if v: print(time_stamp() + 'Found Missing Fields: {}\n{}'.format(len(df), df))
		if save:
			if not pathname:
				pathname = self.data_location + 'miss_merged.csv'
			df.to_csv(pathname, date_format='%Y-%m-%d', index=True)
			print(time_stamp() + 'Saved found missing fields to: {}'.format(pathname))
		return df

	def cols(self, data=None, filename=None, save=False, v=False):
		if filename is None or filename == 'merged':
			filename = 'cols'
			# pathname = None
			pathname = self.data_location + filename + '.csv'
		elif '.csv' == filename[-4:]:
			pathname = self.data_location + filename
		else:
			pathname = self.data_location + filename + '.csv'
		if data is None:
			data = 'merged.csv'
		if isinstance(data, str):
			if '.csv' != data[-4:]:
				if v: print('Adding .csv to file name:\n', data)
				data = data + '.csv'
			print(time_stamp() + 'Loading data to get the columns from:', data)
			data = pd.read_csv(self.data_location + data)
		cols = data.columns.values.tolist()
		print(time_stamp() + 'Columns:')
		print(cols)
		df = pd.DataFrame(cols)
		if save:
			if not pathname: # TODO is this needed?
				pathname = self.data_location + 'cols.csv'
			df.to_csv(pathname, index=False, header=False)
			print(time_stamp() + 'Saved column fields to: {}'.format(pathname))
		return df		

	def front(self, n):
		return self.iloc[:, :n]

	def back(self, n):
		return self.iloc[:, -n:]

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-md', '--merged', type=str, help='The file name of the merged data.')
	parser.add_argument('-o', '--output', type=str, default='merged', help='The file name of the output with no .csv extension.')
	parser.add_argument('-d', '--dates', type=str, help='A list of dates to combine data for.')
	parser.add_argument('-t', '--tickers', type=str, help='A list of tickers to filter data for.')
	parser.add_argument('-f', '--fields', type=str, help='The fields to filter data for.')
	parser.add_argument('-m', '--mode', type=str, help='The mode to run: merged, find, missing, tickers, value, crypto, splits, mark, scrub, tar, gettickers, maxdate, mindate, and get.')
	parser.add_argument('-since', '--since', action='store_true', help='Use all dates since a given date.')
	parser.add_argument('-until', '--until', action='store_true', help='Use all dates up to a given date.')
	parser.add_argument('-sd', '--start_date', type=str, help='The date to start using data from.')
	parser.add_argument('-ed', '--end_date', type=str, help='The date to use data up to.')
	parser.add_argument('-s', '--save', action='store_true', help='Save the results to csv.')
	parser.add_argument('-v', '--verbose', action='store_true', help='Display the result.')
	args = parser.parse_args()
	args.v = args.verbose
	if args.start_date == 'None':
		args.start_date = '2018-05-08'
	print(time_stamp() + str(sys.argv))

	# if os.path.exists('/home/robale5/becauseinterfaces.com/acct/market_data/data/'):
	# 	data_location = '/home/robale5/becauseinterfaces.com/acct/market_data/data/'
	# else:
	# 	# data_location = '../../market_data/test_data/'
	# 	data_location = '/Users/Robbie/Public/market_data/new/data/'
	combine_data = CombineData()#data_location=data_location)

	if args.merged is not None:
		if '.csv' in args.merged:
			merged = combine_data.data_location + args.merged
		else:
			merged = combine_data.data_location + args.merged + '.csv'
		print(time_stamp() + 'Loading data from: ', merged)
		merged = pd.read_csv(merged)
		print(time_stamp() + 'Data loaded.')
	else:
		merged = None

	if args.mode == 'fill' or args.mode == 'missing':
		# merged = 'merged.csv' # 'ws_miss_merged.csv' #'merged_AAPl.csv' #'aapl_tsla_quote.csv'
		missing = 'A_to_ZYME_hist_prices_2020-03-18_to_2020-03-19.csv'
		# missing = 'A_to_ZZZ-CT_hist_prices_2019-08-26_to_2020-02-19.csv'
		# 'AGR_to_ZZZD-CT_hist_prices_2019-09-11_to_2020-02-10.csv'
		# 'a_to_zyne_hist_prices_2018-05-22_to_2020-01-22.csv'
		# 'aapl_to_aapl_hist_prices_2018-05-22_to_2020-01-22.csv'
		# 'a_to_zzz-ct_hist_prices_2018-05-22_to_2020-01-22' #'all_hist_prices'
		df = combine_data.fill_missing(missing, merged, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'find':
		data = merged # 'merged.csv' # 'ws_miss_merged.csv' # None # 'all_hist_prices_new4_merged.csv'
		df = combine_data.find_missing(data, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'merged' or args.mode == 'merge':
		print(time_stamp() + 'Merged Save: ', args.save)
		# quote_df = combine_data.load_data('quote', dates=args.dates)
		# stats_df = combine_data.load_data('stats', dates=args.dates)
		df = combine_data.merge_data(dates=args.dates, save=args.save)
		# Filter as per available WealthSimple listing criteria
		# df = df.loc[(df['primaryExchange'].isin(['New York Stock Exchange','Nasdaq Global Select'])) & (df['week52High'] > 0.5) & (df['avgTotalVolume'] > 50000)]
		print(time_stamp() + 'Merged data:')
		print(df.head())

	elif args.mode == 'tickers':
		df = combine_data.merge_data(dates=args.dates)
		df.reset_index(inplace=True)
		tickers = pd.Series(df.symbol.unique())
		if args.save:
			tickers.to_csv('../data/' + 'all_tickers.csv', date_format='%Y-%m-%d', index=True)
		print(tickers.head())

	elif args.mode == 'value':
		if not isinstance(args.fields, (list, tuple)):
			args.fields = [x.strip() for x in args.fields.split(',')]
		if not isinstance(args.dates, (list, tuple)):
			args.dates = [x.strip() for x in args.dates.split(',')]
		if not isinstance(args.tickers, (list, tuple)):
			args.tickers = [x.strip() for x in args.tickers.split(',')]
		if len(args.fields) == 1 and len(args.dates) == 1 and len(args.tickers) == 1:
			print('{} value for {} on {}:'.format(args.fields[0], args.tickers[0], args.dates[0]))
			result = combine_data.value(args.dates, args.tickers, args.fields)
			print(result)
			print('-' * DISPLAY_WIDTH)
			exit()
		else:
			print('Value option only works when one field, date, and ticker are provided.')

	elif args.mode == 'crypto':
		df = combine_data.crypto_data(prep=True, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'splits':
		df = combine_data.splits(merged, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'mark':
		df = combine_data.mark_miss(merged, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'scrub':
		df = combine_data.scrub(merged, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'tar' or args.mode == 'target':
		df = combine_data.target(merged, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'gettickers':
		df = combine_data.get_tickers(filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'maxdate':
		max_date = combine_data.max_date(args.merged)

	elif args.mode == 'mindate':
		max_date = combine_data.min_date(args.merged)

	elif args.mode == 'cols':
		cols = combine_data.cols(data=merged, filename=args.output, save=args.save, v=args.v)

	elif args.mode == 'get':
		df = combine_data.get(dates=args.dates, tickers=args.tickers, merged=merged, filename=args.output, save=args.save, v=args.v)

	else:
		if args.dates and args.tickers and args.fields:
			df = combine_data.data_point(args.fields, combine_data.comp_filter(args.tickers, combine_data.date_filter(args.dates, merged=merged, since=args.since, until=args.until)), filename=args.output, save=args.save, v=args.v)
		if args.dates and args.tickers and args.fields is None:
			df = combine_data.comp_filter(args.tickers, combine_data.date_filter(args.dates, merged=merged, since=args.since, until=args.until), filename=args.output, save=args.save, v=args.v)
		if args.dates and args.tickers is None and args.fields:
			df = combine_data.data_point(args.fields, combine_data.date_filter(args.dates, merged=merged, since=args.since, until=args.until), filename=args.output, save=args.save, v=args.v)
		if args.dates is None and args.tickers and args.fields:
			df = combine_data.data_point(args.fields, combine_data.comp_filter(args.tickers, merged=merged), filename=args.output, save=args.save, v=args.v)
		if args.dates and args.tickers is None and args.fields is None:
			df = combine_data.date_filter(args.dates, merged=merged, since=args.since, until=args.until, filename=args.output, save=args.save, v=args.v)
		if args.dates is None and args.tickers and args.fields is None:
			print('Merging all dates for:', args.tickers)
			print('Save:', args.save)
			df = combine_data.comp_filter(args.tickers, merged=merged, filename=args.output, save=args.save, v=args.v)
		if args.dates is None and args.tickers is None and args.fields:
			df = combine_data.data_point(args.fields, merged=merged, filename=args.output, save=args.save, v=args.v)
		if args.dates is None and args.tickers is None and args.fields is None:
			print('Save:', args.save)
			df = combine_data.merge_data(save=args.save) # TODO Add filename support

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/combine_data.py >> /home/robale5/becauseinterfaces.com/acct/logs/combine01.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/combine_data.py -m fill -s >> /home/robale5/becauseinterfaces.com/acct/logs/fill03.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/combine_data.py -m get -t "aapl, tsla" -s >> /home/robale5/becauseinterfaces.com/acct/logs/get10.log 2>&1 &

# nohup python -u market_data/combine_data.py -sd None --until -d 2020-07-31 -o merged_all_until-2020-07 -s -v >> logs/combine02.log 2>&1 &

# nohup python -u market_data/combine_data.py -m splits -md merged_all_until-2020-07.csv -o merged_all_until-2020-07 -s -v >> logs/combine09.log 2>&1 &

# splits, mark, scrub, tar