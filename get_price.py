# import acct
# import trade
# from market_data.market_data import MarketData
from market_data.combine_data import CombineData

import tensorflow as tf
import numpy as np
import pandas as pd
import argparse
import datetime
import os
import gc

# tf.compat.v1.disable_eager_execution()

server = False
if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
	server = True

if not server:
	import matplotlib as mpl
	import matplotlib.pyplot as plt
	mpl.rcParams['figure.figsize'] = (8, 6)
	mpl.rcParams['axes.grid'] = False

v = True
DISPLAY_WIDTH = 98
# TRAIN_SPLIT = 300000 # Automate as 70%
BATCH_SIZE = 256
BUFFER_SIZE = 10000
EVALUATION_INTERVAL = 200 # steps_per_epoch
EPOCHS = 10
HISTORY_SIZE = 2 #720
TARGET_SIZE = 0 #72
STEP = 1 #6
tf.random.set_seed(13)
DATA_NEEDED = 100

# Download data
# zip_path = tf.keras.utils.get_file(origin='https://storage.googleapis.com/tensorflow/tf-keras-datasets/jena_climate_2009_2016.csv.zip', fname='jena_climate_2009_2016.csv.zip', extract=True)
# csv_path, _ = os.path.splitext(zip_path)
csv_path = 'data/jena_climate_2009_2016.csv'

