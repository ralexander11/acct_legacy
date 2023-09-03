import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
from market_data.combine_data import CombineData
import datetime as dt
import argparse
import os, sys

# Make numpy printouts easier to read
np.set_printoptions(precision=3, suppress=True)

def time_stamp(offset=0):
	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
		offset = 4
	time_stamp = (dt.datetime.now() + dt.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def prep_data(ticker=None, merged=None, fields=None, crypto=False, train=False, v=True):
	if v: print(time_stamp() + 'Prepare data')
	combine_data = CombineData()
	if merged is None:
		merged = 'merged.csv'
	if fields is None:
		fields = 'fields.csv'
	if crypto:
		url = 'http://becauseinterfaces.com/acct/market_data/data/crypto_prep_merged.csv'
		fields = ['symbol','date','askPrice','askSize','bidPrice','bidSize','latestPrice','target']
		column_names = fields
		if ticker is None:
			ticker = 'BTCUSDT'
		merged = 'crypto_prep_merged.csv'
		if v: print(time_stamp() + f'URL: {url}')
	else:
		url = 'http://becauseinterfaces.com/acct/market_data/data/merged.csv'
		fields = ['symbol', 'date', 'avgTotalVolume', 'change', 'changePercent', 'close', 'delayedPrice', 'extendedChange', 'extendedChangePercent', 'extendedPrice', 'high', 'iexMarketPercent', 'iexRealtimePrice', 'iexRealtimeSize', 'iexVolume', 'latestPrice', 'latestVolume', 'low', 'marketCap', 'open', 'peRatio', 'previousClose', 'previousVolume', 'volume', 'week52High', 'week52Low', 'ytdChange', 'avg10Volume', 'avg30Volume', 'beta', 'day200MovingAvg', 'day30ChangePercent', 'day50MovingAvg', 'day5ChangePercent', 'marketcap', 'maxChangePercent', 'month1ChangePercent', 'month3ChangePercent', 'month6ChangePercent', 'sharesOutstanding', 'ttmEPS', 'week52change', 'week52high', 'week52low', 'year1ChangePercent', 'year2ChangePercent', 'year5ChangePercent', 'ytdChangePercent', 'target']
		column_names = fields
		# merged = 'merged.csv'

	if v: print(time_stamp() + f'Ticker: {ticker}')
	if isinstance(merged, str):
		if '.csv' not in merged:
			merged = merged + '.csv'
	if v: print(time_stamp() + f'Merged filename: {merged}')

	if '.csv' in merged and os.path.exists(combine_data.data_location + merged) and not crypto:
		if v: print(time_stamp() + 'Merged data exists.')
		merged_data = pd.read_csv(combine_data.data_location + merged)
		merged_data = merged_data.set_index(['symbol','date'])
		# dataset = combine_data.comp_filter(ticker, merged_data)
		dataset = combine_data.data_point(fields, combine_data.comp_filter(ticker, merged_data))
		if v: print(time_stamp() + 'Data filtered for ticker and fields:', dataset.shape)
		# dataset = dataset[fields]
		# if v: print('Remove columns:', dataset.shape)
	elif isinstance(merged, pd.DataFrame):
		print('Data provided:', merged.shape)
		# if 'target' not in merged.columns.values.tolist():
		# 	merged['target'] = np.nan
		# dataset = combine_data.comp_filter(ticker, merged)
		# dataset = merged[column_names]
		dataset = combine_data.data_point(fields, merged)
		# dataset = dataset.set_index(['symbol','date'])
		if v: print('Remove columns:', dataset.shape)
	else:
		# TODO Maybe remove this
		print('Load data from:', url)
		raw_dataset = pd.read_csv(url, names=column_names) # TODO change column_names to fields
		dataset = raw_dataset.copy()
		dataset = dataset.loc[dataset['symbol'] == ticker]

	# if v: print(time_stamp() + f'Dataset tail 1.')
	# if v: print(dataset.tail())
	# dataset.drop(['symbol','date'], axis=1, inplace=True)
	# print(time_stamp() + 'nan counts:')
	# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		# print(dataset.isna().sum())
	# print(dataset)

	# cols = dataset.columns.values.tolist()
	# cols.remove('target')
	# print('cols 1:', cols)
	print('shape before remove na cols:', dataset.shape)
	# print(dataset.iloc[:, :-1])
	# dataset.iloc[:, :-1].dropna(axis=1, how='all', inplace=True) # This was used to avoid dropping the target col
	cols = dataset.columns.values.tolist()
	if 'target' in cols:
		cols.remove('target')
	print('cols:', cols)
	dataset.dropna(axis=1, how='all', inplace=True)
	print('shape after remove na cols:', dataset.shape)
	dataset = dataset.loc[:, (dataset != 0).any(axis=0)]
	# dataset = dataset.loc[:, (dataset != 0 | ~dataset.isna()).any(axis=0)]
	# dataset.drop('ttmEPS', axis=1, inplace=True) # TODO temp solution
	print('dataset:\n', dataset)

	print('shape before remove na rows:', dataset.shape)
	# print(dataset)
	# dataset.to_csv('test_data.csv')
	# TODO Better missing data handling
	dataset.dropna(axis=0, subset=cols, inplace=True)
	print('shape after remove na rows:', dataset.shape)
	if 'target' not in dataset.columns.values.tolist():
		merged['target'] = np.nan
	# exit()
	if train:
		dataset.dropna(axis=0, subset=['target'], inplace=True)
		if v: print('target filter out nan:', dataset.shape)
	# if v: with pd.option_context('display.max_rows', None, 'display.max_columns', None):
	# 	if v: print(dataset.dtypes)
	print(time_stamp() + 'Dataset Min Date:', dataset['date'].min())
	print(time_stamp() + 'Dataset Max Date:', dataset['date'].max())
	if v: print(time_stamp() + f'Convert to floats.')
	# TODO Handle other feature types
	symbol_col = dataset.pop('symbol')
	date_col = dataset.pop('date')
	dataset = dataset.astype('float', errors='ignore')
	dataset = pd.merge(date_col, dataset, left_index=True, right_index=True, sort=False)
	dataset = pd.merge(symbol_col, dataset, left_index=True, right_index=True, sort=False)
	print(time_stamp() + 'Dataset Shape:', dataset.shape)
	# dataset.drop(['symbol','date'], axis=1, errors='ignore', inplace=True)
	# v = True
	# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
	# 	if v: print('dataset types:')
	# 	if v: print(dataset.dtypes)
	# 	if v: print(time_stamp() + f'Dataset:')
	# 	if v: print(dataset)
	return dataset

def get_features_and_labels(ticker=None, data=None, fields=None, crypto=False, frac_per=0.8, train=False, v=True):
	if frac_per == 1:
		train = False
	data = prep_data(ticker=ticker, merged=data, fields=fields, crypto=crypto, train=train, v=v)
	try:
		seed = args.seed
		print('Random seed set as:', seed)
	except Exception as e:
		seed = None
	dataset = data.sample(frac=1, random_state=seed)
	frac = int(len(dataset) * frac_per)
	if v: print(time_stamp() + f'dataset len: {len(dataset)}')
	if v: print(time_stamp() + f'frac: {frac}')
	if train:
		train_dataset = dataset[:frac]
		test_dataset = dataset.drop(train_dataset.index)
	else:
		train_dataset = test_dataset = dataset.copy()

	# if v: print(time_stamp() + 'Dataset Statistics Summary')
	# if v: print(train_dataset.describe().transpose())

	train_features = train_dataset.copy()
	test_features = test_dataset.copy()

	if train or 'target' in dataset.columns.values.tolist():
		train_labels = train_features.pop('target')
		test_labels = test_features.pop('target')
	else:
		train_labels = pd.DataFrame()
		test_labels = pd.DataFrame()
	train_features.drop(['symbol','date'], axis=1, errors='ignore', inplace=True)
	test_features.drop(['symbol','date'], axis=1, errors='ignore', inplace=True)
	# test_features['symbol'] = 0
	# test_features['date'] = 0
	# train_features.to_csv('train_features01.csv')


	return train_features, test_features, train_labels, test_labels, dataset

def normalize_data(train_features=None, data=None, fields=None, v=True):
	if v: print(time_stamp() + 'Normalize training features')
	if train_features is None:
		train_features = get_features_and_labels(data=data, fields=fields, train=True, v=v)[0]
	normalizer = preprocessing.Normalization()
	normalizer.adapt(np.array(train_features))
	if v: print(time_stamp() + 'Normalized Mean:')
	if v: print(normalizer.mean.numpy())
	# if v: print('shape:', train_features.shape)
	# df = pd.DataFrame(normalizer.mean.numpy())
	# file_name = 'data/' + 'tsla' + '_norm.csv'
	# df.to_csv(file_name)
	# exit()
	return normalizer

def build_and_compile_model(norm):
	model = keras.Sequential([
		norm,
		layers.Dense(64, activation='relu'),
		layers.Dense(64, activation='relu'),
		layers.Dense(1)
	])

	model.compile(loss='mean_absolute_error',
				optimizer=tf.keras.optimizers.Adam(0.001))
	return model

def get_fut_price(ticker, date=None, data=None, crypto=False, only_price=False, model_name=None, train=False, v=False):
	# TODO Maybe support multiple tickers and dates
	if isinstance(ticker, (list, tuple)):
		ticker = ticker[0]
	if isinstance(date, (list, tuple)):
		date = date[0]
	combine_data = CombineData()
	# if data is None:
	# 	data = 'merged.csv'
	data = combine_data.comp_filter(ticker, combine_data.date_filter(date, merged=data))
	# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
	print(time_stamp() + 'Model Input Data: {}\n{}'.format(data.shape, data))
	price = main(ticker, data=data, crypto=crypto, only_price=only_price, model_name=model_name, train=train)
	return price

def plot_prediction(x, y, train_features, train_labels):
	plt.scatter(train_features['latestPrice'], train_labels, label='Data')
	plt.scatter(x, y, color='k', label='Predictions')
	# plt.plot(x, y, color='k', label='Predictions')
	plt.xlabel('latestPrice')
	plt.ylabel('target')
	plt.legend()
	plt.show()

def main(ticker=None, train=False, fields=None, crypto=False, data=None, only_price=False, model_name=None, save=False, v=False):
	if v: print(time_stamp() + f'TensorFlow Version: {tf.__version__}')
	if v: print(time_stamp() + f'Train: {train}')
	if v: print(time_stamp() + f'Save: {save}')
	if v: print(time_stamp() + f'Crypto: {crypto}')

	if ticker is None and not crypto:
		ticker = 'tsla'
	if ticker is None and crypto:
		ticker = 'BTCUSDT'
	file_name = 'models/' + ticker.lower() + '_model'
	if model_name:
		file_name = 'models/' + model_name
	if os.path.exists('/home/robale5/becauseinterfaces.com/'):
		file_name = '/home/robale5/becauseinterfaces.com/acct/' + file_name
	if v: print(time_stamp() + f'File Name: {file_name}')
	if v: print(time_stamp() + f'Model exists:', os.path.exists(file_name))
	os.makedirs(file_name, exist_ok=True)

	if not train:
		frac_per = 1
	else:
		frac_per = 0.8
	train_features, test_features, train_labels, test_labels, dataset = get_features_and_labels(ticker=ticker, fields=fields, crypto=crypto, data=data, frac_per=frac_per, train=train, v=v)
		# print('test_features:')
		# print(test_features)
	if test_features.empty:
		print(time_stamp() + f'No data for {ticker} to run model.')
		return

	if os.path.exists(file_name) and not train:
		if v: print(time_stamp() + 'Load model from: ' + ticker.lower() + '_model')
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('test_features types:')
		if v: print(test_features.dtypes)
		if v: print(time_stamp() + f'test_features:')
		if v: print(test_features)
		if v: print(time_stamp() + 'test_features shape:', test_features.shape)
		model = tf.keras.models.load_model(file_name)
		# print(model.to_yaml())
		print(model.summary())
		print(time_stamp() + 'test_features shape:', test_features.shape)

		# test_features['avgTotalVolume'] = test_features['avgTotalVolume'].astype(object)
		# with pd.option_context('display.max_rows', None):
		# 	print(test_features.dtypes)
		# test_features.to_csv('data/test_features.csv')

		test_predictions = model.predict(test_features, verbose=1)
		test_predictions = test_predictions.flatten()
		dataset['prediction'] = pd.Series(test_predictions, index=test_features.index)
		
		dataset['pred_dir'] = dataset['prediction'] - dataset['latestPrice']
		if 'target' in dataset.columns.values.tolist():
			dataset['real_dir'] = dataset['target'] - dataset['latestPrice']
			dataset['dir_check'] = dataset['pred_dir'] * dataset['real_dir'] >= 0
		else:
			dataset['real_dir'] = None
			dataset['dir_check'] = None
		if v: print('dataset:\n', dataset)
		if v:
			print(time_stamp() + 'Prediction Results:')
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(time_stamp() + f'test_labels (x):\n{test_labels}')
				print(time_stamp() + f'test_predictions (y):\n{test_predictions}')

			if not os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
				plot_prediction(test_labels, test_predictions, train_features, train_labels)

			print(time_stamp() + 'Evaluate loaded ' + ticker.lower() + '_model:')
			test_results = {}
			test_results['reloaded'] = model.evaluate(test_features, test_labels, verbose=0)
	else:
		normalizer = normalize_data(train_features, data=data, fields=fields, v=v)

		if v: print(time_stamp() + 'Build and compile model')
		model = build_and_compile_model(normalizer)
		if v: print(time_stamp() + 'Model Summary:')
		if v: model.summary()

		if v: print(time_stamp() + 'Fit model')
		history = model.fit(train_features, train_labels, validation_split=0.2, verbose=0, epochs=100)
		# TODO Option to display fitting history

		if v: print(time_stamp() + 'Evaluate model')
		test_results = {}
		test_results['model'] = model.evaluate(test_features, test_labels, verbose=0)

		if v: print(time_stamp() + 'Predict with model')
		test_predictions = model.predict(test_features)
		test_predictions = test_predictions.flatten()
		if v: print(time_stamp() + 'Prediction Results:')

		dataset['prediction'] = pd.Series(test_predictions, index=test_features.index)
		dataset['pred_dir'] = dataset['prediction'] - dataset['latestPrice']
		if 'target' in dataset.columns.values.tolist():
			dataset['real_dir'] = dataset['target'] - dataset['latestPrice']
			dataset['dir_check'] = dataset['pred_dir'] * dataset['real_dir'] >= 0
		else:
			dataset['real_dir'] = None
			dataset['dir_check'] = None
		if v: print('dataset:\n', dataset)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print(time_stamp() + f'test_labels (x):\n{test_labels}')
			if v: print(time_stamp() + f'test_predictions (y):\n{test_predictions}')
		if not os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
			plot_prediction(test_labels, test_predictions, train_features, train_labels)

		if save:
			if model_name:
				if v: print(time_stamp() + 'Saving model as: ' + model_name)
			else:
				if v: print(time_stamp() + 'Saving model as: ' + ticker.lower() + '_model')
			print('file_name:', file_name)
			model.save(file_name)
			dataset.to_csv(file_name + '/assets/' + ticker.lower() + '_pred.csv')
	if v: print(time_stamp() + 'Test Results:')
	if v: df = pd.DataFrame(test_results, index=['Mean absolute error [target]']).T
	if v: print(df)

	if only_price:
		if len(test_predictions) == 1:
			result = test_predictions[0]
		else:
			result = test_predictions
	else:
		result = dataset.copy()

	if v: print(time_stamp() + f'Result:\n{result}')
	# result.to_csv('data/tsla_result_tmp05.csv')
	return result


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--data', type=str, default='merged.csv', help='The file name of the merged data.')
	parser.add_argument('-s', '--save', action='store_true', help='Save the model for reuse.')
	parser.add_argument('-t', '--ticker', type=str, help='A single ticker to use.')
	parser.add_argument('-n', '--train', action='store_true', help='Train a new model.')
	parser.add_argument('-c', '--crypto', action='store_true', help='If using for cryptocurrencies.')
	parser.add_argument('-seed', '--seed', type=int, help='Set the seed number for the randomness in the sorting of the input data when training.')
	parser.add_argument('-f', '--fields', type=str, help='The fields to use in the model.')
	parser.add_argument('-v', '--verbose', action='store_false', help='Display the result.')
	parser.add_argument('-o', '--output', type=str, help='The optional file name of the model.')
	parser.add_argument('-mn', '--model_name', type=str, help='The optional file name of the model.')
	args = parser.parse_args()
	print(time_stamp() + str(sys.argv))
	if args.output:
		args.model_name = args.output

	result = main(args.ticker, train=args.train, fields=args.fields, crypto=args.crypto, data=args.data, model_name=args.model_name, save=args.save, v=args.verbose)

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/fut_price.py -n -t tsla --seed 11 -s >> /home/robale5/becauseinterfaces.com/acct/logs/fut_price09.log 2>&1 &

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/fut_price.py -d merged_bak_2021-02-25.csv -n -t tsla --seed 11 -s >> /home/robale5/becauseinterfaces.com/acct/logs/fut_price09.log 2>&1 &

# nohup python -u fut_price.py -n -t tsla -s >> logs/fut_price02.log 2>&1 &

# nohup python -u fut_price.py -n -t tsla --seed 11 -d merged_all_until-2020-07 -o tsla_wndw_model01 -s >> logs/fut_price11.log 2>&1 &

# python fut_price.py -n -t vfv-ct -o vfv-test01 -s -d vfv-ct_merged_test01