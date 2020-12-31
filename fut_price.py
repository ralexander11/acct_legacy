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
import os

# Make numpy printouts easier to read
np.set_printoptions(precision=3, suppress=True)

def time_stamp(offset=0):
	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
		offset = 4
	time_stamp = (dt.datetime.now() + dt.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def prep_data(ticker=None, merged='merged.csv', crypto=False, v=True):
	if v: print(time_stamp() + 'Prepare data')
	combine_data = CombineData()
	if crypto:
		url = 'http://becauseinterfaces.com/acct/market_data/data/crypto_prep_merged.csv'
		column_names = ['symbol','date','askPrice','askSize','bidPrice','bidSize','latestPrice','target']
		if ticker is None:
			ticker = 'BTCUSDT'
		merged = 'crypto_prep_merged.csv'
		if v: print(time_stamp() + f'URL: {url}')
	else:
		url = 'http://becauseinterfaces.com/acct/market_data/data/merged.csv'
		column_names = ['symbol', 'date', 'avgTotalVolume', 'change', 'changePercent', 'close', 'delayedPrice', 'extendedChange', 'extendedChangePercent', 'extendedPrice', 'high', 'iexMarketPercent', 'iexRealtimePrice', 'iexRealtimeSize', 'iexVolume', 'latestPrice', 'latestVolume', 'low', 'marketCap', 'open', 'peRatio', 'previousClose', 'previousVolume', 'volume', 'week52High', 'week52Low', 'ytdChange', 'avg10Volume', 'avg30Volume', 'beta', 'day200MovingAvg', 'day30ChangePercent', 'day50MovingAvg', 'day5ChangePercent', 'marketcap', 'maxChangePercent', 'month1ChangePercent', 'month3ChangePercent', 'month6ChangePercent', 'sharesOutstanding', 'ttmEPS', 'week52change', 'week52high', 'week52low', 'year1ChangePercent', 'year2ChangePercent', 'year5ChangePercent', 'ytdChangePercent', 'factor', 'cur_factor', 'target']
		# merged = 'merged.csv'

	if v: print(time_stamp() + f'Ticker: {ticker}')

	if os.path.exists(combine_data.data_location + merged) and not crypto:
		if v: print(time_stamp() + 'Merged data exists.')
		merged_data = pd.read_csv(combine_data.data_location + merged)
		merged_data = merged_data.set_index(['symbol','date'])
		dataset = combine_data.comp_filter(ticker, merged_data)
		if v: print(dataset.shape)
		dataset = dataset[column_names]
		if v: print(dataset.shape)
	else:
		raw_dataset = pd.read_csv(url, names=column_names)
		dataset = raw_dataset.copy()
		dataset = dataset.loc[dataset['symbol'] == ticker]

	if v: print(time_stamp() + f'Dataset tail 1.')
	if v: print(dataset.tail())
	dataset.drop(['symbol','date'], axis=1, inplace=True)
	# print(time_stamp() + 'nan counts:')
	# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
	# 	print(dataset.isna().sum())
	# dataset.dropna(axis=0, inplace=True)
	dataset.dropna(axis=0, subset=['target'], inplace=True)
	if v: print(dataset.shape)
	# if v: with pd.option_context('display.max_rows', None, 'display.max_columns', None):
	# 	if v: print(dataset.dtypes)
	if v: print(time_stamp() + f'Convert to floats.')
	dataset = dataset.astype('float', errors='ignore')
	# if v: with pd.option_context('display.max_rows', None, 'display.max_columns', None):
	# 	if v: print(dataset.dtypes)
	if v: print(time_stamp() + f'Dataset tail 2.')
	if v: print(dataset.tail())
	return dataset

def get_features_and_labels(ticker=None, dataset=None, crypto=False, frac_per=0.8, v=True):
	if dataset is None:
		dataset = prep_data(ticker=ticker, crypto=crypto, v=v)
	frac = int(len(dataset) * frac_per)
	if v: print(time_stamp() + f'dataset len: {len(dataset)}')
	if v: print(time_stamp() + f'frac: {frac}')
	train_dataset = dataset[:frac]
	test_dataset = dataset.drop(train_dataset.index)

	# if v: print(time_stamp() + 'Dataset Statistics Summary')
	# if v: print(train_dataset.describe().transpose())

	train_features = train_dataset.copy()
	test_features = test_dataset.copy()

	train_labels = train_features.pop('target')
	test_labels = test_features.pop('target')
	return train_features, test_features, train_labels, test_labels

def normalize_data(train_features=None, v=True):
	if v: print(time_stamp() + 'Normalize training features')
	if train_features is None:
		train_features = get_features_and_labels(v=v)[0]
	normalizer = preprocessing.Normalization()
	normalizer.adapt(np.array(train_features))
	if v: print(time_stamp() + 'Normalized Mean:')
	if v: print(normalizer.mean.numpy())
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

def plot_prediction(x, y, train_features, train_labels):
	plt.scatter(train_features['latestPrice'], train_labels, label='Data')
	plt.plot(x, y, color='k', label='Predictions')
	plt.xlabel('latestPrice')
	plt.ylabel('target')
	plt.legend()
	plt.show()

def main(ticker=None, train=False, crypto=False, save=False, v=False):
	if v: print(time_stamp() + f'TensorFlow Version: {tf.__version__}')
	if v: print(time_stamp() + f'Train:', train)

	if ticker is None:
		ticker = 'tsla'
	if crypto and ticker is None:
		ticker = 'BTCUSDT'

	train_features, test_features, train_labels, test_labels = get_features_and_labels(ticker=ticker, crypto=crypto, v=v)

	file_name = 'misc/models/' + ticker.lower() + '_model'
	if v: print(time_stamp() + f'File Name: {file_name}')
	if v: print(time_stamp() + f'Model exists:', os.path.exists(file_name))
	if os.path.exists(file_name) and not train:
		if v: print(time_stamp() + 'Load model from: ' + ticker.lower() + '_model')
		model = tf.keras.models.load_model(file_name)
		test_predictions = model.predict(test_features)
		test_predictions = test_predictions.flatten()
		if v: print(time_stamp() + 'Prediction Results:')
		if v: print(time_stamp() + f'test_labels (x):\n{test_labels}')
		if v: print(time_stamp() + f'test_predictions (y):\n{test_predictions}')

		plot_prediction(test_labels, test_predictions, train_features, train_labels)

		if v: print(time_stamp() + 'Evaluate loaded ' + ticker.lower() + '_model:')
		test_results = {}
		test_results['reloaded'] = model.evaluate(test_features, test_labels, verbose=0)
	else:
		# train_features, test_features, train_labels, test_labels = get_features_and_labels(ticker=ticker, crypto=crypto, v=v)
		normalizer = normalize_data(train_features, v=v)

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
		if v: print(time_stamp() + f'test_labels (x):\n{test_labels}')
		if v: print(time_stamp() + f'test_predictions (y):\n{test_predictions}')

		plot_prediction(test_labels, test_predictions, train_features, train_labels)

		if save:
			if v: print(time_stamp() + 'Save model as: ' + ticker.lower() + '_model')
			model.save(file_name)

	if v: print(time_stamp() + 'Test Results:')
	if v: df = pd.DataFrame(test_results, index=['Mean absolute error [target]']).T
	if v: print(df)

	if len(test_predictions) == 1:
		result = test_predictions[0]
	else:
		result = test_predictions

	if v: print(time_stamp() + f'Result:\n{result}')
	return result


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--save', action='store_true', help='Save the model for reuse.')
	parser.add_argument('-t', '--ticker', type=str, help='A single ticker to use.')
	parser.add_argument('-n', '--train', action='store_true', help='Train a new model.')
	parser.add_argument('-c', '--crypto', action='store_true', help='If using for cryptocurrencies.')
	args = parser.parse_args()

	result = main(args.ticker, train=args.train, save=args.save, v=True)

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/fut_price.py -n -s >> /home/robale5/becauseinterfaces.com/acct/logs/fut_price01.log 2>&1 &

# TODO
# Convert to main function
# Add argparse
# Add option to select crypto
# Add option to provide ticker
# Add option to select Canadian
# Add save option
# Add train option
# Output single price
# Add verbose option
# Clean up code