def time_stamp(offset=0):
	if os.path.exists('/home/robale5/becauseinterfaces.com/acct/'):
		offset = 4
	time_stamp = (datetime.datetime.now() + datetime.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def create_time_steps(length):
	time_steps = []
	for i in range(-length, 0, 1):
		time_steps.append(i)
	return time_steps

def show_plot(plot_data, delta, title):
	labels = ['History', 'True Future', 'Model Prediction']
	marker = ['.-', 'rx', 'go']
	time_steps = create_time_steps(plot_data[0].shape[0])
	if delta:
		future = delta
	else:
		future = 0
	plt.title(title)
	for i, x in enumerate(plot_data):
		if i:
			plt.plot(future, plot_data[i], marker[i], markersize=10, label=labels[i])
		else:
			plt.plot(time_steps, plot_data[i].flatten(), marker[i], label=labels[i])
	plt.legend()
	plt.xlim([time_steps[0], (future+5)*2])
	plt.xlabel('Time-Step')
	return plt

def multivariate_data(dataset, target, start_index, end_index, history_size, target_size, step=1, single_step=True, v=False):
	count = 0
	if v: print('\nstart_index:', start_index)
	if v: print('end_index:', end_index)
	if v: print('history_size:', history_size)
	if v: print('target_size:', target_size)
	if v: print('step:', step)
	data = []
	labels = []
	prior = None

	start_index = start_index + history_size
	if end_index is None:
		end_index = len(dataset) - target_size
	if v: print('start_index_2:', start_index)
	if v: print('end_index_2:', end_index)
	if v: print('range:', range(start_index, end_index))
	if v: print()

	for i in range(start_index, end_index):
		count += 1
		cond = count == 1
		if v and cond: print('count:', count)
		indices = range(i-history_size, i, step)
		if v and cond: print('indices:', indices)
		data.append(dataset[indices])
		if v and cond: print('data:\n', data)
		if v and cond: print('data len:', len(data))
		if v and cond: print('data len[0]:', len(data[0]))
		if single_step:
			labels.append(target[i+target_size])
			if count == 1:
				prior_index = (i+target_size) - 1
				prior = target[prior_index]
				if v: print('prior_index:', prior_index)
				if v: print('prior:', prior)
			if v and cond: print('target index:', (i+target_size))
			if v and cond: print('labels:\n', labels)
		else:
			labels.append(target[i:i+target_size])
			if cond:
				prior_index = (i+target_size) - 1
				prior = target[prior_index]

	return np.array(data), np.array(labels), prior

def prep_data(path, data_mean=None, data_std=None, norm=False, train=True, v=False):
	# TODO Maybe make data_mean, data_std instance variables
	print('-' * DISPLAY_WIDTH)
	print(time_stamp() + 'Prep data...')
	if not isinstance(path, str):
		df = path
		df = df.dropna(subset=['iexLastUpdated']) # TODO Do this when train=True?
		# with pd.option_context('display.max_columns', None):
		# 	print(df)#.head())
		datetime_cols = ['closeTime', 'delayedPriceTime', 'extendedPriceTime', 'iexLastUpdated', 'latestTime', 'latestUpdate', 'openTime', 'exDividendDate', 'latestEPSDate', 'shortDate', 'lastTradeTime']
		all_zeros_cols = ['iexAskPrice', 'iexAskSize', 'iexBidPrice', 'iexBidSize', 'dividendRate', 'dividendYield', 'peRatioHigh', 'peRatioLow']
		categorical_data_cols = ['calculationPrice', 'companyName_x', 'latestSource', 'companyName_y', 'primaryExchange', 'sector']
		all_nan_cols = ['askPrice', 'askSize', 'bidPrice', 'bidSize', 'EPSSurpriseDollar', 'returnOnCapital']
		has_nan_cols = ['insiderPercent', 'priceToBook']
		unsure_cols = ['institutionPercent']
		drop_cols = datetime_cols + all_zeros_cols + categorical_data_cols + all_nan_cols + has_nan_cols + unsure_cols
		dataset = df.drop(drop_cols, axis=1, errors='ignore')
		cols = ['changePercent', 'day50MovingAvg', 'latestPrice']
		dataset = dataset[cols]
		if v: print(dataset)#.head())
		for tar_col, col in enumerate(dataset.columns.values.tolist()):
			if col == 'latestPrice':
				break
		if v: print('latestPrice tar_col:', tar_col)
		# dataset.plot(subplots=True)
		# plt.show()
		# exit()

	else: # From an example in the documentation
		df = pd.read_csv(path)
		dataset = df[['p (mbar)', 'T (degC)', 'rho (g/m**3)']]
		dataset.index = df['Date Time']
		tar_col = 1
		if v: print(dataset)#.head())
		# features.plot(subplots=True)
		# plt.show()
	dataset = dataset.values
	# if v: print('dataset:\n', dataset)
	if train:
		TRAIN_SPLIT = int(len(dataset) * 0.7)
	else:
		TRAIN_SPLIT = len(dataset)
	if v: print('dataset len:', len(dataset))
	if v: print('train_split:', TRAIN_SPLIT)
	if v: print('val_split:', len(dataset) - TRAIN_SPLIT)
	if norm:
		if data_mean is None:
			data_mean = dataset[:TRAIN_SPLIT].mean(axis=0)
		if v: print('data_mean:', data_mean)
		if data_std is None:
			data_std = dataset[:TRAIN_SPLIT].std(axis=0)
		if v: print('data_std: ', data_std)
		dataset = (dataset - data_mean) / data_std
		df_mean_std = pd.DataFrame(columns=cols, data=[data_mean, data_std], index=None)
		if v: print('df_mean_std:\n', df_mean_std)
	if v: print('dataset normalized[5]:\n', dataset[:5])
	if v: print('target[5]:\n', (dataset[:, tar_col])[:5])
	if v: print('target len:', len(dataset[:, 1]))
	x_train, y_train, _ = multivariate_data(dataset, dataset[:, tar_col], 0, TRAIN_SPLIT, HISTORY_SIZE, TARGET_SIZE, STEP, single_step=True, v=v)
	x_val, y_val, prior = multivariate_data(dataset, dataset[:, tar_col], TRAIN_SPLIT, None, HISTORY_SIZE, TARGET_SIZE, STEP, single_step=True, v=v)
	if v: print('\nx_train[3]:\n{}'.format(x_train[:3]))#.shape))
	if v: print('y_train[3]: {}'.format(y_train[:3]))#[0].shape))
	if v: print('x_val[3]:\n{}'.format(x_val[:3]))#.shape))
	if v: print('y_val[3]: {}'.format(y_val[:3]))#[0].shape))
	if v: print()


	train_data = tf.data.Dataset.from_tensor_slices((x_train, y_train))
	train_data = train_data.cache().shuffle(BUFFER_SIZE).batch(BATCH_SIZE).repeat()
	if v: print('\ntrain_data:', train_data)
	val_data = tf.data.Dataset.from_tensor_slices((x_val, y_val))
	val_data = val_data.batch(BATCH_SIZE).repeat()
	if v: print('val_data:  ', val_data)
	# if v: print('val_data len:\n', len(val_data))
	# exit()
	return train_data, val_data, x_train, tar_col, prior, data_mean, data_std, df_mean_std

def create_model(x_train, v=False):
	print('\n' + time_stamp() + 'Create model...')
	if x_train.size == 0:
		return
	if v: print(x_train.shape)
	if v: print(x_train.shape[-2:])
	if v: print()
	# exit()
	model = tf.keras.models.Sequential()
	model.add(tf.keras.layers.LSTM(32, input_shape=x_train.shape[-2:]))
	model.add(tf.keras.layers.Dense(1))

	model.compile(optimizer=tf.keras.optimizers.RMSprop(), loss='mae')
	return model

def train_model(model, train_data, val_data, v=False):
	print('\n' + time_stamp() + 'Train model...')
	history = model.fit(train_data, epochs=EPOCHS, steps_per_epoch=EVALUATION_INTERVAL, validation_data=val_data, validation_steps=50)
	return history

def plot_train_history(history, title, v=False):
	loss = history.history['loss']
	val_loss = history.history['val_loss']
	epochs = range(len(loss))
	plt.figure()
	plt.plot(epochs, loss, 'b', label='Training loss')
	plt.plot(epochs, val_loss, 'r', label='Validation loss')
	plt.title(title)
	plt.legend()
	plt.show()

def show_result(model, val_data, train_data, tar_col, data_mean, data_std, v=False):
	# TODO Maybe make data_mean, data_std instance variables
	count = 0
	n = 1
	if v: print('val_data take ' + str(n), val_data.take(n))
	if v: print()
	for x, y in val_data.take(n):
		count += 1
		if v: print('result count:', count)
		if v: print('x[3]:\n', x[:3])
		if v: print('y[3]:\n', y[:3])
		pred = model.predict(x)
		if v: print('pred[3]:\n', pred[:3])
		pred_real = pred[0][0]
		if data_mean is not None:
			pred_real = (pred_real * data_std[tar_col]) + data_mean[tar_col]
			if v: print('pred:', pred_real)
		actual = y[0].numpy()
		if data_std is not None:
			actual = (actual * data_std[tar_col]) + data_mean[tar_col]
			if v: print('actual:', actual)
		if v: print('diff:', actual - pred_real)
		# plot = show_plot([x[0][:, 1].numpy(), y[0].numpy(), pred[0]], 1, 'Single Step Prediction')
		# plot.show()
	count = 0
	for x, y in train_data.take(3):
		count += 1
		if v: print('result train count:', count)
		if data_mean is not None:
			prior = (x[0].numpy() * data_std[tar_col]) + data_mean[tar_col]
		else:
			prior = x[0].numpy()
		if v: print('prior_x:\n', prior)
		if data_std is not None:
			prior = (y[0].numpy() * data_std[tar_col]) + data_mean[tar_col]
		else:
			prior = y[0].numpy()
		if v: print('prior_y:\n', prior)
	return pred_real, actual

def pred_price(df, v=False):
	train_data, val_data, x_train, tar_col, prior, data_mean, data_std, df_mean_std = prep_data(df, norm=True, train=True, v=v)
	model = create_model(x_train=x_train, v=v)
	if model is None:
		return None, None, None, None, None
	# for x, y in val_data.take(1):
	# 	pred = model.predict(x)
	# 	print('\npred shape:', pred.shape)
	# 	print('pred[3]:\n', pred[:3])
	hist = train_model(model=model, train_data=train_data, val_data=val_data, v=v)
	if v: print('hist:', hist)
	# plot_train_history(hist, 'Training and validation loss')
	pred, actual = show_result(model=model, val_data=val_data, train_data=train_data, tar_col=tar_col, data_mean=data_mean, data_std=data_std, v=v)
	if data_mean is not None:
		prior = (prior * data_std[tar_col]) + data_mean[tar_col]
	return pred, prior, actual, model, df_mean_std

def get_price(df, ticker, path=None, data_mean=None, data_std=None, tar_col=None, merged_data=None, new_train=True, train=False):#, lite=False):
	print(time_stamp() + 'Predict price for ticker: {}'.format(ticker))
	ticker = ticker.lower()
	if path is None:
		path = '/home/robale5/becauseinterfaces.com/acct/misc/models/'
		if not os.path.exists(path):
			path = 'misc/models/'
			# path = '~/Public/models/'
	filepath = path + ticker + '_model'
	# print('model_path:', filepath)
	if not os.path.exists(filepath) or train:# and not lite:
		if new_train or train:
			predictions = main(ticker, merged_data=merged_data, v=False)
			with pd.option_context('display.max_columns', None):
				print(time_stamp() + 'Predictions:\n', predictions)
			if predictions is None:
				tf.keras.backend.clear_session()
				return
		else:
			print('No model for {}.'.format(ticker))
			return
	# if lite:
	# 	import tflite_runtime.interpreter as tflite
	# 	interpreter = tflite.Interpreter(model_path=filepath)
	model = tf.keras.models.load_model(filepath, custom_objects=None, compile=True)
	data_path = filepath + '/assets/' + ticker + '_mean_std.csv'
	with open(data_path, 'r') as f:
		df_mean_std = pd.read_csv(f, index_col=None)
	cols = df_mean_std.columns.values.tolist()
	for tar_col, col in enumerate(cols):
		if col == 'latestPrice':
			break # TODO Maybe handle if value is not present
	if tar_col is None:
		tar_col = 2
	if data_mean is None:
		data_mean = np.array(df_mean_std.iloc[0])
	if data_std is None:
		data_std = np.array(df_mean_std.iloc[1])
	x_data = df[cols]
	y_data = np.array([df.iloc[:, tar_col].values[1]])
	x_data = np.array([x_data.values])
	x_data_norm = (x_data - data_mean) / data_std
	x_data_norm = x_data_norm.astype(np.float64)
	data = tf.data.Dataset.from_tensor_slices((x_data_norm, y_data))
	data = data.batch(BATCH_SIZE).repeat()
	# print('data:\n', data)
	for x, y in data.take(1):
		# print('x:\n', x)
		price = model.predict(x)
	price = price[0][0]
	price = (price * data_std[tar_col]) + data_mean[tar_col]
	# Test to clean up memory
	del model
	gc.collect()
	tf.keras.backend.clear_session()
	return price

def convert_lite(tickers=None, model=None, save=True):
	if tickers is None:
		ticker =['tsla'] # For testing
	if not isinstance(tickers, (list, tuple)):
		tickers = [tickers]
	for ticker in tickers:
		ticker = ticker.lower()
		path = 'misc/models/'
		# path = '~/Public/models/'
		filepath = path + ticker + '_model'
		print('model_path:', filepath)
		model = tf.keras.models.load_model(filepath, custom_objects=None, compile=True)
		print('\nmodel:', model)
		converter = tf.lite.TFLiteConverter.from_keras_model(model)
		print('\nconverter:', converter)
		tflite_model = converter.convert() # KeyError here
		print('\ntflite_model:', tflite_model)
		if save:
			save_filepath = 'misc/models_lite/' + ticker + '_model'
			tf.keras.models.save_model(tflite_model, save_filepath, overwrite=True, include_optimizer=True, save_format=None, signatures=None, options=None)
			print(time_stamp() + 'Model saved to:', save_filepath)
	return tflite_model

def main(tickers=None, merged_data=None, v=True):
	combine_data = CombineData()
	predictions = pd.DataFrame(columns=['ticker','prediction','prior','changePercent','actual','actual_changePer'])
	if tickers is not None:
		if not isinstance(tickers, (list, tuple)):
			tickers = [str(tickers)]
		for ticker in tickers:
			ticker = ticker.lower()
			merged = 'merged_final.csv'
			# print(combine_data.data_location + merged)
			if merged_data is not None:
				df = combine_data.comp_filter(ticker, merged_data)
				if df.shape[0] < DATA_NEEDED:
					return
			elif os.path.exists(combine_data.data_location + merged):
				print(time_stamp() + 'Merged data exists.')
				merged_data = pd.read_csv(combine_data.data_location + merged)
				merged_data = merged_data.set_index(['symbol','date'])
				df = combine_data.comp_filter(ticker, merged_data) # TODO Don't load each time, keep in memory
			else:
				print(time_stamp() + 'Saving down merged data.')
				df = combine_data.comp_filter(ticker, save=True)
			print('Creating model to predict price for {}.'.format(ticker))
			pred, prior, actual, model, df_mean_std = pred_price(df, v=v)
			if pred is None:
				return
			predictions = predictions.append({'ticker':ticker, 'prediction':pred, 'prior':prior, 'changePercent':(pred-prior)/prior, 'actual':actual, 'actual_changePer':(actual-prior)/prior}, ignore_index=True)
			path = '/home/robale5/becauseinterfaces.com/acct/misc/models/'
			if not os.path.exists(path):
				filepath = 'misc/models/' + ticker + '_model'
			tf.keras.models.save_model(model, filepath, overwrite=True, include_optimizer=True, save_format=None, signatures=None, options=None)
			df_mean_std.to_csv('misc/models/' + ticker + '_model/assets/' + ticker + '_mean_std.csv', date_format='%Y-%m-%d', index=False)
	else:
		pred, prior, actual, model, df_mean_std = pred_price(csv_path, v=v)
		if pred is None:
			return
		predictions = predictions.append({'ticker':None, 'prediction':pred, 'prior':None, 'changePercent':None, 'actual':None, 'actual_changePer':None}, ignore_index=True)
	return predictions


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--train', action='store_true', help='Train a new model if existing model is not found.')
	args = parser.parse_args()
	print(time_stamp() + str(sys.argv))

	predictions = main(['tsla','aapl'])
	with pd.option_context('display.max_columns', None):
		print(time_stamp() + 'predictions:\n', predictions)

# Redo models: fb, snap, crm, ttd, grpn

# predictions:
#    ticker  prediction   prior  changePercent  actual  actual_changePer
# 0   tsla  305.790849  307.51      -0.005591  305.80         -0.005561
# 1   aapl  178.330856  174.28       0.023243  170.97         -0.018992


# ('AZZ', '2019-05-01') 44.14423 <class 'str'>
# ('AZZ', '2019-05-02') 44.13875 <class 'float'>

# ('AXS-D', '2019-12-10') 25.28 <class 'float'>
# ('AXS-D', '2019-12-11') 25.28 <class 'str'>