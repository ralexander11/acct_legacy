#!/usr/bin/env python

import acct
import pandas as pd
import numpy as np
# import pygame
# from pygame.locals import *
import collections
import itertools
import functools
import argparse
import datetime
# TODO import datetime as dt
import warnings
import getpass
import random
import time
import math
import os, sys
import re
import pickle
from sqlite3 import Binary
import timeit
import cProfile
# try:
# 	from rich import print
# except ImportError:
# 	print('Rich print not supported.')
# 	pass

DISPLAY_WIDTH = 98
pd.set_option('display.width', None)
pd.options.display.float_format = '{:,.2f}'.format
warnings.filterwarnings('ignore')

args = None
world = None
new_db = True
USE_PIN = None

# TODO yaml based config settings
END_DATE = None
MAX_HOURS = 12
WORK_DAY = 8
PAY_PERIODS = 2
GESTATION = 3 # 7
MAX_CORPS = 2
INIT_PRICE = 10.0
INIT_CAPITAL = 25000 # Not used
EXPLORE_TIME = 1
INC_BUFFER = 3
REDUCE_PRICE = 0.01 # 0.1

def time_stamp(offset=0):
	if END_DATE is None or False:
		offset = 4
	time_stamp = (datetime.datetime.now() + datetime.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def delete_db(db_name=None):
	if db_name is None:
		db_name = 'econ01.db'
	db_path = 'db/'
	if os.path.exists(db_path + db_name):
		os.remove(db_path + db_name)
		print(time_stamp() + 'Database file reset: {}'.format(db_path + db_name))
	else:
		print(time_stamp() + 'The database file does not exist to be reset at: {}.'.format(db_path + db_name))

econ_accts = [
	('Cash','Asset'),
	('Info','Admin'),
	('Natural Wealth','Equity'),
	('Nation Wealth','Equity'),
	('Investments','Asset'),
	('Shares','Equity'),
	('Gain','Revenue'),
	('Loss','Expense'),
	('Land','Asset'),
	('Buildings','Asset'),
	('Building Produced','Revenue'),
	('Equipment Produced','Revenue'),
	('Equipment','Asset'),
	('Equipped','Asset'),
	('Machine','Equipment'),
	('Tools','Equipment'),
	('Furniture','Equipment'),
	('Inventory','Asset'),
	('WIP Inventory','Asset'),
	('WIP Equipment','Asset'),
	('Building Under Construction','Asset'),
	('Land In Use','Asset'),
	('Buildings In Use','Asset'),
	('Equipment In Use','Asset'),
	('Commodities','Inventory'),
	('Cost of Goods Sold','Expense'),
	('Cost Pool','Transfer'),
	('Sales','Revenue'),
	('Goods Produced','Revenue'),
	('Goods Consumed','Expense'),
	('Accounts Receivable','Asset'),
	('Accounts Payable','Liability'),
	('Salary Expense','Expense'),
	('Salary Income','Revenue'),
	('Wages Payable','Liability'),
	('Wages Expense','Expense'),
	('Wages Receivable','Asset'),
	('Wages Income','Revenue'),
	('Depr. Expense','Expense'),
	('Accum. Depr.','Asset'),
	('Loss on Impairment','Expense'),
	('Accum. Impairment Losses','Asset'),
	('Spoilage Expense','Expense'),
	('Worker Info','Info'),
	('Hire Worker','Info'),
	('Fire Worker','Info'),
	('Start Job','Info'),
	('Quit Job','Info'),
	('Subscription Available','Info'),
	('Subscription Info','Info'),
	('Order Subscription','Info'),
	('Sell Subscription','Info'),
	('End Subscription','Info'),
	('Cancel Subscription','Info'),
	('Subscription Expense','Expense'),
	('Subscription Revenue','Revenue'),
	('Service Info','Info'),
	('Service Available','Info'),
	('Service Expense','Expense'),
	('Service Revenue','Revenue'),
	('Dividend Receivable','Asset'),
	('Dividend Income','Revenue'),
	('Dividend Payable','Liability'),
	('Dividend Expense','Expense'),
	('Commission Expense','Expense'),
	('Investment Gain','Revenue'),
	('Investment Loss','Expense'),
	('Unrealized Gain','Revenue'),
	('Unrealized Loss','Expense'),
	('Interest Expense','Expense'),
	('Interest Income','Revenue'),
	('Education','Asset'),
	('Studying Education','Asset'),
	('Education Expense','Expense'),
	('Education Produced','Revenue'),
	('Education Revenue','Revenue'),
	('Technology','Asset'),
	('Researching Technology','Asset'),
	('Technology Expense','Expense'),
	('Technology Produced','Revenue'),
	('Deposits','Liability'),
	('Bank Cash','Asset'),
	('Loan','Liability'),
	('Loans Receivable','Asset'),
	('Bad Debts Expense','Expense'),
	('Write-off','Revenue'), # Other Income account
	('Gift','Revenue'),
	('Gift Expense','Expense'),
	('End of Day','Info'),
	('End of Turn','Info'),
	('Save','Info'),
] # TODO Remove div exp once retained earnings is implemented

class World:
	# _instance = None
	def __init__(self, factory, accts=None, ledger=None, governments=1, population=2, new_db=True):#, args=None):# World
		# if World._instance is not None:
		# 	raise Exception('Use World.get_model() instead of creating a new instance.')
		# pygame.init()
		self.paused = False
		self.factory = factory
		self.accts = accts
		self.ledger = ledger
		global args
		if args is None:
			args = argparse.Namespace(database=None, command=None, delay=0, reset=False, random=True, seed=None, items=None, time=None, capital=1000000, governments=1, players=0, population=1, max_pop=None, users=0, win=False, pin=False, early=False, jones=False)
		# World._instance = self
		# self.accts = EntityFactory.get_accts()
		# self.ledger = EntityFactory.get_ledger()  # Access shared Ledger
		# print('New db: {}'.format(new_db))
		if new_db or args.reset:
			self.accts.clear_tables(v=True)
			print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Create World ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))
			self.now = datetime.datetime(1986,10,1).date() # TODO Make start_date constant
			self.set_table(self.now, 'date')
			print(self.now)
			if args.items is None:
				if args.jones:
					items_file = 'data/items_jones.csv'
				else:
					items_file = 'data/items.csv'
			else:
				items_file = 'data/' + args.items
			self.items = self.accts.load_items(items_file) # TODO Change config file to JSON and load into a graph structure
			self.items = self.items.reset_index() # TODO Avoid this?
			self.items['fulfill'] = self.items.apply(lambda x: x['item_id'] if x['fulfill'] is None else x['fulfill'], axis=1)
			self.items = self.items.set_index('item_id') # TODO Avoid this?
			try:
				self.econ_graph()
			except ImportError:
				pass
			self.items_map = pd.DataFrame(columns=['item_id', 'child_of'], index=['item_id']).dropna() # TODO Is this needed still?
			self.set_table(self.items_map, 'items_map')
			self.global_needs = self.create_needs()
			print(time_stamp() + 'Loading items from: {}'.format(items_file))
			self.demand = pd.DataFrame(columns=['date','entity_id','item_id','qty','reason'])
			self.set_table(self.demand, 'demand')
			self.delay = pd.DataFrame(columns=['txn_id', 'entity_id','delay','hours','job','item_id'])
			self.set_table(self.delay, 'delay')
			self.tech = pd.DataFrame(columns=['technology', 'date', 'entity_id','time_req','days_left', 'done_date','status'])
			self.set_table(self.tech, 'tech')
			self.governments = governments
			self.population = population
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Items Config: \n{}'.format(self.items))
			if args.win:
				self.win_conditions = self.set_win(win_defaults=True, v=True)
				self.set_table(self.win_conditions, 'win_conditions')
			else:
				self.win_conditions = None
			self.env = self.create_world(date=self.now)
			self.setup_prices()
			self.produce_queue = pd.DataFrame(columns=['item_id', 'entity_id','qty', 'freq', 'last', 'one_time', 'man'])
			print('\nInitial Produce Queue: \n{}'.format(self.produce_queue))
			self.set_table(self.produce_queue, 'produce_queue')
			self.end = False
			player_count = args.players
			# Create gov for each government
			for government in range(1, self.governments + 1):
				user = False
				if player_count:
					user = True
					player_count -= 1
				self.entities = self.accts.get_entities()
				last_entity_id = self.entities.reset_index()['entity_id'].max()
				self.factory.create(Government, 'Government-' + str(last_entity_id + 1), items=None, user=user)
			for gov in self.factory.get(Government):
				self.indiv_items_produced = self.items[self.items['producer'].str.contains('Individual', na=False)].reset_index() # TODO Move to own function
				self.indiv_items_produced = self.indiv_items_produced['item_id'].tolist()
				self.indiv_items_produced = ', '.join(self.indiv_items_produced)
				print('\nCreate founding population for government {}.'.format(gov.entity_id))
				print('{} | Interest Rate: {}'.format(gov.bank, gov.bank.interest_rate))
				if args.jones:
					# Get list of businesses from items data
					self.businesses = []
					for index, producers in self.items['producer'].items():#.iteritems():
						if producers is not None:
							if isinstance(producers, str):
								producers = [x.strip() for x in producers.split(',')]
							self.businesses += producers
					self.businesses = list(collections.OrderedDict.fromkeys(filter(None, self.businesses)))
					if 'Individual' in self.businesses:
						self.businesses.remove('Individual')
					if 'Bank' in self.businesses:
						self.businesses.remove('Bank')
					print('Businesses:', self.businesses)
				user_count = args.users
				for person in range(1, self.population + 1):
					print('\nPerson: {}'.format(person))
					user = False
					if user_count:
						user = True
						user_count -= 1
					self.entities = self.accts.get_entities()
					last_entity_id = self.entities.reset_index()['entity_id'].max()
					self.factory.create(Individual, 'Person-' + str(last_entity_id + 1), self.indiv_items_produced, self.global_needs, gov.entity_id, str(last_entity_id + 1), user=user)
					entity = self.factory.get_by_id(last_entity_id + 1)
					# self.prices = pd.concat([self.prices, entity.prices])
			self.entities = self.accts.get_entities()
			self.set_table(self.prices, 'prices')
			# Track historical prices
			tmp_prices = self.prices.reset_index()
			tmp_prices['date'] = self.now
			self.hist_prices = pd.DataFrame(tmp_prices, columns=['date','entity_id','price'])
			self.set_table(self.hist_prices, 'hist_prices')
			# Track historical demand
			tmp_demand = self.demand.copy(deep=True)#.reset_index()
			tmp_demand['date_saved'] = self.now
			self.hist_demand = pd.DataFrame(tmp_demand, columns=['date_saved','date','entity_id','item_id','qty','reason'])
			self.set_table(self.hist_demand, 'hist_demand')
			# Track historical hours and needs
			self.hist_hours = self.entities.loc[self.entities['entity_type'] == 'Individual'].reset_index()
			self.hist_hours = self.hist_hours[['entity_id','hours']].set_index(['entity_id'])
			self.hist_hours['date'] = self.now
			self.hist_hours = self.hist_hours[['date','hours']]
			self.hist_hours['population'] = len(self.factory.registry[Individual])
			for need in self.global_needs:
				self.hist_hours[need] = None
			for individual in self.factory.get(Individual):
				for need in individual.needs:
					self.hist_hours.at[individual.entity_id, need] = individual.needs[need].get('Current Need')
			self.hist_hours = self.hist_hours.reset_index()
			self.hist_hours = self.hist_hours.rename(columns={'index': 'entity_id'})
			# print('\nHist Hours: \n{}'.format(self.hist_hours))
			self.set_table(self.hist_hours, 'hist_hours')
			# Set the default starting gov
			self.gov = self.factory.get(Government)[0]
			print('Start Government: {}'.format(self.gov))
			self.selection = None
			self.active_day = False
			global USE_PIN
			if not self.gov.user and USE_PIN: # TODO Add option to turn pins off
				for user in self.gov.get(Individual, computers=False):
					while True:
						try:
							pin = getpass.getpass('{} enter a 4 digit pin number or enter "exit": '.format(user.name))
							if pin.lower() == 'exit':
								exit()
							pin = int(pin)
						except ValueError:
							print('Not a valid entry. Must be a 4 digit number.')
							continue
						else:
							if len(str(pin)) != 4 or int(pin) < 0:
								print('Not a valid entry. Must be a 4 digit number.')
								continue
							break
					user.pin = pin
		else:
			# pygame.init()
			continue_date = self.get_table('date').values[0][0]
			self.now = datetime.datetime.strptime(continue_date[:10], '%Y-%m-%d').date()
			# self.now += datetime.timedelta(days=-1)
			print(time_stamp() + 'Continuing sim from {} file as of {}.'.format(args.database, self.now))
			self.items = self.accts.get_items()
			self.items_map = self.get_table('items_map')
			self.global_needs = self.create_needs()
			self.demand = self.get_table('prior_demand')
			self.demand['qty'] = self.demand['qty'].astype(float)#, errors='ignore')
			# self.demand['qty'].astype(int)#, errors='ignore')
			self.delay = self.get_table('prior_delay')
			self.tech = self.get_table('tech') # TODO Should this be prior_tech?
			self.entities = self.accts.get_entities('prior_entities').reset_index()
			individuals = self.entities.loc[self.entities['entity_type'] == 'Individual']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Individuals: \n{}'.format(individuals))
			alive_individuals = []
			for index, row in individuals.iterrows():
				current_need_all = [int(float(x.strip())) for x in str(row['current_need']).split(',')]
				if not any(n <= 0 for n in current_need_all):
					alive_individuals.append(row)
			self.population = len(alive_individuals)
			self.start_capital = args.capital / args.population
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Items Config: \n{}'.format(self.items))
			# self.entities = self.accts.get_entities().reset_index() # TODO Test if needed
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Loaded Entities: \n{}'.format(self.entities))
			try:
				# TODO Have this load the win conditions
				self.win_conditions = self.get_table('win_conditions')
				self.win_conditions = self.set_win(self.win_conditions, v=True)
			except Exception as e:
				self.win_conditions = None
			envs = self.entities.loc[self.entities['entity_type'] == 'Environment']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Environments: \n{}'.format(envs))
			for index, env in envs.iterrows():
				entity_data = pickle.loads(env['obj'])
				self.factory.register_instance(entity_data)
				# self.factory.create(Environment, env['name'], env['entity_id'])
			self.env = self.factory.get(Environment)[0]
			self.produce_queue = self.get_table('prior_produce_queue')
			self.end = False
			govs = self.entities.loc[self.entities['entity_type'] == 'Government']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Governments: \n{}'.format(govs))
			for index, gov in govs.iterrows():
				entity_data = pickle.loads(gov['obj'])
				self.factory.register_instance(entity_data)
				# self.factory.create(Government, gov['name'], None, gov['user'], int(gov['entity_id']))
			self.governments = len(govs)
			banks = self.entities.loc[self.entities['entity_type'] == 'Bank']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Banks: \n{}'.format(banks))
			for index, bank in banks.iterrows():
				int_rate = bank['int_rate']
				if int_rate is not None:
					int_rate = float(int_rate)
				entity_data = pickle.loads(bank['obj'])
				self.factory.register_instance(entity_data)
				# self.factory.create(Bank, bank['name'], int(bank['government']), int_rate, None, bank['user'], int(bank['entity_id']))
			for gov in self.factory.get(Government):
				bank_id = self.entities.loc[(self.entities['entity_type'] == 'Bank') & (self.entities['government'] == str(gov.entity_id)), 'entity_id'].values[0]
				print('Bank ID: {}'.format(bank_id))
				gov.bank = self.factory.get_by_id(bank_id)
			for index, indiv in individuals.iterrows():
				current_need_all = [int(float(x.strip())) for x in str(indiv['current_need']).split(',')]
				if not any(n <= 0 for n in current_need_all):
					entity = pickle.loads(indiv['obj'])
					self.factory.register_instance(entity)
					if entity.pin is not None:
						USE_PIN = True
					print('Load Individual: {} | User: {} | entity_id: {}'.format(entity.name, entity.user, entity.entity_id))
					print('Citizen of Government: {}'.format(entity.government))
					print('Parents: {}'.format(entity.parents))
					print('Current Hours:', entity.hours)
					# self.factory.create(Individual, indiv['name'], indiv['outputs'], self.global_needs, int(indiv['government']), int(indiv['founder']), float(indiv['hours']), indiv['current_need'], indiv['parents'], indiv['user'], int(indiv['entity_id']))
			if args.users:
				existing_users = self.factory.get(Individual, users=True, computers=False)
				if args.users > len(existing_users):
					existing_ai = self.factory.get(Individual, users=False, computers=True)
					tmp_users = args.users
					for entity in existing_ai:
						entity.user = True
						print(f'{entity} turned into a user.')
						tmp_users -= 1
						if tmp_users == 0:
							break
			corps = self.entities.loc[self.entities['entity_type'] == 'Corporation']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Corporations: \n{}'.format(corps))
			for index, corp in corps.iterrows():
				entity_data = pickle.loads(corp['obj'])
				self.factory.register_instance(entity_data)
				# legal_form = self.org_type(corp['name'])
				# self.factory.create(legal_form, corp['name'], corp['outputs'], int(corp['government']), int(corp['founder']), corp['auth_shares'], corp['entity_id'])
			nonprofs = self.entities.loc[self.entities['entity_type'] == 'NonProfit']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Non-Profits: \n{}'.format(nonprofs))	
			for index, nonprof in nonprofs.iterrows():
				entity_data = pickle.loads(nonprof['obj'])
				self.factory.register_instance(entity_data)
				# legal_form = self.org_type(nonprof['name'])
				# self.factory.create(legal_form, nonprof['name'], nonprof['outputs'], int(nonprof['government']), int(nonprof['founder']), nonprof['auth_shares'], nonprof['entity_id'])
			self.prices = self.get_table('prior_prices')
			with pd.option_context('display.max_rows', None):
				print('\nPrices: \n{}\n'.format(self.prices))
				print('Technology: \n{}\n'.format(self.tech))
				print('Delays: \n{}\n'.format(self.delay))
			try: # TODO Remove error checking because of legacy db files
				self.hist_prices = self.get_table('hist_prices')
				self.hist_demand = self.get_table('hist_demand')
				self.hist_hours = self.get_table('hist_hours')
			except Exception as e:
				print('Loading Error: {}'.format(repr(e)))
			self.gov = self.factory.get(Government)[0]
			print('Start Government: {}'.format(self.gov))
			self.selection = None
			print('\nRoll back to last full day.')
			try:
				last_eod_index = self.ledger.gl.loc[self.ledger.gl['credit_acct'] == 'End of Day'].iloc[-1].name
			except IndexError:
				print('Less than one day completed in prior run.')
				last_eod_index = 0
			try:
				last_eot_index = self.ledger.gl.loc[self.ledger.gl['credit_acct'] == 'End of Turn'].iloc[-1].name
			except IndexError:
				last_eot_index = 0
			try:
				last_save_index = self.ledger.gl.loc[self.ledger.gl['credit_acct'] == 'Save'].iloc[-1].name
			except IndexError:
				last_save_index = 0
			if last_eot_index > last_eod_index:
				self.active_day = True
			else:
				self.active_day = False
			if last_save_index > last_eot_index:
				entity_id = self.ledger.gl.loc[self.ledger.gl['credit_acct'] == 'Save'].iloc[-1][1]
				entity = self.factory.get_by_id(entity_id)
				entity.saved = True
				self.active_day = True
			print('Active Day:', self.active_day)
			last_eod_index = max(last_eod_index, last_eot_index, last_save_index)
			incomplete_cycle = self.ledger.gl.loc[self.ledger.gl.index > last_eod_index].index.values.tolist()
			print('Number of incomplete transactions: {}'.format(len(incomplete_cycle)))
			self.ledger.remove_entries(incomplete_cycle)
			print()
			for typ in self.factory.registry.keys():
				for entity in self.factory.get(typ):
					entity.factory = factory
					entity.accts = accts
					entity.ledger = ledger
					self.ledger.set_entity(entity.entity_id)
					entity.cash = self.ledger.balance_sheet(['Cash'])
					print('{} Cash: {}'.format(entity.name, entity.cash))
					self.ledger.reset()
				print()
				for entity in self.factory.get(typ):
					self.ledger.set_entity(entity.entity_id)
					entity.nav = self.ledger.balance_sheet()
					print('{} NAV: {}'.format(entity.name, entity.nav))
					self.ledger.reset()
				if len(self.factory.registry[typ]) != 0 and typ != Environment and typ != Government and typ != Bank:
					print('\nPre Entity Sort by NAV: {} \n{}'.format(typ, self.factory.registry[typ]))
					self.factory.registry[typ].sort(key=lambda x: x.nav)
					print('Post Entity Sort by NAV: {} \n{}\n'.format(typ, self.factory.registry[typ]))
			if not self.gov.user and USE_PIN:
				for user in self.gov.get(Individual, computers=False):
					while True:
						try:
							pin = getpass.getpass('{} enter a 4 digit pin number or enter "exit": '.format(user.name))
							if pin.lower() == 'exit':
								exit()
							pin = int(pin)
						except ValueError:
							print('Not a valid entry. Must be a 4 digit number.')
							continue
						else:
							if len(str(pin)) != 4 or int(pin) < 0:
								print('Not a valid entry. Must be a 4 digit number.')
								continue
							break
					user.pin = pin
		print()
		self.cols = self.ledger.gl.columns.values.tolist()
		if 'post_date' in self.cols:
			self.cols.remove('post_date')
		print(self.cols) # For verbosity

	@classmethod
	def get_world(cls):
		return cls._instance

	def set_table(self, table, table_name, v=False):
		if v: print('Orig set table: {}\n{}'.format(table_name, table))
		if not isinstance(table, (pd.DataFrame, pd.Series)):
			try:
				if not isinstance(table, collections.abc.Iterable):
					table = [table]
			except AttributeError:
				if not isinstance(table, collections.Iterable):
					table = [table]
			table = pd.DataFrame(data=table, index=None)
			if v: print('Singleton set table: {}\n{}'.format(table_name, table))
		try:
			table = table.reset_index()
			if v: print('Reset Index - set table: {}\n{}'.format(table_name, table))
		except ValueError as e:
			print('Set table error: {}'.format(repr(e)))
		table.to_sql(table_name, self.ledger.conn, if_exists='replace', index=False)
		if v: print('Final set table: {}\n{}'.format(table_name, table))
		return table

	def get_table(self, table_name, v=False):
		tmp = pd.read_sql_query('SELECT * FROM ' + table_name + ';', self.ledger.conn)
		if v: print('Get table tmp: \n{}'.format(tmp))
		index = tmp.columns[0]
		if v: print('Index: {}'.format(index))
		table = pd.read_sql_query('SELECT * FROM ' + table_name + ';', self.ledger.conn, index_col=index)
		table.index.name = None
		if v: print('Get table: {}\n{}'.format(table_name, table))
		return table

	def econ_graph(self, save=True, v=True):
		if v: print(time_stamp() + 'Making Econ Graph.')
		import networkx as nx
		G = nx.DiGraph()
		G.add_nodes_from(self.items.index)
		colour_map = {'Time','Labour', 'Job', 'Equipment', 'Buildings', 'Subscription', 'Service', 'Commodity', 'Components', 'Education', 'Technology', 'Land'}
		for item_id, item_row in self.items.iterrows():
			item_type = self.get_item_type(item_id)
			if item_row['requirements'] is not None:
				requirements = [x.strip() for x in item_row['requirements'].split(',')]
				for req in requirements:
					G.add_edge(req, item_id)
			else:
				G.remove_node(item_id)
		if save:
			nx.drawing.nx_pydot.write_dot(G, 'data/econ_items.dot')
		self.G = G
		if v: print(time_stamp() + 'Econ Graph made.')
		return self.G

	def setup_prices(self, infile=None, v=True):
		# TODO Maybe make self.prices a multindex with item_id and entity_id
		self.prices = pd.DataFrame(columns=['entity_id','price'])
		if infile is not None:
			self.prices = self.accts.load_csv(infile)
			# TODO load prices from file
		self.prices.index.name = 'item_id'
		if v: print('\nSetup Prices: \n{}'.format(self.prices))
		return self.prices

	def create_world(self, lands=None, date=None):
		print(time_stamp() + 'Creating world.')
		# Create environment instance first
		last_entity_id = self.accts.get_entities().reset_index()['entity_id'].max()
		# print('last_entity_id: {}'.format(last_entity_id))
		if pd.isna(last_entity_id):
			last_entity_id = 0
		env = self.factory.create(Environment, 'Earth-' + str(last_entity_id + 1))#, entity_id=1)
		if lands is None:
			# lands = [
			# 	['Land', 100000],
			# 	['Arable Land', 150000],
			# 	['Forest', 10000],
			# 	['Rocky Land', 1000],
			# 	['Mountain', 10]
			# ]
			# land_items = self.items.loc[(self.get_item_type(self.items['child_of']) == 'Land') | (self.items.index == 'Land')].reset_index() # TODO Handle items where the child is a child of Land
			land_items = self.items.loc[(self.items['child_of'] == 'Land') | (self.items.index == 'Land')].reset_index() # TODO Handle items where the child is a child of Land
			# land_items = self.items.loc[(self.items['child_of'] == 'Land')].reset_index()
			lands = []
			for i, land_item in land_items.iterrows():
				land_id = land_item['item_id']
				if not pd.isnull(land_item['int_rate_var']):
					land_amount = land_item['int_rate_var'] # TODO Maybe create dedicated data column
				else:
					land_amount = 150000 # TODO Default value at top from yaml
				lands.append([land_id, land_amount])
		for land in lands:
			env.create_land(land[0], land[1], date) # TODO Call from env instance
		return env

	def unused_land(self, item=None, entity_id=None, all_land=False, accounts=None, v=True):
		if all_land:
			accounts = ['Land','Land In Use']
		else:
			if accounts is None:
				accounts = ['Land']
		if entity_id is not None:
			if not isinstance(entity_id, int):
				entity_id = entity_id.entity_id
			self.ledger.set_entity(entity_id)
			unused_land = self.ledger.get_qty(items=item, accounts=accounts)
		else:
			unused_land = self.ledger.get_qty(items=item, accounts=accounts, by_entity=True)
		if entity_id is not None:
			if v: print('Unused land of the world: \n{}'.format(unused_land))
		elif all_land:
			if v: print('All land claimed by the following entities: \n{}'.format(unused_land))
		elif item is None:
			if v: print('Unused land claimed by the following entities: \n{}'.format(unused_land))
		else: # TODO Other string combinations
			if v: print('Unused {} claimed by the following entities: \n{}'.format(item, unused_land))
		if entity_id is not None:
			self.ledger.reset()
		return unused_land

	def ticktock(self, ticks=1, v=True):
		self.now += datetime.timedelta(days=ticks)
		self.set_table(self.now, 'date')
		if v: print(self.now)
		return self.now

	def get_hours(self, computers=True, total=False, v=False):
		self.hours = collections.OrderedDict()
		if computers:
			entities = world.gov.get(Individual)
		else:
			entities = world.gov.get(Individual, computers=computers)
		for individual in entities:
			self.hours[individual.name] = individual.hours
		if v:
			print('\nCurrent entity hours:')
			for entity_name, hours in self.hours.items():
				print('{} | Hours: {}'.format(entity_name, hours))
		if total:
			total_hours = sum(self.hours.values())
			return total_hours
		return self.hours

	def set_win(self, win_conditions=None, win_defaults=True, v=False):
		self.tech_win = None
		self.pop_win = None
		self.wealth_win = None
		self.wealth_capita_win = None
		self.land_win = None
		self.item_win = None
		self.use_win = None
		self.left_win = None
		if args.time is not None: # Due to setting global within function
			END_DATE = (datetime.datetime(1986,10,1).date() + datetime.timedelta(days=args.time)).strftime('%Y-%m-%d')
		else:
			END_DATE = None
		if win_conditions is not None:
			win_conditions = win_conditions.set_index('Win Condition')
			self.tech_win = win_conditions['Tech win condition: ', 'Value']
			self.pop_win = win_conditions['Population win condition: ', 'Value']
			self.wealth_win = win_conditions['Wealth win condition: ', 'Value']
			self.wealth_capita_win = win_conditions['Wealth per Capita to win: ', 'Value']
			self.land_win = win_conditions['Land win condition: ', 'Value']
			self.item_win = win_conditions['Item win condition: ', 'Value']
			self.use_win = win_conditions['Use item win condition: ', 'Value']
			self.left_win = win_conditions['Last player left alive: ', 'Value']
			args.time = win_conditions['Sim will end in days: ', 'Value']
			if isinstance(args.time, int):
				END_DATE = (datetime.datetime(1986,10,1).date() + datetime.timedelta(days=args.time)).strftime('%Y-%m-%d')
			win_conditions = win_conditions.reset_index()
			print(f'Win Conditions:\n{win_conditions}\n')
			for _, win_value in win_conditions['Value'].items():#.iteritems():
				if win_value:
					args.win = True
			if not new_db and not args.reset:
				return win_conditions
		if win_defaults and win_conditions is None:
			self.tech_win = self.items.loc[self.items['child_of'] == 'Technology'].iloc[-1].name
			self.pop_win = args.population * 10
			self.wealth_win = args.capital
			self.wealth_capita_win = args.capital / args.population
			self.land_win = int(self.items.loc[self.items['child_of'] == 'Land']['int_rate_var'].sum())
			# self.item_win = self.items.loc[self.items['child_of'].isin(['Equipment', 'Buildings'])].iloc[-1].name
			# self.use_win = self.item_win
			# if args.users > 1 or args.players > 1:
			if args.governments > 1 or args.population > 1 or args.users > 1 or args.players > 1:
				self.left_win = True
			win_conditions = { # TODO Don't duplicate this
				'Tech win condition: ': self.tech_win,
				'Population win condition: ': self.pop_win,
				'Wealth win condition: ': self.wealth_win,
				'Wealth per Capita to win: ': self.wealth_capita_win,
				'Land win condition: ': self.land_win,
				'Item win condition: ': self.item_win,
				'Use item win condition: ': self.use_win,
				'Last player left alive: ': self.left_win,
				'Sim will end on: ': END_DATE,
			}
			win_conditions = pd.DataFrame(win_conditions.items(), columns=['Win Condition', 'Value'])
			print(f'Default Win Conditions:\n{win_conditions}\n')
		while True:
			command = input('\nChoose your type of win conditions with the following commands:\npop, wealth, land, tech, time, capita, use, item, help, done\n')
			if command.lower() == 'pop':
				while True:
					try:
						pop = input(f'Enter the population to reach to win (Currently: {self.pop_win}) : ')
						if pop == '':
							break
						pop = int(pop)
					except ValueError:
						print('Not a valid entry. Must be a positive whole number.')
						continue
					else:
						if pop <= 0:
							continue
						break
				if self.pop_win == '':
					self.pop_win = None
				self.pop_win = pop
				print('Population win condition:', self.pop_win)
			elif command.lower() == 'wealth':
				while True:
					try:
						wealth = input(f'Enter the wealth required to win (Currently: {self.wealth_win}) : ')
						if wealth == '':
							break
						wealth = int(wealth)
					except ValueError:
						print('Not a valid entry. Must be a positive whole number.')
						continue
					else:
						if wealth <= 0:
							continue
						break
				if self.wealth_win == '':
					self.wealth_win = None
				self.wealth_win = wealth
				print('Wealth win condition:', self.wealth_win)
			elif command.lower() == 'capita':
				while True:
					try:
						capita = input(f'Enter the wealth per capita required to win (Currently: {self.wealth_capita_win}) : ')
						if capita == '':
							break
						capita = int(capita)
					except ValueError:
						print('Not a valid entry. Must be a positive whole number.')
						continue
					else:
						if capita <= 0:
							continue
						break
				if self.wealth_capita_win == '':
					self.wealth_capita_win = None
				self.wealth_capita_win = capita
				print('Wealth per Capita to win:', self.wealth_capita_win)
			elif command.lower() == 'land':
				while True:
					try:
						land = input(f'Enter the amount of land to control to win (Currently: {self.land_win}) : ')
						if land == '':
							break
						land = int(land)
					except ValueError:
						print('Not a valid entry. Must be a positive whole number.')
						continue
					else:
						if land <= 0:
							continue
						break
				if self.land_win == '':
					self.land_win = None
				self.land_win = land
				print('Land win condition:', self.land_win)
			elif command.lower() == 'tech':
				tech_list = self.items.loc[self.items['child_of'] == 'Technology']
				print('Technologies Available:\n {}'.format(tech_list.index.values))
				while True:
					tech = input(f'Enter the technology needed to achieve to win (Currently: {self.tech_win}) : ')
					if tech == '':
						break
					if not self.valid_item(tech, typ='Technology'):
						print('Not a valid entry. Must be a technology item name.')
						continue
					break
				self.tech_win = tech.title()
				print('Tech win condition:', self.tech_win)
			elif command.lower() == 'item':
				while True:
					item = input(f'Enter the item needed to obtain to win (Currently: {self.item_win}) : ')
					if item == '':
						break
					if not self.valid_item(item):
						print('Not a valid entry. Must be an item name.')
						continue
					break
				self.item_win = item.title()
				print('Item win condition:', self.item_win)
			elif command.lower() == 'use':
				while True:
					use_item = input(f'Enter the Equipment or Building needed to use to win (Currently: {self.use_win}) : ')
					if use_item == '':
						break
					if not self.valid_item(use_item, typ=['Equipment', 'Buildings']): # TODO Make this a list with Equipment and Buildings, need to update valid_item()
						print('Not a valid entry. Must be an Equipment item name.')
						continue
					break
				self.use_win = use_item.title()
				print('Use item win condition:', self.use_win)
			elif command.lower() == 'time':
				change_time = True
				if args.time is not None:
					change_time = input(f'The sim is already set to end in {args.time} days. Do you want to change it? [y/N]: ')
					if change_time == '':
						change_time = 'N'
					if change_time.upper() == 'Y':
						change_time = True
					elif change_time.upper() == 'N':
						change_time = False
					else:
						print('Not a valid entry. Must be "Y" or "N".')
						continue
				if change_time:
					while True:
						try:
							time = input(f'Enter the time limit in days for the sim (Currently: {args.time}) : ')
							if time == '':
								break
							time = int(time)
						except ValueError:
							print('Not a valid entry. Must be a positive whole number.')
							continue
						else:
							if time <= 0:
								continue
							break
					args.time = time
					if isinstance(args.time, int):
						END_DATE = (datetime.datetime(1986,10,1).date() + datetime.timedelta(days=args.time)).strftime('%Y-%m-%d')
				print('Sim will end on:', END_DATE)
			elif command.lower() == 'left':
				self.left_win = not self.left_win
				print('Last player left alive: ', self.left_win)
			elif command.lower() == 'win':
				win_conditions = { # TODO Don't duplicate this
					'Tech win condition: ': self.tech_win,
					'Population win condition: ': self.pop_win,
					'Wealth win condition: ': self.wealth_win,
					'Wealth per Capita to win: ': self.wealth_capita_win,
					'Land win condition: ': self.land_win,
					'Item win condition: ': self.item_win,
					'Use item win condition: ': self.use_win,
					'Last player left alive: ': self.left_win,
					'Sim will end on: ': END_DATE,
				}
				win_conditions = pd.DataFrame(win_conditions.items(), columns=['Win Condition', 'Value'])
				print(f'Current Win Conditions:\n{win_conditions}\n')
			elif command.lower() == 'help':
				commands = {
					'pop': 'Set the population needed to reach to win.',
					'wealth': 'Set the wealth needed to reach to win.',
					'capita': 'Set the wealth per capita needed to reach to win.',
					'land': 'Set the land needed to control to win.',
					'tech': 'Set the technology needed to achieve to win.',
					'item': 'Set the item needed to obtain to win.',
					'use': 'Set the item needed to use to win.',
					'time': ' Set the time limit of the sim.',
					'left': 'Set so the last player alive wins.',
					'win': 'View currently set win conditions.',
					'help': 'This table of commands.',
					'done': 'Finish setting win conditions',
				}
				cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
				with pd.option_context('display.max_colwidth', 300, 'display.colheader_justify', 'left'):
					print(cmd_table)
			elif command.lower() == 'done':
				break
			else:
				print(f'"{command}" is not a valid command. Type "done" to finish or "help" for more options.')
		win_conditions = { # TODO Don't duplicate this
			'Tech win condition: ': self.tech_win,
			'Population win condition: ': self.pop_win,
			'Wealth win condition: ': self.wealth_win,
			'Wealth per Capita to win: ': self.wealth_capita_win,
			'Land win condition: ': self.land_win,
			'Item win condition: ': self.item_win,
			'Use item win condition: ': self.use_win,
			'Last player left alive: ': self.left_win,
			'Sim will end on: ': END_DATE,
		}
		win_conditions = pd.DataFrame(win_conditions.items(), columns=['Win Condition', 'Value'])
		print(f'Final Win Conditions:\n{win_conditions}\n')
		for _, win_value in win_conditions['Value'].items():#.iteritems():
			if win_value:
				args.win = True
		return win_conditions

	def check_end(self, v=False):
		if self.end:
			# TODO Report the values if time runs out
			return self.end
		population = len(self.factory.registry[Individual])
		if v: print('Population: {}'.format(population))
		industry = len(self.factory.registry[Corporation])
		if v: print('Industry: {}'.format(industry))
		if args.win: # Win conditions
			if len(self.factory.get(Government)) == 1: # TODO If single gov or multi gov
				player_type = Individual
			else:
				player_type = Government
			for player in self.factory.get(player_type):
				if v: print(f'Checking win conditons for {player.name}.')
				if player.parents[0] is None and player.parents[1] is None:
					player.children = []
					player.entities = []
					# If single gov, for each founder get all entities controlled
					for entity in self.factory.get([Individual]):
						if len(self.factory.get(Government)) == 1:
							if entity.founder == player.founder:
								player.children.append(entity.entity_id)
						else:
							if entity.government == player.government:
								player.children.append(entity.entity_id)	
					for entity in self.factory.get([Corporation, NonProfit]):
						if len(self.factory.get(Government)) == 1:
							if entity.founder == player.founder:
								player.entities.append(entity.entity_id)
						else:
							if entity.government == player.government:
								player.children.append(entity.entity_id)
					player.entities += player.children
					if v: print(f'Children for {player.name}: {player.children}')
					if v: print(f'Entities for {player.name}: {player.entities}')
					# Population of a certain size
					if self.pop_win is not None:
						print(f'{player.name} population: {len(player.children)} / {self.pop_win}')
						if len(player.children) >= self.pop_win:
							self.end = True
					self.ledger.set_entity(player.entities)
					if self.wealth_win is not None or self.wealth_capita_win is not None:
						# Wealth of a certain amount
						player.total_nav = self.ledger.balance_sheet()#v=True)
						if self.wealth_win is not None:
							print(f'{player.name} wealth: {player.total_nav} / {self.wealth_win}')
							if player.total_nav >= self.wealth_win:
								self.end = True
						# Certain wealth per capita reached
						if self.wealth_capita_win is not None:
							player.wealth_per_capita = player.total_nav / len(player.children)
							print(f'{player.name} wealth per capita: {player.wealth_per_capita} / {self.wealth_capita_win}')
							if player.wealth_per_capita >= self.wealth_capita_win:
								self.end = True
					# Certain technology reached
					if self.tech_win is not None:
						tech_win_status = self.ledger.get_qty(self.tech_win)
						print(f'{player.name} final tech status: {tech_win_status} | {self.tech_win}')
						if tech_win_status > 0:
							self.end = True
					# Certain item obtained
					if self.item_win is not None:
						item_win_status = self.ledger.get_qty(self.item_win)
						print(f'{player.name} final item qty: {item_win_status} | {self.item_win}')
						if item_win_status > 0:
							self.end = True
					# Certain item used
					if self.use_win is not None:
						# Note: The item must have a usage depreciation metric but not a ticks metric
						use_win_status = self.ledger.get_qty(self.use_win)
						print(f'{player.name} final item qty: {use_win_status} | {self.use_win}')
						if use_win_status != 0:
							self.end = True
					# Land held of a certain amount
					if self.land_win is not None:
						land_types = self.items.loc[self.items['child_of'] == 'Land'].index.values.tolist()
						land_types.append('Land')
						land_held = self.ledger.get_qty(land_types)
						land_held = land_held['qty'].sum()
						print(f'{player.name} land held: {land_held} / {self.land_win}')
						if land_held >= self.land_win:
							self.end = True
					self.ledger.reset()
					if self.end:
						print(f'{player.name} has won!')
			# No other players alive
			if self.left_win:
				users = [entity for entity in self.factory.get(Individual) if entity.user]
				print(f'Players left: {len(users)} / {max(args.governments, args.population, args.users, args.players)}')
				if len(users) <= 1:
					self.end = True
		if END_DATE is not None: # Also for debugging
			days_left = datetime.datetime.strptime(END_DATE, '%Y-%m-%d').date() - self.now
			print(time_stamp() + f'Days left: {days_left.days}')
			if self.now == datetime.datetime.strptime(END_DATE, '%Y-%m-%d').date():
				self.end = True
		# Confirm if want to end sim, ability to keep playing save
		if population <= 0:
			print('Econ Sim ended due to human extinction.')
			self.end = True
		return self.end

	def edit_item(self, item=None, prpty=None, value=None, v=True):
		if item is None:
			while True:
				item = input('Enter an item: ')
				if item == '':
					return
				if self.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
		if v: print('{} properties: \n{}'.format(item.title(), self.items.loc[[item.title()]].squeeze()))
		if prpty is None:
			while True:
				prpty = input('Enter a property: ')
				if prpty == '':
					return
				if prpty in self.items.columns.values.tolist():
					break
				else:
					print('Not a valid entry.')
					continue
		value = input('Enter new value: ')
		self.items.loc[[item.title()], prpty] = value
		cur = self.ledger.conn.cursor()
		items_query = f'''
			UPDATE items
			SET {prpty} = ?
			WHERE item_id = ?;
		'''
		# print(items_query)
		values = (value, item.title())
		cur.execute(items_query, values)
		self.ledger.conn.commit()
		cur.close()
		# print(self.accts.get_items())
		return self.items

	def util(self, gl=None, save=False, v=True):
		# Function used to investigate the GL
		# save = True
		if v: print()
		if save is None:
			while True:
				save = input('Save? [Y/n]: ')
				if save == '':
					save = 'Y'
				if save.upper() == 'Y':
					save = True
					break
				elif save.upper() == 'N':
					save = False
					break
				else:
					print('Not a valid entry. Must be "Y" or "N".')
					continue
		if gl is None:
			gl = self.ledger.gl.copy(deep=True)
		hist_hours = self.hist_hours
		hist_hours['date'] = pd.to_datetime(hist_hours['date']).dt.strftime('%Y-%m-%d')
		# date_mask = hist_hours['date'] == '1986-10-01'
		# print(hist_hours['date'] == '1986-10-01')
		# print('date_mask:\n', date_mask)
		# to_drop = hist_hours[date_mask].head(args.population).index
		# print('to_drop:', to_drop)
		# hist_hours = hist_hours.drop(to_drop)
		hist_hours['total_hours'] = self.hist_hours.groupby('date')['hours'].transform('sum')
		try:
			hist_hours['total_Thirst'] = self.hist_hours.groupby('date')['Thirst'].transform('sum')
			hist_hours['total_Hunger'] = self.hist_hours.groupby('date')['Hunger'].transform('sum')
			hist_hours['total_Clothing'] = self.hist_hours.groupby('date')['Clothing'].transform('sum')
			hist_hours['total_Shelter'] = self.hist_hours.groupby('date')['Shelter'].transform('sum')
			hist_hours['total_Fun'] = self.hist_hours.groupby('date')['Fun'].transform('sum')
			hist_hours = hist_hours.drop(['hours', 'Thirst', 'Hunger', 'Clothing', 'Shelter', 'Fun'], axis=1)
		except KeyError as e:
			print(f'Util key error: {e}')
		hist_hours['max_hours'] = self.hist_hours['population'] * 12
		hist_hours['hours_used'] = hist_hours['max_hours'] - hist_hours['total_hours']
		hist_hours = hist_hours.drop_duplicates(subset='date')
		if v: print('hist_hours:\n', hist_hours)

		hist_demand = self.hist_demand
		hist_demand['date'] = pd.to_datetime(hist_demand['date']).dt.strftime('%Y-%m-%d')
		hist_demand['total_qty'] = self.hist_demand.groupby('date')['qty'].transform('sum')
		hist_demand = hist_demand.drop(['date_saved', 'entity_id', 'item_id', 'qty', 'reason'], axis=1)
		hist_demand = hist_demand.drop_duplicates(subset='date')
		if v: print('hist_demand:\n', hist_demand)

		gl = pd.merge(gl, hist_hours, on='date', how='left')
		gl = pd.merge(gl, hist_demand, on='date', how='left')
		self.set_table(gl, 'util')
		if v: print(f'util gl:\n{gl}')
		if save:
			# TODO Improve save name logic
			outfile = 'econ_util_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
			save_location = 'data/'
			try:
				gl.to_csv(save_location + outfile, date_format='%Y-%m-%d')
				print('File saved as ' + save_location + outfile)
			except Exception as e:
				print(f'Error saving: {e}')
		return gl

	def valid_corp(self, ticker):
		if not isinstance(ticker, str):
			return False
		ticker = ticker.title()
		tickers = []
		for index, producers in self.items['producer'].items():#.iteritems():
			if producers is not None:
				if isinstance(producers, str):
					producers = [x.strip() for x in producers.split(',')]
				producers = list(collections.OrderedDict.fromkeys(filter(None, producers)))
				tickers += producers
			else:
				if self.items.loc[index, 'child_of'] == 'Non-Profit' or self.items.loc[index, 'child_of'] == 'Governmental':
					tickers += [index]
		tickers = list(collections.OrderedDict.fromkeys(filter(None, tickers)))
		if ticker in tickers:
			return True
		else:
			return False

	def valid_item(self, item, typ=None):
		if not isinstance(item, str):
			return False
		item = item.title()
		if typ is None:
			if item in self.items.index:
				return True
			else:
				return False
		else:
			if not isinstance(typ, (list, tuple)):
				typ = [typ]
			items_typ = self.items.reset_index()
			items_typ['item_type'] = items_typ.apply(lambda x: x['item_id'] if x['child_of'] is None else self.get_item_type(x['item_id']), axis=1)
			items_typ = items_typ.loc[items_typ['item_type'].isin(typ)]
			# print(f'Items Typ: {item} | {typ}')# \n{item_typ}')
			if item in items_typ['item_id'].values:
				return True
			else:
				return False

	def valid_need(self, need):
		if not isinstance(need, str):
			return False
		need = need.title()
		if need in self.global_needs:
			return True
		else:
			return False

	def get_item_type_old(self, item): # TODO Delete this
		try:
			if self.items.loc[item, 'child_of'] is None:
				return item
			else:
				return self.get_item_type(self.items.loc[item, 'child_of'])
		except IndexError as e:
			return self.get_item_type(self.items_map.loc[item, 'child_of'])

	def get_item_type(self, item, level=None, count=0):
		if level is not None:
			if count >= level:
				return item
		count += 1
		try:
			if self.items.loc[item, 'child_of'] is None:
				return item
			else:
				return self.get_item_type(self.items.loc[item, 'child_of'], level, count)
		except IndexError as e:
			return self.get_item_type(self.items_map.loc[item, 'child_of'], level, count)

	def org_type(self, name):
		if name == 'Government':
			return Government
		elif name == 'Governmental':
			return Governmental
		elif name == 'Non-Profit':
			return NonProfit
		else:
			try:
				return self.org_type(self.items.loc[name, 'child_of'])
			except KeyError:
				return Corporation

	def toggle_user(self, target=None):
		if target is None:
			for entity in self.factory.get(Individual):
				print('{} | User: {}'.format(entity, entity.user))
			for entity in self.factory.get(Government):
				print('{} | User: {}'.format(entity, entity.user))
			while True:
				try:
					selection = input('Enter an entity ID number of an Individual or Government to toggle whether it is user controlled: ')
					if selection == '':
						return
					selection = int(selection)
				except ValueError:
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, self.factory.get([Individual, Government], ids=True)))
					continue
				if selection not in self.factory.get([Individual, Government], ids=True):
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, self.factory.get([Individual, Government], ids=True)))
					continue
				target = self.factory.get_by_id(selection)
				break
		target.user = not target.user
		if isinstance(target, Government):
			for citizen in target.get(Individual):
				if not citizen.user:
					citizen.user = not citizen.user
				else:
					if not target.user:
						citizen.user = not citizen.user
		# TODO Update entities table in db
		return target

	def get_price(self, item, entity_id=None):
		# if not isinstance(entity_id, int) and entity_id is not None:
		# if not np.issubdtype(entity_id, np.integer) and entity_id is not None:
		if isinstance(entity_id, Entity):
			entity_id = entity_id.entity_id # Incase an entity object is passed instead
		new = False
		try:
			current_prices = self.prices.loc[item]
			if isinstance(current_prices, pd.Series):
				current_prices = current_prices.to_frame().transpose()
			#print('Item Prices: \n{}'.format(current_prices))
		except KeyError as e:
			new = True
		if entity_id and not new:
			#print('Entity: {}'.format(entity_id))
			current_prices = current_prices.loc[current_prices['entity_id'] == entity_id]
			if current_prices.empty:
				# Add price for that entity if it doesn't exist yet
				new = True
				# cur_price = self.get_price(item)
				# new_price = pd.DataFrame({'entity_id': [entity_id], 'item_id': [item],'price': [cur_price]}).set_index('item_id')
				# self.prices = self.prices.append(new_price)
				# print('After appending: \n{}'.format(new_price))
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	print(self.prices)
				# self.set_table(self.prices, 'prices')
				# return cur_price
		if entity_id and new:
			if entity_id == world.env.entity_id:
				cur_price = 0.0
			else:
				cur_price = self.get_price(item)
			new_price = pd.DataFrame({'entity_id': [entity_id], 'item_id': [item],'price': [cur_price]}).set_index('item_id')
			# self.prices = self.prices.append(new_price)
			self.prices = pd.concat([self.prices, new_price])
			# print('After appending: \n{}'.format(new_price))
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print(self.prices)
			# self.prices = self.prices.sort_values(['item_id'])
			self.set_table(self.prices, 'prices')
			return cur_price
		if new: # Base case
			# Get optional default start price in items data
			price = self.items.loc[item, 'start_price']
			if price is not None:
				price = float(price)
				print(f'{item} has a default start price of: {price}')
				return price

			item_type = world.get_item_type(item)
			if item_type in ['Education', 'Technology'] or item == 'Study' or item == 'Research':
				return 0.0
			print(f'No price seen for {item} yet. Will use global default: {INIT_PRICE}')
			return INIT_PRICE
		#print('Current Prices: \n{}'.format(current_prices))
		price = current_prices['price'].min()
		# print('Price for {}: {}'.format(item, price))
		return price

	def reduce_prices(self, v=False):
		# world.prices['price'] = world.prices['price'] * (1 - REDUCE_PRICE)#).clip(lower=0.01)
		world.prices['price'] = world.prices['price'].where(world.prices['price'] == 0, (world.prices['price'] * (1 - REDUCE_PRICE)).clip(lower=0.01)).round(2)
		if v: print(world.prices)
		print('All prices reduced by {0:.0%}.'.format(REDUCE_PRICE))
		return world.prices

	def create_needs(self):
		global_needs = []
		print(self.items['satisfies'])
		for _, item_satifies in self.items['satisfies'].items():#.iteritems():
			if item_satifies is None:
				continue
			item_needs = [x.strip() for x in item_satifies.split(',')]
			global_needs += item_needs
		global_needs = list(collections.OrderedDict.fromkeys(global_needs))
		global_needs = self.needs_analysis(global_needs)
		print('Global Needs: \n{}'.format(global_needs))
		return global_needs

	def needs_analysis(self, needs):
		global_needs = {}
		for need in needs:
			items_info = self.items[self.items['satisfies'].str.contains(need, na=False)]
			items_info['item_type'] = items_info.apply(lambda x: self.get_item_type(x.name), axis=1)
			if ((items_info['item_type'] == 'Commodity') | (items_info['item_type'] == 'Subscription') | (items_info['item_type'] == 'Service')).all():
				global_needs[need] = 'consumption'
			else:
				global_needs[need] = 'capital'
		return global_needs

	def update_econ(self):
		self.t1_start = time.perf_counter()
		if not self.active_day:
			if str(self.now) == str(self.ledger.gl['date'].min()):
				# TODO Consider a better way to do this
				# for individual in self.factory.get(Individual):
					# capital = args.capital / self.population
					# individual.capitalize(amount=capital)#25000 # Hardcoded
				for gov in self.factory.get(Government):
					self.gov = gov
					if args.jones:
						self.gov.bank.print_money(1000000)
					else:
						self.gov.bank.print_money(args.capital)
					for individual in self.gov.get(Individual):
						self.start_capital = args.capital / self.population
						individual.loan(amount=self.start_capital, roundup=False)
						if args.jones:
							individual.start_items(['Casual Clothes', 'Low Cost Apartment'])
				self.gov = self.factory.get(Government)[0]
				print('Start Government: {}'.format(self.gov))
				if args.jones:
					for business in self.businesses:
						gov.incorporate(name=business)

					self.ledger.set_entity(self.gov.bank.entity_id)
					bank_cash = self.ledger.balance_sheet(['Cash'])
					self.ledger.reset()
					print('Central Bank Cash:', bank_cash)

				self.checkpoint_entry(eod=False, save=True)

			# Save prior days tables: entities, prices, demand, delay, produce_queue
			self.prior_entities = self.entities
			self.set_table(self.prior_entities, 'prior_entities')
			self.prior_prices = self.prices
			self.set_table(self.prior_prices, 'prior_prices')
			self.prior_demand = self.demand
			self.set_table(self.prior_demand, 'prior_demand')
			self.prior_delay = self.delay
			self.set_table(self.prior_delay, 'prior_delay')
			self.prior_produce_queue = self.produce_queue
			self.set_table(self.prior_produce_queue, 'prior_produce_queue')

			if self.check_end(v=False):
				keep_playing = False
				for entity in self.factory.get():
					if entity.user:
						while True:
							keep_playing = input('Do you want to continue playing? [Y/n]: ')
							if keep_playing == '':
								keep_playing = 'Y'
							if keep_playing.upper() == 'Y':
								keep_playing = True
								break
							elif keep_playing.upper() == 'N':
								keep_playing = False
								break
							else:
								print('Not a valid entry. Must be "Y" or "N".')
								continue
					if keep_playing:
						self.end = False
						break
				if not keep_playing:
					return

			print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Econ Updated ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))
			print(time_stamp() + 'Current Date 01: {}'.format(self.now))
			self.entities = self.accts.get_entities().reset_index()
			#prices_disp = self.entities[['entity_id','name']].merge(self.prices.reset_index(), on=['entity_id']).set_index('item_id')
			self.population = len(self.factory.registry[Individual])
			self.industry = len(self.factory.registry[Corporation])
			self.governments = len(self.factory.registry[Government])
			print('Population: {}'.format(self.population))
			print('Industry: {}'.format(self.industry))
			print('Governments: {}'.format(self.governments))
			for individual in self.factory.get(Individual):
				individual.reset_hours()
			self.prices = self.prices.sort_values(['entity_id'], na_position='first')
			with pd.option_context('display.max_rows', None):
				print('\nPrices: \n{}\n'.format(self.prices))
				print('Technology: \n{}\n'.format(self.tech))
				print('Delays: \n{}\n'.format(self.delay))
				print('Auto: \n{}\n'.format(self.produce_queue))

			self.set_table(self.tech, 'tech')
			demand_items = self.demand.drop_duplicates(['item_id']) # TODO Is this needed?
			self.set_table(self.demand, 'demand')

			for individual in self.factory.get(Individual):
				individual.birth_check()

			print(time_stamp() + 'Current Date 02: {}'.format(self.now))
			t3_start = time.perf_counter()
			for entity in self.factory.get():
				#print('Entity: {}'.format(entity))
				t3_1_start = time.perf_counter()
				entity.depreciation_check()
				t3_1_end = time.perf_counter()
				print(time_stamp() + '3.1: Dep check took {:,.2f} sec for {}.'.format((t3_1_end - t3_1_start), entity.name, entity.entity_id))
				if not entity.user:
					t3_2_start = time.perf_counter()
					entity.repay_loans()
					t3_2_end = time.perf_counter()
					print(time_stamp() + '3.2: Dbt check took {:,.2f} sec for {}.'.format((t3_2_end - t3_2_start), entity.name, entity.entity_id))
				t3_3_start = time.perf_counter()
				entity.check_interest()
				t3_3_end = time.perf_counter()
				print(time_stamp() + '3.3: Int check took {:,.2f} sec for {}.'.format((t3_3_end - t3_3_start), entity.name, entity.entity_id))
				t3_4_start = time.perf_counter()
				entity.check_subscriptions()
				t3_4_end = time.perf_counter()
				print(time_stamp() + '3.4: Sub check took {:,.2f} sec for {}.'.format((t3_4_end - t3_4_start), entity.name, entity.entity_id))
				t3_5_start = time.perf_counter()
				entity.check_salary()
				t3_5_end = time.perf_counter()
				print(time_stamp() + '3.5: Sal check took {:,.2f} sec for {}.'.format((t3_5_end - t3_5_start), entity.name, entity.entity_id))
				t3_6_start = time.perf_counter()
				entity.pay_wages()
				t3_6_end = time.perf_counter()
				print(time_stamp() + '3.6: Wag check took {:,.2f} sec for {}.'.format((t3_6_end - t3_6_start), entity.name, entity.entity_id))
				# if not entity.user:
				# 	t3_7_start = time.perf_counter()
				# 	entity.wip_check()
				# 	t3_7_end = time.perf_counter()
				# 	print(time_stamp() + '3.7: WIP check took {:,.2f} sec for {}.'.format((t3_7_end - t3_7_start), entity.name, entity.entity_id))
				if isinstance(entity, Corporation):
					t3_7_start = time.perf_counter()
					if args.jones: # TODO Handle this better
						entity.maintain_inv()
					t3_7_end = time.perf_counter()
					print(time_stamp() + '3.7: Inv check took {:,.2f} sec for {}.'.format((t3_7_end - t3_7_start), entity.name, entity.entity_id)) # TODO This is very slow
			t3_end = time.perf_counter()
			print(time_stamp() + '3: Entity check took {:,.2f} min.'.format((t3_end - t3_start) / 60))
			print()

		# User mode
		self.active_day = False
		user_check = any([entity for entity in self.factory.get() if entity.user])
		if user_check or self.paused:
			for player in self.factory.get(Government):
				print('~' * DISPLAY_WIDTH)
				print(time_stamp() + 'Current Date: {}'.format(self.now))
				indv_player_check = any([e.user for e in player.get(Individual)])
				if not player.user and not indv_player_check:
					print()
					print(time_stamp() + '{} is a computer user.'.format(player.name))
					continue
				elif player.user:
					print('Player: {}'.format(player.name))
				else:
					print('Government: {}'.format(player.name))
				# print('Citizen Entities: \n{}'.format(player.get(envs=False)))
				self.selection = None
				if player.user:
					self.ledger.default = player.get(ids=True)
					print('Ledger default set to: {}'.format(self.ledger.default))
				self.ledger.reset()
				self.gov = player
				# print('Checking player auto produce queue.')
				# for entity in player.get():
				# 	entity.auto_produce()
				world.get_hours(v=True)
				while True:#sum(self.get_hours(computers=False).values()) > 0:
					if self.selection is None:
						user_entities = player.get(Individual, computers=False)
						if user_entities:
							user_entities = [e for e in user_entities if e.hours != 0]
							if not user_entities:
								break
							self.selection = user_entities[0]
							if USE_PIN:
								while True:
									try:
										pin = getpass.getpass('Enter the 4 digit pin number for {} or enter "exit": '.format(self.selection.name))
										if pin.lower() == 'exit':
											exit()
										pin = int(pin)
									except ValueError:
										print('Not a valid entry. Must be a 4 digit number.')
										continue
									else:
										if len(str(pin)) != 4 or int(pin) < 0:
											print('Not a valid entry. Must be a 4 digit number.')
											continue
										elif self.selection.pin == pin:
											break
						else:
							print('Not entities with hours left.')
							break
						if not self.selection.saved:
							self.selection.auto_produce()
							self.selection.wip_check(time_only=not self.selection.auto_wip)
					if isinstance(self.selection, Individual):
						print('\nEntity Selected: {} | Hours: {}'.format(self.selection.name, self.selection.hours))
					else:
						print('\nEntity Selected: {}'.format(self.selection))
					if isinstance(self.selection, Individual):
						if not self.selection.hours and self.selection.auto_done:
							result = self.selection.action('done')
						else:
							result = self.selection.action()
					else:
						result = self.selection.action()
					if self.selection is not None and isinstance(self.selection, Individual):
						if self.selection.hours == 0:
							# print('\nEntity Selected: {} | Hours: {}'.format(self.selection.name, self.selection.hours))
							print('Enter "done" to end turn. Or "autodone" to automatically end turn.')
					if result == 'end':
						break
			self.ledger.default = None
			if self.paused:
				self.paused = not self.paused
			print()

		# Computer mode
		print(time_stamp() + 'Current Date 03: {}'.format(self.now))
		print(time_stamp() + 'Checking if corporations are needed for items demanded.')
		t2_start = time.perf_counter()
		# for individual in self.factory.get(Individual, users=False):
		# 	print('Individual: {} | {}'.format(individual.name, individual.entity_id))
		# 	for need in individual.needs:
		# 		#print('Need: {}'.format(need))
		# 		individual.corp_needed(need=need)
		# 		individual.item_demanded(need=need)
		# 	for index, item in demand_items.iterrows():
		# 		#print('Corp Check Demand Item: {}'.format(item['item_id']))
		# 		individual.corp_needed(item=item['item_id'], demand_index=index)

		print()
		with pd.option_context('display.max_rows', None):
			print('World Demand Start: \n{}'.format(world.demand))
		print()
		if not world.demand.empty:
			individuals = itertools.cycle(self.factory.get(Individual, users=False))
			for index, item in world.demand.iterrows():
				# corp = None
				# while corp is None: # Too slow
				try:
					individual = next(individuals)
				except StopIteration:
					break
				print('Individual: {} | Hours: {} | Corp Check for Item: {}'.format(individual.name, individual.hours, item['item_id']))
				corp = individual.corp_needed(item=item['item_id'], qty=item['qty'], demand_index=index)

		t2_end = time.perf_counter()
		print(time_stamp() + '2: Corp needed check took {:,.2f} min.'.format((t2_end - t2_start) / 60))

		print()
		print(time_stamp() + 'Current Date 04: {}'.format(self.now))
		t4_start = time.perf_counter()
		print(time_stamp() + 'Check Demand List:')
		for entity in self.factory.get(users=False):
			t4_1_start = time.perf_counter()
			print(time_stamp() + 'Current Date 04.1 for {}: {}'.format(entity.name, self.now))
			#print('\nDemand check for: {} | {}'.format(entity.name, entity.entity_id))
			# entity.set_price() # TODO Is this needed?
			entity.auto_produce()
			t4_1_end = time.perf_counter()
			print(time_stamp() + '4.1: Demand list; auto check took {:,.2f} sec for {}.\n'.format(t4_1_end - t4_1_start, entity.name))
			if self.end_turn(check_hrs=True, user_check=user_check): return
			# if isinstance(entity, Individual):
			# 	entity.needs_decay()
			# 	if entity.dead:
			# 		continue
			if isinstance(entity, Individual) and not entity.user:
				print(time_stamp() + 'Current Date 04.2 for {}: {}'.format(entity.name, self.now))
				t4_2_start = time.perf_counter()
				# if str(self.now) == str(self.ledger.gl['date'].min()):
				# 	priority = False
				# else:
				# 	priority = True
				entity.address_needs(priority=True, method='consumption', v=args.verbose)
				t4_2_end = time.perf_counter()
				print(time_stamp() + '4.2: Demand list; address needs consumption 1 check took {:,.2f} sec for {}.\n'.format(t4_2_end - t4_2_start, entity.name))
				if self.end_turn(check_hrs=True, user_check=user_check): return
				print(time_stamp() + 'Current Date 04.3 for {}: {}'.format(entity.name, self.now))
				t4_3_start = time.perf_counter()
				entity.address_needs(method='capital', v=args.verbose)
				t4_3_end = time.perf_counter()
				print(time_stamp() + '4.3: Demand list; address needs capital check took {:,.2f} sec for {}.\n'.format(t4_3_end - t4_3_start, entity.name))
				if self.end_turn(check_hrs=True, user_check=user_check): return
				# print('{} {} need at: {}'.format(entity.name, need, entity.needs[need]['Current Need']))
			print(time_stamp() + 'Current Date 04.4 for {}: {}'.format(entity.name, self.now))
			t4_4_start = time.perf_counter()
			entity.check_demand(multi=True, others=not isinstance(entity, Individual), needs_only=True, v=args.verbose)
			t4_4_end = time.perf_counter()
			print(time_stamp() + '4.4: Demand list; needs check took {:,.2f} min for {}.\n'.format(t4_4_end - t4_4_start, entity.name))
			if self.end_turn(check_hrs=True, user_check=user_check): return
			if isinstance(entity, Individual) and not entity.user:
				print(time_stamp() + 'Current Date 04.5 for {}: {}'.format(entity.name, self.now))
				t4_5_start = time.perf_counter()
				entity.address_needs(obtain=False, priority=False, method='consumption', v=args.verbose)
				t4_5_end = time.perf_counter()
				print(time_stamp() + '4.5: Demand list; address needs consumption 2 check took {:,.2f} sec for {}.\n'.format(t4_5_end - t4_5_start, entity.name))
				if self.end_turn(check_hrs=True, user_check=user_check): return
			

		for entity in self.factory.get(users=False):
			print(time_stamp() + 'Current Date 04.6 for {}: {}'.format(entity.name, self.now))
			t4_6_start = time.perf_counter()
			print(time_stamp() + f'WIP List Check for: {entity.name}')
			entity.wip_check()
			t4_6_end = time.perf_counter()
			print(time_stamp() + '4.6: Demand list; WIP check took {:,.2f} sec for {}.\n'.format(t4_6_end - t4_6_start, entity.name))
			if self.end_turn(check_hrs=True, user_check=user_check): return

		for entity in self.factory.get(users=False):
			print(time_stamp() + f'Demand List Check for: {entity.name}')
			i = 0
			while True:
				i += 1
				print(time_stamp() + f'Current Date 04.7 for {entity.name}: {self.now} | Loop: {i}')
				t4_7_start = time.perf_counter()
				# if self.end_turn(check_hrs=True, user_check=user_check): return
				hours = self.get_hours(total=True)
				if hours < 1:
					print(f'Total entity hours: {hours}')
					break
				tmp_demand = world.demand
				# with pd.option_context('display.max_rows', None):
				# 	print(f'tmp_demand repr: \n{repr(tmp_demand)}')
				# 	print(f' world.demand repr: \n{repr(world.demand)}')
				entity.check_demand(multi=True, others=not isinstance(entity, Individual), v=args.verbose)
				t4_7_end = time.perf_counter()
				print(time_stamp() + '4.7: Demand list; loop check took {:,.2f} sec for {}.\n'.format(t4_7_end - t4_7_start, entity.name))
				# print(f'Demand equals: {tmp_demand.equals(world.demand)}')
				if isinstance(entity, Individual) and not entity.user: # TODO Is the user guard needed?
					if entity.hours == 0:
						print(f'{entity.name} has no hours left to check demand list.')
						break
				if tmp_demand.equals(world.demand):
					print(time_stamp() + f'No change in demand for: {entity.name}')
					break
			if isinstance(entity, Individual) and not entity.user:
				print(time_stamp() + 'Current Date 04.8 for {}: {}'.format(entity.name, self.now))
				t4_8_start = time.perf_counter()
				entity.address_needs(obtain=False, v=args.verbose)
				t4_8_end = time.perf_counter()
				print(time_stamp() + '4.8: Demand list; address needs 3 check took {:,.2f} sec for {}.\n'.format(t4_8_end - t4_8_start, entity.name))
			print(time_stamp() + 'Current Date 04.9 for {}: {}'.format(entity.name, self.now))
			t4_9_start = time.perf_counter()
			entity.check_inv()
			if self.end_turn(check_hrs=True, user_check=user_check): return
			entity.tech_motivation()
			t4_9_end = time.perf_counter()
			print(time_stamp() + '4.9: Demand list; inv and tech check took {:,.2f} sec for {}.\n'.format(t4_9_end - t4_9_start, entity.name))

		t4_end = time.perf_counter()
		print(time_stamp() + '4: Demand list check took {:,.2f} min.\n'.format((t4_end - t4_start) / 60))
		print()

		print(time_stamp() + 'Current Date 05: {}'.format(self.now))
		t5_start = time.perf_counter()
		print('Check Optional Items:')
		for entity in self.factory.get(users=False):#(Corporation):
			print('\nOptional check for: {} | {}'.format(entity.name, entity.entity_id))
			entity.check_optional(v=args.verbose)
			entity.check_inv()
			if self.end_turn(check_hrs=True, user_check=user_check): return
			# entity.tech_motivation()
			if isinstance(entity, Corporation):
				# entity.list_shareholders(largest=True)
				entity.dividend()
		t5_end = time.perf_counter()
		print(time_stamp() + '5: Optional check took {:,.2f} min.\n'.format((t5_end - t5_start) / 60))
		print()

		self.end_turn(check_hrs=False)

	def end_turn(self, check_hrs=False, user_check=None):
		end = False
		if check_hrs:
			if not args.early:
				return
			if user_check:
				return
		if check_hrs and self.get_hours(total=True) != 0:
			return
		if check_hrs and self.get_hours(total=True) == 0:
			print(time_stamp() + 'Turn ending early because all hours are used up.\n\n')
			end = True
		# User and computer mode
		print(time_stamp() + 'Current Date 06: {}'.format(self.now))
		t6_start = time.perf_counter()
		print('Check Prices:')
		# for entity in self.factory.get():
		# 	print('\nPrices check for: {}'.format(entity.name))
			# entity.check_prices()
		# for _ in range(world.population):
		world.reduce_prices()
		t6_end = time.perf_counter()
		print(time_stamp() + '6: Prices check took {:,.2f} sec.'.format(t6_end - t6_start))
		print()

		print(time_stamp() + 'Current Date 07: {}'.format(self.now))
		t7_start = time.perf_counter()
		for individual in self.factory.get(Individual):
			# priority_needs = {} # TODO Clean this up with address_needs()
			# for need in individual.needs:
			# 	priority_needs[need] = individual.needs[need]['Current Need']
			# priority_needs = {k: v for k, v in sorted(priority_needs.items(), key=lambda item: item[1])}
			# priority_needs = collections.OrderedDict(priority_needs)
			# for need in priority_needs:
				#print('Individual Name: {} | {}'.format(individual.name, individual.entity_id))
				# if not individual.user:
				# 	individual.threshold_check(need, priority=True)
					# individual.address_need(need, priority=True)
				# print('{} {} need at: {}'.format(individual.name, need, individual.needs[need]['Current Need']))
			individual.needs_decay()
			if individual.dead:
				break
		t7_end = time.perf_counter()
		print(time_stamp() + '7: Needs decay took {:,.2f} min.'.format((t7_end - t7_start) / 60))
		print()

		print(time_stamp() + 'Current Date 08: {}'.format(self.now))
		t8_start = time.perf_counter()
		for typ in self.factory.registry.keys():
			for entity in self.factory.get(typ):
				entity.release_check()#v=True)
		print()
		self.get_hours(v=True)
		print()
		world.unused_land(all_land=True)
		print()
		for typ in self.factory.registry.keys():
			for entity in self.factory.get(typ):
				if isinstance(entity, Corporation): # TODO Temp fix for negative balances
					entity.negative_bal()
				self.ledger.set_entity(entity.entity_id)
				entity.cash = self.ledger.balance_sheet(['Cash'])
				print('{} Cash: {}'.format(entity.name, entity.cash))
				self.ledger.reset()
			print()
			for entity in self.factory.get(typ):
				self.ledger.set_entity(entity.entity_id)
				entity.nav = self.ledger.balance_sheet()
				print('{} NAV: {}'.format(entity.name, entity.nav))
				self.ledger.reset()

			# TODO Add a way to see the NAV and Cash for the country, which is different than the gov. It would be all the entities of the gov consolidated

			# To switch things up
			if len(self.factory.registry[typ]) != 0 and typ != Environment and typ != Government and typ != Bank:
				print('\nPre Entity Sort by NAV: {} \n{}'.format(typ, self.factory.registry[typ]))
				self.factory.registry[typ].sort(key=lambda x: x.nav)
				print('Post Entity Sort by NAV: {} \n{}\n'.format(typ, self.factory.registry[typ]))
				# if args.random:
				# 	print('\nPre Entity Shuffle: {} \n{}'.format(typ, self.factory.registry[typ]))
				# 	random.shuffle(self.factory.registry[typ])
				# 	print('Post Entity Shuffle: {} \n{}\n'.format(typ, self.factory.registry[typ]))
				# else:
				# 	lst = self.factory.get(typ)
				# 	lst.append(lst.pop(0))

		t8_end = time.perf_counter()
		print(time_stamp() + '8: Cash check took {:,.2f} sec.'.format(t8_end - t8_start))
		print()

		t9_start = time.perf_counter()
		# for individual in self.factory.registry[Individual]:#[::-1]:
		# 	print('{} | Hours: {}'.format(individual, individual.hours))
		# 	if individual.hours == MAX_HOURS:
		# 		print('Last Individual with full time left: {}'.format(individual))
		# 		break
		# individual = self.factory.registry[Individual][-1]
		# individual = [e for e in self.factory.registry[Individual] if not e.user]

		if args.random and not (args.users >= 1 or args.players >= 1): # TODO Maybe add population target
			# TODO Add (args.random or args.births) switch
			individuals = world.gov.get(Individual, users=False)
			for individual in individuals:
				birth_roll = random.randint(1, 20)
				print('Birth Roll for {}: {}'.format(individual.name, birth_roll))
				if birth_roll == 20:
					individual.birth()

		# if args.random:
		# 	death_roll = random.randint(1, 40)
		# 	print('Death Roll: {}'.format(death_roll))
		# 	if death_roll == 40:# or (str(self.now) == '1986-10-03'):
		# 		print('{} randomly dies!'.format(individual.name))
		# 		individual.set_need('Hunger', -100, forced=True)

		print()
		print(time_stamp() + 'Current Date 09: {}'.format(self.now))
		print()
		with pd.option_context('display.max_rows', None):
			print('World Demand End: \n{}'.format(world.demand))
		print()
		self.entities = self.accts.get_entities().reset_index()
		self.inventory = self.ledger.get_qty(items=None, accounts=['Inventory','Equipment','Buildings','Equipment In Use', 'Buildings In Use', 'Equipped'], show_zeros=False, by_entity=True)
		self.inventory = self.entities[['entity_id','name']].merge(self.inventory, on=['entity_id'])
		with pd.option_context('display.max_rows', None):
			print('Global Items: \n{}'.format(self.inventory))
		print()
		t9_end = time.perf_counter()
		print(time_stamp() + '9: Birth check and reporting took {:,.2f} min.'.format((t9_end - t9_start) / 60))

		self.checkpoint_entry()
		self.t1_end = time.perf_counter()
		print('\n' + time_stamp() + 'End of Econ Update for {}. It took {:,.2f} min.'.format(self.now, (self.t1_end - self.t1_start) / 60))
		self.ticktock(v=False) # TODO User
		return end

		# # Book End of Day entry
		# eod_entry = [ self.ledger.get_event(), 0, 0, world.now, '', 'End of day entry', '', '', '', 'Info', 'End of Day', 0 ]
		# self.ledger.journal_entry([eod_entry])
		# # Track historical prices
		# tmp_prices = self.prices.reset_index()
		# tmp_prices['date'] = self.now
		# self.hist_prices = pd.concat([self.hist_prices, tmp_prices])
		# # self.hist_prices = self.hist_prices.dropna()
		# self.set_table(self.hist_prices, 'hist_prices')
		# # Track historical demand
		# tmp_demand = self.demand.copy(deep=True)#.reset_index()
		# tmp_demand['date_saved'] = self.now
		# self.hist_demand = pd.concat([self.hist_demand, tmp_demand])
		# self.set_table(self.hist_demand, 'hist_demand')
		# # print('\nHist Demand: \n{}'.format(self.hist_demand))
		# # Track historical hours and needs
		# self.entities = self.accts.get_entities()
		# # print('Entities: \n{}'.format(self.entities))
		# tmp_hist_hours = self.entities.loc[self.entities['entity_type'] == 'Individual'].reset_index()
		# tmp_hist_hours = tmp_hist_hours[['entity_id','hours']].set_index(['entity_id'])
		# tmp_hist_hours['date'] = self.now
		# tmp_hist_hours = tmp_hist_hours[['date','hours']]
		# for need in self.global_needs:
		# 	tmp_hist_hours[need] = None
		# for individual in self.factory.get(Individual):
		# 	for need in individual.needs:
		# 		tmp_hist_hours.at[individual.entity_id, need] = individual.needs[need].get('Current Need')
		# self.hist_hours = pd.concat([self.hist_hours, tmp_hist_hours])
		# self.set_table(self.hist_hours, 'hist_hours')
		# # print('\nHist Hours: \n{}'.format(self.hist_hours))

		# # print('\nItems Map: \n{}'.format(self.items_map))

	def handle_events(self):
		self.paused = False
		while True:
			# events = pygame.event.get()
			for event in events:
				print('Event: {} | Type: {}'.format(event, event.type))
				if event.type == KEYDOWN:
					if event.key == K_SPACE:
						self.paused = not self.paused
					elif event.key == K_ESCAPE:
						exit()
			if self.paused:
				# time.sleep(0.1)
				return
			else:
				return

	def checkpoint_entry(self, eod=True, save=False, v=False):
		entities = self.accts.get_entities()
		if v: print('Entities: \n{}'.format(entities))
		if v: print()
		cur = self.ledger.conn.cursor()
		obj_query = '''
			UPDATE entities
			SET obj = ?
			WHERE entity_id = ?;
		'''
		for entity in self.factory.get():
			# print('before del')
			# print(entity)
			# print(entity.__dict__)
			# print('repr1')
			# print(repr(entity))
			# tmp_entity = entity.__dict__.copy()
			# print('repr2')
			# print(repr(tmp_entity))
			# if tmp_entity.get('accts'):
			# 	tmp_entity.pop('accts')
			# if tmp_entity.get('ledger'):
			# 	tmp_entity.pop('ledger')
			# if tmp_entity.get('factory'):
			# 	tmp_entity.pop('factory')
			# print('repr3')
			# print(repr(tmp_entity))
			# print('after del')
			# print(entity)
			# print(entity.__dict__)
			# print('new obj')
			# print(tmp_entity)
			# Save and strip references
			if v: print()
			# print(f'attr before: {entity.__dict__}')
			accts = entity.__dict__.pop('accts', None)
			ledger = entity.__dict__.pop('ledger', None)
			factory = entity.__dict__.pop('factory', None)
			bank = entity.__dict__.pop('bank', None)

			try:
				if v: print(f'pickleing: {entity} | repr: {repr(entity)}')
				# if v: print(f'attr: {entity.__dict__}')
				entity_data = pickle.dumps(entity, pickle.HIGHEST_PROTOCOL)
				# if v: print(f'entity_data: {entity_data}')
				values = (Binary(entity_data), entity.entity_id)
				if v: print('pickle values:', values)
			except TypeError as e:
				if v: print(f'Save error on entity: {entity.name} | error: {e}')
				values = (None, entity.entity_id)
				if v: print('pickle values err:', values)
			finally:
				# Restore references
				if accts:
					entity.accts = accts
				if ledger:
					entity.ledger = ledger
				if factory:
					entity.factory = factory
				if bank:
					entity.bank = bank
			cur.execute(obj_query, values)
		self.ledger.conn.commit()
		cur.close()
		# Book End of Day entry
		if self.selection is None:
			entity_id = 1
		else:
			entity_id = self.selection.entity_id
		if eod:
			eod_entry = [ self.ledger.get_event(), 0, 0, self.now, '', 'End of day entry', '', '', '', 'Info', 'End of Day', 0 ]
			self.ledger.journal_entry([eod_entry])
		elif save:
			save_entry = [ self.ledger.get_event(), entity_id, entity_id, self.now, '', 'Save point entry', '', '', '', 'Info', 'Save', 0 ]
			self.ledger.journal_entry([save_entry])
		else:
			eot_entry = [ self.ledger.get_event(), entity_id, entity_id, self.now, '', 'End of turn entry', '', '', '', 'Info', 'End of Turn', 0 ]
			self.ledger.journal_entry([eot_entry])
		if eod:
			# Track historical prices
			tmp_prices = self.prices.reset_index()
			tmp_prices['date'] = self.now
			self.hist_prices = pd.concat([self.hist_prices, tmp_prices])
			self.set_table(self.hist_prices, 'hist_prices')
			# Track historical demand
			tmp_demand = self.demand.copy(deep=True)
			tmp_demand['date_saved'] = self.now
			self.hist_demand = pd.concat([self.hist_demand, tmp_demand])
			self.set_table(self.hist_demand, 'hist_demand')
			# if v: print('\nHist Demand: \n{}'.format(self.hist_demand))
			# Track historical hours and needs
			self.entities = self.accts.get_entities().reset_index()
			# if v: print('Entities: \n{}'.format(self.entities))
			tmp_hist_hours = self.entities.loc[self.entities['entity_type'] == 'Individual'].reset_index()
			tmp_hist_hours = tmp_hist_hours[['entity_id','hours']].set_index(['entity_id']) # TODO Does this need to be set as the index?
			tmp_hist_hours['date'] = self.now
			tmp_hist_hours = tmp_hist_hours[['date','hours']]
			tmp_hist_hours['population'] = len(self.factory.registry[Individual])
			for need in self.global_needs:
				tmp_hist_hours[need] = None
			for individual in self.factory.get(Individual):
				for need in individual.needs:
					tmp_hist_hours.at[individual.entity_id, need] = individual.needs[need].get('Current Need')
			tmp_hist_hours = tmp_hist_hours.reset_index()
			tmp_hist_hours = tmp_hist_hours.rename(columns={'index': 'entity_id'})
			self.hist_hours = pd.concat([self.hist_hours, tmp_hist_hours])
			self.set_table(self.hist_hours, 'hist_hours')
			# if v: print('\nHist Hours: \n{}'.format(self.hist_hours))
		else:
			# Save prior days tables: entities, prices, demand, delay, produce_queue
			self.entities = self.accts.get_entities().reset_index()
			self.prior_entities = self.entities
			self.set_table(self.prior_entities, 'prior_entities')
			self.prior_prices = self.prices
			self.set_table(self.prior_prices, 'prior_prices')
			self.prior_demand = self.demand
			self.set_table(self.prior_demand, 'prior_demand')
			self.prior_delay = self.delay
			self.set_table(self.prior_delay, 'prior_delay')
			self.prior_produce_queue = self.produce_queue
			self.set_table(self.prior_produce_queue, 'prior_produce_queue')
		self.util(save=False)


class Entity:
	def __init__(self, name):# Entity
		self.name = name
		self.accts = EntityFactory.get_accts()
		self.ledger = EntityFactory.get_ledger()  # Access shared Ledger
		self.factory = EntityFactory.get_factory()
		#print('Entity created: {}'.format(name))
		# TODO Move government here for inheritance and overwrite in subclasses as needed, such as Government

	def adj_price(self, item, qty=1, rate=None, direction=None):
		if rate is None:
			if direction == 'up':
				rate = 1.1 #1.01
			elif direction == 'down':
				rate = 0.9 #0.99
			elif direction == 'up_low':
				rate = 1.02 #1.002
			elif direction == 'up_very_low':
				rate = 1.0002 # 1.02 #1.002
			elif direction == 'down_high':
				rate = 0.8 #0.98
			else:
				rate = 1.1 #1.01
		producer_count = world.prices.loc[(world.prices.index == item)].shape[0]
		if producer_count > 1 and (direction == 'down' or direction == 'down_high'):
			price = self.match_price(item)
			if price is not None:
				return price
		if item == self.name:
			print('{} cannot get a price for shares of {}.'.format(self.name, item))
			return 1 # TODO Fix how prices for corporate entities work. Could have a price column on the entities table
		price = world.get_price(item, self.entity_id)
		orig_price = price
		item_type = world.get_item_type(item)
		if item_type in ['Technology','Education'] or isinstance(self, Environment):
			if price != 0:
				world.prices.at[item, 'price'] = 0
				print('{} sets price for {} from {} to {}.'.format(self.name, item, price, 0))
			return
		# print('{} price before adjustment: {}'.format(item, price))
		#qty = int(math.ceil(qty / 10)) # To reduce the number of times the loop runs
		#for _ in range(int(math.ceil(qty))):
		price = price * rate
		if price < 0.01:
			price = 0.01
		price = round(price, 2)
		# Remove old price values from world prices, separately update entity item prices, then append updated values to end of world prices
		#print('Item: {}'.format(item))
		if isinstance(self, Environment):
			price = 0
		entity_prices = world.prices.loc[world.prices['entity_id'] == self.entity_id]
		#print('Entity Prices Before: \n{}'.format(entity_prices))
		try:
			target_item = entity_prices.loc[item]
			#print('Target Item: \n{}'.format(target_item))
		except KeyError as e: # TODO Handle this better
			#print('Error Catch: {} | {}'.format(e, repr(e)))
			new_row = pd.DataFrame({'entity_id': self.entity_id, 'price': INIT_PRICE}, [item])#.set_index('item_id')
			#print('New Row: \n{}'.format(new_row))
			# entity_prices = entity_prices.append(new_row)
			entity_prices = pd.concat([entity_prices, new_row])

		#print('Entity Prices Mid: \n{}'.format(entity_prices))
		entity_prices.at[item, 'price'] = price
		#print('Entity Prices After: \n{}'.format(entity_prices))
		world.prices = world.prices.loc[world.prices['entity_id'] != self.entity_id]
		world.prices = pd.concat([world.prices, entity_prices]) # TODO Handle this better
		#world.prices.at[item, 'price'] = price # Old method
		print('{} adjusts {} price by a rate of {} from ${} to ${}.'.format(self.name, item, rate, orig_price, price))
		world.set_table(world.prices, 'prices')
		return price

	def set_price(self, item=None, qty=0, price=None, markup=0.1, at_cost=False, v=True):
		if item is None: # TODO Look into why this is called in update_econ()
			if self.produces is None:
				if v: print('{} produces no items.'.format(self.name))
				return
			for item in self.produces:
				price = world.get_price(item, self.entity_id)
				item_type = world.get_item_type(item)
				if item_type in ['Technology','Education'] or isinstance(self, Environment): # TODO Maybe support creating types of land like planting trees to make forest
					if price != 0:
						# world.prices.at[item, 'price'] = 0
						price = 0
						world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = price
						#print('{} sets price for {} from {} to {}.'.format(self.name, item, price, 0))
					return
				cost = 0
				self.ledger.set_entity(self.entity_id)
				cost_entries = self.ledger.gl.loc[(self.ledger.gl['item_id'] == item) & (self.ledger.gl['credit_acct'] == 'Cost Pool')]
				if not cost_entries.empty:
					cost_entries.sort_values(by=['date'], ascending=False, inplace=True)
					#print('Cost Entries: \n{}'.format(cost_entries))
					cost = cost_entries.iloc[0]['price']
				qty_held = self.ledger.get_qty(items=item, accounts=['Inventory'])
				#print('Qty held by {} when setting price for {}: {}'.format(self.name, item, qty_held))
				self.ledger.reset()
				#print('{}\'s current price for {}: {}'.format(self.name, item, price))
				if price < cost and qty_held <= qty:
					if at_cost:
						world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost
						if v: print('{} sets price for {} from {} to cost at {}.'.format(self.name, item, price, cost))
					else:
						world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost * (1 + markup)
					if v: print('{} sets price for {} from {} to {}.'.format(self.name, item, price, cost * (1 + markup)))
		else:
			if price is not None:
				orig_price = world.get_price(item, self.entity_id)
				# world.prices.at[item, 'price'] = price
				world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = price
				if v: print('{} manually sets price for {} from {} to {}.'.format(self.name, item, orig_price, price))
				return
			price = world.get_price(item, self.entity_id)
			item_type = world.get_item_type(item)
			if item_type in ['Technology','Education'] or isinstance(self, Environment): # TODO Maybe support creating types of land like planting trees to make forest
				if price != 0:
					# world.prices.at[item, 'price'] = 0
					price = 0
					world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = price
					#print('{} sets price for {} from {} to {}.'.format(self.name, item, price, 0))
				return
			cost = 0
			self.ledger.set_entity(self.entity_id)
			cost_entries = self.ledger.gl.loc[(self.ledger.gl['item_id'] == item) & (self.ledger.gl['credit_acct'] == 'Cost Pool')]
			if not cost_entries.empty:
				cost_entries.sort_values(by=['date'], ascending=False, inplace=True)
				#print('Cost Entries: \n{}'.format(cost_entries))
				cost = cost_entries.iloc[0]['price']
			qty_held = self.ledger.get_qty(items=item, accounts=['Inventory'])
			if v: print('Qty held by {} when setting price for {}: {}'.format(self.name, item, qty_held))
			self.ledger.reset()
			if v: print('{}\'s current price for {}: {}'.format(self.name, item, price))
			if price < cost and qty_held <= qty:
				if at_cost:
					world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost
					if v: print('{} sets price for {} from {} to cost at {}.'.format(self.name, item, price, cost))
				else:
					world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost * (1 + markup)
					if v: print('{} sets price for {} from {} to {}.'.format(self.name, item, price, cost * (1 + markup)))
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	print(world.prices)
		world.set_table(world.prices, 'prices')

	def match_price(self, item):
		orig_price = world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price']
		if orig_price.empty:
			return
		orig_price = orig_price.values[0]
		# TODO Maybe get all entities carrying or producing the item
		low_price = world.prices.loc[(world.prices.index == item), 'price'].min()
		if low_price < orig_price:
			world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = low_price
			print('{} matches price for {} from {} to {}.'.format(self.name, item, orig_price, low_price))
			world.set_table(world.prices, 'prices')
			return low_price

	def transact(self, item, price, qty, counterparty, acct_buy='Inventory', acct_sell='Inventory', acct_rev='Sales', desc_pur=None, desc_sell=None, item_type=None, cash_used=0, buffer=False, v=True):
		if qty == 0:
			return [], False
		purchase_event = []
		cost = False
		quirk = ''
		if item_type == 'Education':
			quirk = ' education service'
		if desc_pur is None:
			desc_pur = item + quirk + ' purchased'
		if desc_sell is None:
			desc_sell = 'Sale of ' + item + quirk
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		cash -= cash_used
		#print('Cash: {}'.format(cash))
		self.ledger.set_entity(counterparty.entity_id)
		qty_avail = self.ledger.get_qty(items=item, accounts=[acct_sell])
		# if item_type == 'Education': # TODO This causes issue
		# 	qty_avail = abs(qty_avail)
		if item_type != 'Service' and item_type != 'Education': # TODO Handle Services better
			if v: print('Qty Available to purchase from {}: {}'.format(counterparty.name, qty_avail))
		self.ledger.reset()
		if cash >= (qty * price) or counterparty.entity_id == self.entity_id:
			#print('Transact Item Type: {}'.format(item_type))
			qty_possible = qty
		else:
			try:
				qty_possible = math.floor(cash / price) # Will buy what can be afforded
			except ZeroDivisionError as e:
				qty_possible = qty
			if qty_possible != 0 and price != 0:
				if v: print('{} does not have enough cash to purchase {} units of {} for {} each. Cash: {} | Qty Possible: {}'.format(self.name, qty, item, price, cash, qty_possible))
		if qty_possible != 0:
			qty = qty_possible
			if qty > qty_avail or item_type == 'Service' or item_type == 'Education': # Will buy what is available
				if item_type != 'Service' and item_type != 'Education': # TODO Combine this with above if stmt?
					qty = qty_avail
				if qty_avail != 0:
					if v: print('{} does not have enough {} on hand to sell {} units of {}. Will sell qty on hand: {}'.format(self.name, item, qty, item, qty_avail))
			if ((qty <= qty_avail and qty_avail != 0) or item_type == 'Service' or item_type == 'Education'):
				amount = round(price * qty, 2)
				if item_type is not None and item_type != 'Service' and item_type != 'Education':
					if v: print('{} transacted with {} for {} {}'.format(self.name, counterparty.name, qty, item))
					self.ledger.set_entity(counterparty.entity_id)
					if v: print('{} getting historical cost of {} {}.'.format(counterparty.name, qty, item))
					cost_amt = self.ledger.hist_cost(qty, item, 'Inventory')#, v=True)
					#print('Cost: {}'.format(cost_amt))
					self.ledger.reset()
					purchase_event += counterparty.release(item, qty=qty) # TODO Needs to be tested further
					avg_price = cost_amt / qty
					cogs_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', desc_sell, item, avg_price, qty, 'Cost of Goods Sold', acct_sell, cost_amt ]
					
					sale_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', desc_sell, item, price, qty, 'Cash', acct_rev, amount ]
					purchase_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', desc_pur, item, price, qty, acct_buy, 'Cash', amount ]
					purchase_event += [cogs_entry, sale_entry, purchase_entry]
					# if buffer:
					# 	counterparty.adj_price(item, qty, direction='up')
					# 	return purchase_event, cost
					# self.ledger.journal_entry(purchase_event)
					counterparty.adj_price(item, qty, direction='up')
					return purchase_event, cost
				else:
					if item_type is None:
						if v: print('{} transacted with {} for {} {} shares.'.format(self.name, counterparty.name, qty, item))
					sell_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', desc_sell, item, price, qty, 'Cash', acct_sell, amount ]
					purchase_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', desc_pur, item, price, qty, acct_buy, 'Cash', amount ]
					purchase_event += [sell_entry, purchase_entry]
					# if buffer:
					# 	counterparty.adj_price(item, qty, direction='up')
					# 	return purchase_event, cost
					# self.ledger.journal_entry(purchase_event)
					counterparty.adj_price(item, qty, direction='up')
					return purchase_event, cost
			else:
				if v: print('{} does not have enough {} on hand to sell {} units of {}. Qty on hand: {}'.format(self.name, item, qty, item, qty_avail))
				return purchase_event, cost
		else:
			# qty_possible = math.floor(cash / price)
			if v: print('{} does not have enough cash to purchase {} units of {} for {} each. Cash: {} | Qty Possible: {}'.format(self.name, qty, item, price, cash, qty_possible))
			if not self.user:
				cost = True
				result = self.loan(amount=((qty * price) - cash), item='Credit Line 5', auto=True)
				if result:
					purchase_event, cost = self.transact(item, price, qty, counterparty, acct_buy=acct_buy, acct_sell=acct_sell, acct_rev=acct_rev, desc_pur=desc_pur, desc_sell=desc_sell, item_type=item_type, buffer=buffer, v=v)
				if result is False:
					self.bankruptcy()
				# counterparty.adj_price(item, qty, direction='down')
			return purchase_event, cost

	def purchase(self, item, qty, acct_buy=None, acct_sell='Inventory', acct_rev='Sales', wip_acct='WIP Inventory', priority=False, reason_need=False, buffer=False, v=True):
		# TODO Clean up
		if qty == 0:
			return
		qty = int(math.ceil(qty))
		qty_wanted = qty
		# TODO Add support for purchasing from multiple entities
		outcome = None
		item_type = world.get_item_type(item)
		if acct_buy is None:
			if item_type == 'Equipment':
				acct_buy = 'Equipment'
			elif item_type == 'Buildings':
				acct_buy = 'Buildings'
			elif item_type == 'Land':
				acct_buy = 'Land'
			else:
				acct_buy = 'Inventory'
		if item_type == 'Service' or item_type == 'Education':
			# Check if producer exists and get their ID
			# TODO Support multiple of the same producer
			# TODO Handle this better with a dumby journal entry
			producers = world.items.loc[item, 'producer']
			if isinstance(producers, str):
				producers = [x.strip() for x in producers.split(',')]
			# producers = list(set(filter(None, producers)))
			producers = list(collections.OrderedDict.fromkeys(filter(None, producers)))
			producer_entities = []
			for producer in producers:
				for entity in world.gov.get(): # TODO Allow trading with other govs
					if producer == entity.name.split('-')[0]:
						producer_entities.append(entity.entity_id)
			serv_prices = {k:world.get_price(item, k) for k in producer_entities}
			quirk = ''
			if not serv_prices:
				if item_type == 'Education':
					quirk = ' education'
				else:
					quirk = ''
				if item_type == 'Education' and 'Individual' in producers and isinstance(self, Individual):
					counterparty = self
				elif args.jones:
					counterparty = self.factory.get_by_name('Hi-Tech U', generic=True)
				elif self.user:
					entities = world.gov.get(computers=True, ids=True, envs=False)
					while True:
						try:
							selection = input('Enter an entity ID number to purchase the {}{} service from: '.format(item, quirk))
							# if selection == '':
							# 	return
							selection = int(selection)
						except ValueError:
							print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, entities))
							continue
						if selection not in entities:
							print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, entities))
							continue
						counterparty = self.factory.get_by_id(selection)
						break
				else:
					if v: print('No {} to offer {}{} service. Will add it to the demand table by {}.'.format(', '.join(producers), item, quirk, self.name))
					self.item_demanded(item, qty, priority=priority, reason_need=reason_need, v=v)
					return
			else:
				counterparty_id = min(serv_prices, key=lambda k: serv_prices[k])
				counterparty = self.factory.get_by_id(counterparty_id)
			if counterparty is None:
				if v: print('No {} to offer {}{} service. Will add it to the demand table for {}.'.format(', '.join(producers), item, quirk, self.name))
				self.item_demanded(item, qty, priority=priority, reason_need=reason_need, v=v)
				return
			if v: print('{} chooses {} for the {}{} service counterparty.'.format(self.name, counterparty.name, item, quirk))
			if item_type == 'Service':
				acct_buy = 'Service Expense'
				acct_sell = 'Service Revenue'
			elif item_type == 'Education':
				acct_buy = 'Education Expense'
				acct_sell = 'Education Revenue'
		elif item_type == 'Subscription':
			if v: print(f'Ordering a Subscription for {item}.')
			result = self.order_subscription(item, qty=qty, v=v)
			return result
		self.ledger.reset()
		# TODO Consider if want to purchase none inventory assets by replacing Inventory below with acct_buy
		global_inv = self.ledger.get_qty(item, ['Inventory'], by_entity=True)#, v=True)
		prices_tmp = world.prices.reset_index()
		# print('prices_tmp:', prices_tmp)
		prices_tmp.rename(columns={'index': 'item_id'}, inplace=True)
		global_inv = global_inv.merge(prices_tmp, on=['entity_id','item_id'])
		global_inv.sort_values(by=['price'], ascending=True, inplace=True)
		# print('Global purchase inventory for: {} \n{}'.format(item, global_inv))
		if item_type in ['Commodity', 'Components']:
			global_inv = global_inv.loc[global_inv['entity_id'] != self.entity_id]
		if self.entity_id in global_inv['entity_id'].values:
			if global_inv.shape[0] >= 2:
				if v: print('Global Purchase Inventory reordered for {}: \n{}'.format(item, global_inv))
			n = global_inv.loc[global_inv['entity_id'] == self.entity_id].index[0]
			if v: print('Self purchase index for {}: {}'.format(self.name, n))
			# global_inv = pd.concat([global_inv.iloc[[n],:], global_inv.drop(n, axis=0)], axis=0)
			global_inv['new'] = range(1, len(global_inv) + 1)
			global_inv.at[n,'new'] = 0
			global_inv = global_inv.sort_values('new').drop('new', axis=1)
		if global_inv.shape[0] >= 2:
			if v: print('Global Purchase Inventory for {}: \n{}'.format(item, global_inv))
		if global_inv.empty:
			global_qty = 0
		else:
			global_qty = global_inv['qty'].sum()
		wip_global_qty = self.ledger.get_qty(items=item, accounts=wip_acct)
		if v: print('{} wants to purchase {} {} | Available for sale: {} | WIP: {}'.format(self.name, qty, item, global_qty, wip_global_qty))

		# Check which entity has the goods for the cheapest
		if item_type == 'Service':
			if v: print('{} trying to purchase Service: {}'.format(self.name, item))
			result, time_required, max_qty_possible, incomplete = counterparty.produce(item, qty, buffer=buffer, v=v)
			#print('Service purchase produce result: \n{}'.format(result))
			if not result:
				return
			try:
				self.adj_needs(item, qty)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				pass
			outcome, cost = self.transact(item, price=world.get_price(item, counterparty.entity_id), qty=qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=buffer, v=v)
			if outcome is None:
				outcome = []
			result += outcome
		elif item_type == 'Education':
			outcome, cost = self.transact(item, price=world.get_price(item, counterparty.entity_id), qty=qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=True, v=v)
			if outcome is None:
				outcome = []
			return outcome
		else:
			i = 0
			result = []
			cost = False
			purchased_qty = 0
			cash_used = 0
			while qty > 0:
				#print('Purchase Qty Loop: {} | {}'.format(qty, i))
				try:
					purchase_qty = global_inv.iloc[i].loc['qty']
				except IndexError as e:
					if v: print('No other entities hold {} to purchase the remaining qty of {}.'.format(item, qty))
					break
				if purchase_qty > qty:
					purchase_qty = qty
				counterparty_id = global_inv.iloc[i].loc['entity_id']
				#print('Counterparty ID: {}'.format(counterparty_id))
				counterparty = self.factory.get_by_id(counterparty_id)
				#print('Purchase Counterparty: {}'.format(counterparty.name))
				if counterparty.entity_id == self.entity_id:
					if v: print('{} attempting to transact with themselves for {} {}.'.format(self.name, purchase_qty, item))
					if item_type == 'Land':
						if v: print(f'Land acct_buy before: {acct_buy}')
						acct_buy = 'Land'
					price = 0
					self.ledger.set_entity(self.entity_id)
					cost_entries = self.ledger.gl.loc[(self.ledger.gl['item_id'] == item) & (self.ledger.gl['credit_acct'] == 'Cost Pool')]
					if not cost_entries.empty:
						cost_entries.sort_values(by=['date'], ascending=False, inplace=True)
						#print('Cost Entries: \n{}'.format(cost_entries))
						price = cost_entries.iloc[0]['price']
					self.ledger.reset()
					#return
				else:
					price = world.get_price(item, counterparty.entity_id)
				#print('Purchase QTY: {}'.format(purchase_qty))
				# Check if able to hold item
				incomplete, in_use_event, time_required, max_qty_possible = self.fulfill(item, qty=purchase_qty, reqs='hold_req', amts='hold_amount', v=v)
				if incomplete:
					if v: print('{} cannot purchase {} {} because it does not meet the requirements to hold it.'.format(self.name, purchase_qty, item))
					break
				result += in_use_event
				result_tmp, cost = self.transact(item, price=price, qty=purchase_qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, cash_used=cash_used, buffer=buffer, v=v)
				if not result_tmp:
					break
				if counterparty.entity_id != self.entity_id:
					cash_used += result_tmp[-1][-1]
				result += result_tmp
				purchased_qty += purchase_qty
				qty -= purchase_qty
				i += 1
			if qty_wanted > purchased_qty and item_type != 'Land':
				qty_wanted = max(qty_wanted - wip_global_qty, 0)
				if qty_wanted > 0:
					if cost:
						#self.item_demanded(item, qty_wanted - purchased_qty, cost=cost, priority=priority, v=v)
						pass
					else:
						qty_demanded = max(qty_wanted - purchased_qty, 0)
						self.item_demanded(item, qty_demanded, priority=priority, reason_need=reason_need, v=v)
		# if v: print('Purchase Result: {} {} \n{}'.format(qty, item, result))
		if buffer:
			return result
		else:
			self.ledger.journal_entry(result)
		return result

	def sale(self, item, qty, v=True):
		if qty == 0:
			return
		item_type = world.get_item_type(item)
		if item_type not in ['Land', 'Buildings', 'Equipment']:
			if v: print('{} is a {} which cannot be put up for sale.'.format(item, item_type))
			return
		# Put item up for sale
		self.ledger.set_entity(self.entity_id)
		qty_on_hand = self.ledger.get_qty(items=item, accounts=[item_type])
		self.ledger.reset()
		if v: print('{} has {} {} on hand.'.format(self.name, qty, item))
		if qty_on_hand >= qty:
			self.ledger.set_entity(self.entity_id)
			if v: print('{} getting historical cost of {} {}.'.format(self.name, qty, item))
			cost_amt = self.ledger.hist_cost(qty, item, item_type)#, v=True)
			self.ledger.reset()
			price = round(cost_amt / qty, 2)
			sale_entry = [ self.ledger.get_event(), self.entity_id, self.entity_id, world.now, '', f'Put {item} up for sale', item, price, qty, 'Inventory', item_type, cost_amt ]
			sale_event = [sale_entry]
			self.ledger.journal_entry(sale_event)
		else:
			if v: print('{} does not have {} {} to put up for sale. Qty on hand: {}'.format(self.name, qty, item, qty_on_hand))

	def check_sale(self, thresh=1, v=True):
		self.ledger.set_entity(self.entity_id)
		items_on_hand = self.ledger.get_qty(accounts=['Equipment'])
		self.ledger.reset()
		if v: print('items_on_hand:', items_on_hand)
		for _, item in items_on_hand.iterrows():
			if item['qty'] > tresh:
				self.sale(self, item['item_id'], item['qty'] - tresh)

	def gift(self, item, qty, counterparty, account=None):
		gift_event = []
		if item == 'Cash':
			price = 1
			# TODO Check if enough cash
			self.ledger.set_entity(self.entity_id)
			cash = self.ledger.balance_sheet(['Cash'])
			self.ledger.reset()
			if cash >= price * qty:
				giftee_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Cash gift received from {}'.format(self.name), '', '', '', 'Cash', 'Gift', price * qty ]
				giftor_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Cash gift given to {}'.format(counterparty.name), '', '', '', 'Gift Expense', 'Cash', price * qty ]
				gift_event += [giftee_entry, giftor_entry]
				self.ledger.journal_entry(gift_event)
			else:
				print('{} does not have enough cash to gift ${} to {}. Cash: {}'.format(self.name, qty, counterparty.name, cash))
		else:
			# TODO Fix accounting to not be at cost
			price = 1
			if account is None:
				account = 'Inventory' # TODO Support other accounts
			self.ledger.set_entity(self.entity_id)
			qty_held = self.ledger.get_qty(item, account)
			self.ledger.reset()
			if qty_held >= qty:
				incomplete, in_use_event, time_required, max_qty_possible = counterparty.fulfill(item, qty=qty, reqs='hold_req', amts='hold_amount')
				gift_event += in_use_event
				if incomplete:
					print('{} does not have the ability to receive {} {} as a gift from {}.'.format(counterparty.name, qty, item, self.name))
					return
				self.ledger.set_entity(self.entity_id)
				print('{} getting historical cost of {} {} to gift.'.format(self.name, qty, item))
				cost_amt = self.ledger.hist_cost(qty, item, 'Inventory')#, v=True)
				self.ledger.reset()
				giftee_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Gift received from {}'.format(self.name), item, cost_amt / qty, qty, account, 'Gift', cost_amt ]
				giftor_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Gift given to {}'.format(counterparty.name), item, cost_amt / qty, qty, 'Gift Expense', account, cost_amt ]
				gift_event += [giftee_entry, giftor_entry]
				self.ledger.journal_entry(gift_event)
			else:
				print('{} does not have enough {} to gift {} units to {}.'.format(self.name, item, qty, counterparty.name))

	def release(self, item=None, qty=1, event_id=None, reqs='hold_req', amts='hold_amount', v=False):
		if v: print('{} release for {} x {}.'.format(self.name, item, qty))
		release_event = []
		if item is not None:
			item_info = world.items.loc[item]
			# reqs = 'requirements' #'usage_req' #
			# amts = 'amount' #'use_amount' #
			if item_info[reqs] is None or item_info[amts] is None:
				return release_event
			requirements = [x.strip() for x in item_info[reqs].split(',')]
			req_types = [world.get_item_type(x) for x in requirements] # TODO This check might not be needed anymore
			if v: print('Requirement types for {}: {}'.format(item, req_types))
			if not any(x in req_types for x in ['Land', 'Buildings', 'Equipment']):
				# if v: print('No Land, Buildings, or Equipment required for {}.'.format(item))
				return release_event
			# freq = item_info['freq']
			# if freq is None:
			# 	freq = []
			# 'animal' not in item_info['freq'] and
		self.ledger.set_entity(self.entity_id)
		if event_id is None:
			try:
				event_ids = self.ledger.hist_cost(qty, item, acct='Inventory', event_id=True)
			except IndexError as e:
				item_type = world.get_item_type(item)
				event_ids = self.ledger.hist_cost(qty, item, acct=item_type, event_id=True)
			if event_ids.empty:
				return release_event
			if v: print('event_ids:\n', event_ids)
		else:
			if isinstance(event_id, int):
				event_ids = pd.DataFrame({'price':[0], 'qty':[qty], 'avail_qty':[qty], 'event_id':[event_id]}, index=None)
				if v: print('event_id given:\n', event_ids)
		for _, row in event_ids.iterrows():
			proportion = 1
			event_id = row['event_id']
			if row['qty'] < row['avail_qty']: # TODO Test this
				print('Release qty for event_id {}: {}'.format(event_id, row['qty']))
				print('Release avail_qty for event_id {}: {}'.format(event_id, row['avail_qty']))
				proportion = row['qty'] / row['avail_qty']
				print('Release proportion for event_id {}: {}'.format(event_id, proportion))
			if v: print('in_use event_id:', event_id)
			rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			# if v: print('RVSL TXNs:\n{}'.format(rvsl_txns))
			release_txns = self.ledger.gl[(self.ledger.gl['credit_acct'].str.contains('In Use', na=False)) & (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['event_id'] == event_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))] # TODO Is this needed?
			if v: print('Release TXNs:\n{}'.format(release_txns))
			in_use_txns = self.ledger.gl[(self.ledger.gl['debit_acct'].str.contains('In Use', na=False)) & (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['event_id'] == event_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
			if v: print('All In Use TXNs:\n{}'.format(in_use_txns))

			# Check for Events with WIP in debit but not in credit and exclude those
			wip_in_use_txns = self.ledger.gl[(self.ledger.gl['debit_acct'].str.contains('WIP', na=False)) & (~self.ledger.gl['credit_acct'].str.contains('WIP', na=False)) & (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['event_id'] == event_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
			if v: print('All WIP In Use TXNs:\n{}'.format(wip_in_use_txns))
			wip_in_use_txns_cr = self.ledger.gl[(~self.ledger.gl['debit_acct'].str.contains('WIP', na=False)) & (self.ledger.gl['credit_acct'].str.contains('WIP', na=False)) & (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['event_id'] == event_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
			if v: print('WIP In Use TXNs Cr:\n{}'.format(wip_in_use_txns_cr))
			wip_in_use_txns = wip_in_use_txns[~(wip_in_use_txns['event_id'].isin(wip_in_use_txns_cr['event_id']))]
			if v: print('WIP In Use TXNs:\n{}'.format(wip_in_use_txns))
			in_use_txns = in_use_txns[~(in_use_txns['event_id'].isin(wip_in_use_txns['event_id']))]
			if v: print('In Use TXNs:\n{}'.format(in_use_txns))

			matches = []
			for _, in_use_txn in in_use_txns.iterrows():
				match = False
				for _, release_txn in release_txns.iterrows():
					if release_txn.index in matches:
						continue
					if in_use_txn['qty'] == release_txn['qty'] and in_use_txn['item_id'] == release_txn['item_id']:
						matches.append(release_txn.index)
						match = True
						break
				if match:
					continue
				# Check to ensure not releasing more than currently held
				if v: print('in_use acct: {}'.format(in_use_txn['debit_acct']))
				qty_held = self.ledger.get_qty(in_use_txn['item_id'], in_use_txn['debit_acct'])
				amount_held = self.ledger.balance_sheet(in_use_txn['debit_acct'], in_use_txn['item_id'])
				if qty_held < in_use_txn['qty']:
					print('{} only has {} {} instead of {}.'.format(self.name, qty_held, in_use_txn['item_id'], in_use_txn['qty']))
					qty = qty_held
				else:
					qty = in_use_txn['qty']
				if qty_held == 0:
					continue
				if amount_held < in_use_txn['amount']:
					print('{} only has {} {} balance instead of {}.'.format(self.name, amount_held, in_use_txn['item_id'], in_use_txn['amount']))
					amount = amount_held
				else:
					amount = in_use_txn['amount']
				if proportion != 1:
					print('{} qty before proportion: {}'.format(in_use_txn['item_id'], qty))
				qty = int(round(qty * proportion, 0))
				release_entry = [ in_use_txn['event_id'], in_use_txn['entity_id'], in_use_txn['cp_id'], world.now, in_use_txn['loc'], in_use_txn['item_id'] + ' released', in_use_txn['item_id'], in_use_txn['price'], qty, in_use_txn['credit_acct'], in_use_txn['debit_acct'], amount_held ]
				release_event += [release_entry]
		self.ledger.reset()
		if v: print('final release event: {}'.format(release_event))
		if v: print(f'final hold_event_ids for {self.name}:', self.hold_event_ids)
		return release_event

	def consume(self, item, qty, need=None, buffer=False, v=True):
		# TODO Test release Land and Buildings
		consume_event = []
		if qty == 0:
			return consume_event
		self.ledger.set_entity(self.entity_id)
		qty_held = self.ledger.get_qty(items=item, accounts=['Inventory'])#, v=True)
		self.ledger.reset()
		# if isinstance(qty_held, pd.DataFrame):
		# 	qty_held = qty_held['qty'].sum()
		if v: print('{} holds {} qty of {} and is looking to consume {} units.'.format(self.name, qty_held, item, qty))
		if qty_held >= qty:
			if v: print('{} consumes: {} {}'.format(self.name, qty, item))
			consume_event += self.release(item, qty=qty)
			self.ledger.set_entity(self.entity_id)
			if v: print('{} getting historical cost of {} {}.'.format(self.name, qty, item))
			cost = self.ledger.hist_cost(qty, item, 'Inventory')#, v=True)
			self.ledger.reset()
			#print('Cost: {}'.format(cost))
			price = cost / qty
			consume_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', item + ' consumed', item, price, qty, 'Goods Consumed', 'Inventory', cost ]
			consume_event += [consume_entry]
			if buffer:
				return consume_event
			self.ledger.journal_entry(consume_event)
			self.adj_needs(item, qty) # TODO Add error checking
			return consume_event
		else:
			if v: print('{} does not have enough {} on hand to consume {} units of {}.'.format(self.name, item, qty, item))
			return consume_event

	def in_use(self, item, qty=1, price=None, account=None, buffer=False, v=False):
		if v: print('{} setting {} {} to be in use. Price: {} | Account: {}'.format(self.name, qty, item, price, account))
		if account is None:
			account = world.get_item_type(item)
		self.ledger.set_entity(self.entity_id)
		try: # TODO Make this nicer
			if not self.gl_tmp.empty:
				self.ledger.gl = self.gl_tmp[(self.gl_tmp['entity_id'] == self.entity_id)]
				# print('gl_tmp:\n{}'.format(self.ledger.gl.tail()))
		except AttributeError as e:
			self.gl_tmp = pd.DataFrame(columns=world.cols)
			# print('In Use Error: {}'.format(repr(e)))
		qty_held = self.ledger.get_qty(items=item, accounts=[account], v=v)
		self.ledger.reset()
		if qty_held >= qty:# or buffer:
			if price is None:
				self.ledger.set_entity(self.entity_id)
				amount = self.ledger.hist_cost(qty=qty, item=item, acct=account)
				self.ledger.reset()
				price = amount / qty
			else:
				amount = price * qty
			in_use_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', item + ' in use', item, price, qty, account + ' In Use', account, amount ]
			in_use_event = [in_use_entry]
			if buffer:
				return in_use_event
			self.ledger.journal_entry(in_use_event)
			try:
				self.adj_needs(item, qty)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				return True
		else:
			print('{} does not have enough {} available to use {} units. Qty held: {}'.format(self.name, item, qty, qty_held))

	# entries = self.in_use(req_item, req_qty * (1-modifier) * qty, price=price, buffer=True)

	def use_item(self, item, uses=1, counterparty=None, target=None, buffer=False, check=False):
		# usable = world.items.loc[item, 'metric']
		# if not usable:
		# 	print('{} is not usable. {}'.format(item, usable))
		# 	return []
		# elif 'usage' not in usable: # TODO This does not work with Water Well
		# 	print('{} is not usable. {}'.format(item, usable))
		# 	return []

		# check to ensure entity has item they are using. And if attacking making sure it is equipped
		# item_type = world.get_item_type(item)
		self.ledger.set_entity(self.entity_id)
		item_qty = self.ledger.get_qty(accounts=['Equipment', 'Equipment In Use', 'Equipped', 'Buildings', 'Buildings In Use'], items=item)
		self.ledger.reset()
		if item_qty == 0:
			if counterparty is None:
				print('{} does not have {} item to use.'.format(self.name, item))
			else:
				print('{} does not have {} item to attack {}\'s {} with.'.format(self.name, item, counterparty.name, target))
			return
		v = False
		if item == 'Hydroponics':
			v = True
		incomplete, use_event, time_required, max_qty_possible = self.fulfill(item, qty=uses, reqs='usage_req', amts='use_amount', check=check, v=v)
		# TODO Maybe book journal entries within function and add buffer argument
		if incomplete or check: # TODO Exit early on check after depreciation
			if not check:
				print(f'{self.name} cannot fulfill requirements to use {item} item.')
			return
		if counterparty is not None and target is not None:
			if self.hours < MAX_HOURS:
				print('{} cannot attack this turn. Attacking requires {} full hours time and {} only has {} remaining.'.format(self.name, MAX_HOURS, self.name, self.hours))
				return
			dmg_types = world.items.loc[item, 'dmg_type']
			if dmg_types is not None:
				dmg_types = [x.strip() for x in dmg_types.split(',')]
			dmgs = world.items.loc[item, 'dmg']
			if dmgs is not None:
				dmgs = [x.strip() for x in dmgs.split(',')]
			for i, dmg in enumerate(dmgs):
				if dmg is None:
					dmg = 0
				dmg = float(dmg)
				try:
					target = int(target)
				except ValueError:
					print('{} attempting to attack {} item held by {}'.format(self.name, target, counterparty.name))
				if isinstance(target, int):
					print('{} attempting to attack Entity ID: {}'.format(self.name, target))
					target = self.factory.get_by_id(target)
				if world.valid_item(target):
					target_type = world.get_item_type(target)
					self.ledger.set_entity(counterparty.entity_id)
					target_qty = self.ledger.get_qty(accounts=target_type, items=target)
					self.ledger.reset()
					if target_qty == 0:
						print('{} target does not have {} item to attack with {}.'.format(counterparty.name, target, item))
						return
					if dmg_types is not None:
						res_types = [x.strip() for x in world.items['res_type'][target].split(',')]
						for j, res_type in enumerate(res_types):
							if res_type == dmg_type[i]:
								break
						res = [x.strip() for x in world.items['res'][target].split(',')]
						res = list(map(float, res))
						resilience = res[j]
					else:
						res = [x.strip() for x in world.items['res'][target].split(',')]
						res = list(map(float, res))
						resilience = res[0]
					if resilience is None or resilience == 0:
						resilience = 1
					resilience = float(resilience)
					print('{} attacks with {} for {} damage against {} with resilience of {}.'.format(self.name, item, dmg, target, resilience))
					reduction = dmg / resilience
					if reduction > 1:
						reduction = 1
					for n in range(uses):
						#target_type = world.get_item_type(target)
						self.ledger.set_entity(counterparty.entity_id)
						target_bal = self.ledger.balance_sheet(accounts=['Buildings','Equipment','Accum. Depr.','Accum. Impairment Losses'], item=target)
						asset_cost = self.ledger.balance_sheet(accounts=['Buildings','Equipment'], item=target)
						print('Target Balance: {}'.format(target_bal))
						self.ledger.reset()
						impairment_amt = asset_cost * reduction
						if target_bal < impairment_amt:
							impairment_amt = target_bal
						counterparty.impairment(target, impairment_amt) # TODO Damage shouldn't be booked until fulfillment and depreciation is passed
					self.set_hours(MAX_HOURS)
				elif isinstance(target, Individual):# or target is None:
					self.ledger.set_entity(self.entity_id)
					item_qty = self.ledger.get_qty(accounts=['Equipped'], items=item)
					self.ledger.reset()
					if item_qty == 0:
						print('{} does not have {} item equipped to attack {} with.'.format(self.name, item, counterparty.name))
						return
					self.ledger.default = None
					self.ledger.set_entity(target.entity_id)
					armour_items = self.ledger.get_qty(accounts=['Equipped'], items=None) # TODO Fix this, only returning 0
					self.ledger.default = world.gov.get(ids=True)
					self.ledger.reset()
					resilience = 0
					# print('Target Armour: \n{}'.format(armour_items))
					for _, item_row in armour_items.iterrows():
						item = item_row['item_id']
						if dmg_types is not None:
							res_types = [x.strip() for x in world.items['res_type'][item].split(',')]
							for j, res_type in enumerate(res_types):
								if res_type == dmg_types[i]:
									break
							res = [x.strip() for x in world.items['res'][item].split(',')]
							res = list(map(float, res))
						else:
							res = [x.strip() for x in world.items['res'][item].split(',')]
							res = list(map(float, res))
							j = 0
						res = res[j]
						if res is None:
							res = 0
						resilience += res * item_row['qty']
						# TODO Depreciate target's armour
						# entries, uses = target.depreciation(item, lifespan, metric, uses=1)
						# print('Target Resilience: {}'.format(resilience))
					if resilience == 0:
						resilience = 1
					reduction = dmg / resilience
					if reduction > 1:
						reduction = 1
					need_delta = -(reduction)
					for need in world.global_needs:
						target.set_need(need, need_delta, attacked=True, v=True)
					print('{} attacks with {} for {} damage ({} resilience) against {}.'.format(self.name, item, dmg, resilience, target.name))
				else:
					print('Cannot attack a {} with a {}.'.format(target, item))
					return
		# In both cases using the item still uses existing logic
		orig_uses = uses
		metrics = world.items.loc[item, 'metric']
		if isinstance(metrics, str):
			metrics = [x.strip() for x in metrics.split(',')]
			metrics = list(filter(None, metrics))
		if metrics is None:
			metrics = ''
		lifespans = world.items.loc[item, 'lifespan']
		if isinstance(lifespans, str):
			lifespans = [x.strip() for x in lifespans.split(',')]
			lifespans = list(filter(None, lifespans))
		if lifespans is None:
			lifespans = ''
		#print('{} Metrics: {} | Lifespans: {}'.format(item, metrics, lifespans))
		for i, metric in enumerate(metrics):
			lifespan = int(lifespans[i])
			#print('{} Metric: {} | Lifespan: {}'.format(item, metric, lifespan))
			if metric == 'usage':
				entries, uses = self.depreciation(item, lifespan, metric, uses, buffer=buffer)
				if entries:
					use_event += entries
					if orig_uses != uses:
						print('{} could not use {} {} as requested; was used {} times.'.format(self.name, item, orig_uses, uses))
				else:
					print('{} could not use {} {} as requested.'.format(self.name, item, uses))
					incomplete = True
		if incomplete or check: # TODO Add check to depreciation() to exit early on this check
			return
		try:
			self.adj_needs(item, uses)
		except AttributeError as e:
			#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
			pass
		if not use_event and not incomplete:
			#print('{} has no requirements in order to be used by {}.'.format(item, self.name))
			return True
		return use_event

	def equip_item(self, item, qty=1):
		equipable = world.items.loc[item, 'metric']
		if not equipable:
			print('{} is not equipable. {}'.format(item, equipable))
			return []
		elif 'equipped' not in equipable:
			print('{} is not equipable. {}'.format(item, equipable))
			return []
		item_type = world.get_item_type(item)
		self.ledger.set_entity(self.entity_id)
		item_qty = self.ledger.get_qty(accounts=item_type, items=item)
		self.ledger.reset()
		equip_event = []
		if item_qty >= qty:
			# Ensure only one of each item class is equipped at a time
			item_class = world.get_item_type(item, level=1)
			# print('item_class:', item_class)
			if item_class != 'Equipment':
				items = world.items.loc[world.items['child_of'] == item_class].index.tolist()
				# print('items:', items)
			else:
				items = item
			self.ledger.set_entity(self.entity_id)
			equipped_qty = self.ledger.get_qty(accounts='Equipped', items=items)
			self.ledger.reset()
			if isinstance(equipped_qty, pd.DataFrame):
				if equipped_qty.empty:
					equipped_qty = 0
				else:
					equipped_qty = equipped_qty['qty'].sum()
			# print('equipped_qty:', equipped_qty)
			if equipped_qty == 0:
				hist_cost = self.ledger.hist_cost(qty, item, item_type)
				equip_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Equip ' + item, item, hist_cost / qty, qty, 'Equipped', item_type, hist_cost ]
				equip_event = [equip_entry]
				self.ledger.journal_entry(equip_event)
			else:
				print('{} cannot equip {} as they already have different {} equipped.'.format(self.name, item, item_class))
		return equip_event

	def unequip_item(self, item, qty=1):
		equipable = world.items.loc[item, 'metric']
		if not equipable:
			print('{} is not equipable. {}'.format(item, equipable))
			return []
		elif 'equipped' not in equipable:
			print('{} is not equipable. {}'.format(item, equipable))
			return []
		item_type = world.get_item_type(item)
		self.ledger.set_entity(self.entity_id)
		item_qty = self.ledger.get_qty(accounts=item_type, items=item)
		self.ledger.reset()
		unequip_event = []
		if item_qty <= qty:
			hist_cost = self.ledger.hist_cost(qty, item, item_type)
			unequip_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Unequip ' + item, item, hist_cost / qty, qty, item_type, 'Equipped', hist_cost ]
			unequip_event = [unequip_entry]
			self.ledger.journal_entry(unequip_event)
		return unequip_event

	def check_productivity(self, item, date=None, v=False):
		if date is not None:
			self.ledger.set_date(str(date))
		self.ledger.set_entity(self.entity_id)
		equip_list = self.ledger.get_qty(accounts=['Equipment'])
		self.ledger.reset()
		if v: print('Equip List: \n{}'.format(equip_list))
		if equip_list.empty:
			return None, None
		if v: print('Productivity Item Check: {}'.format(item))
		items_info = world.items[world.items['productivity'].str.contains(item, na=False)]
		efficiencies = []
		for index, item_row in items_info.iterrows():
			productivity = [x.strip() for x in item_row['productivity'].split(',')]
			for i, productivity_item in enumerate(productivity):
				if productivity_item == item:
					break
			efficiencies_list = [x.strip() for x in item_row['efficiency'].split(',')]
			efficiency = efficiencies_list[i]
			efficiencies.append(efficiency)
		efficiencies = pd.Series(efficiencies)
		if v: print('Productivity Efficiencies: \n{}'.format(efficiencies))
		items_info = items_info.assign(efficiencies=efficiencies.values)
		items_info.reset_index(inplace=True)
		if v: print('Items Info: \n{}'.format(items_info))
		if not equip_list.empty and not items_info.empty:
			equip_info = equip_list.merge(items_info)
			equip_info.sort_values(by='efficiencies', ascending=False, inplace=True)
			equip_info = equip_info.reset_index(drop=True)
			if v: print('Items Info Merged: \n{}'.format(equip_info))
			if equip_info.empty:
				return None, None
			# equip_qty = float(equip_info['qty'].iloc[0])
			# equip_capacity = float(equip_info['capacity'].iloc[0])
			# if v: print('Equip Capacity: {}'.format(equip_capacity))
			# TODO Consider how to factor in equipment capacity and WIP time
			modifier = float(equip_info['efficiencies'].iloc[0])
			if v: print('Modifier: {}'.format(modifier))
			# coverage = (req_qty * modifier * qty) // equip_capacity
			# print('Charges: {}'.format(coverage))
			# Book deprecition on use of item
			print('{} used {} equipment to do {} task better by {}.'.format(self.name, equip_info['item_id'].iloc[0], item, modifier))
			# TODO Returned equip_info should be equip_info['item_id'].iloc[0]
			return modifier, equip_info
		return None, None

	def fulfill(self, item, qty, reqs='requirements', amts='amount', partial=None, man=False, check=False, buffer=False, show_results=False, vv=False, v=True): # TODO Maybe add buffer=True
		if v: print(f'~{self.name} fulfill: {item} Qty: {qty} | Partial: {partial} | Check: {check} | buffer: {buffer} | Man: {man} | Reqs: {reqs}')
		try:
			if not self.gl_tmp.empty:
				if vv: print('gl_tmp is not empty:\n', self.gl_tmp.tail())
				self.ledger.gl = self.gl_tmp
		except AttributeError as e:
			self.gl_tmp = pd.DataFrame(columns=world.cols)
		incomplete = False
		if qty == 0:
			if v: print(f'!fulfill return due to qty == 0 for {item}')
			return None, [], None, 0
		event = []
		hold_event_ids = []
		prod_hold = []
		wip_choice = False
		wip_complete = False
		time_required = False
		time_check = False
		whole_qty = 1
		if reqs == 'hold_req':
			action = 'hold'
		elif reqs == 'usage_req':
			action = 'use'
		else:
			action = 'produce'
		if partial is not None:
			txn_id = world.delay.loc[partial, 'txn_id']
			desc = self.ledger.gl.loc[txn_id, 'description']
			if vv: print('Partial description for txn_id {}: {}'.format(txn_id, desc))
			if 'Capturing' in desc or 'being caught' in desc:
				reqs = 'int_rate_fix'
				amts = 'int_rate_var'
		hours_deltas = collections.OrderedDict()
		for individual in self.factory.get(Individual):
			hours_deltas[individual.name] = 0
		tmp_delay = world.delay.copy(deep=True)
		item_info = world.items.loc[item]
		item_type = world.get_item_type(item)
		if vv: print('Item Info: \n{}'.format(item_info))
		if item_info[reqs] is None or item_info[amts] is None:
			if v: print(f'!fulfill return due to no reqs for: {item} | Reqs: {reqs}')
			return None, [], None, 0
		requirements = [x.strip() for x in item_info[reqs].split(',')]
		if vv: print('Requirements: {}'.format(requirements))
		requirement_types = [world.get_item_type(requirement) for requirement in requirements]
		if vv: print('Requirement Types: {}'.format(requirement_types))
		amounts = [x.strip() for x in item_info[amts].split(',')]
		amounts = list(map(float, amounts))
		if vv: print('Requirement Amounts: {}'.format(amounts))
		requirements_details = list(itertools.zip_longest(requirements, requirement_types, amounts))
		if vv: print('Requirements Details for {}: \n{}'.format(item, requirements_details))

		if reqs in ['requirements','int_rate_fix'] and item_info['hold_req'] is not None and item_info['hold_amount'] is not None:
			hold_requirements = [x.strip() for x in item_info['hold_req'].split(',')]
			if vv: print('Hold Requirements: {}'.format(hold_requirements))
			hold_requirement_types = [world.get_item_type(hold_requirement) for hold_requirement in hold_requirements]
			if vv: print('Hold Requirement Types: {}'.format(hold_requirement_types))
			hold_amounts = [x.strip() for x in item_info['hold_amount'].split(',')]
			hold_amounts = list(map(float, hold_amounts))
			if vv: print('Hold Requirement Amounts: {}'.format(hold_amounts))
			hold_requirements_details = list(itertools.zip_longest(hold_requirements, hold_requirement_types, hold_amounts))
			if vv: print('Hold Requirements Details for {}: \n{}'.format(item, hold_requirements_details))
			hold_additional = []
			for hold_requirement in hold_requirements_details:
				exists = False
				for j, requirement in enumerate(requirements_details):
					if hold_requirement[0] == requirement[0]:
						# print('{} hold requirement in production requirement for {}.'.format(hold_requirement[0], item))
						exists = True
						# if hold_requirement[2] > requirement[2]:
						# requirements_details[j] = (requirement[0], requirement[1], requirement[2]+hold_requirement[2])
						requirements_details[j] = (requirement[0], requirement[1], max(requirement[2], hold_requirement[2]))
					if exists:
						break
				if not exists:
					hold_additional.append(hold_requirement)
			requirements_details += hold_additional
			if vv: print('Post Hold Requirements Details for {}: \n{}'.format(item, requirements_details))

		item_freq = world.items.loc[item, 'freq']
		if item_freq is not None:
			if isinstance(item_freq, str):
				item_freq = [x.strip() for x in item_freq.split(',')]
		else:
			item_freq = []
		results = pd.DataFrame(columns=['item_id', 'qty', 'modifier', 'qty_req', 'qty_held', 'incomplete', 'max_qty'], index=None)
		# TODO Sort so requirements with a capacity are first after time
		max_qty_possible = qty
		# print('item: {} | max_qty_possible: {}'.format(item, max_qty_possible))
		for requirement in requirements_details:
			self.ledger.set_entity(self.entity_id)
			req_item = requirement[0]
			req_item_type = requirement[1]
			req_qty = requirement[2]
			if req_qty is None:
				req_qty = 1
			req_freq = world.items.loc[req_item, 'freq']
			if req_freq is not None:
				if isinstance(req_freq, str):
					req_freq = [x.strip() for x in req_freq.split(',')]
			else:
				req_freq = []
			if v: print(f'Required Item: {req_item} | Type: {req_item_type} | Qty: {req_qty} | Freq: {req_freq}')

			if req_item_type == 'Time' and partial is None:
				# TODO Consider how Equipment could reduce time requirements
				time_required = True
				time_check = True
				if vv: print('Time Required: {}'.format(time_required))
				modifier, items_info = self.check_productivity(req_item)
				# Switch to turn time off
				if args.inf_time:
					time_required = False
					time_check = False
					modifier = 1
					if vv: print('(inf) Time Required: {}'.format(time_required))
				if vv: print('Modifier: {}'.format(modifier))
				self.ledger.reset()
				self.ledger.set_entity(self.entity_id)
				if modifier is not None:
					mod_item = items_info['item_id'].iloc[0]
					if vv: print('Time Modifier Item: {}'.format(mod_item))
					entries = self.use_item(mod_item, check=check)
					self.ledger.set_entity(self.entity_id)
					if not entries:
						entries = []
						modifier = 0
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl.loc[self.ledger.gl['entity_id'] == self.entity_id]
				else:
					modifier = 0
				if not self.gl_tmp.empty:
					# if vv: print('Tmp GL land: \n{}'.format(self.gl_tmp.tail()))
					self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
				req_qty = req_qty * (1 - modifier)
				if vv: print(f'Time Modifier End: {modifier} req_qty: {req_qty}')
				if req_qty < 1:
					time_required = False
					time_check = False
					if vv: print(f'{item} no longer requires {req_item} to produce due to {mod_item}.')

			elif (req_item_type == 'Non-Profit' or req_item_type == 'Governmental') and partial is None:
				if self.name.split('-')[0] == req_item:
					continue
				if req_item not in world.gov.get([NonProfit, Governmental]):
					if isinstance(self, Corporation):
						owner_id = self.list_shareholders(largest=True)
						owner = self.factory.get_by_id(owner_id)
					else:
						owner = self
					entity = owner.incorporate(req_item)
				incomplete = True
				max_qty_possible = 0
				if v: print(f'!fulfill return due to Non-Profit or Governmental org: {req_item}')
				return incomplete, event, time_required, max_qty_possible

			elif req_item_type == 'Land' and partial is None:
				modifier, items_info = self.check_productivity(req_item)
				self.ledger.set_entity(self.entity_id)
				if modifier is not None:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					self.ledger.set_entity(self.entity_id)
					if not entries:
						entries = []
						modifier = 0
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl.loc[self.ledger.gl['entity_id'] == self.entity_id]
				else:
					modifier = 0
				if not self.gl_tmp.empty:
					# if vv: print('Tmp GL land: \n{}'.format(self.gl_tmp.tail()))
					self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
				land = self.ledger.get_qty(items=req_item, accounts=['Land'])
				qty_needed = req_qty * (1-modifier) * qty
				if v: print(f'{self.name} requires {qty_needed} {req_item} to {action} {qty} {item} and has: {land}')
				price = world.get_price(req_item, world.env.entity_id)
				if land < qty_needed:
					needed_qty = (req_qty * (1-modifier) * qty) - land
					if v: print('{} requires {} more {} to produce {}.'.format(self.name, needed_qty, req_item, item))
					# Attempt to purchase land
					if not man:
						result = self.purchase(req_item, needed_qty, buffer=buffer, v=v)
						if result:
							price = price # TODO Handle price when purchasing land better
						if not result:
							self.ledger.set_entity(world.env.entity_id) # Only try to claim land that is remaining
							if not self.gl_tmp.empty:
								self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == world.env.entity_id]
							land_avail = self.ledger.get_qty(items=req_item, accounts=['Land'])
							# print('Land Available: {}'.format(land_avail))
							self.ledger.reset()
							self.ledger.set_entity(self.entity_id)
							qty_claim = int(min(needed_qty, land_avail))
							result = self.claim_land(req_item, qty_claim, price=price, buffer=buffer)
							# print('Land Claim Result: \n{}'.format(result))
							if not result:
								incomplete = True
						if result and buffer:
							for entry in result:
								entry_df = pd.DataFrame([entry], columns=world.cols)
								# self.ledger.gl = self.ledger.gl.append(entry_df)
								self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
							self.gl_tmp = self.ledger.gl
							# print('Tmp GL Land 2: \n{}'.format(self.gl_tmp.tail()))
					else:
						incomplete = True
					if not self.gl_tmp.empty and 'animal' not in item_freq: # TODO Look into this
						tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
						test_gl_tmp = self.gl_tmp.loc[self.gl_tmp['post_date'].isna()] # TODO This works
						# print('Test Post Date Filter: \n{}'.format(self.gl_tmp))
						# self.gl_tmp = self.ledger.gl.append(tmp_gl_tmp)
						self.gl_tmp = pd.concat([self.ledger.gl, tmp_gl_tmp])
						# print('Tmp GL Land 3: \n{}'.format(self.gl_tmp.tail()))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
					else:
						self.ledger.set_entity(self.entity_id)
				land = self.ledger.get_qty(items=req_item, accounts=['Land'])
				try:
					constraint_qty = math.floor(land / (req_qty * (1-modifier)))
					max_qty_possible = min(constraint_qty, max_qty_possible)
					if max_qty_possible < 0:
						if v: print('Negative max_qty_possible for {}: {} | Land: {} | req_qty: {} | req_item: {} | Modifier: {}'.format(item, max_qty_possible, land, req_qty, req_item, modifier)) # TODO Investigate why this is happening
						max_qty_possible = 0
				except ZeroDivisionError:
					constraint_qty = 'inf'
					max_qty_possible = min(max_qty_possible, qty)
					if max_qty_possible < 0:
						if v: print('Negative max_qty_possible: {} | qty: {}'.format(max_qty_possible, qty))
						max_qty_possible = 0
				if max_qty_possible == 0: # TODO Handle in similar way for commodities and other item types?
					incomplete = True
				if v: print('Land Max Qty Possible: {} | Constraint Qty: {}'.format(max_qty_possible, constraint_qty)) # TODO Show the max possible above qty requested
				# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':land, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
				results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty * qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[land], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)
				# if (reqs == 'hold_req' or time_required):# and not incomplete: # TODO Test is "not incomplete" is still needed here
				# TODO Handle land in use during one tick
				# qty_needed = req_qty * (1-modifier) * qty
				entries = self.in_use(req_item, qty_needed, price=price, buffer=True) # TODO Verify qty passed
				# print('Land In Use Entries: \n{}'.format(entries))
				if not entries:
					entries = []
					incomplete = True
				else:
					if reqs != 'hold_req' and not time_required:
						hold_event_ids += [entry[0] for entry in entries]
						if vv: print('{} land hold_event_ids: {}'.format(self.name, hold_event_ids))
				event += entries
				if entries:
					if not self.gl_tmp.empty:
						tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
						# self.ledger.gl = self.ledger.gl.append(tmp_gl_tmp)
						self.ledger.gl = pd.concat([self.ledger.gl, tmp_gl_tmp])
						# print('Ledger Temp Before: \n{}'.format(self.ledger.gl.tail()))
					for entry in entries:
						entry_df = pd.DataFrame([entry], columns=world.cols)
						# self.ledger.gl = self.ledger.gl.append(entry_df)
						self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
					self.gl_tmp = self.ledger.gl
					# print('Ledger Temp New: \n{}'.format(self.ledger.gl.tail()))

			elif req_item_type == 'Buildings' and partial is None:
				in_use = False
				modifier, items_info = self.check_productivity(req_item)
				self.ledger.set_entity(self.entity_id)
				if modifier is not None:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					self.ledger.set_entity(self.entity_id)
					if not entries:
						entries = []
						# incomplete = True
						modifier = 0
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
				else:
					modifier = 0
				building = self.ledger.get_qty(items=req_item, accounts=['Buildings'])
				# Get capacity amount
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None or pd.isna(capacity):
					capacity = 1
				capacity = float(capacity)
				qty_needed = qty * (1-modifier) * req_qty
				if v: print(f'{self.name} requires {req_qty} {req_item} building (Capacity: {capacity}) to {action} {qty} {item} and has: {building}')
				price = world.get_price(req_item, self.entity_id)
				if (building * capacity) < qty_needed:
					self.ledger.reset()
					building_wip = self.ledger.get_qty(items=req_item, accounts=['Building Under Construction'])
					self.ledger.set_entity(self.entity_id)
					if v: print('{} building under construction: {}'.format(req_item, building_wip))
					building += building_wip
					if (building * capacity) < qty_needed:
						remaining_qty = max(qty_needed - (building * capacity), 0)
						required_qty = int(math.ceil(remaining_qty / capacity))
						if building == 0:
							if v: print('{} does not have any {} building and requires {}.'.format(self.name, req_item, required_qty))
						else:
							if v: print('{} does not have enough capacity in {} building and requires {}.'.format(self.name, req_item, required_qty))
						if not man:
							# Attempt to purchase before producing self if makes sense
							result = self.purchase(req_item, required_qty, buffer=buffer, v=v)#, acct_buy='Buildings')#, wip_acct='Building Under Construction')
							req_time_required = False
							if not result:
								if v: print('{} will attempt to produce {} {} itself.'.format(self.name, required_qty, req_item))
								result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, required_qty, debit_acct='Buildings', buffer=buffer, v=v)
							if not result or req_time_required:
								if req_time_required:
									if v: print('{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, item, req_item))
								incomplete = True
							if result and buffer:
								for entry in result:
									entry_df = pd.DataFrame([entry], columns=world.cols)
									# self.ledger.gl = self.ledger.gl.append(entry_df)
									self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
								self.gl_tmp = self.ledger.gl
						else:
							incomplete = True
					else:
						if v: print('{} cannot complete {} now due to requiring time to produce {}.'.format(self.name, item, req_item))
						incomplete = True
					if not self.gl_tmp.empty:
						tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
						# self.gl_tmp = self.ledger.gl.append(tmp_gl_tmp)
						self.gl_tmp = pd.concat([self.ledger.gl, tmp_gl_tmp])
						# print('Tmp GL Building: \n{}'.format(self.gl_tmp.tail()))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
					else:
						self.ledger.set_entity(self.entity_id)
				building = self.ledger.get_qty(items=req_item, accounts=['Buildings'])
				try:
					# Note: If capacity != 1 then req_qty should == 1
					constraint_qty = math.floor((building * capacity) / (req_qty * (1-modifier)))
					max_qty_possible = min(constraint_qty, max_qty_possible)
				except ZeroDivisionError:
					constraint_qty = 'inf'
					max_qty_possible = min(max_qty_possible, qty)
				if v: print(f'Buildings Max Qty Possible: {max_qty_possible} | Constraint Qty: {constraint_qty} | Building: {building}')
				# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':building, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
				results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[math.ceil(qty / capacity)], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[building], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)
				qty_to_use = 0
				build_in_use = 0
				if building != 0:
					if capacity != 1:
						qty_to_use = int(min(building, int(math.ceil((building * capacity) / (max_qty_possible * (1-modifier) * req_qty)))))
					else:
						qty_to_use = int(min(building, int(math.ceil((max_qty_possible * (1-modifier) * req_qty)))))
					if capacity == 1:
						in_use = True
						build_in_use = qty_to_use
					else:
						build_in_use = int(math.floor((max_qty_possible * (1-modifier) * req_qty) / (building * capacity)))
						if v: print('build_in_use:', build_in_use)
						if build_in_use >= 1:
							in_use = True
					if v: print('{} needs to use {} {} times to produce {}. In Use: {}'.format(self.name, req_item, qty_to_use, item, in_use))
				if in_use or reqs == 'hold_req' or time_required: # TODO Handle building in use during one tick and handle building capacity
					entries = self.in_use(req_item, build_in_use, price=price, buffer=True)#, v=True)
					if not entries:
						entries = []
						incomplete = True
						max_qty_possible = 0 # TODO Is this needed?
					else:
						if reqs != 'hold_req' and not time_required:
							hold_event_ids += [entry[0] for entry in entries]
							if isinstance(self, Individual):
								prod_hold += [entry[0] for entry in entries]
							if vv: print('{} building hold_event_ids: {} | {}'.format(self.name, hold_event_ids, prod_hold))
					event += entries
					if entries:
						if not self.gl_tmp.empty:
							tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
							# self.ledger.gl = self.ledger.gl.append(tmp_gl_tmp)
							self.ledger.gl = pd.concat([self.ledger.gl, tmp_gl_tmp])
							# print('Ledger Temp Before: \n{}'.format(self.ledger.gl.tail()))
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
				for _ in range(qty_to_use):
					entries = self.use_item(req_item, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						max_qty_possible = 0 # TODO Is this needed?
					if entries is True:
						entries = []
					event += entries
					if entries:
						if not self.gl_tmp.empty:
							tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
							# self.ledger.gl = self.ledger.gl.append(tmp_gl_tmp)
							self.ledger.gl = pd.concat([self.ledger.gl, tmp_gl_tmp])
							# print('Ledger Temp Before: \n{}'.format(self.ledger.gl.tail()))
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))

			elif req_item_type == 'Equipment' and partial is None: # TODO Make generic for process
				in_use = False
				modifier, items_info = self.check_productivity(req_item)
				self.ledger.set_entity(self.entity_id)
				if modifier is not None:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					self.ledger.set_entity(self.entity_id)
					if not entries:
						entries = []
						# incomplete = True
						modifier = 0
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
				else:
					modifier = 0
				equip_qty = self.ledger.get_qty(items=req_item, accounts=['Equipment'])
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None or pd.isna(capacity):
					capacity = 1
				if isinstance(item_freq, str):
					if 'animal' in item_freq and 'animal' in req_freq:
						capacity = 1
				capacity = float(capacity)
				qty_needed = qty * (1-modifier) * req_qty
				if v: print(f'{self.name} requires {req_qty} {req_item} equipment (Capacity: {capacity}) to {action} {qty} {item} and has: {equip_qty}')
				price = world.get_price(req_item, self.entity_id)
				if (equip_qty * capacity) < qty_needed: # TODO Test item with capacity
					self.ledger.reset()
					equip_qty_wip = self.ledger.get_qty(items=req_item, accounts=['WIP Equipment'])
					self.ledger.set_entity(self.entity_id)
					if v: print('{} equipment being manufactured: {}'.format(req_item, equip_qty_wip))
					equip_qty += equip_qty_wip
					if (equip_qty * capacity) < qty_needed: # TODO Fix this
						remaining_qty = max(qty_needed - (equip_qty * capacity), 0)
						required_qty = int(math.ceil(remaining_qty / capacity))
						if equip_qty == 0:
							if v: print('{} does not have any {} equipment and requires {}.'.format(self.name, req_item, required_qty))
						else:
							if v: print('{} does not have enough capacity on {} equipment and requires {}.'.format(self.name, req_item, required_qty))
						if not man:
							# Attempt to purchase before producing self if makes sense
							result = self.purchase(req_item, required_qty, buffer=buffer, v=v)#, acct_buy='Equipment')#, wip_acct='WIP Equipment')
							# if vv: print('Equip Purchase Result:', result)
							req_time_required = False
							if not result:
								# TODO Needs if isinstance(item_freq, str):
								if 'animal' in item_freq and 'animal' in req_freq and equip_qty < 2 and not man:
									required_qty = 1
									if v: print('{} will attempt to catch remaining {} {} in the wild.'.format(self.name, required_qty, req_item))
									result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, required_qty, reqs='int_rate_fix', amts='int_rate_var', debit_acct='Equipment', buffer=buffer, v=v) # TODO This is a bit hackey
									equip_qty += req_max_qty_possible
									if not req_incomplete:
										if equip_qty < 2:
											incomplete = True
											max_qty_possible = 0
										continue
									else:
										if req_max_qty_possible == 0:
											incomplete = True
											max_qty_possible = 0
											continue
										req_qty = req_max_qty_possible
								else:
									if 'animal' in item_freq and 'animal' in req_freq and incomplete:
										continue
									elif 'animal' in item_freq and 'animal' in req_freq:# and equip_qty - equip_qty_wip <= 3: # TODO Test if this is needed for large amounts
										required_qty = max(math.floor((equip_qty - equip_qty_wip) / 2), 1)
									if v: print('{} will attempt to produce {} {} itself.'.format(self.name, required_qty, req_item))
									if vv: print('&&&&&1')
									if vv: print(f'Produce req_item: {req_item} | qty: {required_qty} | buffer: {buffer} | v: {v}')
									result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, required_qty, debit_acct='Equipment', buffer=buffer, v=v)
									if vv: print(f'Result for req_item: {req_item} | qty: {required_qty} | req_time_required: {req_time_required} | req_max_qty_possible: {req_max_qty_possible} | {req_incomplete} result:\n{result}')
									if vv: print('&&&&&2')
									if v: print('{} attempted to produce {} {} itself.'.format(self.name, required_qty, req_item))
							if not result or req_time_required:
								if req_time_required:
									if v: print('{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, item, req_item))
								incomplete = True
							if result and buffer:
								for entry in result:
									entry_df = pd.DataFrame([entry], columns=world.cols)
									# self.ledger.gl = self.ledger.gl.append(entry_df)
									self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
								self.gl_tmp = self.ledger.gl
						else:
							incomplete = True
					else:
						if v: print('{} cannot complete {} now due to requiring time to produce {}.'.format(self.name, item, req_item))
						incomplete = True
					if not self.gl_tmp.empty:
						tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
						# self.gl_tmp = self.ledger.gl.append(tmp_gl_tmp)
						self.gl_tmp = pd.concat([self.ledger.gl, tmp_gl_tmp])
						# print('Tmp GL Equip: \n{}'.format(self.gl_tmp.tail()))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
					else:
						self.ledger.set_entity(self.entity_id)
				equip_qty = self.ledger.get_qty(items=req_item, accounts=['Equipment'])
				try:
					# Note: If capacity != 1 then req_qty should == 1
					constraint_qty = math.floor((equip_qty * capacity) / (req_qty * (1-modifier)))
					max_qty_possible = min(constraint_qty, max_qty_possible)
				except ZeroDivisionError:
					constraint_qty = 'inf'
					max_qty_possible = min(max_qty_possible, qty)
				if v: print(f'Equipment Max Qty Possible: {max_qty_possible} | Constraint Qty: {constraint_qty} | equip_qty: {equip_qty}')
				# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':equip_qty, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
				results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[math.ceil(qty / capacity)], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[equip_qty], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)
				qty_to_use = 0
				equip_in_use = 0
				if equip_qty != 0:
					qty_to_use = int(min(equip_qty, math.ceil((qty * (1-modifier) * req_qty) / (equip_qty * capacity))))
					# if ((equip_qty * capacity) <= (qty * (1-modifier) * req_qty)):
					# 	in_use = True
					if capacity == 1:
						in_use = True
						equip_in_use = qty_to_use
					else:
						equip_in_use = int(math.floor((qty * (1-modifier) * req_qty) / (equip_qty * capacity)))
						if equip_in_use >= 1:
							in_use = True
				if in_use or reqs == 'hold_req' or time_required: # TODO Confirm handled equipment in use during only one tick
					entries = self.in_use(req_item, equip_in_use, price=price, buffer=True)
					if not entries:
						entries = []
						incomplete = True
					else:
						if reqs != 'hold_req' and not time_required:
							hold_event_ids += [entry[0] for entry in entries]
							if isinstance(self, Individual):
								prod_hold += [entry[0] for entry in entries]
							if vv: print('{} equip hold_event_ids: {} | {}'.format(self.name, hold_event_ids, prod_hold))
					event += entries
					if entries:
						if not self.gl_tmp.empty:
							tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
							# self.ledger.gl = self.ledger.gl.append(tmp_gl_tmp)
							self.ledger.gl = pd.concat([self.ledger.gl, tmp_gl_tmp])
							# print('Ledger Temp Before: \n{}'.format(self.ledger.gl.tail()))
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
				for _ in range(qty_to_use):
					entries = self.use_item(req_item, buffer=True)
					if not entries:
						entries = []
						incomplete = True
					if entries is True:
						entries = []
					event += entries
					if entries:
						if not self.gl_tmp.empty:
							tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
							# self.ledger.gl = self.ledger.gl.append(tmp_gl_tmp)
							self.ledger.gl = pd.concat([self.ledger.gl, tmp_gl_tmp])
							# print('Ledger Temp Before: \n{}'.format(self.ledger.gl.tail()))
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))

			elif req_item_type == 'Components' and partial is None:
				modifier, items_info = self.check_productivity(req_item)
				self.ledger.set_entity(self.entity_id)
				if modifier is not None:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					self.ledger.set_entity(self.entity_id)
					if not entries:
						entries = []
						# incomplete = True
						modifier = 0
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
				else:
					modifier = 0
				try:
					if not self.gl_tmp.empty:
						# print('Tmp GL components: \n{}'.format(self.gl_tmp.tail()))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
				except AttributeError as e:
					# print('No Tmp GL Error components: {}'.format(repr(e)))
					pass
				component_qty = self.ledger.get_qty(items=req_item, accounts=['Components'])
				qty_needed = req_qty * (1-modifier) * qty
				if v: print(f'{self.name} requires {qty_needed} {req_item} components to {action} {qty} {item} and has: {component_qty}')
				if component_qty < qty_needed:
					if v: print('{} does not have enough {} components. Will attempt to aquire some.'.format(self.name, req_item))
					if not man:
						# TODO Improve to be more like commodities
						result = self.purchase(req_item, qty_needed, v=v)#, 'Inventory')#, buffer=True)
						req_time_required = False
						if not result:
							if v: print('{} will attempt to produce {} {} itself.'.format(self.name, qty_needed, req_item))
							result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty_needed, v=v)#, buffer=True)
						if not result or req_time_required:
							if req_time_required:
								if v: print('{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, item, req_item))
							incomplete = True
					else:
						incomplete = True
				try:
					if not self.gl_tmp.empty:
						tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
						# self.gl_tmp = self.ledger.gl.append(tmp_gl_tmp)
						self.gl_tmp = pd.concat([self.ledger.gl, tmp_gl_tmp])
						# print('Tmp GL Component: \n{}'.format(self.gl_tmp.tail()))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
					else:
						self.ledger.set_entity(self.entity_id)
				except AttributeError as e:
					# print('No Tmp GL Error Component: {}'.format(repr(e)))
					pass
				component_qty = self.ledger.get_qty(items=req_item, accounts=['Inventory'])#, v=True)
				try:
					constraint_qty = math.floor(component_qty / (req_qty * (1-modifier)))
					max_qty_possible = min(constraint_qty, max_qty_possible)
				except ZeroDivisionError:
					constraint_qty = 'inf'
					max_qty_possible = min(max_qty_possible, qty)
				if v: print('Components Max Qty Possible: {} | Constraint Qty: {}'.format(max_qty_possible, constraint_qty))
				# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':component_qty, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
				results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty * qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[component_qty], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)
				if not check:
					entries = self.consume(req_item, qty=qty_needed, buffer=True)
					if not entries:
						entries = []
						incomplete = True
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))

			elif req_item_type == 'Commodity' and partial is None:
				modifier, items_info = self.check_productivity(req_item)
				self.ledger.set_entity(self.entity_id)
				if modifier is not None:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					self.ledger.set_entity(self.entity_id)
					if not entries:
						entries = []
						# incomplete = True
						modifier = 0
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# if item == 'Hydroponics' or item == 'Wire':
						# 	if vv: print('Ledger Temp commodity: \n{}'.format(self.ledger.gl.tail(10)))
				else:
					modifier = 0
				try:
					if not self.gl_tmp.empty:
						if vv: print('##############################')
						# if item == 'Hydroponics' or item == 'Wire' or item =='Cotton Gin' or item =='Cotton Spinner':
						if vv: print('Tmp GL commodity 01: \n{}'.format(self.gl_tmp.tail(10)))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
						if vv: print('self.ledger.gl 01: \n{}'.format(self.ledger.gl.tail(10)))
						if vv: print('##############################')
				except AttributeError as e:
					# if item == 'Anvil' or item =='Cotton Gin' or item =='Cotton Spinner':
					if vv: print('No Tmp GL Error commodity: {}'.format(repr(e)))
					pass
				material_qty_held = self.ledger.get_qty(items=req_item, accounts=['Inventory'])#, v=True)

				if isinstance(item_freq, str) and isinstance(req_freq, str):
					if 'animal' in item_freq and 'animal' in req_freq and material_qty_held < 2 and not man:
						# qty_needed = max((req_qty * (1 - modifier) * qty) - material_qty_held, 0)
						if material_qty_held == 1:
							qty_needed = 1
						else:
							qty_needed = 1 #2
						if v: print('{} will attempt to catch {} {} in the wild.'.format(self.name, qty_needed, req_item))
						result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty_needed, reqs='int_rate_fix', amts='int_rate_var', v=v) # TODO This is a bit hackey
						material_qty_held += req_max_qty_possible
						if not req_incomplete:
							if material_qty_held < 2:
								incomplete = True
								max_qty_possible = 0
							continue
						else:
							if req_max_qty_possible == 0:
								incomplete = True
								max_qty_possible = 0
								continue
							req_qty = req_max_qty_possible # TODO Investigate this further
						# return req_incomplete, result, req_time_required, req_max_qty_possible
						# if result:
							# req_qty = req_max_qty_possible # TODO Investigate this further
						# 	incomplete = True # So the animal isn't breed in same round it is captured

				qty_needed = req_qty * (1 - modifier) * qty
				if v: print(f'{self.name} requires {qty_needed} {req_item} commodity to {action} {qty} {item} and has: {material_qty_held}')
				if req_qty < 1 and req_qty > 0:
					whole_qty = (1 / req_qty)
					qty_ratio = math.ceil(qty / whole_qty)
					max_qty_possible = whole_qty * qty_ratio
					# max_qty_possible = qty # TODO This could cause an issue if Land or Buildings are a restriction. Maybe keep a table instead
					if v: print('Since qty is less than 1: {} requires {} {} commodity to produce {} {} and has: {}'.format(self.name, qty_needed, req_item, qty, item, material_qty_held))
					if qty < whole_qty:
						if v: print(f'!fulfill return due to qty < whole_qty: {req_item}')
						return self.fulfill(item, max_qty_possible, man=man, v=v)
					if v: print('{} {} is greater than or equal to the whole qty of {}. Max Qty Possible: {}'.format(qty, item, whole_qty, max_qty_possible))
				qty_needed = max(qty_needed - material_qty_held, 0)
				if isinstance(req_freq, str):
					if 'animal' in req_freq and 'animal' not in item_freq:
						qty_needed = max(qty_needed - material_qty_held + 2, 0)
				if v: print('material_qty_held: {} | req_qty: {} | modifier: {} | qty: {} | qty_needed: {} | item: {} | req_item: {}'.format(material_qty_held, req_qty, modifier, qty, qty_needed, item, req_item))
				if qty_needed > 0:
					if v: print('{} does not have enough {} commodity and requires {} more units.'.format(self.name, req_item, qty_needed))
					# TODO Maybe add logic so that producers wont try and purchase items they can produce
					if not man:
						# Attempt to purchase before producing
						result = self.purchase(req_item, qty_needed, v=v)#, 'Inventory')#, buffer=True)
						partial_qty = False
						purchased_qty = 0
						if result:
							purchase_entries = pd.DataFrame(result, columns=world.cols, index=None)
							#print('Purchase Entries: \n{}'.format(purchase_entries))
							purchase_entries = purchase_entries.loc[purchase_entries['entity_id'] == self.entity_id]
							purchased_qty = purchase_entries['qty'].sum()
							if purchased_qty < qty_needed:
								if v: print('{} could only purchase {} of {} required.'.format(self.name, purchased_qty, qty_needed))
								#incomplete = True # TODO Decide how best to handle when not enough qty is available to be purchased
								partial_qty = True
								qty_needed = max(qty_needed - purchased_qty, 0)
						req_time_required = False
						if not result or partial_qty:
							# TODO Needs if isinstance(item_freq, str) and isinstance(req_freq, str):
							if 'animal' in item_freq and 'animal' in req_freq and (material_qty_held + purchased_qty) < 2 and not man:
								# if incomplete:
								# 	continue
								if v: print('{} will attempt to catch remaining {} {} in the wild.'.format(self.name, qty_needed, req_item))
								result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty_needed, reqs='int_rate_fix', amts='int_rate_var', v=v) # TODO This is a bit hackey
								if not req_incomplete:
									if material_qty_held < 2:
										incomplete = True
										max_qty_possible = 0
									continue
								else:
									if req_max_qty_possible == 0:
										incomplete = True
										max_qty_possible = 0
										continue
									req_qty = req_max_qty_possible
							else:
								if 'animal' in item_freq and 'animal' in req_freq and incomplete:
									continue
								if v: print('{} will attempt to produce {} {} itself.'.format(self.name, qty_needed, req_item))
								result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty_needed, v=v)#, buffer=True)
						if not result or req_time_required:
							if req_time_required:
								if v: print('{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, item, req_item))
							incomplete = True
							if 'animal' in item_freq and 'animal' in req_freq:
								max_qty_possible = 0 # TODO Test if this causes issues for non-animals
					else:
						incomplete = True
				# self.ledger.set_entity(self.entity_id)
				try:
					if not self.gl_tmp.empty:
						if vv: print('******************************')
						if vv: print('Tmp GL Commodity 02: \n{}'.format(self.gl_tmp.tail()))
						tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
						if vv: print('tmp_gl_tmp: \n{}'.format(tmp_gl_tmp))
						if vv: print('self.ledger.gl 02: \n{}'.format(self.ledger.gl.tail(8)))
						# self.ledger.reset()
						# if v: print('self.ledger.gl 02b: \n{}'.format(self.ledger.gl.tail(8)))
						tmp_gl_check = self.ledger.gl.loc[self.ledger.gl.index == 0]
						if vv: print('tmp_gl_check: \n{}'.format(tmp_gl_check))
						if tmp_gl_check.empty:
							if vv: print('self.ledger.gl 02c: \n{}'.format(self.ledger.gl.tail(8)))
							self.gl_tmp = pd.concat([self.ledger.gl, tmp_gl_tmp])
						# if item =='Cotton Gin' or item =='Cotton Spinner':
						if vv: print('Tmp GL Commodity 03: \n{}'.format(self.gl_tmp.tail(8)))
						self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
						if vv: print('self.ledger.gl 03: \n{}'.format(self.ledger.gl.tail(8)))
						if vv: print('******************************')
					else:
						# if item =='Cotton Gin' or item =='Cotton Spinner':
						if vv: print('No Tmp GL Data for Commodity: {}'.format(self.gl_tmp))
						self.ledger.set_entity(self.entity_id)
				except AttributeError as e:
					# if item =='Cotton Gin' or item =='Cotton Spinner':
					if vv: print('No Tmp GL Error Commodity: {}'.format(repr(e)))
					pass
				material_qty = self.ledger.get_qty(items=req_item, accounts=['Inventory'], v=vv)
				if v: print('Item: {} | qty: {} | req_item: {} | req_qty: {} | material_qty: {} | modifier: {} | max_qty_possible: {}'.format(item, qty, req_item, req_qty, material_qty, modifier, max_qty_possible))
				try:
					# TODO Needs if isinstance(req_freq, str):
					if 'animal' in req_freq and material_qty <= 2:
						max_qty_possible = 0
						constraint_qty = 0
						incomplete = True
						self.item_demanded(req_item, 3 - material_qty, v=v)
					else:
						constraint_qty = math.floor(material_qty / (req_qty * (1-modifier)))
						if v: print(f'Commodity Constraint Qty: {constraint_qty} | Max Qty Possible: {max_qty_possible} | material_qty: {material_qty} | req_qty: {req_qty} | modifier: {modifier}')
						max_qty_possible = min(constraint_qty, max_qty_possible)
				except ZeroDivisionError:
					constraint_qty = 'inf'
					max_qty_possible = min(max_qty_possible, qty)
				# if max_qty_possible == 0: # TODO This should not be needed
				# 	incomplete = True
				if v: print('Commodity Max Qty Possible: {} | Constraint Qty: {}'.format(max_qty_possible, constraint_qty))
				# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':material_qty, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
				results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty * qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[material_qty], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)
				if item =='Cotton Gin' or item =='Cotton Spinner':
					if v: print('Commodity results:\n', results)
				if not check:
					consume_qty = req_qty * (1 - modifier) * qty # TODO Should this be qty_needed?
					if v: print(f'consume_qty: {consume_qty} | qty_needed: {qty_needed} | req_item: {req_item} | qty: {qty} | constraint_qty: {constraint_qty} | modifier: {modifier} | item: {item}')
					# TODO Needs if isinstance(item_freq, str) and isinstance(req_freq, str):
					if not 'animal' in req_freq or not 'animal' in item_freq:
						entries = self.consume(req_item, qty=consume_qty, buffer=True) # TODO Verify fix for how this assumed all required qty was obtained # req_qty * (1 - modifier) * qty # Old was qty=material_qty
						if not entries:
							entries = []
							incomplete = True
						event += entries
						if entries:
							for entry in entries:
								entry_df = pd.DataFrame([entry], columns=world.cols)
								# self.ledger.gl = self.ledger.gl.append(entry_df)
								self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
							self.gl_tmp = self.ledger.gl
							# if item =='Cotton Gin' or item =='Cotton Spinner':
							if vv: print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))

			elif req_item_type == 'Service' and partial is None:
				# TODO Add support for qty to Services
				if v: print('{} will attempt to purchase the {} service to produce {} {}.'.format(self.name, req_item, qty, item))
				qty_needed = req_qty * qty
				entries = self.purchase(req_item, qty_needed, buffer=True, v=v)
				if not entries:
					if v: print('{} will attempt to produce {} {} itself.'.format(self.name, qty_needed, req_item))
					entries, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty_needed, buffer=True, v=v) # TODO Consider if manual switch needed
				if not entries: # TODO Consider if Time requirement can be handled like above
					entries = []
					if v: print('{} was unable to obtain {} service.'.format(self.name, req_item))
					max_qty_possible = 0
					incomplete = True
				event += entries
				if entries:
					for entry in entries:
						entry_df = pd.DataFrame([entry], columns=world.cols)
						# self.ledger.gl = self.ledger.gl.append(entry_df)
						self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
					self.gl_tmp = self.ledger.gl
					# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))

			elif req_item_type == 'Subscription' and partial is None:
				# TODO Add support for capacity to Subscriptions
				# TODO Add check to ensure payment has been made recently (maybe on day of)
				qty_needed = qty * req_qty
				subscription_state = self.ledger.get_qty(items=req_item, accounts=['Subscription Info'])
				if v: print(f'{self.name} requires {qty_needed} {req_item} subscription to {action} {qty} {item} and has: {subscription_state}')
				qty_needed = 1 # TODO Test this as it was a quick fix for a bug
				if subscription_state < qty_needed:
					qty_remain = qty_needed - subscription_state
					if v: print('{} does not have {} {} subscription active. Will attempt to activate {}.'.format(self.name, qty_needed, req_item, qty_remain))
					if not man:
						entries = self.order_subscription(item=req_item, qty=qty_remain, buffer=True, v=v)
						if not entries:
							entries = []
							if v: print('{} was unable to activate {} subscription.'.format(self.name, req_item))
							incomplete = True
							max_qty_possible = 0
						event += entries
						if entries:
							for entry in entries:
								entry_df = pd.DataFrame([entry], columns=world.cols)
								# self.ledger.gl = self.ledger.gl.append(entry_df)
								self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
							self.gl_tmp = self.ledger.gl
							# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
					else:
						incomplete = True

			elif req_item_type == 'Job' and partial is None:
				modifier = 0
				if item_type == 'Job' or item_type == 'Labour':
					if isinstance(self, Individual):
						experience = abs(self.ledger.get_qty(items=req_item, accounts=['Salary Income']))
						if experience < req_qty:
							incomplete = True
							# TODO Add to demand table
							if v: print(f'!fulfill return due to not enough exp for Job: {req_item}')
							return incomplete, event, time_required, max_qty_possible
				else:
					# TODO Add support for modifier
					workers = self.ledger.get_qty(items=req_item, accounts=['Worker Info'])
					if vv: print('Workers as {}: {}'.format(req_item, worker_state))
					# Get capacity amount
					capacity = world.items.loc[req_item, 'capacity']
					if capacity is None or pd.isna(capacity):
						capacity = 1
					capacity = float(capacity)
					if v: print('{} has {} {} available with {} capacity each to produce {} {}.'.format(self.name, workers, req_item, capacity, qty, item))
					qty_needed = qty * req_qty
					if ((workers * capacity) / qty_needed) < 1:
						remaining_qty = qty_needed - (workers * capacity)
						required_qty = int(math.ceil(remaining_qty / capacity))
						if not man:
							if workers <= 0:
								if v: print('{} does not have a {} available to work. Will attempt to hire {}.'.format(self.name, req_item, required_qty))
							else:
								if v: print('{} does not have enough capacity for {} jobs. Will attempt to hire {}.'.format(self.name, req_item, required_qty))
							for _ in range(required_qty):
								entries = self.hire_worker(job=req_item, qty=1, man=man, buffer=True)
								# print('Job Entries: {}'.format(entries))
								if not entries:
									entries = []
									incomplete = True # TODO Fix failing if only one cannot be hired
								event += entries
								if entries:
									for entry in entries:
										entry_df = pd.DataFrame([entry], columns=world.cols)
										# self.ledger.gl = self.ledger.gl.append(entry_df)
										self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
									self.gl_tmp = self.ledger.gl
									# print('Job Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
						else:
							incomplete = True
						# print('req_item: {} | qty: {} | workers: {} | req_qty: {} | max_qty_possible: {}'.format(req_item, qty, workers, req_qty, max_qty_possible))
						try:
							if not self.gl_tmp.empty:
								tmp_gl_tmp = self.gl_tmp.loc[self.gl_tmp.index == 0]
								# self.gl_tmp = self.ledger.gl.append(tmp_gl_tmp)
								self.gl_tmp = pd.concat([self.ledger.gl, tmp_gl_tmp])
								# print('Tmp GL Job: \n{}'.format(self.gl_tmp.tail()))
								self.ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
							else:
								self.ledger.set_entity(self.entity_id)
						except AttributeError as e:
							# print('No Tmp GL Error Job: {}'.format(repr(e)))
							pass
						workers = self.ledger.get_qty(items=req_item, accounts=['Worker Info'])#, v=True)
						try:
							constraint_qty = math.floor((workers * capacity) / req_qty)
							max_qty_possible = min(constraint_qty, max_qty_possible)
						except ZeroDivisionError:
							constraint_qty = 'inf'
							max_qty_possible = min(max_qty_possible, qty)
						if v: print('Job Max Qty Possible: {} | Constraint Qty: {}'.format(max_qty_possible, constraint_qty))
						# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':workers, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
						results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty * qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[workers], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)

			elif req_item_type == 'Labour':
				qty_held = None
				none_qualify = False
				if item_type == 'Job' or item_type == 'Labour':
					if isinstance(self, Individual): # TODO Test this
						experience = abs(self.ledger.get_qty(items=req_item, accounts=['Wages Income']))
						if experience < req_qty:
							incomplete = True
							# TODO Add to demand table maybe
							if v: print(f'!fulfill return due to not enough exp for Labour or Job: {req_item}.')
							return incomplete, event, time_required, max_qty_possible
				else:
					modifier, items_info = self.check_productivity(req_item)
					self.ledger.set_entity(self.entity_id)
					if modifier is not None:
						entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
						self.ledger.set_entity(self.entity_id)
						if not entries:
							entries = []
							# incomplete = True
							modifier = 0
						if entries is True:
							entries = []
						event += entries
						if entries:
							for entry in entries:
								entry_df = pd.DataFrame([entry], columns=world.cols)
								# self.ledger.gl = self.ledger.gl.append(entry_df)
								self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
							self.gl_tmp = self.ledger.gl
							# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
					else:
						modifier = 0
					# if partial is not None:
					# 	delay = world.delay.loc[partial, 'delay']
					# 	labour_date = (world.now - datetime.timedelta(days=int(delay)))
					# 	print('labour_date:', labour_date)
					# 	self.ledger.set_start_date(str(labour_date)) # TODO Not sure if this is needed
					# else:

					labour_done = 0
					# TODO Not sure if this is needed now
					# self.ledger.set_start_date(str(world.now))
					# labour_done = self.ledger.get_qty(items=req_item, accounts=['Wages Expense','Cost Pool'])#, v=True)
					# self.ledger.reset()
					# self.ledger.set_entity(self.entity_id)

					# labour_required = req_qty * (1-modifier) * qty
					labour_required = math.ceil((req_qty * (1-modifier) * qty) * 100) / 100 # Round up to two decimal places
					# Labourer does the amount they can, and get that value from the entries. Then add to the labour hours done and try again
					if partial is not None:
						if v: print('Partial Labour Index: {}'.format(partial))
						job = world.delay.loc[partial, 'job']
						if req_item == job:
							labour_required = world.delay.loc[partial, 'hours']
							total_labour_required = req_qty * (1-modifier) * qty
							if v: print(f'{self.name} requires {total_labour_required} {req_item} labour to {action} {qty} {item} and has done: {total_labour_required - labour_required}')
							if v: print('Partial Labour Remaining Hours: {}'.format(labour_required))
					else:
						if v: print('{} requires {} {} labour to produce {} {}.'.format(self.name, labour_required, req_item, qty, item))
					orig_labour_required = labour_required # TODO This might not be needed
					hours_remain = 0
					while labour_done < labour_required:
						required_hours = max(labour_required - labour_done, 0)
						if v: print('Labour Done in Cycle: {} | Labour Required: {} | Remaining Hours: {} | WIP Choice: {} | Time Req: {}'.format(labour_done, labour_required, required_hours, wip_choice, time_required))
						orig_required_hours = required_hours
						# if item_type == 'Education':
						# 	print('{} has not studied enough {} today. Will attempt to study for {} hours.'.format(self.name, req_item, required_hours)) #MAX_HOURS = 12
						# 	required_hours = min(required_hours, MAX_HOURS)
						# 	counterparty = self
						# 	entries = self.accru_wages(job=req_item, counterparty=counterparty, labour_hours=required_hours, wage=0, buffer=True, v=v)
						# else:
						if v: print(f'{self.name} to {action} {qty} {item} requires {req_item} labour for {required_hours} hours.')
						# TODO Maybe support WIP Services
						# if (qty == 1 or orig_labour_required > MAX_HOURS) and reqs != 'hold_req' and item_type != 'Service':
						# if qty == 1 and reqs != 'hold_req' and item_type != 'Service':
						if reqs != 'hold_req' and item_type != 'Service':
							if man and not wip_choice and partial is None and not incomplete:
								while True:
									if self.auto_wip:
										choice = 'Y'
									else:
										if required_hours > self.hours:
											# TODO Maybe make this automatic
											choice = input('Should {} ({} hours available) work on the {} over multiple days? [Y/n]: '.format(self.name, self.hours, item))
										else:
											choice = input('Should {} ({} hours available) work on the {} over multiple days? [y/N]: '.format(self.name, self.hours, item))
									if choice == '':
										if required_hours > self.hours:
											choice = 'Y'
										else:
											choice = 'N'
									if choice.upper() == 'Y':
										wip_choice = True
										break
									elif choice.upper() == 'N':
										wip_choice = False
										break
									else:
										print('Not a valid entry. Must be "Y" or "N".')
										continue
							elif isinstance(self, Individual):
								if required_hours > self.hours: # TODO Check against global hours
									wip_choice = True
							else: # TODO Test this
								if required_hours > MAX_HOURS or labour_done > 0:
									wip_choice = True	
						if wip_choice:
							if man and isinstance(self, Individual):
								if self.hours > 0:
									while True:
										if incomplete:
											required_hours = 0
											break
										try:
											if self.auto_wip:
												required_hours = orig_required_hours
											else:
												required_hours = input('Enter the amount of hours to hire {} ({} hours available) to work on {}[{}]: '.format(self.name, self.hours, item, min(self.hours, orig_required_hours)))
											if required_hours == '':
												required_hours = orig_required_hours
											required_hours = float(required_hours)
										except ValueError:
											print('"{}" is not a valid entry. Must be a number.'.format(required_hours))
											continue
										if required_hours > orig_required_hours:
											print('{} hours is more than is required. Will use {} hours instead.'.format(required_hours, orig_required_hours))
											required_hours = orig_required_hours
											break
										if required_hours > self.hours:
											print('"{}" is more hours than {} has remaining. Will use the remaining {} hours.'.format(required_hours, self.name, self.hours))
											required_hours = self.hours
											break
										break
									if required_hours == 0:
										break
							else:
								# required_hours = min(required_hours, WORK_DAY)
								if isinstance(self, Individual):
									if self.hours:
										required_hours = max(min(orig_required_hours, self.hours), 0)
								else:
									required_hours = max(min(required_hours, WORK_DAY), 0)
								 # TODO Or MAX_HOURS?
								# if required_hours < WORK_DAY:# and labour_done > 0:
								# 	wip_choice = False # TODO Test this
								# 	wip_complete = True
								# 	if required_hours == 0:
								# 		break
								# if orig_required_hours < WORK_DAY:
								# 	required_hours = orig_required_hours
							# if required_hours != orig_labour_required:
							time_required = True
						required_hours = math.ceil(required_hours * 100) / 100 # Round up to two decimal places
						if v: print('{} will attempt to hire {} labour for {} hours. Time Req: {} | WIP Choice: {} | WIP Complete: {}'.format(self.name, req_item, required_hours, time_required, wip_choice, wip_complete))
						# if 'Individual' in world.items.loc[item, 'producer'] and qty == 1:
						# 	counterparty = self
						# elif item_type == 'Education':
						# 	counterparty = self
						# else:
						counterparty = self.worker_counterparty(req_item, man=man, v=v)
						if isinstance(counterparty, tuple):
							counterparty, entries = counterparty
							event += entries
							if entries:
								for entry in entries:
									entry_df = pd.DataFrame([entry], columns=world.cols)
									# self.ledger.gl = self.ledger.gl.append(entry_df)
									self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
								self.gl_tmp = self.ledger.gl
								# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
						if counterparty == 'none_qualify':
							none_qualify = True
							counterparty = None
						entries = self.accru_wages(job=req_item, counterparty=counterparty, labour_hours=required_hours, buffer=True, v=v)
						# print('Labour Entries: \n{}'.format(entries))
						# print('WIP Choice: {} | Labour Done: {}'.format(wip_choice, labour_done))
						if not entries and ((not wip_choice) or not labour_done):# and not wip_complete: # TODO Test "and not wip_complete"
							entries = []
							incomplete = True
							if wip_choice:
								time_required = False
							# if item_type != 'Education':
							#print('World Demand Before: \n{}'.format(world.demand))
							# demand_count = world.demand.loc[world.demand['item_id'] == item].shape[0]
							# if not man:
							# 	print('Demand Count Buckets for {}: {}'.format(item, demand_count))
							# if demand_count:
							# 	try:
							# 		qty_possible = max(int(math.floor(labour_done / (req_qty * (1-modifier)))), 1)
							# 	except ZeroDivisionError:
							# 		qty_possible = qty
							# 	qty_poss_bucket = max(int(math.ceil(qty_possible // demand_count)), 1)
							# 	# TODO Better handle zero remaining when qty_poss_bucket is also 1
							# 	qty_poss_remain = qty_possible % qty_poss_bucket
							# 	print('Labour Done for {}: {} | Qty Possible for {}: {}'.format(req_item, labour_done, item, qty_possible))
							# 	print('Qty Poss. per Bucket: {} | Qty Poss. Remain: {}'.format(qty_poss_bucket, qty_poss_remain))
							# 	world.demand.loc[world.demand['item_id'] == item, 'qty'] = qty_poss_bucket
							# 	for i, row in world.demand.iterrows():
							# 		if row['item_id'] == item:
							# 			break
							# 	world.demand.at[i, 'qty'] = qty_poss_bucket + qty_poss_remain
							# 	world.demand.loc[world.demand['item_id'] == item, 'reason'] = 'labour'
							# 	world.set_table(world.demand, 'demand')
							# 	print('{} adjusted {} on demand list due to labour constraint.'.format(self.name, item))
								#print(time_stamp() + 'World Demand After: \n{}'.format(world.demand))
							break
						# elif not entries and item_type == 'Education': # TODO Fix how Study works to use WIP system
						# 	entries = []
						# 	incomplete = True
						# 	if wip_choice:
						# 		time_required = False
						elif not entries:
							entries = []
						event += entries
						if entries:
							for entry in entries:
								entry_df = pd.DataFrame([entry], columns=world.cols)
								# self.ledger.gl = self.ledger.gl.append(entry_df)
								self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
							self.gl_tmp = self.ledger.gl
							# print('Ledger Temp: \n{}'.format(self.ledger.gl.tail()))
						if entries:
							hours_done = entries[0][8]
							labour_done += hours_done # Same as required_hours
							if v: print('Labour done at end of cycle: {} | Hours done: {} | Incomplete: {}'.format(labour_done, hours_done, incomplete))
							counterparty.set_hours(hours_done)
							hours_deltas[counterparty.name] += hours_done
							hours_remain = max(orig_required_hours - hours_done, 0)
							# if item_type == 'Education':
							# 	break
							# print('Partial - Orig Hours: {} | Hours Done: {} | Hours Remain: {} | Partial: {} | Time Required: {}'.format(orig_required_hours, hours_done, hours_remain, partial, time_required))
						elif not entries and wip_choice:
							hours_remain = max(orig_labour_required - labour_done, 0)
							if not hours_remain:
								time_required = False
							break
						else:
							hours_remain = max(orig_labour_required - labour_done, 0)
					# print('Partial - Partial: {} | Time Required: {}'.format(partial, time_required))
					if wip_choice and time_required and partial is None and hours_remain:
						# TODO Check existing delay table for same items
						already_wip = False
						for index, row in tmp_delay.iterrows():
							txn_id = row['txn_id']
							try:
								check_row = self.ledger.gl.loc[txn_id]
							except KeyError:
								continue
							# print('Entity ID: {} | Item ID: {}'.format(check_row['entity_id'], check_row['item_id']))
							if check_row['entity_id'] != self.entity_id:
								continue
							if check_row['item_id'] == item:
								already_wip = True
								break
						if not already_wip:
							# if time_check:
							# 	for i, req in enumerate(requirements_details): # Incase Time isn't the first item
							# 		if req[1] == 'Time':
							# 			break
							# 	delay_amount = requirements_details[i][2] + 1
							# else:
							# 	delay_amount = 1
							delay_amount = 1
							# tmp_delay = tmp_delay.append({'txn_id':None, 'entity_id':self.entity_id, 'delay':delay_amount, 'hours':hours_remain, 'job':req_item, 'item_id':item}, ignore_index=True)
							tmp_delay = pd.concat([tmp_delay, pd.DataFrame({'txn_id':[None], 'entity_id':[self.entity_id], 'delay':[delay_amount], 'hours':[hours_remain], 'job':[req_item], 'item_id':[item]})], ignore_index=True)
							# print('tmp_delay: \n{}'.format(tmp_delay))
					# print('Labour Done End: {} | Labour Required: {} | WIP Choice: {}'.format(labour_done, labour_required, wip_choice))
					if (wip_choice or wip_complete) and not hours_remain and not time_check:
						time_required = False
					if (not wip_choice and not wip_complete) and partial is None:
						try:
							if man and incomplete:
								individuals = self.get_children(founder=True, ids=False)
								hours_avail = sum(indv.hours for indv in individuals)
								constraint_qty = math.floor((hours_avail + labour_done) / (req_qty * (1-modifier)))
								max_qty_possible = min(constraint_qty, max_qty_possible)
							else:
								constraint_qty = math.floor(labour_done / (req_qty * (1-modifier)))
								max_qty_possible = min(constraint_qty, max_qty_possible)
						except ZeroDivisionError:
							constraint_qty = 'inf'
							max_qty_possible = min(max_qty_possible, qty)
						# if item_type == 'Education': # TODO Handle this better
						# 	max_qty_possible = max(1, max_qty_possible)
						# print('Max Qty Possible with {} Labour: {}'.format(req_item, max_qty_possible))
					else:
						if labour_done > 0 and not incomplete:# and labour_required != labour_done:
							# max_qty_possible = 1
							# constraint_qty = 1
							if wip_choice or wip_complete: # TODO Test this better
								max_qty_possible = min(max_qty_possible, qty)
								constraint_qty = None
							else:
								max_qty_possible = 1
								constraint_qty = 1
						else:
							if wip_choice:# or wip_complete: # TODO Test this better
								if none_qualify:
									max_qty_possible = 0
									constraint_qty = 0
								else:
									max_qty_possible = min(max_qty_possible, qty)
									constraint_qty = None
							else:
								max_qty_possible = 0
								constraint_qty = 0
					if v: print('Labour Max Qty Possible for {}: {} | WIP Choice: {} | WIP Complete: {} | Time Req: {} | Partial: {} | Labour Done: {} | Constraint Qty: {} | Incomplete: {}'.format(item, max_qty_possible, wip_choice, wip_complete, time_required, partial, labour_done, constraint_qty, incomplete))
					# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':qty_held, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
					results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty * qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[qty_held], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)

			elif req_item_type == 'Education' and partial is None:
				modifier = 0
				if item_type == 'Job' or item_type == 'Labour' or item_type == 'Education':
					# if type(self) == Individual:
					if isinstance(self, Individual):
						edu_status = self.ledger.get_qty(items=req_item, accounts=['Education','Education Expense'])
						edu_status_wip = self.ledger.get_qty(items=req_item, accounts=['Studying Education'])
						# req_qty = int(req_qty)
						if v: print('{} has {} education hours for {} and requires {} to be a {}.'.format(self.name, edu_status, req_item, req_qty, item))
						if edu_status >= req_qty:
							if v: print('{} has knowledge of {} to create {}.'.format(self.name, req_item, item))
						elif edu_status + edu_status_wip >= req_qty:
							if v: print('{} is working on knowledge of {} to create {}.'.format(self.name, req_item, item))
							incomplete = True
							max_qty_possible = 0
						else:
							if not man and not check:
								req_qty_needed = req_qty - (edu_status + edu_status_wip)
								if v: print('Studying Education: {} | Hours Needed: {}'.format(req_item, req_qty_needed))
								req_time_required = False
								result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty=req_qty_needed, v=v)#, buffer=True)
								self.ledger.set_entity(self.entity_id)
								if req_time_required:
									edu_status_wip = self.ledger.get_qty(items=req_item, accounts=['Studying Education'])
									if edu_status_wip == 0:
										self.item_demanded(req_item, req_max_qty_possible, v=v)
								if not result:
									if v: print('Studying Education not successfull for: {}'.format(req_item))
									#entries = []
									incomplete = True
									max_qty_possible = 0
									edu_status = self.ledger.get_qty(items=req_item, accounts=['Studying Education'])
									if edu_status == 0 and not req_time_required:
										self.item_demanded(req_item, req_qty_needed, v=v)
								else:
									edu_status = self.ledger.get_qty(items=req_item, accounts=['Education','Education Expense'])
									if v: print('{} now has {} education hours for {} and requires {} to be a {}.'.format(self.name, edu_status, req_item, req_qty, item))
									if edu_status < req_qty:
										#entries = []
										incomplete = True
										max_qty_possible = 0
							else:
								# TODO Test this
								incomplete = True
								max_qty_possible = 0
						constraint_qty = None
						# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':edu_status, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
						results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[edu_status], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)

			elif req_item_type == 'Technology' and partial is None:
				modifier = 0
				self.ledger.reset()
				tech_done_status = self.ledger.get_qty(items=req_item, accounts=['Technology'])
				tech_status_wip = self.ledger.get_qty(items=req_item, accounts=['Researching Technology'])
				tech_status = tech_done_status + tech_status_wip
				if tech_done_status >= req_qty:
					if v: print('{} has knowledge of {} technology to create {}.'.format(self.name, req_item, item))
				elif (tech_done_status + tech_status_wip) >= req_qty:
					if v: print('{} is working on knowledge of {} technology to create {}.'.format(self.name, req_item, item))
					max_qty_possible = 0
					incomplete = True
				else:
					if not man:
						if v: print('{} attempting to research technology: {}'.format(self.name, req_item))
						req_time_required = False
						result, req_time_required, req_max_qty_possible, req_incomplete = self.produce(req_item, qty=req_qty, v=v)#, buffer=True)
						if req_time_required:
							tech_status = self.ledger.get_qty(items=req_item, accounts=['Researching Technology'])
							if tech_status == 0:
								self.item_demanded(req_item, req_qty, v=v)
							else:
								if v: print('{} researching technology: {}'.format(self.name, req_item))
						if not result:
							if v: print('{} technology researching not successfull for: {}'.format(self.name, req_item))
							#entries = []
							incomplete = True
							tech_status = self.ledger.get_qty(items=req_item, accounts=['Researching Technology'])
							if tech_status == 0 and not req_time_required:
								self.item_demanded(req_item, req_qty, v=v)
						else:
							tech_status = self.ledger.get_qty(items=req_item, accounts=['Technology'])
							if v: print('{} technology status for {}: {}'.format(self.name, req_item, tech_status))
							if tech_status == 0:
								#entries = []
								incomplete = True
						max_qty_possible = 0
					else:
						incomplete = True
				constraint_qty = None
				# results = results.append({'item_id':req_item, 'qty':req_qty * qty, 'modifier':modifier, 'qty_req':(req_qty * (1-modifier) * qty), 'qty_held':tech_status, 'incomplete':incomplete, 'max_qty':constraint_qty}, ignore_index=True)
				results = pd.concat([results, pd.DataFrame({'item_id':[req_item], 'qty':[req_qty * qty], 'modifier':[modifier], 'qty_req':[(req_qty * (1-modifier) * qty)], 'qty_held':[tech_status], 'incomplete':[incomplete], 'max_qty':[constraint_qty]})], ignore_index=True)
			self.ledger.reset()
		if incomplete or check:
			for individual in world.gov.get(Individual):
				if v: print('Reset hours for {} from {} to {}.'.format(individual.name, individual.hours, individual.hours+hours_deltas[individual.name]))
				individual.set_hours(-hours_deltas[individual.name])
			hold_event_ids = []
			if v: print(f'{self.name} cannot {action} {qty} {item} at this time. The max possible is: {max_qty_possible}\n')
			if v: print(time_stamp() + 'Hours reset on {}:'.format(world.now))
			for individual in world.gov.get(Individual):
				if v: print('{} Hours: {}'.format(individual.name, individual.hours))
			if v: print()
			if max_qty_possible and not man and not check and not wip_choice and whole_qty <= max_qty_possible:
				event = []
				# print('tmp_gl before recur for item: {} \n{}'.format(item, self.gl_tmp))
				self.gl_tmp = pd.DataFrame(columns=world.cols) # TODO Confirm this is needed
				if v: print(f'{self.name} will try again to {action} {item} but for {max_qty_possible} units. whole_qty: {whole_qty} | max_qty_possible {max_qty_possible}')
				incomplete, event_max_possible, time_required, max_qty_possible = self.fulfill(item, max_qty_possible, man=man, v=v)
				event += event_max_possible
		else:
			world.delay = tmp_delay.copy(deep=True) # TODO This would not factor in any changes to world.delay from a lower stack frame but that might not matter
			world.set_table(world.delay, 'delay')
			# TODO Maybe avoid labour WIP by treating labour like a commodity and then "consuming" it when it is used in the WIP
			if not wip_choice or man:
				self.hold_event_ids += hold_event_ids
			if isinstance(self, Individual):
				self.prod_hold += prod_hold
			# print('{} Final self.hold_event_ids for {}: {} | {}'.format(self.name, item, self.hold_event_ids, hold_event_ids))
		self.gl_tmp = pd.DataFrame(columns=world.cols)
		if show_results:
			if incomplete:
				if v: print(f'\nResult of trying to produce {qty} {item} by {self.name}:\n{results}')
			else:
				if v: print(f'\nResult of producing {qty} {item} by {self.name}:\n{results}')
		if v: print(f'!fulfill return due to finishing for item: {item}. | incomplete: {incomplete} | time_required: {time_required} | max_qty_possible: {max_qty_possible}')
		return incomplete, event, time_required, max_qty_possible

	def produce(self, item, qty, debit_acct=None, credit_acct=None, desc=None , price=None, reqs='requirements', amts='amount', man=False, wip=False, buffer=False, vv=False, v=True):
		# TODO Replace man with self.user
		if v: print()
		if v: print(f'***** Produce {qty} {item} ****')
		item_type = world.get_item_type(item)
		if item_type == 'Land': # TODO This is a temp hackey fix
			produce_event = self.claim_land(item, qty, buffer=buffer)
			return produce_event, False, produce_event[-1][8], False
		if v: print(f'Produce: {item} | qty: {qty} | item_type: {item_type} | wip: {wip} | name: {self.name} | user: {self.user}')
		if vv: print(f'produces: {self.produces}')
		if not self.user:
			# if isinstance(self, Individual):
			# 	if item_type == 'Education':
			# 		pass
			if item not in self.produces and not (isinstance(self, Individual) and item_type == 'Education'): # TODO Should this be kept long term?
				if v: print(f'{self.name} does not produce {item}.')
				return [], False, 0, True
		if wip: # TODO Test this
			wip_result = self.wip_check(items=item)
			if wip_result:
				wip_qty = wip_result[-1][8]
				if v: print(f'WIP for {item} completed for {wip_qty}.')
				if wip_qty >= qty:
					return [], False, 0, True
				else:
					qty -= wip_qty
		incomplete, produce_event, time_required, max_qty_possible = self.fulfill(item, qty, reqs=reqs, amts=amts, man=man, show_results=True, v=v)
		if incomplete:
			return [], time_required, max_qty_possible, incomplete
		orig_qty = qty
		qty = max_qty_possible
		if v: print(f'Qty after set to max_qty_possible: {qty} | orig_qty: {qty}')
		# print('Item: {} | Max Qty Possible: {}'.format(item, max_qty_possible))
		# print('Produced Qty: {} | Orig Qty:{}'.format(qty, orig_qty))
		# Mark Land etc. as in use (is now handled in fulfill)
		# hold_incomplete, in_use_event, hold_time_required, hold_max_qty_possible = self.fulfill(item, qty=qty, reqs='hold_req', amts='hold_amount')
		# if hold_incomplete:
		# 	print('{} cannot hold {} {} it produced.'.format(self.name, qty, item))
		# 	return [], hold_time_required, hold_max_qty_possible, hold_incomplete
		# produce_event += in_use_event
		if item_type == 'Subscription':
			if v: print('Cannot produce a Subscription; will try and order it.')
			outcome = self.order_subscription(item, v=v)
			return [], time_required, max_qty_possible, incomplete
		elif item_type == 'Education':
			# Treat Education like a service
			if v: print('Cannot produce Education; will try and purchase it as a Service.')
			# TODO This may be bugged and needs better handling logic
			if produce_event:
				qty = produce_event[0][8]
				max_qty_possible = max(0, max_qty_possible - qty)
			outcome = self.purchase(item, qty, v=v)
			if not outcome:
				return [], time_required, max_qty_possible, incomplete
			produce_event += outcome
			# return [], time_required, max_qty_possible, incomplete

		#print('Item Type: {}'.format(item_type))
		if debit_acct is None:
			if item_type == 'Technology':
				debit_acct = 'Technology'
			elif item_type == 'Education':
				debit_acct = 'Education'
			elif item_type == 'Equipment':
				if isinstance(self, Individual) or man: # TODO Check this
					debit_acct = 'Equipment'
				else:
					debit_acct = 'Inventory'
			elif item_type == 'Buildings':
				if isinstance(self, Individual) or man:
					debit_acct = 'Buildings'
				else:
					debit_acct = 'Inventory'
			elif item_type == 'Land':
				if isinstance(self, Individual) or man:
					debit_acct = 'Land'
				else:
					debit_acct = 'Inventory'
			else:
				debit_acct = 'Inventory'
			if time_required:
				if item_type == 'Technology':
					debit_acct = 'Researching Technology'
				elif item_type == 'Education':
					debit_acct='Studying Education'
				elif item_type == 'Equipment':
					if isinstance(self, Individual) or man:
						debit_acct = 'WIP Equipment'
					else:
						debit_acct = 'WIP Inventory'
				elif item_type == 'Buildings':
					if isinstance(self, Individual) or man:
						debit_acct = 'Building Under Construction'
					else:
						debit_acct = 'WIP Inventory'
				else:
					debit_acct = 'WIP Inventory'
		else:
			if time_required:
				if debit_acct == 'Technology':
					debit_acct = 'Researching Technology'
				elif debit_acct == 'Education':
					debit_acct='Studying Education'
				elif debit_acct == 'Equipment':
					debit_acct = 'WIP Equipment'
				elif debit_acct == 'Buildings':
					debit_acct = 'Building Under Construction'
				else:
					debit_acct = 'WIP Inventory'
		if credit_acct is None:
			if item_type == 'Technology':
				credit_acct = 'Technology Produced'
			elif item_type == 'Education':
				credit_acct = 'Education Produced'
			elif item_type == 'Equipment':
				credit_acct = 'Equipment Produced'
			elif item_type == 'Buildings':
				credit_acct = 'Building Produced'
			else:
				credit_acct = 'Goods Produced' # TODO Change
			# if time_required:
			# 	credit_acct = credit_acct
		if desc is None:
			if item_type == 'Technology':
				desc = item + ' researched'
				if time_required:
					desc = 'Researching ' + item
			elif item_type == 'Education':
				desc = item + ' studied'
				if time_required:
					desc = 'Studying ' + item
			elif item_type == 'Equipment':
				if reqs == 'int_rate_fix':
					desc = item + ' captured'
				else:
					desc = item + ' manufactured'
				if time_required:
					if reqs == 'int_rate_fix':
						desc = 'Capturing ' + item
					else:
						desc = 'Manufacturing ' + item
			elif item_type == 'Buildings':
				desc = item + ' constructed'
				if time_required:
					desc = 'Constructing ' + item
			else:
				if reqs == 'int_rate_fix':
					desc = item + ' caught'
				else:
					desc = item + ' produced'
				if time_required:
					if reqs == 'int_rate_fix':
						desc = item + ' being caught'
					else:
						desc = item + ' in process'
		# if args.random and item_type == 'Commodity':
		# 	rand = random.randint(1, 3)
		# 	qty = qty * rand
		cost_entries = [[]]
		indirect_cost_entries = [[]]
		produce_entry = []
		if price is None:
			# Add ticks based depreciation to cost
			# TODO Factor in how much capacity is used
			cost = 0

			# Filter GL for entity
			self.ledger.set_entity(self.entity_id)
			# Find last Cost Pool entry
			cost_pool_gls = self.ledger.gl.loc[self.ledger.gl['debit_acct'] == 'Cost Pool']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	if vv: print('Cost Pool TXNs: \n{}'.format(cost_pool_gls))
			if not cost_pool_gls.empty and not isinstance(self, Individual):
			# if not cost_pool_gls.empty and type(self) != Individual:
				last_txn = cost_pool_gls.index.values[-1]
				# if vv: print('Last Cost Pool TXN: {}'.format(last_txn))
				# Filter for all entries since then
				self.ledger.set_start_txn(last_txn)
				recent_gls = self.ledger.gl
				recent_gls['debit_acct_type'] = recent_gls.apply(lambda x: self.ledger.get_acct_elem(x['debit_acct']), axis=1)
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	if vv: print('Recent GLs Acct Type: \n{}'.format(recent_gls))
				# Filter for expense entries
				indirect_costs = recent_gls.loc[recent_gls['debit_acct_type'] == 'Expense']
				indirect_costs = indirect_costs.loc[indirect_costs['debit_acct'] != 'Cost of Goods Sold']
				indirect_costs = indirect_costs.loc[indirect_costs['debit_acct'] != 'Dividend Expense'] # TODO Divs should not be an expense
				# Do logic like below
				cost += indirect_costs['amount'].sum()
				indirect_costs.drop('debit_acct_type', axis=1, inplace=True)
				#print('Cost DF: \n{}'.format(indirect_costs))
				# if vv: print('Indirect Cost: {}'.format(cost))
				indirect_costs = indirect_costs[['event_id', 'entity_id', 'cp_id', 'date', 'loc', 'description', 'item_id', 'price', 'qty', 'credit_acct', 'debit_acct', 'amount']]
				#print('Cost DF After Swap: \n{}'.format(indirect_costs))
				indirect_costs.rename({'debit_acct': 'credit_acct', 'credit_acct': 'debit_acct'}, axis='columns', inplace=True)
				#print('Cost DF After Rename: \n{}'.format(indirect_costs))
				indirect_costs.debit_acct = 'Cost Pool'
				indirect_costs['qty'] = indirect_costs['qty'].fillna('')
				indirect_costs['price'] = indirect_costs['price'].fillna('')
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	if vv: print('Indirect Cost DF End: \n{}'.format(indirect_costs))
				indirect_cost_entries = indirect_costs.values.tolist()
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	if vv: print('Indirect Cost Entries: \n{}'.format(indirect_cost_entries))
				if item_type != 'Service' and item_type != 'Education':
					produce_event += indirect_cost_entries
			self.ledger.reset()

			cost_df = pd.DataFrame(produce_event, columns=world.cols)
			cost_df = cost_df.loc[cost_df['entity_id'] == self.entity_id]
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				if vv: print('Cost DF Start: \n{}'.format(cost_df))
			if not cost_df.empty:
				cost_df['debit_acct_type'] = cost_df.apply(lambda x: self.ledger.get_acct_elem(x['debit_acct']), axis=1)
				with pd.option_context('display.max_rows', None, 'display.max_columns', None):
					if vv: print('Cost DF Acct Type: \n{}'.format(cost_df))
				cost_df = cost_df.loc[cost_df['debit_acct_type'] == 'Expense']
				if not cost_df.empty:
					cost += cost_df['amount'].sum()
					cost_df.drop('debit_acct_type', axis=1, inplace=True)
					#print('Cost DF: \n{}'.format(cost_df))
					#print('Cost Price: {}'.format(cost))
					cost_df = cost_df[['event_id', 'entity_id', 'cp_id', 'date', 'loc', 'description', 'item_id', 'price', 'qty', 'credit_acct', 'debit_acct', 'amount']]
					#print('Cost DF After Swap: \n{}'.format(cost_df))
					cost_df.rename({'debit_acct': 'credit_acct', 'credit_acct': 'debit_acct'}, axis='columns', inplace=True)
					#print('Cost DF After Rename: \n{}'.format(cost_df))
					cost_df.debit_acct = 'Cost Pool'
					with pd.option_context('display.max_rows', None, 'display.max_columns', None):
						if vv: print('Cost DF End: \n{}'.format(cost_df))
					cost_entries = cost_df.values.tolist()
					with pd.option_context('display.max_rows', None, 'display.max_columns', None):
						if vv: print('Cost Entries: \n{}'.format(cost_entries))
					if item_type != 'Service' and item_type != 'Education':
						produce_event += cost_entries
					if vv: print('Cost 1: {}'.format(cost))
			cost = round(cost, 2)
			if v: print(f'Produce price 01: {price} | Cost: {cost} | Qty: {qty}')
			price = round(cost / qty, 2)
			if v: print(f'Produce price 02: {price}')
			if price == 0: # No cost
				price = world.get_price(item, self.entity_id)
				if v: print(f'Produce price 03: {price}')
				cost = round(price * qty, 2)
		else:
			cost = round(price * qty, 2)
		if item_type != 'Service' and item_type != 'Education':
			if cost_entries[0]:
				credit_acct = 'Cost Pool'
			produce_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', desc, item, price, qty, debit_acct, credit_acct, cost ]
		if produce_entry:
			produce_event += [produce_entry]

		byproducts = world.items['byproduct'][item]
		byproduct_amts = world.items['byproduct_amt'][item]
		if byproducts is not None and byproduct_amts is not None:
			if isinstance(byproducts, str):
				byproducts = [x.strip() for x in byproducts.split(',')]
			# byproducts = list(set(filter(None, byproducts)))
			byproducts = list(collections.OrderedDict.fromkeys(filter(None, byproducts)))
			if isinstance(byproduct_amts, str):
				byproduct_amts = [x.strip() for x in byproduct_amts.split(',')]
			# byproduct_amts = list(filter(None, byproduct_amts))
			byproduct_amts = list(collections.OrderedDict.fromkeys(filter(None, byproduct_amts)))
			for byproduct, byproduct_amt in zip(byproducts, byproduct_amts):
				byproduct_item_type = world.get_item_type(byproduct)
				desc = item + ' byproduct produced'
				# TODO Support other account types, such as for pollution
				by_price = 0 #world.get_price(byproduct, self.entity_id)
				byproduct_amt = float(byproduct_amt)
				if debit_acct == 'WIP Inventory': # TODO Proper accounting for polution
					debit_acct_by = 'Inventory'
				else:
					debit_acct_by = 'Inventory'
				byproduct_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', desc, byproduct, by_price, round(byproduct_amt * qty), debit_acct_by, credit_acct, round(round(by_price * byproduct_amt) * qty, 2) ]
				if byproduct_entry:
					produce_event += [byproduct_entry]
		qty_distribute = qty
		if item_type == 'Technology':
			current_demand = world.demand[(world.demand['item_id'] == item) & (world.demand['qty'] == qty)]
		else:
			current_demand = world.demand[(world.demand['entity_id'] == self.entity_id) & (world.demand['item_id'] == item) & (world.demand['qty'] == qty)]
		if not current_demand.empty:
			qty_distribute -= qty
			to_drop = current_demand.index.tolist()
			world.demand = world.demand.drop(to_drop).reset_index(drop=True)
			world.set_table(world.demand, 'demand')
			if v: print('{} exists on the demand table exactly for {} will drop index items {}.'.format(item, self.name, to_drop))
			with pd.option_context('display.max_rows', None):
				if vv: print('World Demand: {} \n{}'.format(world.now, world.demand))
		to_drop = []
		# if orig_qty != qty and qty != 0:
		# 	print('World Demand: \n{}'.format(world.demand))
		for index, demand_item in world.demand.iterrows():
			if qty_distribute == 0:
				break
			if item_type == 'Education':
				if demand_item['item_id'] == item and demand_item['entity_id'] == self.entity_id:
					if qty_distribute >= demand_item['qty']:
						to_drop.append(index)
						qty_distribute -= demand_item['qty']
					else:
						world.demand.at[index, 'qty'] -= qty_distribute
						qty_distribute -= qty_distribute
			else:
				if demand_item['item_id'] == item:
					if qty_distribute >= demand_item['qty']:
						to_drop.append(index)
						qty_distribute -= demand_item['qty']
					else:
						world.demand.at[index, 'qty'] -= qty_distribute
						qty_distribute -= qty_distribute
		if to_drop:
			world.demand = world.demand.drop(to_drop).reset_index(drop=True)
			world.set_table(world.demand, 'demand')
			if v: print('{} exists on the demand table will drop index items {}.'.format(item, to_drop))
			with pd.option_context('display.max_rows', None):
				if vv: print('World Demand: {} \n{}'.format(world.now, world.demand))
		if orig_qty != qty and qty != 0:
			if v: print('Partially Fulfilled Qty for: {} | Orig Qty: {} | Qty Produced: {}'.format(item, orig_qty, qty))
			# print('World Demand Changed: \n{}'.format(world.demand))
		if buffer:
			return produce_event, time_required, max_qty_possible, incomplete
		# Ensure the same event_id for all transactions
		event_id = max([entry[0] for entry in produce_event])
		for entry in produce_event:
			if entry[0] != event_id:
				if entry[0] in self.hold_event_ids:
					self.hold_event_ids = [event_id if x == entry[0] else x for x in self.hold_event_ids]
				if isinstance(self, Individual):
					if entry[0] in self.prod_hold:
						self.prod_hold = [event_id if x == entry[0] else x for x in self.prod_hold]
				if vv: print('{} Orig event_id: {} | New event_id: {} | {}'.format(self.name, entry[0], event_id, self.hold_event_ids))
				entry[0] = event_id
		self.ledger.journal_entry(produce_event)
		if world.delay['txn_id'].isnull().values.any():
			rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			# Get list of WIP txns for different item types
			wip_txns = self.ledger.gl[(self.ledger.gl['debit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (self.ledger.gl['entity_id'] == self.entity_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
			if vv: print('WIP TXNs: \n{}'.format(wip_txns))
			if not wip_txns.empty:
				txn_id = int(wip_txns.index[-1])
				partial_work = world.delay.loc[world.delay['txn_id'].isnull()]
				if vv: print('Partial Work: \n{}'.format(partial_work))
				partial_index = partial_work.index[-1]
				if vv: print('Partial Index: {}'.format(partial_index))
				world.delay.at[partial_index, 'txn_id'] = txn_id
				world.set_table(world.delay, 'delay')
				if vv: print('World Delay: \n{}'.format(world.delay))
		if produce_event[-1][-3] in ['Inventory', 'WIP Inventory']:
			self.set_price(item, qty, v=v)
		else:
			self.set_price(item, qty, at_cost=True, v=v)
		# if man: # TODO Make this the case for not man also
		if v: print(f'***** Produce end {qty} {item} ****')
		if v: print()
		return produce_event, time_required, max_qty_possible, incomplete
		# return qty, time_required # TODO Return the qty instead of True, or can use max_qty_possible for qty if complete

	def set_produce(self, item, qty, freq=0, one_time=False, man=False):
		# TODO Maybe make multindex with item_id and entity_id
		# pd.DataFrame(columns=['item_id', 'entity_id','qty', 'freq', 'last', 'one_time', 'man'])
		current_pro_queue = world.produce_queue.loc[(world.produce_queue['item_id'] == item) & (world.produce_queue['entity_id'] == self.entity_id)]
		if not current_pro_queue.empty:
			print('This item exists on the production queue as: \n{}'.format(current_pro_queue))
			print('It will be replaced with the new values below: ')
		# world.produce_queue = world.produce_queue.append({'item_id':item, 'entity_id':self.entity_id, 'qty':qty, 'freq':freq, 'last':freq, 'one_time':one_time, 'man':man,}, ignore_index=True)
		world.produce_queue = pd.concat([world.produce_queue, pd.DataFrame({'item_id':[item], 'entity_id':[self.entity_id], 'qty':[qty], 'freq':[freq], 'last':[freq], 'one_time':[one_time], 'man':[man]})], ignore_index=True)
		world.produce_queue = pd.concat([world.produce_queue, current_pro_queue]).drop_duplicates(keep=False) # TODO There may be a better way to get the difference between two dfs

		if one_time:
			index = world.produce_queue.last_valid_index()
			# print('Last index:', index)
			result, time_required, max_qty_possible, incomplete = self.produce(item, qty, man=man)
			if result:  # TODO This is a temp hackey fix
				if result[-1][9] == 'Land':
					qty = max_qty_possible
			if incomplete and max_qty_possible != 0 and one_time:
				qty = max_qty_possible
				result, time_required, max_qty_possible, incomplete = self.produce(item, qty, man=man)
			if result:
				# print('result qty:', qty)
				world.produce_queue.loc[index, 'last'] = world.produce_queue.loc[index, 'freq']
				world.produce_queue.loc[index, 'qty'] -= qty
				if world.produce_queue.loc[index, 'qty'] <= 0:
					world.produce_queue.drop([index], inplace=True)
				else:
					if self.hours > 0:
						self.auto_produce(index)

		world.set_table(world.produce_queue, 'produce_queue')
		print('Set Produce Queue by {}: \n{}'.format(self.name, world.produce_queue))

	def auto_produce(self, index=None, v=False):
		if v: print(f'\nChecking {self.name}\'s auto produce queue.')
		if world.produce_queue.empty:
			return
		entity_pro_queue = world.produce_queue.loc[world.produce_queue['entity_id'] == self.entity_id]
		if index is not None:
			entity_pro_queue = entity_pro_queue.loc[index]
			entity_pro_queue = entity_pro_queue.to_frame().T
		for index, que_item in entity_pro_queue.iterrows():
			if que_item['last'] == 0:
				item = que_item['item_id']
				man = que_item['man']
				qty = que_item['qty']
				if isinstance(man, str):
					if man == 'True':
						man = True
					else:
						man = False
				try: # TODO Temp for legacy save files
					one_time = que_item['one_time']
				except KeyError as e:
					world.produce_queue['one_time'] = False
					world.produce_queue = world.produce_queue[['item_id', 'entity_id', 'qty', 'freq', 'last', 'one_time', 'man']]
					one_time = False
				if isinstance(one_time, str):
					if one_time == 'True':
						one_time = True
					else:
						one_time = False
				if not world.delay.loc[(world.delay['entity_id'] == self.entity_id) & (world.delay['item_id'] == item)].empty:
					if v: print(f'Skipping autoproduce for {item} as it is already a WIP.')
					self.wip_check(time_only=not self.auto_wip)

				result, time_required, max_qty_possible, incomplete = self.produce(item, qty, man=man)
				if incomplete and max_qty_possible != 0 and one_time:
					qty = max_qty_possible
					result, time_required, max_qty_possible, incomplete = self.produce(item, qty, man=man)
				if result:
					world.produce_queue.loc[index, 'last'] = que_item['freq']
					if one_time:
						world.produce_queue.loc[index, 'qty'] -= qty
						if world.produce_queue.loc[index, 'qty'] <= 0:
							world.produce_queue.drop([index], inplace=True)
						else:
							if self.hours > 0:
								self.auto_produce(index)
			else:
				world.produce_queue.loc[index, 'last'] -= 1
		world.set_table(world.produce_queue, 'produce_queue')

	def get_raw(self, item, qty=1, raw=None, orig_item=None, base=False, v=False):
		if raw is None:
			raw = collections.defaultdict(int)
		if orig_item is None:
			orig_item = item
		item_info = world.items.loc[item]
		item_type = world.get_item_type(item)
		# print(f'{item}:\n{item_info}')
		if item_info['requirements'] is None or item_info['amount'] is None:
			if base:
				if item_type in ['Technology', 'Education']:
					raw[item] = qty
				else:
					raw[item] += qty
			return raw # Base case
		requirements = [x.strip() for x in item_info['requirements'].split(',')]
		requirement_types = [world.get_item_type(requirement) for requirement in requirements]
		amounts = [x.strip() for x in item_info['amount'].split(',')]
		amounts = list(map(float, amounts))
		requirements_details = list(itertools.zip_longest(requirements, requirement_types, amounts))
		if v: print(f'Requirements Details for {qty} {item}: \n{requirements_details}')
		for requirement in requirements_details:
			# TODO Make option for this to catch when items have no requirements only
			if requirement[1] in ['Land', 'Commodity', 'Labour', 'Job', 'Education', 'Technology', 'Time'] and not base:
				# print(f'inner: {item} {requirement}')
				if requirement[1] in ['Technology', 'Education']:
					raw[requirement[0]] = requirement[2]
				else:
					raw[requirement[0]] += (requirement[2] * qty)
			elif 'animal' in str(item_info['freq'] or ''):
				raw[requirement[0]] += (requirement[2] * qty)
			else:
				if requirement[1] in ['Education']:
					qty = 1
				self.get_raw(requirement[0], requirement[2] * qty, raw, item, base=base, v=v)
		if item != orig_item:
			return raw
		raw = pd.DataFrame(raw.items(), index=None, columns=['item_id', 'qty'])
		# total = raw['qty'].sum()
		# raw = raw.append({'item_id':'Total', 'qty':total}, ignore_index=True)
		raw.loc['Total'] = raw.sum()
		if base:
			if v: print(f'\nTotal base resources needed to produce: {qty} {item}')
		else:
			if v: print(f'\nTotal resources needed to produce: {qty} {item}')
		with pd.option_context('float_format', '{:,.1f}'.format):
			if v: print(raw)
		return raw

	def wip_check(self, check=False, time_only=False, items=None, v=False):
		if items is not None: # TODO Not finished
			if not isinstance(items, (list, tuple)):
				items = [x.strip().title() for x in items.split(',')]
			wip_items = world.delay.loc[(world.delay['item_id'].isin(items)) & (world.delay['entity_id'] == self.entity_id)]
			if wip_items.empty:
				return
		self.ledger.refresh_ledger()
		rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of WIP txns for different item types
		if items is not None:
			wip_done_txns = self.ledger.gl[(self.ledger.gl['credit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['item_id'].isin(items)) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]['event_id']
			if v: print('wip_done_txns for items:\n', wip_done_txns)
			wip_txns = self.ledger.gl[(self.ledger.gl['debit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['item_id'].isin(items)) & (~self.ledger.gl['event_id'].isin(rvsl_txns)) & (~self.ledger.gl['event_id'].isin(wip_done_txns))]
		else:
			wip_done_txns = self.ledger.gl[(self.ledger.gl['credit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (self.ledger.gl['entity_id'] == self.entity_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]['event_id']
			if v: print('wip_done_txns:\n', wip_done_txns)
			wip_txns = self.ledger.gl[(self.ledger.gl['debit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (self.ledger.gl['entity_id'] == self.entity_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns)) & (~self.ledger.gl['event_id'].isin(wip_done_txns))]
		if v: print('WIP TXNs: \n{}'.format(wip_txns))
		if not wip_txns.empty:
			result = []
			if v: print('WIP Transactions: \n{}'.format(wip_txns))
			# Compare the gl dates to the WIP time from the items table
			#items_time = world.items[world.items['requirements'].str.contains('Time', na=False)]
			items_continuous = world.items[world.items['freq'].str.contains('continuous', na=False)]
			for index, wip_lot in wip_txns.iterrows():
				time_check = False
				wip_event = []
				hours = None
				item = wip_lot['item_id']
				qty = wip_lot['qty']
				if v: print('WIP Index Check: {}'.format(index))
				if v: print('WIP Item Check: {}'.format(item))
				#if v: print('Continuous Items: \n{}'.format(items_continuous))
				requirements = world.items.loc[item, 'requirements']
				if isinstance(requirements, str):
					requirements = [x.strip() for x in requirements.split(',')]
				requirements = list(filter(None, requirements))
				if v: print('WIP Requirements for {}: {}'.format(item, requirements))
				timespan = 0
				for i, requirement in enumerate(requirements):
					requirement_type = world.get_item_type(requirement)
					if v: print('Requirement Timespan: {} | {}'.format(requirement, i))
					if requirement_type == 'Time':
						time_check = True
						break
				if v: print('Time Requirement: {}'.format(requirement))
				#amounts = [x.strip() for x in items_time['amount'][item].split(',')]
				amounts = world.items.loc[item, 'amount']
				if isinstance(amounts, str):
					amounts = [x.strip() for x in amounts.split(',')]
				amounts = list(map(float, amounts))
				if v: print('Amounts: {}'.format(amounts))
				if time_check: # TODO This will cause problems where an item requires Time and a lot of labour such that it becomes WIP
					if v: print('Time Check for: {}'.format(requirement))
					timespan = amounts[i]
					date_done = (datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=int(timespan))).date()
					days_left = (date_done - world.now).days
					delayed = None
					if not world.delay.empty:
						try:
							delayed = world.delay.loc[world.delay['txn_id'] == index, 'delay'].values[0]
						except Exception as e:
							delayed = None
					if days_left < 0 and delayed is None:
						continue
					for equip_requirement in requirements:
						if v: print('Equip Requirement: {}'.format(equip_requirement))
						if equip_requirement in items_continuous.index.values:
							result = self.use_item(equip_requirement, check=check)
							if not result and not check:
								print('{} WIP Progress for {} using equipment was not successfull.'.format(self.name, item))
								if world.delay.empty:
									# world.delay = world.delay.append({'txn_id':index, 'entity_id':self.entity_id, 'delay':1, 'hours':None, 'job':None, 'item_id':item}, ignore_index=True)
									world.delay = pd.concat([world.delay, pd.DataFrame({'txn_id':[index], 'entity_id':[self.entity_id], 'delay':[1], 'hours':[None], 'job':[None], 'item_id':[item]})], ignore_index=True)
									world.set_table(world.delay, 'delay')
								elif index in world.delay['txn_id'].values:
									world.delay.loc[world.delay['txn_id'] == index, 'delay'] += 1
									world.set_table(world.delay, 'delay')
								else:
									# world.delay = world.delay.append({'txn_id':index, 'entity_id':self.entity_id, 'delay':1, 'hours':None, 'job':None, 'item_id':item}, ignore_index=True)
									world.delay = pd.concat([world.delay, pd.DataFrame({'txn_id':[index], 'entity_id':[self.entity_id], 'delay':[1], 'hours':[None], 'job':[None], 'item_id':[item]})], ignore_index=True)
									world.set_table(world.delay, 'delay')
								return
					start_date = datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d').date()
					if v: print('Start Date: {}'.format(start_date))
					self.ledger.set_date(str(start_date))
					modifier, items_info = self.check_productivity(requirement)
					if v: print('Modifier: {}'.format(modifier))
					self.ledger.reset()
					self.ledger.set_entity(self.entity_id)
					if modifier:
						if v: print('Time Modifier Item: {}'.format(items_info['item_id'].iloc[0]))
						entries = self.use_item(items_info['item_id'].iloc[0], check=check)
						if not entries:
							entries = []
							modifier = 0
						if entries is True:
							entries = []
						wip_event += entries
					else:
						modifier = 0
					self.ledger.reset()
					if v: print('Modifier End: {}'.format(modifier))
					timespan = timespan * (1 - modifier)
				elif time_only:
					continue
				if check:
					continue
				delay = 0
				hours = None
				partial_index = None
				if not world.delay.empty:
					try:
						delay = world.delay.loc[world.delay['txn_id'] == index, 'delay'].values[0]
						hours = world.delay.loc[world.delay['txn_id'] == index, 'hours'].values[0]
						if hours is not None:
							partial_index = world.delay.loc[world.delay['txn_id'] == index].index.tolist()[0]
							if v: print('Partial Index: {}'.format(partial_index))
						if hours is None:
							if delay == 1:
								print(f'{item} delayed by {delay} day.')
							else:
								print(f'{item} delayed by {delay} days.')
						else:
							if delay == 1:
								print(f'{item} delayed by {delay} day and {hours} hours.')
							else:
								print(f'{item} delayed by {delay} days and {hours} hours.')
					except (KeyError, IndexError) as e:
						delay = 0
						hours = None
					if hours:# is not None:
						job = world.delay.loc[world.delay['txn_id'] == index, 'job'].values[0] # TODO Test items requiring lots of labour for more than one job
						if v: print('WIP Partial Job: {}'.format(job))
						partial_index = world.delay.loc[world.delay['txn_id'] == index].index.tolist()[0]
						if v: print('Partial Index: {}'.format(partial_index))
						incomplete, partial_work_event, time_required, max_qty_possible = self.fulfill(item, qty=1, partial=partial_index, man=self.user, v=v)
						if v: print('Partial WIP Fulfill - Incomplete: {} | Time Required: {}\nPartial WIP Event: \n{}'.format(incomplete, time_required, partial_work_event))
						if incomplete or not partial_work_event:
							world.delay.at[partial_index, 'delay'] += 1
							days = (world.now - datetime.datetime(1986,10,1).date()).days
							print('Current WIP day:', days)
							print('{} WIP Progress for {} was not successfull.'.format(self.name, item))
							continue
						else:
							work_df = pd.DataFrame(partial_work_event, columns=world.cols)
							hours_worked = work_df.loc[(work_df['item_id'] == job) & (work_df['debit_acct'] == 'Wages Expense')]['qty'].sum()
							print(f'wip hours_worked: {hours_worked}')
							current_delay_hours = world.delay.loc[partial_index, 'hours']
							print(f'wip current_delay_hours: {current_delay_hours}')
							remain_wip_hours = max(current_delay_hours - hours_worked, 0)
							world.delay.at[partial_index, 'hours'] = remain_wip_hours #partial_work_event[-1][8]
							if world.delay.at[partial_index, 'hours'] != 0:
								world.delay.at[partial_index, 'delay'] += 1 # TODO This may not be needed with hours == 0 check below
							if v: print('World Delay Adj: \n{}'.format(world.delay))
							world.set_table(world.delay, 'delay')
							for entry in partial_work_event:
								if entry[0] != wip_lot['event_id']:
									if entry[0] in self.hold_event_ids:
										self.hold_event_ids = [wip_lot['event_id'] if x == entry[0] else x for x in self.hold_event_ids]
									if isinstance(self, Individual):
										if entry[0] in self.prod_hold:
											self.prod_hold = [wip_lot['event_id'] if x == entry[0] else x for x in self.prod_hold]
									if v: print('{} WIP Orig Partial event_id: {} | New Partial event_id: {} | {}'.format(self.name, entry[0], wip_lot['event_id'], self.hold_event_ids))
									entry[0] = wip_lot['event_id']
							self.ledger.journal_entry(partial_work_event)
					try:
						delay = world.delay.loc[world.delay['txn_id'] == index, 'delay'].values[0]
						hours = world.delay.loc[world.delay['txn_id'] == index, 'hours'].values[0]
						if hours is None:
							if delay == 1:
								print(f'{item} delayed by {delay} day after.')
							else:
								print(f'{item} delayed by {delay} days after.')
						else:
							if delay == 1:
								print(f'{item} delayed by {delay} day and {hours} hours after.')
							else:
								print(f'{item} delayed by {delay} days and {hours} hours after.')
					except (KeyError, IndexError) as e:
						delay = 0
						hours = None
				timespan += delay
				if v: print('WIP lifespan with delay of {} for {}: {}'.format(delay, item, timespan))
				date_done = (datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=int(timespan))).date()
				if v: print('WIP date done for {}: {} | Today is: {} | Hours: {}'.format(item, date_done, world.now, hours))
				days_left = (date_done - world.now).days
				if days_left < timespan and days_left >= 0:
					if hours is None:
						if wip_lot['debit_acct'] == 'Researching Technology':
							world.tech = world.tech.set_index('technology')
							world.tech.at[item, 'time_req'] = int(timespan)
							world.tech.at[item, 'days_left'] = days_left
							world.tech = world.tech.reset_index()
							if v: print('wip tech table:\n', world.tech)
						print(f'{self.name} has {days_left} WIP days left for {item} out of {timespan}. [{index}]')
					else:
						print(f'{self.name} has {days_left} WIP days and {hours} hours left for {item} out of {timespan} days. [{index}]')
				# If the time elapsed has passed
				if hours == 0 and not time_check:
					date_done = world.now
					hours = None
				elif hours == 0:
					hours = None
				if date_done == world.now and (hours is None):# or hours is np.nan):
					# Undo "in use" entries for related items
					release_event = []
					release_event += self.release(item, event_id=wip_lot['event_id'], qty=qty, reqs='requirements', amts='amount')#, v=True)
					if v: print('wip_check release_event:\n', release_event)
					if release_event:
						for entry in release_event:
							entry_df = pd.DataFrame([entry], columns=world.cols)
							# self.ledger.gl = self.ledger.gl.append(entry_df)
							self.ledger.gl = pd.concat([self.ledger.gl, entry_df])
						self.gl_tmp = self.ledger.gl
						# if v: print('tail:\n', self.gl_tmp.tail())
					# Mark Land, Buildings, and Equipment as in use
					hold_incomplete, in_use_event, hold_time_required, hold_max_qty_possible = self.fulfill(item, qty=qty, reqs='hold_req', amts='hold_amount', buffer=True, v=v)
					self.ledger.reset()
					self.gl_tmp = None
					if hold_incomplete:
						print('{} cannot hold {} {} that it produced over time.'.format(self.name, qty, item))
						return
					wip_event += in_use_event
					if v: print('WIP is done for {} - Date Done: {} | Today is: {} | Hours: {}'.format(item, date_done, world.now, hours))
					# if partial_complete:
					if partial_index is not None: # TODO Capture additional labour costs in finished WIP entry
						world.delay = world.delay.drop([partial_index]).reset_index(drop=True)
					self.ledger.journal_entry(release_event)

					# Book the entry to move from WIP to Inventory
					if v: print('WIP account for {}: {}'.format(item, wip_lot['debit_acct']))
					# if v: print('WIP Lot: \n{}'.format(wip_lot))
					if wip_lot['debit_acct'] == 'Researching Technology':
						debit_acct = 'Technology'
						desc = wip_lot['item_id'] + ' researched'
					elif wip_lot['debit_acct'] == 'Studying Education':
						debit_acct = 'Education'
						desc = wip_lot['item_id'] + ' learned'
					elif wip_lot['debit_acct'] == 'WIP Equipment':
						debit_acct = 'Equipment' # TODO Test Equipment that takes Time to produce
						desc = wip_lot['item_id'] + ' manufactured'
					elif wip_lot['debit_acct'] == 'Building Under Construction':
						debit_acct = 'Buildings'
						desc = wip_lot['item_id'] + ' constructed'
					elif wip_lot['debit_acct'] == 'WIP Inventory':
						debit_acct = 'Inventory'
						desc = wip_lot['item_id'] + ' produced'
					else:
						debit_acct = 'Inventory'
						desc = wip_lot['item_id'] + ' produced'
					wip_entry = [ wip_lot['event_id'], wip_lot['entity_id'], wip_lot['cp_id'], world.now, wip_lot['loc'], desc, wip_lot['item_id'], wip_lot['price'], wip_lot['qty'] or '', debit_acct, wip_lot['debit_acct'], wip_lot['amount'] ]
					wip_event += [wip_entry]
					# Ensure the same event_id for all transactions
					for entry in wip_event:
						if entry[0] != wip_lot['event_id']:
							if entry[0] in self.hold_event_ids:
								self.hold_event_ids = [wip_lot['event_id'] if x == entry[0] else x for x in self.hold_event_ids]
							if entry[0] in self.prod_hold:
								self.prod_hold = [wip_lot['event_id'] if x == entry[0] else x for x in self.prod_hold]
							print('{} Orig WIP event_id: {} | New WIP event_id: {} | {}'.format(self.name, entry[0], wip_lot['event_id'], self.hold_event_ids))
							entry[0] = wip_lot['event_id']
					if v: print('WIP Event: \n{}'.format(wip_event))
					self.ledger.journal_entry(wip_event)
					if wip_lot['debit_acct'] == 'Researching Technology':
						world.tech = world.tech.set_index('technology')
						world.tech.at[item, 'status'] = 'done'
						world.tech.at[item, 'done_date'] = world.now
						world.tech = world.tech.reset_index()
						if v: print('wip tech table:\n', world.tech)
					if wip_event[-1][-3] == 'Inventory':
						self.set_price(wip_lot['item_id'], wip_lot['qty'], v=v)
					result += wip_event
			return result

	def release_check(self, v=False):
		self.hold_event_ids = list(collections.OrderedDict.fromkeys(filter(None, self.hold_event_ids))) # Remove any dupes
		if v: print('Release check for {}: {}'.format(self.name, self.hold_event_ids))
		release_event = []
		for event_id in self.hold_event_ids:
			if v: print('Release check for event_id:', event_id)
			release_event += self.release(event_id=event_id, v=v)
			# if v: print('release_event:\n', release_event)
		self.ledger.journal_entry(release_event)
		release_event_ids = [row[0] for row in release_event]
		if v: print('release_event_ids:', release_event_ids)
		self.hold_event_ids = [x for x in self.hold_event_ids if x not in release_event_ids]
		if v: print('Release check hold_event_ids:', self.hold_event_ids)
		self.hold_check()

	def hold_check(self, v=False):
		if not isinstance(self, Individual):
			return
		self.prod_hold = list(collections.OrderedDict.fromkeys(filter(None, self.prod_hold))) # Remove any dupes
		if v: print('{} | {}'.format(self.name, self.prod_hold))
		hold_event = []
		for event_id in self.prod_hold:
			if v: print('Hold check for event_id:', event_id)
			entries = self.ledger.gl.loc[(self.ledger.gl['event_id'] == event_id) & ~(self.ledger.gl['debit_acct'].str.contains('In Use', na=False))]
			# if v: print('entries:\n', entries)
			for _, entry in entries.iterrows():
				item = entry['item_id']
				qty = entry['qty']
				hold_incomplete, in_use_event, hold_time_required, hold_max_qty_possible = self.fulfill(item, qty=qty, reqs='hold_req', amts='hold_amount', v=v)
				if hold_incomplete:
					print('{} cannot hold {} {} it produced.'.format(self.name, item, qty)) # TODO Handle this condition somehow
				hold_event += in_use_event
			# if v: print('hold_event:\n', hold_event)
		self.ledger.journal_entry(hold_event)
		self.prod_hold = []

	def check_inv(self, v=False):
		if isinstance(self, Corporation):
			v = False
		if v: print('{} running inventory check.'.format(self.name))
		self.check_salary(check=True)
		self.check_subscriptions(check=True)
		self.wip_check(check=True)
		if v: print('{} finished inventory check.\n'.format(self.name))

	def check_prices(self):
		if self.produces is None:
			return
		self.ledger.set_entity(self.entity_id)
		for item in self.produces:
			if not self.check_eligible(item): # TODO Maybe cache this
				continue
			item_type = world.get_item_type(item)
			if item_type in ('Education', 'Technology', 'Land'): # TODO Support creating types of land like planting trees to make forest
				continue
			elif item_type in ('Subscription', 'Service'):
				self.ledger.set_date(str(world.now - datetime.timedelta(days=1)))
				hist_bal = self.ledger.balance_sheet(['Subscription Revenue','Service Revenue'], item)#, v=True)
				self.ledger.reset()
				self.ledger.set_entity(self.entity_id)
				print('Serv and Sub Hist Bal of {} for {}: {}'.format(item, self.name, hist_bal))
				if hist_bal:
					self.ledger.set_start_date(str(world.now - datetime.timedelta(days=1)))
					self.ledger.set_date(str(world.now - datetime.timedelta(days=1)))
					cur_bal = self.ledger.balance_sheet(['Subscription Revenue','Service Revenue'], item)#, v=True)
					self.ledger.reset()
					self.ledger.set_entity(self.entity_id)
					print('Cur Bal of {} for {}: {}'.format(item, self.name, cur_bal))
					if not cur_bal:
						self.adj_price(item, direction='down')
			else:
				qty_inv = self.ledger.get_qty(item, ['Inventory'])
				print('Qty of {} for {}: {}'.format(item, self.name, qty_inv))
				if qty_inv > 0:
					self.adj_price(item, direction='down')
				else:
					# If the entity has made the item in the past, and someone else has or is making the item, and they dont have and are not making the item
					wip_qty_inv = self.ledger.get_qty(item, ['WIP Inventory']) # Must be zero, qty in inv already known to be zero
					self.ledger.set_date(str(world.now - datetime.timedelta(days=1)))
					hist_bal = self.ledger.balance_sheet(['Sales','Goods Produced','Building Produced','Equipment Produced','Spoilage Expense'], item) # Must not be zero
					self.ledger.reset()
					global_qty_inv = self.ledger.get_qty(item, ['Inventory','WIP Inventory']) # Must be greater than zero
					self.ledger.set_entity(self.entity_id)
					print('Inv Hist Bal of {} for {}: {} | WIP Inv: {} | Global qty: {}'.format(item, self.name, hist_bal, wip_qty_inv, global_qty_inv))
					metrics = world.items.loc[item, 'metric']
					if metrics is None:
						metrics = []
					if hist_bal != 0 and wip_qty_inv == 0 and global_qty_inv > 0:
						self.adj_price(item, direction='down')
					elif hist_bal != 0 and ('spoilage' in metrics or 'obsolescence' in metrics) and wip_qty_inv == 0 and global_qty_inv == 0:
						print('Adjust food price down due to spoilage.')
						self.adj_price(item, direction='down')
					else:
						price = world.get_price(item, self.entity_id)
						print('No price change for {} from: {}'.format(item, price))
			self.ledger.reset()

	def negative_bal(self):
		for item in self.produces:
			qty_inv = self.ledger.get_qty(item, ['Inventory'])
			if qty_inv < 0:
				print('{} has a negative item balance of {} {}. Will attempt to produce {} units'.format(self.name, qty_inv, item, abs(qty_inv)))
				self.produce(item, abs(qty_inv))


	def capitalize(self, amount=None, buffer=False):
		if amount is None:
			amount = INIT_CAPITAL
		capital_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Deposit capital', '', '', '', 'Cash', 'Equity', amount ]
		capital_event = [capital_entry]
		if buffer:
			return capital_event
		self.ledger.journal_entry(capital_event)
		#return capital_event

	def auth_shares(self, ticker, qty=None, counterparty=None):
		if counterparty is None:
			counterparty = self
		if qty is None:
			qty = 100000
		auth_shares_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Authorize shares', ticker, '', qty, 'Shares', 'Info', 0 ]
		auth_shares_event = [auth_shares_entry]
		self.ledger.journal_entry(auth_shares_event)

	def buy_shares(self, ticker, price, qty, counterparty):
		desc_pur = ticker + ' shares purchased'
		desc_sell = ticker + ' shares sold'
		result, cost = self.transact(ticker, price, qty, counterparty, 'Investments', 'Shares', desc_pur=desc_pur, desc_sell=desc_sell)
		self.ledger.journal_entry(result)
		return result

	# Allow individuals to incorporate organizations without human input
	def incorporate(self, name=None, item=None, qty=None, price=None, auth_qty=None, founders=None):
		INC_TIME = 0#MAX_HOURS - 4
		entity = None
		if isinstance(self, Individual):
			if self.hours < INC_TIME:
				print('{} does not have enough time to incorporate {}. Requires a full day of {} hours.'.format(self.name, name, INC_TIME))
				return
		elif isinstance(self, Government):
			pass
		else:
			largest_shareholder_id = self.list_shareholders(largest=True)
			if largest_shareholder_id is None:
				return
			largest_shareholder = self.factory.get_by_id(largest_shareholder_id)
			entity = largest_shareholder
			print('{} will attempt to incorporate {} on behalf of {}. Owner Hours: {}'.format(entity.name, name, self.name, entity.hours))
			if entity.hours < INC_TIME:
				print('{} does not have enough time to incorporate {}. Requires a full day of {} hours.'.format(entity.name, name, INC_TIME))
				return
		if price is None:
			price = 1
		if qty is None and founders is None and item is not None:
			# qty = 5000 # TODO Fix temp defaults
			demand_qty = world.demand.loc[world.demand['item_id'] == item]['qty'].sum()
			raw_mats = self.get_raw(item, demand_qty)
			try:
				qty = raw_mats.iloc[-1]['qty'] * INIT_PRICE * INC_BUFFER
			except AttributeError as e:
				qty = None
			print(f'{item} ({demand_qty}) incorp amount: {qty}')
		if auth_qty is None:
			auth_qty = 100000 # TODO Determine dynamically?
		if qty is None:
			qty = 5000 # TODO Fix temp defaults
		if founders is None:
			if args.jones:
				if isinstance(self, Government):
					founders = {self.bank: qty}
					# print(f'Jones founders Gov: {founders}')
				else:
					founders = {world.gov.bank: qty}
					# print(f'Jones Founders world: {founders}')
				# print(f'Jones founders: {founders}')
			else:
				founders = {self: qty}
		if qty is None:
			qty = sum(founders.values())
		entities = self.accts.get_entities()
		if name is None and item is not None:
			names = world.items.loc[item, 'producer']
			if isinstance(names, str):
				names = [x.strip() for x in names.split(',')]
			# names = list(set(filter(None, names)))
			names = list(collections.OrderedDict.fromkeys(filter(None, names)))
			name = names[0]
			#print('Ticker: {}'.format(name))
		if name == 'Bank' and world.gov.bank is not None:
			print('{} already has a bank. Only one Central Bank per Government is allowed at this time.'.format(world.gov))
			return
		legal_form = world.org_type(name)
		# print('Legal Form: {}'.format(legal_form))
		if legal_form == Corporation:
			for founder, founder_qty in founders.items():
				self.ledger.set_entity(founder.entity_id)
				founder_cash = self.ledger.balance_sheet(['Cash'])
				self.ledger.reset()
				#print('Cash: {}'.format(cash))
				if price * founder_qty > founder_cash:
					print('{} does not have enough cash to incorporate {}. Cash: {} | Required: {}'.format(founder.name, name, founder_cash, price * founder_qty))
					return
		items_produced = world.items[world.items['producer'].str.contains(name, na=False)].reset_index()
		items_produced = items_produced['item_id'].tolist()
		items_produced = ', '.join(items_produced)
		# print('Items Produced: {}'.format(items_produced))
		last_entity_id = entities.reset_index()['entity_id'].max()
		name = name + '-' + str(last_entity_id + 1)
		#print('Corp Name: \n{}'.format(name))
		corp = self.factory.create(legal_form, name, items_produced, self.government, self.founder, auth_qty)#, int(last_entity_id + 1))
		# world.prices = pd.concat([world.prices, corp.prices])
		# world.items_map = world.items_map.append({'item_id':name, 'child_of':'Shares'}, ignore_index=True)
		world.items_map = pd.concat([world.items_map, pd.DataFrame({'item_id':[name], 'child_of':['Shares']})], ignore_index=True)
		if name.split('-')[0] == 'Bank':
			world.gov.bank = corp
			print('{}\'s central bank created.'.format(world.gov))
		counterparty = corp
		if legal_form == Corporation:
			self.auth_shares(name, auth_qty, counterparty)
			for founder, qty in founders.items():
				founder.buy_shares(name, price, qty, counterparty)
		if INC_TIME:
			if entity is None:
				self.set_hours(INC_TIME)
			else:
				entity.set_hours(INC_TIME)
		return corp

	def corp_needed(self, item=None, qty=0, need=None, ticker=None, demand_index=None, v=False):
		# Choose the best item
		if item is None and need is not None:
			items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
			if items_info.empty:
				return
			need_satisfy_rate = []
			for index, item_row in items_info.iterrows():
				needs = [x.strip() for x in item_row['satisfies'].split(',')]
				for i, need_item in enumerate(needs):
					if need_item == need:
						break
				satisfy_rates = [x.strip() for x in item_row['satisfy_rate'].split(',')]
				satisfy_rate = satisfy_rates[i]
				need_satisfy_rate.append(satisfy_rate)
			need_satisfy_rate = pd.Series(need_satisfy_rate)
			# if v: print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
			items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)
			items_info = items_info.sort_values(by='satisfy_rate', ascending=False).reset_index()
			#items_info.reset_index(inplace=True)
			item = items_info['item_id'].iloc[0]
			if v: print('Item Choosen: {}'.format(item))
		if ticker is None and item is not None:
			tickers = world.items.loc[item, 'producer']
			if tickers is None:
				return
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			tickers = list(collections.OrderedDict.fromkeys(filter(None, tickers)))
			# if v: print('Tickers: {}'.format(tickers))
		elif ticker is not None:
			if not isinstance(ticker, (list, tuple)):
				tickers = [str(ticker)]
			else:
				tickers = str(ticker)
			# TODO Recursively check required items and add their producers to the ticker list
		# Check if item is produced or being produced
		# TODO How to handle service qty check
		if item is not None:
			item_type = world.get_item_type(item)
			qty_exists = self.ledger.get_qty(item, ['Inventory','WIP Inventory'])
			if v: print('QTY of {} existing: {}'.format(item, qty_exists))
		else:
			qty_exists = 0
		# If not being produced incorporate and produce item
		if qty_exists <= qty: # TODO Fix this for when Food stops being produced
			for ticker in tickers:
				count = 0
				if v: print('Ticker: {}'.format(ticker))
				if ticker == 'Individual':
					# if v: print('{} produced by individuals, no corporation needed.'.format(item))
					continue
				for corp in world.gov.get([Corporation, NonProfit]): # TODO Check Non-Profits also
					# if v: print('Corp: {}'.format(corp))
					if ticker == corp.name.split('-')[0]:
						self.ledger.set_entity(corp.entity_id)
						bankrupt = self.ledger.balance_sheet(['Write-off'])
						print('Bankruptcy check for {} in corp needed: {}'.format(corp.name, bankrupt))
						self.ledger.reset()
						if not bankrupt:
							count += 1
						if v: print('{} corp count: {}'.format(corp.name, count))
						if count >= MAX_CORPS:
							if v: print('{} {} corporation already exists.'.format(count, corp.name))
							if corp is not None and item_type == 'Subscription' and demand_index is not None:
								to_drop = []
								to_drop = world.demand.loc[world.demand['item_id'] == item].index.tolist()
								world.demand = world.demand.drop(to_drop)#.reset_index(drop=True)
								world.set_table(world.demand, 'demand')
								print('{} dropped {} [{}] Subscription from the demand table for {}. To Drop: {}'.format(self.name, item, demand_index, corp.name, to_drop))
								with pd.option_context('display.max_rows', None):
									if v: print('World Demand: {} \n{}'.format(world.now, world.demand))
							return corp
				corp = self.incorporate(name=ticker, item=item)
				# TODO Have the demand table item cleared when entity gets the subscription
				if corp is not None and item_type == 'Subscription' and demand_index is not None:
					world.demand = world.demand.drop([demand_index])#.reset_index(drop=True)
					world.set_table(world.demand, 'demand')
					print('{} dropped {} [{}] Subscription from the demand table for {}.'.format(self.name, item, demand_index, corp.name))
					with pd.option_context('display.max_rows', None):
						if v: print('World Demand: {} \n{}'.format(world.now, world.demand))
				return corp

	def tech_motivation(self, v=False):
		tech_info = world.items[world.items['child_of'] == 'Technology']
		tech_info.reset_index(inplace=True)
		#print('Tech Info: \n{}'.format(tech_info))
		# self.ledger.reset() # No longer needed
		for _, tech_row in tech_info.iterrows():
			tech = tech_row['item_id']
			# print('Checking motivation for tech: {}'.format(tech))
			if self.check_eligible(tech):
				#print('Tech Check: {}'.format(tech))
				tech_done_status = self.ledger.get_qty(items=tech, accounts=['Technology'])
				tech_research_status = self.ledger.get_qty(items=tech, accounts=['Researching Technology'])
				tech_status = tech_done_status + tech_research_status
				if tech_status == 0 or (tech_row['freq'] == 'repeatable' and tech_research_status == 0):
					#print('Tech Needed: {}'.format(tech))
					outcome = self.item_demanded(tech, qty=1)
					if outcome:
						print('tech table before:\n', world.tech)
						world.tech = pd.concat([world.tech, pd.DataFrame({'technology':[tech], 'date':[world.now], 'entity_id':[self.entity_id], 'time_req':[''], 'days_left':[''], 'done_date':[''], 'status':['wip']})], ignore_index=True)
						print('tech table after:\n', world.tech)
					# 	return tech

	def check_eligible(self, item, check=False, v=False):
		if v: print(f'Eligible Item Check: {item} | Check all: {check}')
		if world.items.loc[item, 'requirements'] is None: # Base case
			return True
		requirements = [x.strip() for x in world.items.loc[item, 'requirements'].split(',')]
		if v: print('Eligible Item Requirements: {} | {}'.format(item, requirements))
		for requirement in requirements:
			item_type = world.get_item_type(requirement)
			if v: print('Check {} Eligible Requirement: {} | {}'.format(item, requirement, item_type))
			if item_type == 'Technology':
				tech_status = self.ledger.get_qty(items=requirement, accounts=['Technology'])
				if tech_status == 0:
					if v: print('Do not have {} tech for item: {}'.format(requirement, item))
					return False
				elif tech_status >= 0:
					if v: print('Have {} tech for item: {}'.format(requirement, item))
					return True
			else:
				if item == requirement:
					if v: print('{} requires itself: {}'.format(requirement))
					continue # TODO Test this better
				if self.check_eligible(requirement, check=check):
					continue
				else:
					return False
		if v: print('No new tech needed for item: {}'.format(item))
		return True

	def qty_demand(self, item, need=None, item_type=None):
		item_info = world.items.loc[item]
		if item_type is None:
			item_type = world.get_item_type(item)
		#print('Item Info: \n{}'.format(item_info))
		decay_rate = self.needs[need]['Decay Rate']
		if need is None: # This should never happen
			need = item_info['satisfies']
			qty = int(math.ceil(decay_rate / float(item_info['satisfy_rate'])))
			return qty
		# Support items with multiple satisfies
		else:
			needs = [x.strip() for x in item_info['satisfies'].split(',')]
			for i, need_item in enumerate(needs):
				if need_item == need:
					break
			satisfy_rates = [x.strip() for x in item_info['satisfy_rate'].split(',')]
			qty = int(math.ceil(decay_rate / float(satisfy_rates[i])))
			# if args.random and item_type != 'Commodity':
			# 	rand = random.randint(1, 3)
			# 	qty = qty * rand
			#qty = qty * world.population
			return qty

	def check_constraint(self, item, constraint='labour'):
		demand_constrained = world.demand.loc[(world.demand['item_id'] == item) & (world.demand['reason'] == constraint)]
		#print('Demand Constrained: \n{}'.format(demand_constrained))
		if not demand_constrained.empty:
			print('{} cannot add {} to demand list as it is constrained by {}.'.format(self.name, item, constraint))
			return True

	def item_demanded(self, item=None, qty=None, need=None, reason_need=False, cost=False, priority=False, vv=False, v=True):
		if qty == 0:
			return
		if item is None and need is not None: # TODO This isn't used currently
			reason_need = True
			items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
			#print('Items Info Before: \n{}'.format(items_info))
			if items_info.empty:
				return
			need_satisfy_rate = []
			for index, item_row in items_info.iterrows():
				needs = [x.strip() for x in item_row['satisfies'].split(',')]
				for i, need_item in enumerate(needs):
					if need == need_item:
						break
				satisfy_rates = [x.strip() for x in item_row['satisfy_rate'].split(',')]
				satisfy_rate = satisfy_rates[i]
				need_satisfy_rate.append(satisfy_rate)
			need_satisfy_rate = pd.Series(need_satisfy_rate)
			#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
			items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)
			#print('Items Info After: \n{}'.format(items_info))
			items_info = items_info.sort_values(by='need_satisfy_rate', ascending=False)
			items_info.reset_index(inplace=True)
			for index, items_info_row in items_info.iterrows():
				#item = items_info['item_id'].iloc[0]
				item = items_info_row['item_id']
				requirements = items_info_row['requirements']
				requirements = [x.strip() for x in requirements.split(',')]
				#print('Requirements: \n{}'.format(requirements))
				requirement_types = [world.get_item_type(x) for x in requirements]
				if 'Time' not in requirement_types:
					return
				if self.check_eligible(item):
					break
		# Only allow one technology on demand list at a time
		item_type = world.get_item_type(item)
		if item_type == 'Technology':
			for index, demand_item in world.demand.iterrows():
				check_tech = demand_item['item_id']
				check_item_type = world.get_item_type(check_tech)
				if check_item_type == 'Technology':
					#print('Cannot add {} technology to demand list because {} technology is already on it.'.format(item, check_tech))
					return
		if not self.check_eligible(item):
			if v: print('{} does not have tech for {} so it cannot be added to the demand list.'.format(self.name, item))
			return

		if qty is None:
			if item_type == 'Service':
				qty = 1
			else:
				qty = self.qty_demand(item, need, item_type)
		if v: print(f'Qty demanded: {qty} | Need: {need}')

		# Check if entity already has item on demand list
		if not world.demand.empty:
			# vv = True
			if vv: print(f'World Demand DF: \n{world.demand}')
			item_demand = world.demand.loc[(world.demand['item_id'] == item) & (world.demand['entity_id'] == self.entity_id)]
			if vv: print(f'Item Demand: \n{item_demand}')
			qty_demand = item_demand['qty'].sum()
			if vv: print(f'Qty already demanded: {qty_demand} | qty: {qty}')
			if qty_demand >= qty:
				if v: print(f'{self.name} already has {qty_demand} {item} on demand list.')
				return
			if qty_demand > 0 and qty_demand < qty:
				qty -= qty_demand
				if v: print(f'New qty demanded: {qty}')

		# if not world.demand.empty: # TODO Commodity replaces existing commodity if qty is bigger. # TODO Need to factor in qty.
		# 	vv = True
		# 	if vv: print('World Demand DF 2: \n{}'.format(world.demand))
		# 	#if item_type != 'Commodity': # TODO No longer needed
		# 	# temp_df = world.demand[['entity_id','item_id']]
		# 	temp_df = world.demand[['entity_id','item_id','qty']]
		# 	if vv: print('Temp Demand DF: \n{}'.format(temp_df))
		# 	#temp_new_df = pd.DataFrame({'entity_id': self.entity_id, 'item_id': item}, index=[0])  # TODO No longer needed
		# 	temp_new_df = pd.DataFrame(columns=['entity_id','item_id','qty'])
		# 	if vv: print('Temp Fresh Demand DF: \n{}'.format(temp_new_df))
		# 	# temp_new_df = temp_new_df.append({'entity_id': self.entity_id, 'item_id': item}, ignore_index=True) # TODO No longer needed
		# 	temp_new_df = pd.concat([temp_new_df, pd.DataFrame({'entity_id': [self.entity_id], 'item_id': [item], 'qty': [qty]})])
		# 	if vv: print('Temp New Demand DF: \n{}'.format(temp_new_df))
		# 	#check = temp_df.intersection(temp_new_df) # TODO No longer needed
		# 	check = pd.merge(temp_df, temp_new_df, how='inner', on=['entity_id','item_id'])
		# 	if vv: print('Demand Already Check: \n{}'.format(check))
		# 	if not check.empty:
		# 		if vv: print('Demand Check not empty.')
		# 		if item_type != 'Commodity' and item_type != 'Components':
		# 			if v: print('{} already on demand list for {}.'.format(item, self.name))
		# 		exit()
		# 		return

		if item_type == 'Service':
			#print('Current Demand : \n{}'.format(world.demand['item_id']))
			qty = 1 # TODO Is this needed still?
			if item in world.demand['item_id'].values:
				if v: print('{} service already on the demand table for {}.'.format(item, self.name)) # TODO Finish this
				return
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			# tickers = list(set(filter(None, tickers)))
			tickers = list(collections.OrderedDict.fromkeys(filter(None, tickers)))
			#print('Tickers: {}'.format(tickers))
			for ticker in tickers: # TODO Check to entity register
				corp_shares = self.ledger.get_qty(ticker, ['Investments'])
				if corp_shares != 0:
					return
		
		if qty != 0 and not self.check_constraint(item):
			if cost:
				if priority:
					new_demand = pd.DataFrame({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'cost'}, index=[0])
					world.demand = pd.concat([new_demand, world.demand], ignore_index=True)
				else:
					# world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'cost'}, ignore_index=True)
					world.demand = pd.concat([world.demand, pd.DataFrame({'date':[world.now], 'entity_id':[self.entity_id], 'item_id':[item], 'qty':[qty], 'reason':['cost']})], ignore_index=True)
				world.set_table(world.demand, 'demand')
			elif reason_need:
				if priority:
					new_demand = pd.DataFrame({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'need'}, index=[0])
					world.demand = pd.concat([new_demand, world.demand], ignore_index=True)
				else:
					# world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'need'}, ignore_index=True)
					# world.demand = pd.concat([world.demand, pd.DataFrame({'date': [world.now], 'entity_id': [self.entity_id], 'item_id': [item], 'qty': [qty], 'reason': ['need']})])
					world.demand.loc[len(world.demand)] = {'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'need'}
				world.set_table(world.demand, 'demand')
			else:
				if priority:
					new_demand = pd.DataFrame({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'existance'}, index=[0])
					world.demand = pd.concat([new_demand, world.demand], ignore_index=True)
				else:
					# world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'existance'}, ignore_index=True)
					world.demand = pd.concat([world.demand, pd.DataFrame({'date': [world.now], 'entity_id': [self.entity_id], 'item_id': [item], 'qty': [qty], 'reason': ['existance']})], ignore_index=True)
				world.set_table(world.demand, 'demand')
			if qty == 1:
				if v: print('{} added to demand list for {} unit by {}.'.format(item, qty, self.name))
				if v: print(world.demand)
			else:
				if v: print('{} added to demand list for {} units by {}.'.format(item, qty, self.name))
				if v: print(world.demand)
			#print('Demand after addition: \n{}'.format(world.demand))
			return item, qty

	def check_demand(self, multi=True, others=True, needs_only=False, vv=False, v=True):
		if self.produces is None:
			return
		if needs_only:
			if vv: print('{} demand check for needed items: \n{}'.format(self.name, self.produces))
		else:
			if vv: print('{} demand check for items: \n{}'.format(self.name, self.produces))
		# for item in self.produces:
		checked = []
		for index, demand_item in world.demand.iterrows():
			item = demand_item['item_id']
			if vv: print(f'Demand Index: {index} | Item: {item} | multi: {multi} | others: {others} | needs_only: {needs_only}')
			if item in checked:
				if vv: print(f'Already checked item {item}.')
				continue
			if needs_only:
				if demand_item['reason'] != 'need':
					continue
			item_type = world.get_item_type(item)
			if v: print(f'Demand Index: {index} | Item: {item} | Item type: {item_type} | multi: {multi} | others: {others} | needs_only: {needs_only}')
			if item_type != 'Land':
				checked.append(item)
			if item_type == 'Subscription':
				continue
			elif item_type == 'Land': #TODO Handle land better
				if isinstance(self, Individual) and not needs_only: # TODO Assumes land is never a direct need
					if self.hours < 1:
						if v: print(f'{self.name} has less than 1 hour left ({self.hours}) and cannot claim land from the demand list.')
						continue
					to_drop = []
					# Claim land items for self first
					if demand_item['entity_id'] == self.entity_id: # TODO Make this less ugly
						self_demand = world.demand.loc[world.demand['entity_id'] == self.entity_id]
						if not self_demand.empty:
							for idx, demand_row in self_demand.iterrows():
								# item = demand_row['item_id']
								# item_type = world.get_item_type(item)
								# if item_type == 'Land':
								if demand_row['item_id'] == item:
									qty = demand_row['qty']
									if v: print(f'{self.name} attempting to claim {qty} {item} for its self from the demand table.')
									result = self.claim_land(item, demand_row['qty'], account='Inventory', v=v)
									if not result:
										result = self.purchase(item, demand_row['qty'], acct_buy='Inventory', v=v)
									if result:
										if result[0][8] == demand_row['qty']:
											to_drop.append(idx)
										else:
											world.demand.at[idx, 'qty'] = demand_row['qty'] - result[0][8] # If not all the Land demanded was claimed
											if v: print('World Self Demand Land:\n{}'.format(world.demand))
							world.demand = world.demand.drop(to_drop).reset_index(drop=True)
							world.set_table(world.demand, 'demand')
							if to_drop:
								if v: print('World Self Demand Land:\n{}'.format(world.demand))
					else: # TODO Test this better
						for idx, demand_row in world.demand.iterrows():
							# item = demand_row['item_id']
							# item_type = world.get_item_type(item)
							# if item_type == 'Land':
							if demand_row['item_id'] == item:
								qty = demand_row['qty']
								if v: print(f'{self.name} attempting to claim {qty} {item} from the demand table.')
								result = self.claim_land(item, demand_row['qty'], account='Inventory', v=v)
								if not result:
									result = self.purchase(item, demand_row['qty'], acct_buy='Inventory', v=v)
								if result:
									if v: print(f'{self.name} demand land claim result qty for {item}: {result[0][8]}')
									if result[0][8] == demand_row['qty']:
										to_drop.append(idx)
									else:
										world.demand.at[idx, 'qty'] = demand_row['qty'] - result[0][8] # If not all the Land demanded was claimed
										if v: print('World Demand Land:\n{}'.format(world.demand))
						world.demand = world.demand.drop(to_drop).reset_index(drop=True)
						world.set_table(world.demand, 'demand')
						if to_drop:
							if v: print('World Demand:\n{}'.format(world.demand))
			if vv: print(f'{self.name} produces: {self.produces}')
			if item not in self.produces:
				continue
			if vv: print('Check Demand Item for {}: {}'.format(self.name, item))
			#print('World Demand: \n{}'.format(world.demand))
			to_drop = []
			qty = 0
			qty_existance = 0
			# Filter for item and add up all qtys to support multiple entries
			if multi:
				for idx, demand_row in world.demand.iterrows():
					if item_type == 'Education': # TODO Maybe add Service also
						if demand_row['entity_id'] == self.entity_id: # TODO Could filter df for entity_id first
							if demand_row['item_id'] == item:
								qty = demand_row['qty']
								qty = int(math.ceil(qty))
								break
					else:
						demanded_by = self.factory.get_by_id(demand_row['entity_id'])
						if vv: print(f'demanded_by: {demanded_by} | demanded_by type: {type(demanded_by)} | Is not individual? {not isinstance(demanded_by, Individual)}')
						if others or (not others and demand_row['entity_id'] == self.entity_id) or not isinstance(demanded_by, Individual):
							if demand_row['item_id'] == item:
								qty += demand_row['qty']
								qty = int(math.ceil(qty))
								to_drop.append(idx)
			else:
				if item_type == 'Education': # TODO Maybe add Service also
					if demand_item['entity_id'] == self.entity_id: # TODO Could filter df for entity_id first
						qty = demand_item['qty']
						qty = int(math.ceil(qty))
				else:
					qty += demand_item['qty']
					qty = int(math.ceil(qty))
					to_drop.append(index)
			if vv: print(f'Demand qty: {qty} for {item}')
			if qty == 0:
				continue
			if isinstance(self, Corporation):
				if qty > 10:
					qty = math.ceil(qty / MAX_CORPS)
			if v: print()
			if v: print(time_stamp() + 'Current Date when Checking Demand: {}'.format(world.now))
			if v: print('{} attempting to produce {} {} from the demand table. Max Corps: {}'.format(self.name, qty, item, MAX_CORPS))
			item_demand = world.demand[world.demand['item_id'] == item]
			# reason_need = False

			# if 'need' in item_demand['reason'].values:
			# 	self.adj_price(item, qty, direction='up')
			# 	reason_need = True
			# elif 'existance' in item_demand['reason'].values:
			# 	self.adj_price(item, qty, direction='up')
			outcome, time_required, max_qty_possible, incomplete = self.produce(item, qty, wip=True, v=v)#reason_need)
			if vv: print('Demand Check Outcome: {} \n{}'.format(time_required, outcome))
			if to_drop:
				index = to_drop[-1]
			try: # TODO Not needed any more
				if not outcome and world.demand.loc[index, 'reason'] == 'Labour':
					if v: print('Retrying demand check of {} for qty of 1 (instead of {}) due to labour constraint. ({}) {}'.format(item, qty, to_drop[0], world.demand.loc[index, 'reason']))
					qty = 1
					outcome, time_required, max_qty_possible, incomplete = self.produce(item, qty, v=v)
			except KeyError as e:
				if v: print('Error: Retrying demand check of {} for qty of 1 (instead of {}) due to labour constraint. {}'.format(item, qty, repr(e)))
				print('Error: index {} | outcome: {} | to_drop: {} World Demand:\n{}'.format(index, outcome, to_drop, world.demand))
			if vv: print('Second Demand Check Outcome: {} \n{}'.format(time_required, outcome))
			# if outcome:
			# 	qty = max_qty_possible
			# 	# if item_type == 'Education':
			# 	# 	edu_hours = int(math.ceil(qty - MAX_HOURS))
			# 	# 	#print('Edu Hours: {} | {}'.format(edu_hours, index))
			# 	# 	if edu_hours > 0:
			# 	# 		world.demand.at[index, 'qty'] = edu_hours
			# 	# 		world.set_table(world.demand, 'demand')
			# 	# 	#print('Demand After: \n{}'.format(world.demand))
			# 	if item_type == 'Technology':
			# 		return
			# 	else:
			# 		try:
			# 			world.demand = world.demand.drop(to_drop).reset_index(drop=True) # TODO This was causing items to be removed twice in error
			# 			world.set_table(world.demand, 'demand')
			# 		except KeyError as e:
			# 			#print('Error: {}'.format(repr(e)))
			# 			pass
			# 		print('{} removed from demand list for {} units by {}.\n'.format(item, qty, self.name)) # TODO Fix this when only possible qty is produced
			# 		with pd.option_context('display.max_rows', None):
			# 			print('World Demand: {} \n{}'.format(world.now, world.demand))

	def check_optional(self, priority=False, v=True):
		if self.produces is None:
			return
		items_list = world.items[world.items['producer'] != None]
		#print('Items List: \n{}'.format(items_list))
		for item in self.produces:
			if not self.check_eligible(item): # TODO Maybe cache this
				continue
			# Only make optional productive items for items produced once before
			self.ledger.set_entity(self.entity_id)
			past_qty_check = self.ledger.get_qty(item, show_zeros=True, always_df=True)
			self.ledger.reset()
			if past_qty_check.empty:
				continue
			#print('Produces Item: {}'.format(item))
			# print(f'{item} satisfies:', world.items.loc[item, 'satisfies'])
			if world.items.loc[item, 'satisfies'] is not None:
				priority = True
			requirements = world.items.loc[item, 'requirements']
			if requirements is None:
				if v: print('{} has no requirements.'.format(item))
				continue
			if isinstance(requirements, str):
				requirements = [x.strip() for x in requirements.split(',')]
			requirements = list(filter(None, requirements))
			#print('Requirements: \n{}'.format(requirements))
			for requirement in requirements:
				#print('Requirement: {}'.format(requirement))
				possible_items = items_list.loc[items_list['productivity'].str.contains(requirement, na=False)]
				#print('Possible Items: \n{}'.format(possible_items))
				productivity_items = pd.DataFrame(columns=['item_id','efficiency'])
				for index, prod_item in possible_items.iterrows():
					productivities = [x.strip() for x in prod_item['productivity'].split(',')]
					for i, productivity in enumerate(productivities):
						if productivity == requirement:
							break
					efficiencies = [x.strip() for x in prod_item['efficiency'].split(',')]
					efficiencies = list(map(float, efficiencies))
					efficiency = efficiencies[i]
					# productivity_items = productivity_items.append({'item_id': prod_item.name, 'efficiency': efficiency}, ignore_index=True)
					productivity_items = pd.concat([productivity_items, pd.DataFrame({'item_id': [prod_item.name], 'efficiency': [efficiency]})], ignore_index=True)
				productivity_items = productivity_items.sort_values(by='efficiency', ascending=True)
				#print('Productivity Items: \n{}'.format(productivity_items))
				if not productivity_items.empty:
					for index, prod_item in productivity_items.iterrows():
						if self.check_eligible(prod_item['item_id']):
							item_type = world.get_item_type(prod_item['item_id'])
							self.ledger.set_entity(self.entity_id)
							current_qty = self.ledger.get_qty(prod_item['item_id'], [item_type, 'WIP ' + item_type])#, v=True)
							self.ledger.reset()
							#print('Current Qty of {}: {}'.format(item['item_id'], current_qty))
							if current_qty == 0:
								result = self.purchase(prod_item['item_id'], qty=1, priority=priority, v=v)#, acct_buy=item_type) # TODO Handle more than 1 qty?
								if result:
									break

	def claim_land(self, item, qty, price=0, counterparty=None, account='Land', priority=False, buffer=False, v=True):
		# If too much land is claimed by user, the min possible will be claimed automatically
		if qty <= 0:
			return
		yield_price = price
		if counterparty is None:
			counterparty = world.env
			yield_price = 0
		elif counterparty == world.env:
			yield_price = 0
		if v: print('{} attempting to claim {} {} from entity: {}.'.format(self.name, qty, item, counterparty.name))
		if account != 'Land':
			price = world.get_price(item, counterparty.entity_id)
			if price == 0:
				price = INIT_PRICE
				self.set_price(item, price=price, v=v)
			# print('Price of {} land set to: {}'.format(item, price))
		explore_time = world.items['int_rate_fix'][item] # TODO Maybe create dedicated data column
		if explore_time is None or pd.isnull(explore_time):
			explore_time = EXPLORE_TIME
		explore_time = int(explore_time)
		explore_time = explore_time * 0.1 # Reduce land claim time requirements
		time_needed = round(qty * explore_time, 3)
		if isinstance(self, (Corporation)):
			largest_shareholder_id = self.list_shareholders(largest=True)
			if largest_shareholder_id is None:
				return
			entity = self.factory.get_by_id(largest_shareholder_id)
			if entity is None:
				if v: print(f'Largest shareholder for {self.name} is {entity}')
				return
			if v: print('{} will attempt to claim {} {} on behalf of {}. Owner Hours: {}'.format(entity.name, qty, item, self.name, entity.hours))
		elif isinstance(self, (NonProfit, Governmental)): # TODO Long term solution for this temp fix
			time_needed = 0
			entity.hours = 12
		else:
			entity = self
		orig_qty = qty
		if entity.hours < time_needed:
			qty = math.floor(entity.hours / (explore_time))
			if qty == 0:
				if v: print(f'{entity.name} requires {explore_time} time to claim {orig_qty} units of {item}. Can claim {qty} units with {entity.hours} hours time.')
				if account == 'Land':
					self.item_demanded(item, orig_qty, priority=priority, v=v)
				return
			if v: print(f'{entity.name} requires {explore_time} time to claim {orig_qty} units of {item}. But can claim {qty} units with {entity.hours} hours of time instead.')
			if self.user:
				while True:
					confirm = input('Do you want to claim {} units of {} instead? [Y/n]: '.format(qty, item))
					if confirm == '':
						confirm = 'Y'
					if confirm.upper() == 'Y':
						confirm = True
						break
					elif confirm.upper() == 'N':
						confirm = False
						break
					else:
						print('Not a valid entry. Must be "Y" or "N".')
						continue
				if not confirm:
					return
			time_needed = round(qty * explore_time, 3)
		orig_hours = entity.hours
		if isinstance(entity, Individual):
			entity.set_hours(time_needed)
		# TODO Decide if fulfill() is required when claiming land from other entity?
		incomplete, claim_land_event, time_required, max_qty_possible = self.fulfill(item, qty, v=v)
		if incomplete:
			entity.hours = orig_hours
			return
		claim_land_entry = []
		yield_land_entry = []
		# TODO Add WIP Time component?
		# if counterparty.entity_id == world.env.entity_id or counterparty is None: # TODO This isn't needed now
		# 	self.ledger.set_entity(world.env.entity_id)
		# else:
		self.ledger.set_entity(counterparty.entity_id) # TODO Support claiming land from other Individuals
		unused_land = self.ledger.get_qty(items=item, accounts=['Land'])
		self.ledger.reset()
		if v: print('{} available to claim by {} from {}: {}'.format(item, self.name, counterparty.name, unused_land))
		if unused_land >= qty:
			amount = round(qty * price, 2)
			yield_amount = round(qty * yield_price, 2)
			if counterparty.entity_id == world.env.entity_id:
				claim_land_entry = [ self.ledger.get_event(), self.entity_id, world.env.entity_id, world.now, '', 'Claim land', item, price, qty, account, 'Natural Wealth', amount ]
				yield_land_entry = [ self.ledger.get_event(), world.env.entity_id, self.entity_id, world.now, '', 'Bestow land', item, yield_price, qty, 'Natural Wealth', 'Land', yield_amount ]
			else:
				claim_land_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Claim land', item, price, qty, account, 'Natural Wealth', amount ]
				yield_land_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Lose land', item, yield_price, qty, 'Natural Wealth', 'Land', yield_amount ]
			if claim_land_entry and yield_land_entry:
				claim_land_event += [yield_land_entry, claim_land_entry]
			if buffer:
				if v: print('{} claims {} units of {} in {} hours. Hours left: {}'.format(self.name, qty, item, time_needed, entity.hours))
				return claim_land_event
			self.ledger.journal_entry(claim_land_event)
			self.item_demanded(item, orig_qty - qty, priority=priority, v=v)
			if v: print('{} claims {} units of {} in {} hours. Hours left: {}'.format(self.name, qty, item, time_needed, entity.hours))
			return claim_land_event
		else:
			unused_land = self.ledger.get_qty(items=item, accounts=['Land'])
			if unused_land < qty:
				if v: print('{} cannot claim {} units of {} because there is only {} units available.'.format(self.name, qty, item, unused_land))
			# unused_land = self.ledger.get_qty(items=item, accounts=['Land'], by_entity=True)
			# print('Unused {} claimed by the following entities: \n{}'.format(item, unused_land))
			unused_land = world.unused_land(item, accounts=['Land','Inventory'])
			entity.hours = orig_hours

	def get_counterparty(self, txns, rvsl_txns, item, account, m=1, n=0, allowed=None, v=False): # TODO Remove parameters no longer needed
		if v: print('Get Counterparty for {} | Item: {}'.format(self.name, item))
		if allowed is None:
			allowed = self.factory.registry.keys()
		else:
			if not isinstance(allowed, (list, tuple)):
				allowed = [allowed]
		if v: print('Allowed: {}'.format(allowed))
		txn = txns.loc[(txns['item_id'] == item) & (~txns['event_id'].isin(rvsl_txns))]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('TXN: \n{}'.format(txn))
		if txn.empty:
			print('No counterparty exists for {}.'.format(item))
			return None, None
		counterparty_id = txn.iloc[n].loc['cp_id']
		if v: print('n: {}'.format(n))
		event_id = txn.iloc[n].loc['event_id']
		if v: print('Event ID: {}'.format(event_id))
		# event_txns = self.ledger.gl[(self.ledger.gl['event_id'] == event_id) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
		# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		# 	if v: print('Event TXNs: \n{}'.format(event_txns))
		# item_txn = event_txns.loc[event_txns['item_id'] == item] # If there are multiple items in same event
		# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		# 	if v: print('Item TXN: \n{}'.format(item_txn))
		# counterparty_txn = item_txn.loc[item_txn['debit_acct'] == account]
		# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		# 	if v: print('Counterparty TXN: {} \n{}'.format(account, counterparty_txn))
		# if v: print('n: {}'.format(n))
		# counterparty_id = counterparty_txn.iloc[n].loc['entity_id']
		counterparty = self.factory.get_by_id(counterparty_id)
		if v: print('Counterparty Type: {}'.format(type(counterparty)))
		while True:
			if counterparty is not None:
				break
			if type(counterparty) not in allowed:
				counterparty_id += 1
				counterparty = self.factory.get_by_id(counterparty_id)
		if v: print('Counterparty: {}'.format(counterparty))
		return counterparty, event_id

	def pay_wages(self, jobs=None, counterparty=None, v=False):
		if jobs is None:
			# Get list of jobs
			# TODO Get list of jobs that have accruals only
			self.ledger.set_entity(self.entity_id)
			wages_payable_list = self.ledger.get_qty(accounts=['Wages Payable'], credit=True)
			self.ledger.reset()
			if v: print('Wages Payable List: \n{}'.format(wages_payable_list))
			jobs = wages_payable_list['item_id']
		# Ensure jobs is a list
		if isinstance(jobs, str):
			jobs = [x.strip() for x in jobs.split(',')]
		# Ensure items on jobs list are unqiue
		jobs = list(collections.OrderedDict.fromkeys(filter(None, jobs)))
		if v: print('Jobs to pay wages: \n{}'.format(jobs))
		rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		wages_paid_txns = self.ledger.gl[( (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['debit_acct'] == 'Wages Payable') & (self.ledger.gl['credit_acct'] == 'Cash') ) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]['event_id']
		# TODO Fix the above not working with WIP items
		if v: print('Wages Paid TXN Event IDs for {}: \n{}'.format(self.name, wages_paid_txns))
		wages_pay_txns = self.ledger.gl[( (self.ledger.gl['entity_id'] == self.entity_id) & (self.ledger.gl['debit_acct'] == 'Wages Expense') & (self.ledger.gl['credit_acct'] == 'Wages Payable') ) & (~self.ledger.gl['event_id'].isin(wages_paid_txns)) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('Wages Pay TXNs for {}: \n{}'.format(self.name, wages_pay_txns))
		for job in jobs:
			job_wages_pay_txns = wages_pay_txns.loc[wages_pay_txns['item_id'] == job]
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				if v: print('Wages Pay TXNs for job: {}\n{}'.format(job, job_wages_pay_txns))
			event_ids = list(job_wages_pay_txns['event_id'].unique())
			counterparties = list(job_wages_pay_txns['cp_id'].unique())
			print(f'event_ids for {job}: {event_ids}')
			print(f'counterparties for {job}: {counterparties}')
			for event_id in event_ids:
				pay_wages_event = []
				self.ledger.set_entity(self.entity_id)
				cash = self.ledger.balance_sheet(['Cash'])
				self.ledger.reset()
				for counterparty_id in counterparties:
					self.ledger.set_entity(self.entity_id)
					self.ledger.gl = self.ledger.gl.loc[(self.ledger.gl['cp_id'] == counterparty_id) & (self.ledger.gl['event_id'] == event_id)]
					wages_payable = -(self.ledger.balance_sheet(['Wages Payable'], job))
					labour_hours = -(self.ledger.get_qty(job, ['Wages Payable']))
					self.ledger.reset()
					price = wages_payable / labour_hours
					print(f'wages_payable for {job} {event_id} {counterparty_id}: {wages_payable}')
					print(f'labour_hours for {job} {event_id} {counterparty_id}: {labour_hours}')
				# for _, txn in job_wages_pay_txns.iterrows():
				# 	counterparty_id = txn['cp_id']
				# 	event_id = txn['event_id']
					counterparty = self.factory.get_by_id(counterparty_id)
					# if v: print('{} Wages Payable for: {} | Event ID: {}'.format(job, counterparty.name, event_id))
					# labour_hours = txn['qty']
					# wages_payable = txn['amount']
					# price = txn['price']
					if cash >= wages_payable or counterparty.entity_id == self.entity_id:
						wages_pay_entry = [ event_id, self.entity_id, counterparty.entity_id, world.now, '', job + ' wages paid', job, price, labour_hours, 'Wages Payable', 'Cash', wages_payable ]
						wages_chg_entry = [ event_id, counterparty.entity_id, self.entity_id, world.now, '', job + ' wages received', job, price, labour_hours, 'Cash', 'Wages Receivable', wages_payable ]
						pay_wages_event += [wages_pay_entry, wages_chg_entry]
						if counterparty.entity_id != self.entity_id:
							cash -= wages_payable
							counterparty.adj_price(job, labour_hours, direction='up_low')
					else:
						print('{} does not have enough cash to pay {} in wages for {}\'s {} work. Cash: {}'.format(self.name, wages_payable, counterparty.name, job, cash))
						result = self.loan(amount=(wages_payable - cash), item='Credit Line 5', auto=True)
						if result:
							self.pay_wages(self, jobs=jobs, counterparty=counterparty, v=v)
						if result is False:
							self.bankruptcy()
				self.ledger.journal_entry(pay_wages_event)
				self.ledger.set_entity(self.entity_id)
				cash = self.ledger.balance_sheet(['Cash'])
				self.ledger.reset()
				if job != 'Study' and job != 'Research':
					print('{} cash after {} wages paid: {}'.format(self.name, job, cash))

	def check_wages(self, job, v=False):
		# PAY_PERIODS = 32 #datetime.timedelta(days=32)
		if v: print('{} pay_periods: {}'.format(self.name, PAY_PERIODS))
		self.ledger.set_entity(self.entity_id)
		rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of Wages Payable txns
		payable = self.ledger.gl[(self.ledger.gl['credit_acct'] == 'Wages Payable') & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
		if v: print('Payable: \n{}'.format(payable))
		paid = self.ledger.gl[(self.ledger.gl['debit_acct'] == 'Wages Payable') & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
		if v: print('Paid: \n{}'.format(paid))
		self.ledger.reset()
		if not payable.empty:
			latest_payable = payable['date'].iloc[-1]
			latest_payable = datetime.datetime.strptime(latest_payable, '%Y-%m-%d').date()
			if v: print('Latest Payable: \n{}'.format(latest_payable))
		else:
			latest_payable = 0
		if not paid.empty:
			latest_paid = paid['date'].iloc[-1]
			latest_paid = datetime.datetime.strptime(latest_paid, '%Y-%m-%d').date()
			if v: print('Latest Paid: \n{}'.format(latest_paid))
		else:
			latest_paid = 0
			return True
		if v: print('Latest Payable: \n{}'.format(latest_payable))
		if v: print('Latest Paid: \n{}'.format(latest_paid))
		last_paid = latest_payable - latest_paid
		if isinstance(last_paid, datetime.timedelta):
			last_paid = last_paid.days
		if v: print('Last Paid: \n{}'.format(last_paid))
		if last_paid < PAY_PERIODS:
			return True

	def accru_wages(self, job, counterparty, labour_hours, wage=None, accrual=False, buffer=False, check=False, v=True):
		if isinstance(counterparty, tuple):
			counterparty = counterparty[0]
		if accrual:
			desc_exp = job + ' wages to be paid'
			desc_rev = job + ' wages to be received'
		else:
			desc_exp = job + ' wages paid'
			desc_rev = job + ' wages received'
		if counterparty is None:
			if v: print('No workers available to do {} job for {} hours.'.format(job, labour_hours))
			return
		if labour_hours == 0:
			if v: print(f'Cannot hire {counterparty.name} as a {job} for {labour_hours} hours.')
			return
		#print('Labour Counterparty: {}'.format(counterparty.name))
		if job == 'Study': # TODO Fix how Study works to use WIP system
			desc_exp = 'Record study hours'
			desc_rev = 'Record study hours'
		if job == 'Research':
			desc_exp = 'Record research hours'
			desc_rev = 'Record research hours'
		if wage is None:
			wage = world.get_price(job, counterparty.entity_id)
		if counterparty == self:
			recently_paid = True
		else:
			recently_paid = self.check_wages(job)
		incomplete, accru_wages_event, time_required, max_qty_possible = self.fulfill(job, qty=labour_hours, reqs='usage_req', amts='use_amount', check=check, v=v)
		if check:
			return
		if recently_paid and not incomplete:
			if counterparty.hours > 0: # TODO Move this above fulfill()
				hours_worked = min(labour_hours, counterparty.hours)
				hours_worked = math.ceil(hours_worked * 100) / 100
				if accrual:
					debit_acct = 'Wages Receivable'
					credit_acct = 'Wages Payable'
				else:
					debit_acct = 'Cash'
					credit_acct = 'Cash'
				amount = round(wage * hours_worked, 2)
				wages_exp_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', desc_exp, job, wage, hours_worked, 'Wages Expense', credit_acct, amount ]
				wages_rev_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', desc_rev, job, wage, hours_worked, debit_acct, 'Wages Income', amount ]
				accru_wages_event += [wages_exp_entry, wages_rev_entry]
			else:
				if not incomplete: # TODO This is not needed
					if v: print('{} does not have enough time left to do {} job for {} hours. Hours: {}'.format(counterparty.name, job, labour_hours, counterparty.hours))
				else: # TODO This is not needed
					if v: print('{} cannot fulfill the requirements to allow {} to work.'.format(self.name, job))
				return
			if buffer:
				if v: print('{} hired {} as a {} for {} hours.'.format(self.name, counterparty.name, job, hours_worked))
				# if job != 'Study' and job != 'Research':
					# counterparty.adj_price(job, labour_hours, direction='up_low')
				return accru_wages_event
			self.ledger.journal_entry(accru_wages_event)
			counterparty.set_hours(hours_worked)
			# if job != 'Study' and job != 'Research':
			# 	counterparty.adj_price(job, labour_hours, direction='up_low')
		else:
			if incomplete:
				if v: print('{} cannot fulfill requirements for {} job.'.format(self.name, job))
			else:
				if v: print('Wages have not been paid for {} recently by {}.'.format(job, self.name))
			counterparty.adj_price(job, labour_hours, direction='down')
			return

	def worker_counterparty(self, job, only_avail=True, exclude=None, man=False, v=True):
		if job == 'Study':# or 'Research':
			return self
		if v: print('{} looking for worker for job: {}'.format(self.name, job))
		option = 1
		if exclude is None:
			exclude = []
		item_type = world.get_item_type(job)
		workers_exp = collections.OrderedDict()
		workers_price = collections.OrderedDict()
		# Get list of eligible individuals
		worker_event = []
		individuals = []
		if man:#self.user:
			individuals_allowed = [indiv for indiv in world.gov.get(Individual) if self.founder == indiv.founder and indiv not in exclude]
		else:
			individuals_allowed = [indiv for indiv in world.gov.get(Individual) if indiv not in exclude]
		for individual in individuals_allowed:
			incomplete, entries, time_required, max_qty_possible = individual.fulfill(job, qty=1, man=man, v=v)#, check=True)
			# TODO Capture entries
			if not incomplete:
				# This will cause all available workers to attempt to become qualified even if they don't get the job in the end. TODO Test if check=True will prevent this.
				individuals.append(individual)
				worker_event += entries
		#print('Eligible Individuals: \n{}'.format(individuals))
		if not individuals:
			return 'none_qualify'
		# Check total wages receivable for that job for each individual
		for individual in individuals:
			experience_wages = 0
			experience_salary = 0
			self.ledger.set_entity(individual.entity_id)
			experience_wages = abs(self.ledger.get_qty(accounts=['Wages Income'], items=job))
			experience_salary = abs(self.ledger.get_qty(accounts=['Salary Income'], items=job))
			experience = experience_wages + experience_salary
			# print('Experience for {}: {:g} | Hours Left: {}'.format(individual.name, experience, individual.hours))
			self.ledger.reset()
			workers_exp[individual] = experience
		for individual in individuals:
			price = world.get_price(job, individual.entity_id)
			workers_price[individual] = price
			if v: print('{} {} price: {} | Experience: {:g} | Hours Left: {}'.format(individual.name, job, price, workers_exp[individual], individual.hours))
		# Filter for workers with enough hours in the day left
		if item_type == 'Job':
			base_hours = WORK_DAY #4
		else:
			base_hours = 0
		if only_avail:
			# workers_avail_exp = {worker: v for worker, v in workers_exp.items() if worker.hours > base_hours}
			workers_avail_exp = collections.OrderedDict((worker, v) for worker, v in workers_exp.items() if worker.hours > base_hours)
			# workers_avail_price = {worker: v for worker, v in workers_price.items() if worker.hours > base_hours}
			workers_avail_price = collections.OrderedDict((worker, v) for worker, v in workers_price.items() if worker.hours > base_hours)
			if man:
				# if option == 1: # Auto select self, fail if hours remain
				if self in workers_avail_exp or self in workers_avail_price:
					worker_choosen = self
					return worker_choosen
				children = self.get_children()
				for child in children:
					if child in workers_avail_exp or child in workers_avail_price:
						worker_choosen = child
						return worker_choosen
				else:
					if option == 1:
						return # TODO Make this an option
					while True: # Always ask, default null option
						try:
							worker_choosen = input('Enter an entity ID number from the above options to hire: ')
							if worker_choosen == '':
								return
							worker_choosen = int(worker_choosen)
						except ValueError:
							print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(worker_choosen, world.gov.get(Individual, ids=True)))
							continue
						if worker_choosen not in world.gov.get(Individual, ids=True):
							print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(worker_choosen, world.gov.get(Individual, ids=True)))
							continue
						else:
							if not isinstance(self, Individual):
								break
							individual_ids = self.get_children(founder=True, ids=True)
							if worker_choosen not in individual_ids:
								worker_choosen = self.factory.get_by_id(worker_choosen)
								if USE_PIN:
									while True: # TODO Make this an Individual entity function
										try:
											pin = getpass.getpass('To approve, enter the 4 digit pin number for {} or enter "exit": '.format(worker_choosen.name))
											if pin.lower() == 'exit':
												exit()
											if pin == '':
												worker_choosen = None
												break
											pin = int(pin)
										except ValueError:
											print('Not a valid entry. Must be a 4 digit number.')
											continue
										else:
											if len(str(pin)) != 4 or int(pin) < 0:
												print('Not a valid entry. Must be a 4 digit number.')
												continue
											elif worker_choosen.pin == pin:
												worker_choosen = worker_choosen.entity_id
												break
							break
					worker_choosen = self.factory.get_by_id(worker_choosen)
				return worker_choosen
		else:
			workers_avail_exp = workers_exp
			workers_avail_price = workers_price
			if man:
				if self in workers_avail_exp or self in workers_avail_price:
					worker_choosen = self
					return worker_choosen
				children = self.get_children()
				for child in children:
					if child in workers_avail_exp or child in workers_avail_price:
						worker_choosen = child
						return worker_choosen
				else:
					while True:
						try:
							worker_choosen = input('Enter an entity ID number from the above options to hire: ')
							if worker_choosen == '':
								return
							worker_choosen = int(worker_choosen)
						except ValueError:
							print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(worker_choosen, world.gov.get(Individual, ids=True)))
							continue
						if worker_choosen not in world.gov.get(Individual, ids=True):
							print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(worker_choosen, world.gov.get(Individual, ids=True)))
							continue
						else:
							if not isinstance(self, Individual):
								break
							individual_ids = self.get_children(founder=True, ids=True)
							if worker_choosen not in individual_ids:
								worker_choosen = self.factory.get_by_id(worker_choosen)
								if USE_PIN:
									while True:
										try:
											pin = getpass.getpass('To approve, enter the 4 digit pin number for {} or enter "exit": '.format(worker_choosen.name))
											if pin.lower() == 'exit':
												exit()
											if pin == '':
												worker_choosen = None
												break
											pin = int(pin)
										except ValueError:
											print('Not a valid entry. Must be a 4 digit number.')
											continue
										else:
											if len(str(pin)) != 4 or int(pin) < 0:
												print('Not a valid entry. Must be a 4 digit number.')
												continue
											elif worker_choosen.pin == pin:
												worker_choosen = worker_choosen.entity_id
												break
							break
					worker_choosen = self.factory.get_by_id(worker_choosen)
				return worker_choosen
		if not workers_avail_price:
			return None, []
		# Choose the worker with the most experience
		worker_choosen_exp = max(workers_avail_exp, key=lambda k:workers_avail_exp[k])
		# Choose the worker for the lowest price
		worker_choosen = min(workers_avail_price, key=lambda k: workers_avail_price[k])
		if worker_choosen.user and not man and worker_choosen is not self:
			while True:
				if self.user:
					if not worker_choosen.other_hire:
						confirm = False
					else:
						confirm = input('Do you want to let the other player hire {} as a {}? (Y/N): '.format(worker_choosen.name, job))
						if confirm == '':
							confirm = 'Y'
				else:
					if not worker_choosen.other_hire:
						confirm = False
					else:
						confirm = input('Do you want the computer to hire {} as a {}? [Y/n]: '.format(worker_choosen.name, job))
						if confirm == '':
							confirm = 'Y'
						if confirm.upper() == 'Y':
							confirm = True
							break
						elif confirm.upper() == 'N':
							confirm = False
							break
						else:
							print('Not a valid entry. Must be "Y" or "N".')
							continue
			if not confirm:
				exclude.append(worker_choosen)
				worker_choosen = self.worker_counterparty(job, only_avail=only_avail, exclude=exclude, man=man, v=v)
				if isinstance(worker_choosen, tuple):
					worker_choosen, worker_event = worker_choosen
				if worker_choosen is None:
					return None, []
		if v: print('Worker Choosen for {}: {}'.format(job, worker_choosen.name))
		if worker_event:
			return worker_choosen, worker_event
		return worker_choosen

	def hire_worker(self, job, counterparty=None, price=0, qty=1, man=False, buffer=False, v=True):
		entries = []
		if counterparty is None:	
			counterparty = self.worker_counterparty(job, only_avail=False, man=man, v=v)
			if isinstance(counterparty, tuple):
				counterparty, entries = counterparty
		if counterparty is None:
			if v: print('No workers available to do {} job for {}.'.format(job, self.name))
			return
		price = world.get_price(job, counterparty.entity_id)
		incomplete, hire_worker_event, time_required, max_qty_possible = self.fulfill(job, qty, v=v)
		if incomplete:
			return
		if entries:
			hire_worker_event += entries
		# hire_worker_entry = [] # TODO Test if not needed
		# start_job_entry = [] # TODO Test if not needed
		hire_worker_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Hired ' + job, job, price, qty, 'Worker Info', 'Hire Worker', 0 ]
		start_job_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Started job as ' + job, job, price, qty, 'Start Job', 'Worker Info', 0 ]
		# if hire_worker_entry and start_job_entry: # TODO Test if not needed
		hire_worker_event += [hire_worker_entry, start_job_entry]
		first_pay = self.pay_salary(job, counterparty, buffer=buffer, first=True)
		event_id = max([entry[0] for entry in hire_worker_event])
		for entry in hire_worker_event:
			if entry[0] != event_id:
				if entry[0] in self.hold_event_ids or entry[0] in counterparty.hold_event_ids:
					self.hold_event_ids = [event_id if x == entry[0] else x for x in self.hold_event_ids]
					counterparty.hold_event_ids = [event_id if x == entry[0] else x for x in counterparty.hold_event_ids]
				if v: print('Hire Orig event_id: {} | New event_id: {} | {} | {}'.format(entry[0], event_id, self.hold_event_ids, counterparty.hold_event_ids))
				entry[0] = event_id
		if not first_pay:
			hire_worker_event = []
			first_pay = []
		else:
			hire_worker_event += first_pay
		if buffer:
			if hire_worker_event:
				if v: print('{} hired {} as a fulltime {}.'.format(self.name, counterparty.name, job))
				if first_pay:
					self.adj_price(job, qty=1, direction='up')
			else:
				if v: print('{} could not hire {} as a fulltime {}.'.format(self.name, counterparty.name, job))
			return hire_worker_event
		self.ledger.journal_entry(hire_worker_event)
		if first_pay:
			self.adj_price(job, qty=1, direction='up')

	def fire_worker(self, job, counterparty, price=0, qty=-1, quit=False, buffer=False):
		ent_id = self.entity_id
		cp_id = counterparty.entity_id
		if quit:
			ent_id, cp_id = cp_id, ent_id
		fire_worker_entry = [ self.ledger.get_event(), ent_id, cp_id, world.now, '', 'Fired ' + job, job, price, qty, 'Worker Info', 'Fire Worker', 0 ]
		quit_job_entry = [ self.ledger.get_event(), cp_id, ent_id, world.now, '', 'Quit job as ' + job, job, price, qty, 'Quit Job', 'Worker Info', 0 ]
		fire_worker_event = [fire_worker_entry, quit_job_entry]
		if buffer:
			counterparty.adj_price(job, qty=1, direction='down')
			return fire_worker_event
		self.ledger.journal_entry(fire_worker_event)
		counterparty.adj_price(job, qty=1, direction='down')

	def check_salary(self, job=None, counterparty=None, check=False):
		if job is not None:
			self.ledger.set_entity(self.entity_id)
			worker_state = self.ledger.get_qty(items=job, accounts=['Worker Info'])
			self.ledger.reset()
			if worker_state:
				worker_state = int(worker_state)
			#print('Worker State: {}'.format(worker_state))
			if not worker_state: # If worker_state is zero
				return
			for _ in range(worker_state):
				self.pay_salary(job, counterparty, check=check)
		elif job is None:
			self.ledger.set_entity(self.entity_id)
			worker_states = self.ledger.get_qty(accounts=['Worker Info'])
			#print('Worker States: \n{}'.format(worker_states))
			rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			salary_txns = self.ledger.gl[( (self.ledger.gl['debit_acct'] == 'Worker Info') & (self.ledger.gl['credit_acct'] == 'Hire Worker') ) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
			#print('Worker TXNs: \n{}'.format(salary_txns))
			self.ledger.reset()
			for index, job_row in worker_states.iterrows():
				#print('Salary Job Row: \n{}'.format(job_row))
				job = job_row['item_id']
				worker_state = job_row['qty']
				#print('Job: {}'.format(job))
				#print('Worker State Before: {}'.format(worker_state))
				if worker_state:
					worker_state = int(worker_state)
				#print('Worker State: {}'.format(worker_state))
				if not worker_state: # If worker_state is zero
					return
				for n in range(worker_state):
					counterparty, event_id = self.get_counterparty(salary_txns, rvsl_txns, job, 'Start Job', n=n, allowed=Individual)#, v=True)
					# Check is fulltime job is still required
					items_req = world.items[world.items['requirements'].str.contains(job, na=False)].reset_index()
					qty_active = self.ledger.get_qty(items=list(items_req['item_id'].values))
					#print('Qty Active: \n{}'.format(qty_active))
					if isinstance(qty_active, pd.DataFrame):
						if qty_active.empty:
							qty_active = 0
						else:
							qty_active = True
					if not qty_active:
						self.fire_worker(job, counterparty)
					else:
						for _ in range(worker_state):
							self.pay_salary(job, counterparty, check=check)

	def pay_salary(self, job, counterparty, salary=None, labour_hours=None, buffer=False, first=False, check=False):
		# TODO Add accru_salary()
		# if type(counterparty) != Individual:
		if not isinstance(counterparty, Individual): # TODO Shouldn't be needed now, this was due to error from inheritance going to a Corporation
			print('Counterparty is not an Individual, it is {} | {}'.format(counterparty.name, counterparty.entity_id))
			return
		if first: # TODO Required due to not using db rollback in fulfill
			pay_salary_event = []
			incomplete = False
			time_required = False
		else:
			incomplete, pay_salary_event, time_required, max_qty_possible = self.fulfill(job, qty=1, reqs='usage_req', amts='use_amount', check=check)
		if check:
			if pay_salary_event and not incomplete:
				self.ledger.journal_entry(pay_salary_event)
				return True
			return
		if salary is None:
			salary = world.get_price(job, counterparty.entity_id)
		if labour_hours is None:
			labour_hours = WORK_DAY
		if (counterparty.hours < labour_hours):# and not first: # TODO Consider if not to worry if they don't have enough hours available on the first day if they are qualified
			print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
			return
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		amount = round(salary * labour_hours, 2)
		if cash >= amount and not incomplete:
			# TODO Add check if enough cash, if not becomes salary payable
			salary_exp_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', job + ' salary paid', job, salary, labour_hours, 'Salary Expense', 'Cash', amount ]
			salary_rev_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', job + ' salary received', job, salary, labour_hours, 'Cash', 'Salary Income', amount ]
			pay_salary_event += [salary_exp_entry, salary_rev_entry]
			# TODO Don't set hours if production is not possible
			counterparty.set_hours(labour_hours)
			if buffer:
				counterparty.adj_price(job, labour_hours, direction='up_low')
				return pay_salary_event
			self.ledger.journal_entry(pay_salary_event)
			print('{}\'s hours: {}'.format(counterparty.name, counterparty.hours))
			counterparty.adj_price(job, labour_hours, direction='up_low')
			return True
		else:
			if not incomplete:
				print('{} does not have enough cash to pay {} for {} salary. Cash: {}'.format(self.name, amount, job, cash))
				result = self.loan(amount=(amount - cash), item='Credit Line 5', auto=True)
				if result:
					self.pay_salary(job, counterparty, salary=salary, labour_hours=labour_hours, buffer=buffer, first=first, check=check)
				if result is False:
					self.bankruptcy()
			else:
				print('{} cannot fulfill the requirements to keep {} working.'.format(self.name, job))
			if not first:
				self.fire_worker(job, counterparty)

	def subscription_counterparty(self, item, v=False):
		# Get entity that produces the item
		if v: print('Subscription Requested: {}'.format(item))
		producers = world.items.loc[item, 'producer']
		if isinstance(producers, str):
			producers = [x.strip() for x in producers.split(',')]
		producers = list(collections.OrderedDict.fromkeys(filter(None, producers)))
		producer_entities = []
		for producer in producers:
			if v: print('Producer: {}'.format(producer))
			for entity in world.gov.get():
				if v: print('Entity: {}'.format(entity))
				if producer == entity.name.split('-')[0]:
					producer_entities.append(entity.entity_id)
				if v: print('Producer Entities: \n{}'.format(producer_entities))
		serv_prices = {k:world.get_price(item, k) for k in producer_entities}
		if not serv_prices and self.user:
			incomplete, entries, time_required, max_qty_possible = self.fulfill(item, qty=1, man=self.user, check=True, v=v)
			if not incomplete:
				counterparty = self
			else:
				for indiv in self.factory.get(Individual):
					# TODO Display a list of available providers for user to choose from
					incomplete, entries, time_required, max_qty_possible = indiv.fulfill(item, qty=1, man=indiv.user, check=True, v=v)
					if not incomplete:
						counterparty = indiv
						break
				# TODO Loop through companies if still incomplete
				if incomplete:
					print('No {} exists that can provide the {} subscription for {}.'.format(', '.join(producers), item, self.name))
					return
		elif not serv_prices:
			counterparty = None
		else:
			counterparty_id = min(serv_prices, key=lambda k: serv_prices[k])
			counterparty = self.factory.get_by_id(counterparty_id)
		if counterparty is None:
			print('No {} exists that can provide the {} subscription for {}.'.format(producer, item, self.name))
			return
		print('{} chooses {} for the {} subscription counterparty.'.format(self.name, counterparty.name, item))
		return counterparty

	def order_subscription(self, item, counterparty=None, price=None, qty=1, priority=False, reason_need=False, buffer=False, v=True):
		qty = 1 # TODO Test this as it was a quick fix for a bug
		if counterparty is None:
			counterparty = self.subscription_counterparty(item)
		if counterparty is None:
			self.item_demanded(item, qty, priority=priority, reason_need=reason_need, v=v)
			return
		if price is None:
			price = world.get_price(item, counterparty.entity_id)
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		# TODO Allow ordering a subscription even without enough cash
		if cash >= price or args.jones:
			order_subscription_event = []
			first_payment = []
			incomplete, entries, time_required, max_qty_possible = counterparty.fulfill(item, qty, man=counterparty.user, v=v)
			if incomplete:
				return
			else:
				pass
				# TODO Check if it has a Subscription Available qty, if not then book one
			if entries:
				order_subscription_event += entries
			order_subscription_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Ordered ' + item, item, price, qty, 'Subscription Info', 'Order Subscription', 0 ]
			sell_subscription_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Sold ' + item, item, price, 0, 'Sell Subscription', 'Subscription Info', 0 ]
			order_subscription_event += [order_subscription_entry, sell_subscription_entry]
			if not args.jones:
				for _ in range(int(qty)):
					first_payment += self.pay_subscription(item, counterparty, buffer=buffer, first=True, v=v)
			event_id = max([entry[0] for entry in order_subscription_event])
			for entry in order_subscription_event:
				if entry[0] != event_id:
					if entry[0] in self.hold_event_ids or entry[0] in counterparty.hold_event_ids:
						self.hold_event_ids = [event_id if x == entry[0] else x for x in self.hold_event_ids]
						counterparty.hold_event_ids = [event_id if x == entry[0] else x for x in counterparty.hold_event_ids]
					if v: print('Sub Orig event_id: {} | New event_id: {} | {} | {}'.format(entry[0], event_id, self.hold_event_ids, counterparty.hold_event_ids))
					entry[0] = event_id
			if not first_payment and not args.jones:
				order_subscription_event = []
				first_payment = []
			elif buffer:
				order_subscription_event += first_payment
				if v: print('{} ordered {} subscription service from {}.'.format(self.name, item, counterparty.name))
				return order_subscription_event
			self.ledger.journal_entry(order_subscription_event)
			return True #TODO Make return order_subscription_event
		else:
			if v: print('{} does not have enough cash to pay {} for {} subscription. Cash: {}'.format(self.name, price, item, cash))
			result = self.loan(amount=(price - cash), item='Credit Line 5', auto=True)
			if result:
				self.order_subscription(item, counterparty=counterparty, price=price, qty=qty, buffer=buffer, v=v)
			if result is False:
				self.bankruptcy()
			#self.item_demanded(item, qty, cost=True, priority=priority) # TODO Decide how to handle
			counterparty.adj_price(item, qty=1, direction='down')

	def cancel_subscription(self, item, counterparty, price=0, qty=-1):
		cancel_subscription_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Cancelled ' + item, item, price, qty, 'Subscription Info', 'Cancel Subscription', 0 ]
		end_subscription_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'End ' + item, item, price, 0, 'End Subscription', 'Subscription Info', 0 ]
		cancel_subscription_event = [cancel_subscription_entry, end_subscription_entry]
		self.ledger.journal_entry(cancel_subscription_event)
		counterparty.adj_price(item, qty=1, direction='down')
		return cancel_subscription_event

	def check_subscriptions(self, counterparty=None, check=False, v=True):
		self.ledger.set_entity(self.entity_id)
		subscriptions_list = self.ledger.get_qty(accounts=['Subscription Info'])
		# print('Subscriptions List: \n{}'.format(subscriptions_list))
		rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		subscriptions_txns = self.ledger.gl[( (self.ledger.gl['debit_acct'] == 'Subscription Info') & (self.ledger.gl['credit_acct'] == 'Order Subscription') ) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Subscriptions TXNs: \n{}'.format(subscriptions_txns))
		self.ledger.reset()
		if not subscriptions_list.empty:
			for index, subscription in subscriptions_list.iterrows():
				item = subscription['item_id']
				freq = world.items.loc[item, 'freq']
				if freq is None:
					freq = 1
				if v: print(f'{item} payment freq: {freq}')
				days = (world.now - datetime.datetime(1986,10,1).date()).days
				if v: print('Current day:', days)
				if (args.jones and world.now == datetime.datetime(1986,10,1).date()):
					if v: print('No rent due on first day of play.')
					return
				if days % freq != 0:
					return
				counterparty, event_id = self.get_counterparty(subscriptions_txns, rvsl_txns, item, 'Sell Subscription') # Gets counterparty from new field in txn
				# Check if fulltime job is still required
				items_req = world.items[world.items['requirements'].str.contains(item, na=False)].reset_index()
				qty_active = self.ledger.get_qty(items=list(items_req['item_id'].values))
				#print('Qty Active: \n{}'.format(qty_active))
				if isinstance(qty_active, pd.DataFrame):
					if qty_active.empty:
						qty_active = 0
					else:
						qty_active = True
				if not qty_active:
					self.cancel_subscription(item, counterparty)
				else:
					self.pay_subscription(subscription['item_id'], counterparty, world.get_price(subscription['item_id'], counterparty.entity_id), subscription['qty'], check=check, v=v)

	def pay_subscription(self, item, counterparty, price=None, qty='', buffer=False, first=False, check=False, v=True):
		if price is None:
			price = world.get_price(item, counterparty.entity_id) # TODO Get price from subscription order
		if first:
			subscription_state = 1
		else:
			self.ledger.set_entity(self.entity_id)
			subscription_state = self.ledger.get_qty(items=item, accounts=['Subscription Info'])
			self.ledger.reset()
			# print('subscription_state:\n', subscription_state)
			if subscription_state:
				subscription_state = int(subscription_state)
		#print('Subscription State: {}'.format(subscription_state))
		if not subscription_state:
			return
		incomplete = False
		pay_subscription_event = []
		for _ in range(subscription_state):
			incomplete, entries, time_required, max_qty_possible = self.fulfill(item, qty=1, reqs='usage_req', amts='use_amount', check=check, v=v)
			pay_subscription_event += entries
			if check:
				continue
			self.ledger.set_entity(self.entity_id)
			cash = self.ledger.balance_sheet(['Cash'])
			self.ledger.reset()
			if (cash >= price and not incomplete) or (counterparty == self and not incomplete):
				pay_subscription_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Payment for ' + item, item, price, qty, 'Subscription Expense', 'Cash', price ]
				charge_subscription_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Received payment for ' + item, item, price, qty, 'Cash', 'Subscription Revenue', price ]
				pay_subscription_event += [pay_subscription_entry, charge_subscription_entry]
				if buffer:
					counterparty.adj_price(item, qty=1, direction='up_very_low')
					continue
				self.ledger.journal_entry(pay_subscription_event)
				counterparty.adj_price(item, qty=1, direction='up_very_low')
				if self.user and not first:
					needs = world.items.loc[item, 'satisfies']
					needs = [x.strip() for x in needs.split(',')]
					for need in needs:
						self.address_need(need)
			else:
				if not incomplete:
					if v: print('{} does not have enough cash to pay {} for {} subscription. Cash: {}'.format(self.name, price, item, cash))
					result = self.loan(amount=(price - cash), item='Credit Line 5', auto=True)
					if result:
						pay_subscription_event = self.pay_subscription(item, counterparty, price=price, qty=qty, buffer=buffer, first=first, check=check, v=v)
						return pay_subscription_event
					if result is False:
						self.bankruptcy()
				else:
					if v: print('{} cannot fulfill the requirements to keep {} subscription.'.format(self.name, item))
				if not first:
					self.cancel_subscription(item, counterparty)
		if not incomplete:
			return pay_subscription_event

	 # For testing and Jones (was collect_material())
	def spawn_item(self, item, qty=1, price=None, counterparty=None, account='Inventory'):
		if counterparty is None:
			counterparty = self
		if price is None:
			price = world.get_price(item, self.entity_id)
		spawn_item_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Spawn ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		spawn_item_event = [spawn_item_entry]
		self.ledger.journal_entry(spawn_item_event)
		return spawn_item_event

	 # For testing (was find_item())
	def spawn_equip(self, item, qty=1, price=None, counterparty=None, account='Equipment'):
		if counterparty is None:
			counterparty = self
		if price is None:
			price = world.get_price(item, self.entity_id)
		spawn_equip_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Spawn Equipment ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		spawn_equip_event = [spawn_equip_entry]
		self.ledger.journal_entry(spawn_equip_event)
		return spawn_equip_event

	def start_items(self, items, account='Equipment'):
		for item in items:
			item_type = world.get_item_type(item)
			if item_type == 'Subscription':
				self.order_subscription(item)
			else:
				self.spawn_item(item, account=account)

	def deposit(self, amount, counterparty=None):
		# TODO Make only one bank allowed per gov and auto select that bank entity as the counter party
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		if cash >= amount:
			# TODO Possibly reverse accounts if all money is deposited with the bank at initiation and loans are given
			deposit_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Deposit cash', '', '', '', 'Cash', 'Cash', amount ] # This entry isn't needed but could be implied
			bank_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Cash deposit', '', '', '', 'Cash', 'Deposits', amount ]
			deposit_event = [deposit_entry, bank_entry]
			self.ledger.journal_entry(deposit_event)
			return deposit_event
		else:
			print('{} does not have {} to deposit with {}. Cash held: {}'.format(self.name, amount, counterparty.name, cash))

	def withdrawal(self, amount, counterparty=None):
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash']) # TODO This assumes only one bank
		self.ledger.reset()
		if cash >= amount:
			withdrawal_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Withdraw cash', '', '', '', 'Cash', 'Cash', amount ]
			bank_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Cash withdraw', '', '', '', 'Deposits', 'Cash', amount ]
			withdrawal_event = [withdrawal_entry, bank_entry]
			self.ledger.journal_entry(withdrawal_event)
			return withdrawal_event
		else:
			print('{} does not have {} to withdraw from {}. Cash held in bank: {}'.format(self.name, amount, counterparty.name, cash))

	def allow_loan(self, counterparty, amount=None):
		# TODO Fully implement this
		self.ledger.set_entity(self.entity_id)
		bankrupt = self.ledger.balance_sheet(['Write-off'])
		if bankrupt:
			self.ledger.reset()
			return True
		debt = self.ledger.balance_sheet(['Loan'])
		if debt <= world.start_capital * 2:
			self.ledger.reset()
			return True
		return False

	def loan(self, amount=1000, counterparty=None, item=None, roundup=True, auto=False):
		if args.jones and auto:
			return
		# TODO Maybe remove default amount
		if roundup:
			if amount < 1000:
				amount = 1000
			else:
				amount = int(round(amount + 499.9, -3))
		if item is None:
			item = 'Init Capital'
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		if not counterparty.allow_loan(self, amount):
			return False
		self.ledger.set_entity(counterparty.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		qty = 1
		if cash >= amount:
			event = self.ledger.get_event() # To give both entries the same event_id # TODO Do this for other entries
			lend_entry = [ event, counterparty.entity_id, self.entity_id, world.now, '', 'Lend cash loan', item, 1, amount, 'Loans Receivable', 'Cash', amount ]
			loan_entry = [ event, self.entity_id, counterparty.entity_id, world.now, '', 'Borrow cash loan', item, 1, amount, 'Cash', 'Loan', amount ] # TODO Rename to: Borrow cash?
			loan_event = [lend_entry, loan_entry]
			self.ledger.journal_entry(loan_event)
			self.deposit(amount, counterparty)
			return loan_event
		else:
			print('{} does not have {} to loan to {}. Cash held by bank: {}'.format(counterparty.name, amount, self.name, cash))

	def repay_loans(self, v=True):
		# if self.user: # TODO Improve this
		# 	return
		self.ledger.set_entity(self.entity_id)
		debts = self.ledger.get_qty(accounts=['Loan'], credit=True)
		if debts.empty:
			print('{} has no debts.'.format(self.name))
			return
		if debts['qty'].sum() == 0:
			print('{} has paid off all of their debts.'.format(self.name))
			return
		other_debts = debts.loc[debts['item_id'] != 'Init Capital']
		if v: print('{} remaining debts:\n{}'.format(self.name, other_debts))
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		if not debts.empty:
			if v: print('{} has {} cash to repay debts:\n{}'.format(self.name, cash, debts))
			# if v: print('{} has {} cash to repay other_debts:\n{}'.format(self.name, cash, other_debts))
		if not other_debts.empty:
			if other_debts['qty'].sum() != 0:
				if cash >= 1000: # TODO Fix hardcoding
					other_debts = debts.loc[debts['qty'] != 0]
					debt_item = other_debts.iloc[0]['item_id']
					amount = -(other_debts.iloc[0]['qty'])
					amount = min(amount, 1000)
					self.repay(amount, item=debt_item)
			else:
				print('{} has paid off all of their other debts.'.format(self.name))
		if cash >= world.start_capital + 1000: # 251000:
			init_debts = debts.loc[debts['item_id'] == 'Init Capital']
			if not init_debts.empty:
				if init_debts['qty'].sum() != 0:
					init_debts = debts.loc[debts['qty'] != 0]
					init_debts = init_debts.reset_index(drop=True)
					debt_item = init_debts['item_id'].iloc[0]
					amount = -(init_debts['qty'].iloc[0])
					amount = min(amount, 1000)
					self.repay(amount, item=debt_item)
				else:
					print('{} has paid off all of their init debts.'.format(self.name))

	def repay(self, amount=1000, counterparty=None, item=None):
		# TODO Maybe remove default amount
		if item is None:
			item = 'Init Capital'
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		qty = 1
		if cash >= amount:
			event = self.ledger.get_event() # To give both entries the same event_id
			loan_repay_entry = [ event, self.entity_id, counterparty.entity_id, world.now, '', 'Repay loan', item, 1, amount, 'Loan', 'Cash', amount ]
			lend_repay_entry = [ event, counterparty.entity_id, self.entity_id, world.now, '', 'Loan repayment', item, 1, amount, 'Cash', 'Loans Receivable', amount ]
			loan_repay_event = [loan_repay_entry, lend_repay_entry]
			self.ledger.journal_entry(loan_repay_event)
			return loan_repay_event
		else:
			print('{} does not have {} to repay loan to {}. Cash held: {}'.format(self.name, amount, counterparty.name, cash))

	def check_interest(self, items=None):
		if items is None:
			items = world.items.loc[world.items['child_of'] == 'Loan'].index.tolist()
		if isinstance(items, str):
			items = [x.strip() for x in items.split(',')]
		for item in items:
			self.ledger.set_entity(self.entity_id)
			loan_bal = -(self.ledger.balance_sheet(['Loan'], item=item))
			cash = self.ledger.balance_sheet(['Cash'])
			self.ledger.reset()
			if loan_bal:
				print('{}: Loan Balance: {}'.format(self.name, loan_bal))
				# TODO Return bs of items with balance for given accounts
				counterparty = world.gov.bank
				int_rate_fix = world.items.loc[item, 'int_rate_fix']
				int_rate_var_check = world.items.loc[item, 'int_rate_var']
				if int_rate_var_check is not None:
					int_rate_var = world.gov.bank.interest_rate
					print('Central Bank Interest Rate: {}'.format(int_rate_var))
				else:
					int_rate_var = 0 # TODO Add var int logic and support
				rate = int_rate_fix + int_rate_var
				if not rate:
					return
				freq = world.items.loc[item, 'freq'] # TODO Add frequency logic
				period = 1 / freq
				int_amount = round(loan_bal * rate * period, 2)
				if cash >= int_amount:
					int_exp_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Interest expense for {}'.format(item), '', '', '', 'Interest Expense', 'Cash', int_amount ]
					int_rev_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Interest income from {}'.format(item), '', '', '', 'Cash', 'Interest Income', int_amount ]
					# TODO Add bank interest revenue entry
					int_exp_event = [int_exp_entry, int_rev_entry]
					self.ledger.journal_entry(int_exp_event)
					return int_exp_event
				else:
					print('{} does not have {} to pay interest to {}. Cash held: {}'.format(self.name, int_amount, counterparty.name, cash))
					result = self.loan(amount=(int_amount - cash), item='Credit Line 5', auto=True)
					if result:
						self.check_interest(items)
					if result is False:
						self.bankruptcy()

	def bankruptcy(self):
		print('{} has declared bankruptcy.'.format(self.name))
		# TODO Support bankruptcy when loans are from other entities other than the gov bank
		# TODO In future also transfer all assets proportionately

		# TODO Check for outstanding debts
		# TODO Check when last interest payment was made
		# TODO If it is greater than some timespan then enter bankruptcy

		# Write off all debt
		bankruptcy_event = []
		counterparty = world.gov.bank
		debt_items = world.items[world.items['child_of'] == 'Loan']
		self.ledger.set_entity(self.entity_id)
		for item_id, item in debt_items.iterrows():
			amount = -(self.ledger.balance_sheet(accounts=['Loan'], item=item_id))
			qty = -(self.ledger.get_qty(accounts=['Loan'], items=item_id, credit=True))
			if not amount and not qty:
				continue
			loan_bankruptcy_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Write-off loans', item_id, qty, amount, 'Loan', 'Write-off', amount ]
			loan_bankruptor_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Write-off bad debts', item_id, qty, amount, 'Bad Debts Expense', 'Loan', amount ]
			bankruptcy_event += [loan_bankruptcy_entry, loan_bankruptor_entry]
		# Transfer all cash to debtors
		cash = self.ledger.balance_sheet(accounts=['Cash'])
		cash_bankruptcy_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Bankruptcy cash transfer', '', '', '', 'Loss', 'Cash', cash ]
		cash_bankruptor_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Bankruptcy cash transfer', '', '', '', 'Cash', 'Gain', cash ]
		bankruptcy_event += [cash_bankruptcy_entry, cash_bankruptor_entry]
		# Transfer all other assets and set them for sale
		inv = self.ledger.get_qty()
		for _, item in inv.iterrows():
			item_type = world.get_item_type(item['item_id'])
			if item_type != 'Asset':
				continue
			amount = self.ledger.balance_sheet(accounts=item['account'], item=item['item_id'])
			asset_bankruptcy_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Bankruptcy asset transfer', item['item_id'], amount / item['qty'], item['qty'], 'Loss', item['account'], cash ]
			asset_bankruptor_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Bankruptcy asset transfer', item['item_id'], amount / item['qty'], item['qty'], 'Inventory', 'Gain', cash ]
			bankruptcy_event += [asset_bankruptcy_entry, asset_bankruptor_entry]
		self.ledger.reset()
		self.ledger.journal_entry(bankruptcy_event)
		return bankruptcy_event

	def depreciation_check(self, items=None): # TODO Add support for explicitly provided items
		if items is None:
			self.ledger.set_entity(self.entity_id)
			items_list = self.ledger.get_qty(accounts=['Buildings','Equipment','Inventory','Buildings In Use', 'Equipment In Use', 'Equipped'])
			#print('Dep. Items List: \n{}'.format(items_list))
			self.ledger.reset()
		for index, item in items_list.iterrows():
			#print('Depreciation Items: \n{}'.format(item))
			qty = item['qty']
			item = item['item_id']
			#print('Depreciation Item: {}'.format(item))
			self.derecognize(item, qty)
			metrics = world.items.loc[item, 'metric']
			if isinstance(metrics, str):
				metrics = [x.strip() for x in metrics.split(',')]
				metrics = list(filter(None, metrics))
			if metrics is None:
				metrics = ''
			lifespans = world.items.loc[item, 'lifespan']
			if isinstance(lifespans, str):
				lifespans = [x.strip() for x in lifespans.split(',')]
				lifespans = list(filter(None, lifespans))
			if lifespans is None:
				lifespans = ''
			for i, metric in enumerate(metrics):
				lifespan = int(lifespans[i])
				#print('{} Metric: {} | Lifespan: {}'.format(item, metric, lifespan))
				if metric != 'usage':
					self.depreciation(item, lifespan, metric)

	def depreciation(self, item, lifespan, metric, uses=1, man=False, buffer=False, v=False):
		# TODO Refactor to separate useage vs ticks apart
		if (metric == 'ticks') or (metric == 'usage') or (metric == 'equipped'):
			self.ledger.set_entity(self.entity_id)
			asset_bal = self.ledger.balance_sheet(accounts=['Buildings','Equipment','Buildings In Use', 'Equipment In Use', 'Equipped'], item=item) # TODO Maybe support other accounts and remove Inventory
			if asset_bal == 0:
				return [], None
			if metric == 'equipped':
				equip_bal = self.ledger.balance_sheet(accounts=['Equipped'], item=item)
				if equip_bal == 0:
					return [], None
			if metric == 'ticks':
				days = (world.now - datetime.datetime(1986,10,1).date()).days
				if days % 7 != 0:
					return [], None
			depreciation_event = []
			if v: print('Asset Bal for {}: {}'.format(item, asset_bal))
			dep_amount = (asset_bal / lifespan) * uses
			if v: print('Dep. amount for {}: {}'.format(item, dep_amount))
			accum_dep_bal = self.ledger.balance_sheet(accounts=['Accum. Depr.'], item=item)
			self.ledger.reset()
			if v: print('Accumulated Depreciation for {}: {}'.format(item, accum_dep_bal))
			remaining_amount = asset_bal - accum_dep_bal
			orig_uses = uses
			if dep_amount > remaining_amount:
				uses = math.floor(remaining_amount / (asset_bal / lifespan))
				self.derecognize(item, 1, metric) # TODO Handle more than 1 qty
				dep_amount = (asset_bal / lifespan) * uses
				new_qty = int(math.ceil((orig_uses - uses) / lifespan))
				if new_qty == 1:
					print('The {} breaks for the {}. Another {} is required to use.'.format(item, self.name, new_qty))
				else:
					print('The {} breaks for the {}. Another {} are required to use.'.format(item, self.name, new_qty))
				# Try to purchase a new item if current one breaks
				if not man:
					# TODO Try to produce first, make aquire function that tries to produce first then attempt to purchase
					outcome = self.purchase(item, new_qty, v=v)
					if outcome:
						entries, new_uses = self.depreciation(item, lifespan, metric, (orig_uses - uses), buffer)
						if entries:
							depreciation_event += entries
							uses += new_uses
					elif not outcome and uses == 0:
						return [], None
				elif not outcome and uses == 0:
					return [], None
			#print('Depreciation: {} {} {} {}'.format(item, lifespan, metric, dep_amount))
			dep_amount = round(dep_amount, 5)
			depreciation_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Depreciation from ' + metric + ' of ' + item, item, '', '', 'Depr. Expense', 'Accum. Depr.', dep_amount ]
			depreciation_event += [depreciation_entry]
			if buffer:
				return depreciation_event, uses
			if metric == 'usage':
				print('{} uses {} {} times.'.format(self.name, item, uses))
			self.ledger.journal_entry(depreciation_event)
			return depreciation_event, uses

		if (metric == 'spoilage') or (metric == 'obsolescence'):
			#print('Spoilage: {} {} days {}'.format(item, lifespan, metric))
			self.ledger.refresh_ledger()
			#print('GL: \n{}'.format(self.ledger.gl.tail()))
			rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			# Get list of Inventory txns
			inv_txns = self.ledger.gl[(self.ledger.gl['debit_acct'] == 'Inventory')
				& (self.ledger.gl['item_id'] == item)
				& (~self.ledger.gl['event_id'].isin(rvsl_txns))]
			#print('Inv TXNs: \n{}'.format(inv_txns))
			if not inv_txns.empty:
				# Compare the gl dates to the lifetime from the items table
				items_spoil = world.items[world.items['metric'].str.contains('spoilage', na=False)]
				metrics = items_spoil.loc[item, 'metric']
				if isinstance(metrics, str):
					metrics = [x.strip() for x in metrics.split(',')]
					metrics = list(filter(None, metrics))
				if metrics is None:
					metrics = ''
				lifespans = items_spoil.loc[item, 'lifespan']
				if isinstance(lifespans, str):
					lifespans = [x.strip() for x in lifespans.split(',')]
					lifespans = list(filter(None, lifespans))
				if lifespans is None:
					lifespans = ''
				for i, metric in enumerate(metrics):
					lifespan = int(lifespans[i])
					if metric == 'spoilage' or metric == 'obsolescence':
						break
				#print('Spoilage Lifespan: {}'.format(item))
				for txn_id, inv_lot in inv_txns.iterrows():
					#print('TXN ID: {}'.format(txn_id))
					#print('Inv Lot: \n{}'.format(inv_lot))
					date_done = (datetime.datetime.strptime(inv_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=int(lifespan))).date()
					#print('Date Done: {}'.format(date_done))
					# If the time elapsed has passed
					if date_done == world.now:
						self.ledger.set_entity(self.entity_id)
						qty = self.ledger.get_qty(item, 'Inventory')
						if qty == 0:
							print('{} spoilage TXNs for {} {} returning zero.'.format(self.name, qty, item))
							return
						txns = self.ledger.hist_cost(qty, item, 'Inventory', remaining_txn=True)
						self.ledger.reset()
						if not isinstance(txns, pd.DataFrame):
							print('{} spoilage TXNs for {} {} returning zero.'.format(self.name, qty, item))
							return
						# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
						# 	print('{} spoilage TXNs for {} {}: \n{}'.format(self.name, qty, item, txns)) # Debug
							# print('Looking fo TXN ID: {}'.format(txn_id))
						#print('Spoilage QTY: {}'.format(qty))
						if txn_id in txns.index:
							txn_qty = txns[txns.index == txn_id]['qty'].iloc[0]
							#print('Spoilage TXN QTY: {}'.format(txn_qty))
							# Book thes spoilage entry
							if qty < txn_qty:
								spoil_entry = [[ inv_lot['event_id'], inv_lot['entity_id'], inv_lot['cp_id'], world.now, inv_lot['loc'], inv_lot['item_id'] + ' spoilage', inv_lot['item_id'], inv_lot['price'], qty or '', 'Spoilage Expense', 'Inventory', inv_lot['price'] * qty ]]
							else:
								spoil_entry = [[ inv_lot['event_id'], inv_lot['entity_id'], inv_lot['cp_id'], world.now, inv_lot['loc'], inv_lot['item_id'] + ' spoilage', inv_lot['item_id'], inv_lot['price'], inv_lot['qty'] or '', 'Spoilage Expense', 'Inventory', inv_lot['amount'] ]]
							self.ledger.journal_entry(spoil_entry)
							self.adj_price(item, qty, direction='down_high')

	def impairment(self, item, amount):
		# TODO Maybe make amount default to None and have optional impact or reduction parameter
		# item_type = world.get_item_type(item)
		# asset_bal = self.ledger.balance_sheet(accounts=[item_type], item=item)

		impairment_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Impairment of ' + item, item, '', '', 'Loss on Impairment', 'Accum. Impairment Losses', amount ]
		impairment_event = [impairment_entry]
		self.ledger.journal_entry(impairment_event)
		return impairment_event

	def derecognize(self, item, qty=1, metric=None, v=False):
		if item == 'Hydroponics':
			v = True
		# TODO Check if item in use
		# TODO Check if item uses land and release that land
		# item_type = world.get_item_type(item)
		self.ledger.set_entity(self.entity_id)
		asset_bal = self.ledger.balance_sheet(accounts=['Buildings','Equipment','Buildings In Use', 'Equipment In Use', 'Equipped'], item=item)# TODO Maybe support other accounts
		if v: print(f'derecognize bal for {item}: {asset_bal}')
		if asset_bal == 0:
			return
		accum_dep_bal = self.ledger.balance_sheet(accounts=['Accum. Depr.'], item=item)
		accum_imp_bal = self.ledger.balance_sheet(accounts=['Accum. Impairment Losses'], item=item)
		self.ledger.reset()
		accum_reduction = abs(accum_dep_bal) + abs(accum_imp_bal)
		if v: print(f'derecognize accum for {item}: {accum_reduction}')
		if accum_reduction >= asset_bal:
			derecognition_event = []
			item_info = world.items.loc[item]
			if (item_info['usage_req'] is None or item_info['use_amount'] is None) and (item_info['hold_req'] is None or item_info['hold_amount'] is None):
				return None, [], None
			if metric == 'usage':
				requirements_use = [x.strip() for x in item_info['usage_req'].split(',') if x is not None]
				amounts_use = [x.strip() for x in item_info['use_amount'].split(',') if x is not None]
				amounts_use = list(map(float, amounts_use))
			else:
				requirements_use = []
				amounts_use = []

			requirements_hold = [x.strip() for x in item_info['hold_req'].split(',') if x is not None]
			amounts_hold = [x.strip() for x in item_info['hold_amount'].split(',') if x is not None]
			amounts_hold = list(map(float, amounts_hold))
			requirements = requirements_use + requirements_hold
			amounts = amounts_use + amounts_hold
			if v: print(f'requirements of {item} for {metric}: {requirements}')
			if v: print(f'amounts of {item} for {metric}: {amounts}')

			for i, requirement in enumerate(requirements):
				requirement_type = world.get_item_type(requirement)
				if requirement_type == 'Land' or requirement_type == 'Buildings' or requirement_type == 'Equipment':
					req_qty = amounts[i] # TODO Support modifiers
					req_price = world.get_price(requirement, self.entity_id) # TODO Use price from entry
					release_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Release ' + requirement + ' used by ' + item, requirement, req_price, req_qty, requirement_type, requirement_type + ' In Use', req_price * req_qty ]
					derecognition_event += [release_entry]

			derecognition_event += self.release(item, qty=qty)
			# TODO Check if item is In Use
			derecognition_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Derecognition of ' + item, item, asset_bal / qty, qty, 'Accum. Depr.', 'Equipment', asset_bal ]
			overage_entry = []
			if accum_reduction > asset_bal:
				overage = accum_reduction - asset_bal
				overage_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Derecognition of ' + item + ' (Overage)', item, overage / qty, qty, 'Accum. Depr.', 'Depr. Expense', overage ]
				derecognition_event += [derecognition_entry, overage_entry]
			else:
				derecognition_event += [derecognition_entry]
			self.ledger.journal_entry(derecognition_event)

	def action(self, command=None, external=False):
		if command is None: # TODO Allow to call bs command from econ.py
			command = args.command
		if command is None and not external:
			try:
				command = input('Enter an action or "help" for more info: ')
			except EOFError as e:
				command = None
				sys.stdin = open('/dev/tty')
				return
		# TODO Add help command to list full list of commands
		if command.lower() == 'select':
			if not world.gov.user and isinstance(world.selection, Individual):
				individual_ids = self.get_children(founder=True, ids=True)#, v=True) # TODO Maybe replace with self.founder check
				individuals = [self.factory.get_by_id(entity_id) for entity_id in individual_ids]
			elif isinstance(world.selection, Corporation):
				largest_shareholder_id = self.list_shareholders(largest=True)
				individual_ids = [largest_shareholder_id]
				if largest_shareholder_id is None:
					return
				individuals = [self.factory.get_by_id(largest_shareholder_id)]
			else:
				individuals = world.gov.get(Individual, computers=False)
			for entity in individuals:
				print('{} Hours: {}'.format(entity, entity.hours))
			print()
			banks = world.gov.get(Bank, computers=False)
			for entity in banks:
				print('{}'.format(entity))
			# TODO Maybe support seeing all corps owned by all individuals the player controls
			corps = []
			if isinstance(self, (Individual, Corporation, Government, Governmental)):
				corps = self.is_shareholder(world.gov.get(Corporation))
			for entity in corps:
				print('{}'.format(entity))
			corp_ids = []
			if not world.gov.user:
				bank_ids = [bank.entity_id for bank in banks]
				corp_ids = [corp.entity_id for corp in corps]
				entities = individual_ids + corp_ids + bank_ids
			else:
				entities = world.gov.get(computers=False, ids=True, envs=False)
			while True:
				try:
					selection = input('Enter an entity ID number: ')
					if selection == '':
						return
					selection = int(selection)
				except ValueError:
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, entities))
					continue
				if selection not in entities:
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, entities))
					continue
				world.selection = self.factory.get_by_id(selection)
				break
			return world.selection
		elif command.lower() == 'superselect':
			entities = self.factory.get()
			for entity in entities:
				if isinstance(entity, Individual):
					print('{} Hours: {}'.format(entity, entity.hours))
				else:
					print('{}'.format(entity))
			print()
			entity_ids = self.factory.get(ids=True)
			while True:
				try:
					selection = input('Enter an entity ID number: ')
					if selection == '':
						return
					selection = int(selection)
				except ValueError:
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, entity_ids))
					continue
				if selection not in entity_ids:
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, entity_ids))
					continue
				world.selection = self.factory.get_by_id(selection)
				break
			return world.selection
		elif command.lower() == 'win':
			print(f'Win Conditions:\n{world.win_conditions}\n')
		# elif command.lower() == 'checkwin':
		# 	print(f'Win Conditions:\n{world.win_conditions}\n')
		# 	# TODO Add ability to keep playing
		# 	world.check_end()
		elif command.lower() == 'edititem':
			world.edit_item()
		elif command.lower() == 'user' or command.lower() == 'toggle' or command.lower() == 'toggleuser':
			target = world.toggle_user()
			if target is None:
				return
			print('{} | User: {}'.format(target.name, target.user))
			if target.user and not isinstance(target, Government):
				world.selection = target
				return world.selection
			else:
				world.selection = None
				return
		elif command.lower() == 'setwin':
			world.set_win(world.win_conditions)
		elif command.lower() == 'incorp':
			while True:
				corp = input('Enter a corp: ')
				if corp == '':
					return
				if world.valid_corp(corp):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			others = False
			counterparty = self
			founders = collections.OrderedDict()
			while True: # TODO Add support for multiple founders (this may be done)
				if others:
					while True:
						try:
							counterparty = input('Enter an entity ID number for the next founder: ')
							if counterparty == '':
								return
							counterparty = int(counterparty)
						except ValueError:
							print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, world.gov.get(ids=True, envs=False)))
							continue
						if counterparty not in world.gov.get(ids=True, envs=False):
							print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, world.gov.get(ids=True, envs=False)))
							continue
						counterparty = self.factory.get_by_id(counterparty)
						break
				try:
					if not others:
						qty = input('Enter the amount of founding capital: ')
					else:
						qty = input('Enter the amount of contributing capital: ')
					if qty == '':
						return
					qty = int(qty)
					founders[counterparty] = qty
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty < 0:
						print('Not a valid entry. Must be a positive whole number.')
						continue
					while True:
						others = input('Any other founders? [y/n]: ')
						# if others == '':
						# 	others = 'Y'
						if others.upper() == 'Y':
							others = True
							break
						elif others.upper() == 'N':
							others = False
							break
						else:
							print('Not a valid entry. Must be "Y" or "N".')
							continue
					if not others:
						break
			self.incorporate(name=corp.title(), founders=founders)
		elif command.lower() == 'raisecap':
			others = False
			investors = collections.OrderedDict()
			while True:
				while True:
					try:
						counterparty = input('Enter an entity ID number for the investor: ')
						if counterparty == '':
							return
						counterparty = int(counterparty)
					except ValueError:
						print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, world.gov.get(ids=True, envs=False)))
						continue
					if counterparty not in world.gov.get(ids=True, envs=False):
						print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, world.gov.get(ids=True, envs=False)))
						continue
					counterparty = self.factory.get_by_id(counterparty)
					break
				try:
					qty = input('Enter the amount of shares to sell to the investor: ')
					if qty == '':
						return
					qty = int(qty)
					investors[counterparty] = qty
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					while True:
						others = input('Any other investors? [y/n]: ')
						# if confirm == '':
						# 	confirm = 'Y'
						if others.upper() == 'Y':
							others = True
							break
						elif others.upper() == 'N':
							others = False
							break
						else:
							print('Not a valid entry. Must be "Y" or "N".')
							continue
					if not others:
						break
			try:
				self.raise_capital(investors=investors)
			except AttributeError as e:
				print('Only corporations can sell shares, but an {} is selected.'.format(self.__class__.__name__))
				print('Error: {}'.format(repr(e)))
		elif command.lower() == 'claimland' or command.lower() == 'claim' or command.lower() == 'c':
			while True:
				item = input('Enter type of land to claim: ')
				if item == '':
					return
				if world.valid_item(item, 'Land'):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} to claim: '.format(item))
					if qty == '':
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			counterparty = 0
			while True:
				try:
					counterparty = input('Enter an entity ID number to claim from ({} for nature)[{}]: '.format(world.env.entity_id, world.env.entity_id))
					if counterparty == '':
						# Shortcut instead of return
						counterparty = world.env.entity_id
					counterparty = int(counterparty)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, self.factory.get_all_ids()))
					continue
				if counterparty not in self.factory.get_all_ids():
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, self.factory.get_all_ids()))
					continue
				counterparty = self.factory.get_by_id(counterparty)
				break
			price = 0
			self.claim_land(item.title(), qty, price, counterparty)
		elif command.lower() == 'hire' or command.lower() == 'work':
			while True:
				item = input('Enter type of job to hire for: ')
				if item == '':
					return
				if world.valid_item(item, 'Labour') or world.valid_item(item, 'Job'):
					break
				else:
					print('Not a valid entry.')
					continue
			worker = self.worker_counterparty(item.title(), only_avail=True, v=True)#, qualified=True)
			if worker == 'none_qualify':
				if args.jones:
					print(f'You are not qualified to work as a {item.title()}.')
				else:
					print(f'No one is qualified to work as a {item.title()}.')
				return
			print('worker:', worker)
			item_type = world.get_item_type(item.title())
			if item_type == 'Job':
				self.hire_worker(item.title(), worker)
			else:
				hours = 0
				while True:
					try:
						hours = input('Enter number of hours for {}: '.format(item))
						if hours == '':
							return
						hours = int(hours)
					except ValueError:
						print('Not a valid entry. Must be a positive whole number.')
						continue
					else:
						if hours <= 0:
							continue
						break
				if args.jones:
					businesses = world.items.loc[item.title(), 'producer']
					businesses = [x.strip() for x in businesses.split(',')]
					# TODO This is a temp fix until the business can be chosen by the user
					if args.random:
						counterparty = random.choice(businesses)
					else:
						counterparty = businesses[0]
					counterparty = self.factory.get_by_name(counterparty, generic=True)
					# TODO Function settings to pay wages immediately
					counterparty.accru_wages(item.title(), worker, hours)
				else:
					self.accru_wages(item.title(), worker, hours)
		elif command.lower() == 'study' or command.lower() == 'rstudy':
			man = True
			if command.lower() == 'rstudy':
				man = False
			while True:
				item = input('Enter item to study: ')
				if item == '':
					return
				if world.valid_item(item, 'Education'):
					break
				else:
					print('Not a valid entry.')
					continue
			hours = 0
			while True:
				try:
					hours = input('Enter number of sessions to study {}: '.format(item))
					if hours == '':
						return
					hours = int(hours)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if hours <= 0:
						continue
					break
			self.produce(item.title(), qty=hours, man=man) # TODO Maybe make a study() function wrapper
		elif command.lower() == 'gift':
			while True:
				item = input('Enter cash or item to gift: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				elif item.title() == 'Cash':
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to gift: '.format(item))
					if qty == '':
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			while True:
				try:
					counterparty = input('Enter an entity ID number to gift {} {} to: '.format(qty, item))
					if counterparty == '':
						return
					counterparty = int(counterparty)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, self.factory.get_all_ids()))
					continue
				if counterparty not in self.factory.get_all_ids():
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, self.factory.get_all_ids()))
					continue
				counterparty = self.factory.get_by_id(counterparty)
				break
			self.gift(item.title(), qty, counterparty)
		elif command.lower() == 'purchase' or command.lower() == 'buy':
			while True:
				item = input('Enter item to purchase: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to purchase: '.format(item.title()))
					if qty == '':
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.purchase(item.title(), qty)
		elif command.lower() == 'sale':
			while True:
				item = input('Enter item to put up for sale: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to put up for sale: '.format(item))
					if qty == '':
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.sale(item.title(), qty)
		elif command.lower() == 'consume':
			while True:
				item = input('Enter item to consume: ') # TODO Some sort of check for non-consumable items
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to consume: '.format(item))
					if qty == '':
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.consume(item.title(), qty)
		elif command.lower() == 'recurproduce' or command.lower() == 'rproduce':
			while True:
				item = input('Enter item to produce: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to produce: '.format(item))
					if qty == '':
						qty = 1
						# return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			result = self.wip_check(items=item.title())
			if result:
				print(f'WIP for {item.title()} completed. If you would like to produce more, enter the produce command again.')
				return
			produce_event, time_required, max_qty_possible, incomplete = self.produce(item.title(), qty)
			if incomplete and max_qty_possible != 0:
				self.produce(item.title(), qty=max_qty_possible)
		elif command.lower() == 'produce' or command.lower() == 'p':
			while True:
				item = input('Enter item to produce: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to produce[1]: '.format(item))
					if qty == '':
						qty = 1
						# return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			result = self.wip_check(items=item.title())
			if result:
				print(f'WIP for {item.title()} completed. If you would like to produce more, enter the produce command again.')
				return
			produce_event, time_required, max_qty_possible, incomplete = self.produce(item.title(), qty, man=True)
			if incomplete and max_qty_possible != 0:
				while True:
					confirm = input('Would you like to produce {} units of {} instead? [Y/n]: '.format(max_qty_possible, item))
					if confirm == '':
						confirm = 'Y'
					if confirm.upper() == 'Y':
						confirm = True
						break
					elif confirm.upper() == 'N':
						confirm = False
						break
					else:
						print('Not a valid entry. Must be "Y" or "N".')
						continue
				if confirm:
					self.produce(item.title(), qty=max_qty_possible)
		elif command.lower() == 'autoproduce' or command.lower() == 'queue' or command.lower() == 'autoproduceonce' or command.lower() == 'mautoproduce' or command.lower() == 'rautoproduce' or command.lower() == 'a':
			one_time = False
			man = False
			if command.lower() == 'queue' or command.lower() == 'autoproduceonce':
				one_time = True
				man = True
			if command.lower() == 'rautoproduce':
				man = False
			if command.lower() == 'mautoproduce':
				man = True
			while True:
				item = input('Enter item to produce: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item to produce[1]: '.format(item))
					if qty == '':
						qty = 1
						# return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			freq = 0
			while True:
				try:
					freq = input('Enter number of days between production of {} {} (0 for daily)[0]: '.format(qty, item))
					if freq == '':
						freq = 0
					freq = int(freq)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if freq < 0:
						continue
					break
			self.set_produce(item.title(), qty, freq, one_time=one_time, man=man)
			# if command.lower() == 'queue' or command.lower() == 'autoproduceonce':
			# 	self.auto_produce(world.produce_queue.index[-1])
		elif command.lower() == 'stopautoproduce' or command.lower() == 'stopa':
			print('World Auto Produce as of {}: \n{}'.format(world.now, world.produce_queue))
			idx = None
			while True:
				try:
					idx = input('Enter the index number of the autoproduce line to remove: ')
					if idx == '':
						return
					idx = int(idx)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number from the autoproduce table index.')
					continue
				else:
					if idx not in world.produce_queue.index.tolist():
						print('Not a valid entry. Must be a positive whole number from the autoproduce table index.')
						continue
					break
			world.produce_queue.drop([idx], inplace=True)
			print('World Auto Produce as of {} after removal: \n{}'.format(world.now, world.produce_queue))
		elif command.lower() == 'autowip':
			self.auto_wip = not self.auto_wip
			print('Auto WIP now set to:', self.auto_wip)
		elif command.lower() == 'wip' or command.lower() == 'w':
			self.wip_check()
		elif command.lower() == 'raw' or command.lower() == 'rawbase' or command.lower() == 'r':
			base = False
			if command.lower() == 'rawbase':# or command.lower() == 'r':
				base = True
			while True:
				item = input('Enter item to see total raw resources required: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter quantity of {} item[1]: '.format(item.title()))
					if qty == '':
						qty = 1
						# return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.get_raw(item.title(), qty, base=base, v=True)
		elif command.lower() == 'address':
			print('Will attempt to address needs with items on hand.')
			# priority_needs = {}
			# for need in self.needs:
			# 	priority_needs[need] = self.needs[need]['Current Need']
			# priority_needs = {k: v for k, v in sorted(priority_needs.items(), key=lambda item: item[1])}
			# priority_needs = collections.OrderedDict(priority_needs)
			# for need in priority_needs:
			self.address_needs(obtain=False)
		elif command.lower() == 'autoaddress':
			if isinstance(self, Individual):
				self.auto_address = not self.auto_address
				print('Auto Address set to:', self.auto_address)
				print('Will run at the end of the day.')
		elif command.lower() == 'use':
			while True:
				item = input('Enter item to use: ') # TODO Some sort of check for non-usable items
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					qty = input('Enter number of uses for {} item: '.format(item))
					if qty == '':
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.use_item(item.title(), qty)
		elif command.lower() == 'equip':
			while True:
				item = input('Enter item to equip: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			self.equip_item(item.title())
		elif command.lower() == 'unequip':
			while True:
				item = input('Enter item to unequip: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			self.unequip_item(item.title())
		elif command.lower() == 'attack':
			while True:
				item = input('Enter item to attack with: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 1
			while True:
				try:
					counterparty = input('Enter an entity ID number to attack: ')
					if counterparty == '':
						return
					counterparty = int(counterparty)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, self.factory.get_all_ids()))
					continue
				if counterparty not in self.factory.get_all_ids():
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, self.factory.get_all_ids()))
					continue
				counterparty = self.factory.get_by_id(counterparty)
				break
			while True:
				try:
					target = input('Enter an item or Individual to attack: ') # TODO Validate item or Individual
					if target == '':
						return
					target = int(target)
				except ValueError:
					if world.valid_item(target):
						break
					else:
						print('"{}" is not a valid entry. Must be a valid item or one of the following numbers: \n{}'.format(target, self.factory.get(Individual, ids=True)))
						continue
				if target not in self.factory.get(Individual, ids=True):
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(target, self.factory.get(Individual, ids=True)))
					continue
				# target = self.factory.get_by_id(target)
				break
			self.use_item(item.title(), qty, counterparty, target)
		elif command.lower() == 'players':
			for entity in self.factory.get():
				print(f'{entity}\t | User: {entity.user}')
				# TODO Add owner, NAV, Cash
		elif command.lower() == 'birth':
			if not world.gov.user:
				individual_ids = self.get_children(founder=True, ids=True)
			else:
				individual_ids = world.gov.get(Individual, ids=True)
			while True:
				try:
					counterparty = input('Enter an entity ID number to conceive with: ')
					if counterparty == '':
						return
					counterparty = int(counterparty)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, individual_ids))
					continue
				if counterparty not in world.gov.get(Individual, ids=True):
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, individual_ids))
					continue
				counterparty = self.factory.get_by_id(counterparty)
				break
			amount_1 = 0
			while True:
				try:
					amount_1 = input('Enter amount of cash to pass on to child from the first parent: ')
					if amount_1 == '':
						return
					amount_1 = int(amount_1)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if amount_1 < 0:
						continue
					break
			amount_2 = 0
			while True:
				try:
					amount_2 = input('Enter amount of cash to pass on to child from the second parent: ')
					if amount_2 == '':
						return
					amount_2 = int(amount_2)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if amount_2 < 0:
						continue
					break
			try:
				self.birth(counterparty, amount_1, amount_2)
			except AttributeError as e:
				print('Only Individuals can give birth, but a {} is selected.'.format(self.__class__.__name__))
				print('Error: {}'.format(repr(e)))
		elif command.lower() == 'seppuku':
			while True:
				confirm = input('Does {} really want to commit seppuku? [y/N]: '.format(self.name))
				if confirm == '':
					confirm = 'N'
				if confirm.upper() == 'Y':
					confirm = True
					break
				elif confirm.upper() == 'N':
					confirm = False
					break
				else:
					print('Not a valid entry. Must be "Y" or "N".')
					continue
			if confirm:
				self.seppuku()
				world.selection = None
				return
		elif command.lower() == 'addplayer':
			self.add_person()
		elif command.lower() == 'addai':
			self.add_person(user=False)
		elif command.lower() == 'emance':
			if not isinstance(self, Individual):
				print('{} is not an Individual and unable to be emancipated from their parents.'.format(self.name))
				return
			self.emancipation()
		elif command.lower() == 'changegov':
			if isinstance(self, Government):
				print('{} is a Government and cannot change change allegiance.'.format(self.name))
				return
			while True:
				try:
					gov_id = input('Enter an entity ID for another Government: ')
					if gov_id == '':
						return
					gov_id = int(gov_id)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(gov_id, self.factory.get(Government, ids=True)))
					continue
				if gov_id not in self.factory.get(Government, ids=True):
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(gov_id, self.factory.get(Government, ids=True)))
					continue
				break
			self.change_allegiance(gov_id)
		elif command.lower() == 'foundgov':
			if not isinstance(self, Individual):
				print('{} is a {} and must be an Individual to found another Government.'.format(self.name, self.__class__.__name__))
				return
			self.found_gov()
		elif command.lower() == 'dividend':
			if not isinstance(self, Corporation):
				print('{} is not a Corporation and unable to pay dividends.'.format(self.name))
				return
			div_rate = 0
			while True:
				try:
					div_rate = input('Enter amount of cash to pass on to child: ')
					if div_rate == '':
						return
					div_rate = float(div_rate)
				except ValueError:
					print('Not a valid entry. Must be a positive number.')
					continue
				else:
					if div_rate <= 0:
						continue
					break
			try:
				self.dividend(div_rate)
			except AttributeError as e:
				print('Only Corporations can pay dividends, but an {} is selected.'.format(self.__class__.__name__))
				print('Error: {}'.format(repr(e)))
		elif command.lower() == 'setprice':
			while True:
				item = input('Enter item to set the price of: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			qty = 0
			while True:
				try:
					price = input('Enter price to set to: ')
					if price == '':
						return
					price = float(price)
				except ValueError:
					print('Not a valid entry. Must be a positive number.')
					continue
				else:
					if price < 0:
						continue
					elif price == 0:
						print('That\'s cheating!')
						continue
					break
			self.set_price(item.title(), qty, price)
		elif command.lower() == 'adjrate':
			change = 0
			while True:
				try:
					change = input('Enter amount to change interest rate by: ')
					if change == '':
						return
					change = float(change)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if change <= 0:
						continue
					break
			try:
				self.adj_rate(change)
			except AttributeError as e:
				print('Only the {} can adjust the interest rate, but {} is selected.'.format(world.gov.bank.name, self.name))
				print('Error: {}'.format(repr(e)))
		elif command.lower() == 'deposit':
			counterparty = world.gov.bank
			while True:
				try:
					amount = input('Enter amount to deposit: ')
					if amount == '':
						return
					amount = float(amount)
				except ValueError:
					print('Not a valid entry. Must be a positive number.')
					continue
				else:
					if amount <= 0:
						continue
					break
			self.deposit(amount, counterparty)
		elif command.lower() == 'withdraw':
			counterparty = world.gov.bank
			while True:
				try:
					amount = input('Enter amount to withdraw: ')
					if amount == '':
						return
					amount = float(amount)
				except ValueError:
					print('Not a valid entry. Must be a positive number.')
					continue
				else:
					if amount <= 0:
						continue
					break
			self.withdrawal(amount, counterparty)
		elif command.lower() == 'loan':
			counterparty = world.gov.bank
			while True:
				try:
					amount = input('Enter amount to borrow as loan: ')
					if amount == '':
						return
					amount = float(amount)
				except ValueError:
					print('Not a valid entry. Must be a positive number.')
					continue
				else:
					if amount <= 0:
						continue
					break
			result = self.loan(amount, counterparty, item=None, roundup=False)
		elif command.lower() == 'repay':
			counterparty = world.gov.bank
			while True:
				try:
					amount = input('Enter amount to repay of loan: ')
					if amount == '':
						return
					amount = float(amount)
				except ValueError:
					print('Not a valid entry. Must be a positive number.')
					continue
				else:
					if amount <= 0:
						continue
					break
			self.repay(amount, counterparty, item=None)
		elif command.lower() == 'bankruptcy':
			while True:
				confirm = input('Does {} really want to declare bankruptcy? [y/N]: '.format(self.name))
				if confirm == '':
					confirm = 'N'
				if confirm.upper() == 'Y':
					confirm = True
					break
				elif confirm.upper() == 'N':
					confirm = False
					break
				else:
					print('Not a valid entry. Must be "Y" or "N".')
					continue
			if confirm:
				self.bankruptcy()
		elif command.lower() == 'owned':
			start_time = timeit.default_timer()
			self.ledger.set_entity(self.entity_id)
			inv = self.ledger.get_qty()
			self.ledger.reset()
			pd.options.display.float_format = '{:,.2f}'.format
			print(inv)
			pd.options.display.float_format = '${:,.2f}'.format
			print('Time taken:', timeit.default_timer() - start_time)
		elif command.lower() == 'own' or command.lower() == 'o':
			start_time = timeit.default_timer()
			self.ledger.set_entity(self.entity_id)
			inv = self.ledger.get_qty(accounts=['Cash', 'Investments', 'Land', 'Buildings', 'Equipment', 'Equipped', 'Subscription Info', 'Inventory', 'WIP Inventory', 'WIP Equipment', 'Building Under Construction', 'Land In Use', 'Buildings In Use', 'Equipment In Use', 'Education Expense', 'Technology', 'Researching Technology'])
			self.ledger.reset()
			pd.options.display.float_format = '{:,.2f}'.format
			print(inv)
			pd.options.display.float_format = '${:,.2f}'.format
			print('Time taken:', timeit.default_timer() - start_time)
		elif command.lower() == 'labour':
			start_time = timeit.default_timer()
			self.ledger.set_entity(self.entity_id)
			inv = self.ledger.get_qty(accounts=['Wages Receivable', 'Education Expense', 'Studying Education'])
			self.ledger.reset()
			print(inv)
			print('Time taken:', timeit.default_timer() - start_time)
		elif command.lower() == 'hours' or command.lower() == 'h':
			world.get_hours(v=True)
		elif command.lower() == 'land':
			world.unused_land()
		elif command.lower() == 'map':
			world.unused_land(all_land=True)
		elif command.lower() == 'world':
			world.unused_land(entity_id=world.env.entity_id)
		elif command.lower() == 'demand':
			print('World Demand as of {}: \n{}'.format(world.now, world.demand))
		elif command.lower() == 'prices':
			with pd.option_context('display.max_rows', None):
				print('\nPrices as of {}: \n{}\n'.format(world.now, world.prices))
		elif command.lower() == 'wages':
			with pd.option_context('display.max_rows', None):
				labour_items = world.items.loc[world.items['child_of'] == 'Labour'].index.values.tolist()
				print(labour_items)
				print(type(labour_items))
				# wages = world.prices.loc[labour_items]
				wages = world.prices[world.prices.index.isin(labour_items)]
				# wages = world.prices.loc[world.prices.index.intersection(labour_items), :]
				print('\nWages as of {}: \n{}\n'.format(world.now, wages))
		elif command.lower() == 'delay' or command.lower() == 'd':
			print('Delayed items as of {}: \n{}'.format(world.now, world.delay))
		elif command.lower() == 'auto':
			print('World Auto Produce as of {}: \n{}'.format(world.now, world.produce_queue))
		elif command.lower() == 'savedf':
			df_name = input('Enter name of df to save: ' )
			save_df = None
			try:
				# save_df = locals()[df_name]
				save_df = getattr(world, df_name)
			except KeyError as e:
				print(f'Error: {repr(e)}')
			if isinstance(save_df, pd.DataFrame):
				file_name = 'data/' + df_name + '_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
				save_df.to_csv(file_name, index=True)
				print(f'{df_name} saved as: {file_name}')
		elif command.lower() == 'cash' or command.lower() == 'money':
			self.ledger.set_entity(self.entity_id)
			self.cash = self.ledger.balance_sheet(['Cash'])
			print('{} Cash: {}'.format(self.name, self.cash))
			self.ledger.reset()
		elif command.lower() == 'items' or command.lower() == 'item':
			print('Use "curitems" command to see the items available at the current tech.')
			items = world.items.index.values
			print('World Items Available: {}\n{}'.format(len(items), items))
			print('\nNote: Enter an item type as a command to see a list of just those items. (i.e. Equipment)')
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{} raw data: \n{}\n'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
			self.get_raw(item.title(), 1, base=False, v=True)
			self.get_raw(item.title(), 1, base=True, v=True)
		elif command.lower() == 'curitems' or command.lower() == 'curitem':
			items = world.items.index.values
			items = [item for item in items if self.check_eligible(item)]
			items = np.array(items)
			print('World Items Currently Available: {}\n{}'.format(len(items), items))
			print('\nNote: Enter an item type as a command to see a list of just those items. (i.e. Equipment)')
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{} raw data: \n{}\n'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
			self.get_raw(item.title(), 1, base=False, v=True)
			self.get_raw(item.title(), 1, base=True, v=True)
		elif command.lower() == 'itemcat':
			item_cat = input('Enter an item category to see all items of that type: ')
			item_cat = item_cat.title()
			item_list = world.items.loc[world.items['child_of'] == item_cat]
			print(item_list.index.values)
		elif command.lower() == 'curitemcat':
			item_cat = input('Enter an item category to see all items of that type that are currently available: ')
			item_cat = item_cat.title()
			item_list = world.items.loc[world.items['child_of'] == item_cat]
			# items = [item for item in item_list.index.values if self.check_eligible(item, check=True)]
			items = []
			for item in item_list.index.values:
				print('item check:', item)
				incomplete, entries, time_required, max_qty_possible = self.fulfill(item, qty=1, check=True, v=False)
				if not incomplete:
					items.append(item)
			print(items)
		elif command.lower() == 'equipment':
			equip_list = world.items.loc[world.items['child_of'] == 'Equipment']
			print('Equipment Available:\n {}'.format(equip_list.index.values))
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'buildings':
			build_list = world.items.loc[world.items['child_of'] == 'Buildings']
			print('Buildings Available:\n {}'.format(build_list.index.values))
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'technology' or command.lower() == 'tech':
			tech_list = world.items.loc[world.items['child_of'] == 'Technology']
			print('Technologies Available:\n {}'.format(tech_list.index.values))
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'education' or command.lower() == 'edu':
			edu_list = world.items.loc[world.items['child_of'] == 'Education']
			print('Education Available:\n {}'.format(edu_list.index.values))
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'subscription' or command.lower() == 'sub':
			sub_list = world.items.loc[world.items['child_of'] == 'Subscription']
			print('Subscriptions Available:\n {}'.format(sub_list.index.values))
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'service':
			serv_list = world.items.loc[world.items['child_of'] == 'Service']
			print('Services Available:\n {}'.format(serv_list.index.values))
			while True:
				item = input('\nEnter an item to see all of its properties (enter to exit): ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'needs' or command.lower() == 'need' or command.lower() == 'n':
			print('\nNeeds are max when 100 and tick down by 1 each day. If any need reaches 0 then the individual dies.')
			print('{} Needs:'.format(self.name))
			for need in world.global_needs:
				print('{}: {}'.format(need, self.needs[need]['Current Need']))
			while True:
				need = input('\nEnter a need to see all the items that satisfy it (enter to exit): ')
				if need == '':
					return
				if world.valid_need(need):
					break
				else:
					print('Not a valid entry.')
					continue
			need_items = world.items[world.items['satisfies'].str.contains(need.title(), na=False)].index.values
			print('Items that satisfy {}: \n{}'.format(need.title(), need_items))
		elif command.lower() == 'productivity' or command.lower() == 'productive':
			productivity_items = []
			for _, item_efficiencies in world.items['productivity'].items():#.iteritems():
				if item_efficiencies is None:
					continue
				item_productivities = [x.strip() for x in item_efficiencies.split(',')]
				productivity_items += item_productivities
			productivity_items = list(collections.OrderedDict.fromkeys(productivity_items))
			print('Requirements that can be made more productive: \n{}'.format(productivity_items))
			while True:
				item = input('\nEnter an item from above to see which other items make it more efficient: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
				if item in productivity_items:
					break
				else:
					print('Not a item in the productivity items list.')
					continue
			productive_items = world.items[world.items['productivity'].str.contains(item.title(), na=False)].index.values
			print('Items that can make {} more productive: \n{}'.format(item, productive_items))
		elif command.lower() == 'otherhire':
			if isinstance(self, Individual):
				self.other_hire = not self.other_hire
				print('{} other_hire set to: {}'.format(self.name, self.other_hire))
			else:
				print('The "otherhire" command is only for Individuals.')
		elif command.lower() == 'delayinput':
			orig_delay = args.delay
			delay = 0
			while True:
				try:
					delay = input('Enter amount of sec to delay econ sim loop by: ')
					if delay == '':
						return
					delay = int(delay)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if delay <= 0:
						continue
					break
			args.delay = delay
			print(f'Loop delay changed from {orig_delay} to {args.delay}')
		elif command.lower() == 'help':
			command_help = {
				'select': 'Choose a different entity (Individual or Corporation).',
				'needs': 'List all needs and items that satisfy those needs.',
				'items': 'List of all items in the sim.',
				'curitems': 'List of all items available for the current tech.',
				'itemcat': 'List all items of a specified category.',
				'curitemcat': 'List all items available of a specified category.',
				'raw': 'Total raw resources needed to produce an item.',
				'rawbase': 'Total base raw resources needed to produce an item.',
				'productivity': 'List all requirements that can be made more efficient.',
				'hours': 'See hours available for each entity.',
				'own': 'See items owned for selected entity.',
				'land': 'See land available to claim.',
				'map': 'See all land in existence.',
				'claim': 'Claim land for free, but it must be defended and takes time.',
				# '\033[4mp\033[0mroduce': 'Produce items.',
				'produce': 'Produce items.',
				'consume': 'Consume items.',
				'autoproduce': 'Produce items automatically.',
				'stopautoproduce': 'Stop producing items automatically.',
				'purchase': 'Purchase items.',
				'sale': 'Put item up for sale.',
				'use': 'Use an item.',
				'hire': 'Hire a part-time or full-time worker.',
				'study': 'Study education and skills as an Individual to improve.',
				'address': 'Automatically address needs with items on hand.',
				'equip': 'Equip an item to attack with it or use it.',
				'unequip': 'Unequip an item that was previously equipped.',
				'attack': 'Attack another Individual or item with an item.',
				'birth': 'Have a child with another Individual.',
				'auto': 'See the auto production queue table.',
				'skip': 'Skip an entities turn even if they have hours left.',
				'accthelp': 'View commands for the accounting system.',
				'more': 'View additional advanced commands.',
				'exit': 'Exit out of the sim.'
			}
			cmd_table = pd.DataFrame(command_help.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
			# for k, v in command_help.items():
			# 	print('{}: {}'.format(k, v))
		elif command.lower() == 'more':
			# TODO Add command and function to put items up for sale
			command_more = {
				'rproduce': 'Produce items, this will also attempt to aquire any required items.',
				'mautoproduce': 'Produce items automatically but not recursively.',
				'autoaddress': 'Automatically address needs with items on hand at the end of each turn.',
				'wip': 'Attempt to complete any items in WIP.',
				'demand': 'See the demand table.',
				'incorp': 'Incorporate a company to produce items.',
				'raisecap': 'Sell additional shares in the Corporation.',
				'dividend': 'Declare dividends for a Corporation.',
				'otherhire': 'Toggle setting to allow Individual to be hired by others.',
				'world': 'See all land owned by the Environment.',
				'gift': 'Gift cash or items between entities.',
				'deposit': 'Deposit cash with the bank.',
				'withdraw': 'Withdraw cash from the bank.',
				'loan': 'Borrow cash from the bank.',
				'repay': 'Repay cash borrowed from the bank.',
				'bankruptcy': 'Declare bankruptcy with the bank.',
				'adjrate': 'Adjust central bank interest rate.',
				'setprice': 'Set the price of items.',
				'emance': 'Emancipation from parents to be treated like a founder.',
				'changegov': 'Change which Government entity is subject to.',
				'foundgov': 'Found a new Government.',
				'players': 'Display all the entities and whether they are human or computer controlled.',
				'user': 'Toggle selected entity between user or computer control.',
				'seppuku': 'Kill the currently selected entity.',
				'addplayer': 'Add a new human player under the selected government.',
				'addai': 'Add a new AI player under the selected government.',
				'superselect': 'Select any entity, including computer users.',
				'edititem': 'Edit the items date from within the sim.',
				'acctmore': 'View more commands for the accounting system.',
				'setwin': 'Set the win conditions.',
				'win': 'See the win conditions.',
				'save': 'Save the current state.',
				'end': 'End the day even if multiple entities have hours left.',
				'exit': 'Exit out of the sim.'
			}
			cmd_table = pd.DataFrame(command_more.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
		elif command.lower() == 'autodone':
			self.auto_done = not self.auto_done
			print('Auto Done set to:', self.auto_done)
		elif command.lower() == 'save':
			world.checkpoint_entry(eod=False, save=True)
		elif command.lower() == 'skip' or command.lower() == 'done':
			if self.auto_address:
				self.address_needs(obtain=False, v=False)
			if isinstance(self, Individual):
				self.set_hours(MAX_HOURS)
			user_entities = self.get_children(founder=True)
			if user_entities:
				user_entities = [e for e in user_entities if e.hours != 0]
				if user_entities:
					world.selection = user_entities[0]
				else:
					world.selection = None
			else:
				world.selection = None
			world.checkpoint_entry(eod=False)
			self.saved = False
		elif command.lower() == 'superend': #'end'
			# world.end = True
			return 'end'
		elif command.lower() == 'exit':
			exit()
		# else:
		# 	print('"{}" is not a valid command. Type "exit" to close or "help" for more options.'.format(command))
		else:
			acct.main(conn=self.ledger.conn, command=command, external=True)
			if command == 'additem' or command == 'removeitem':
				world.items = self.accts.get_items()
				global_needs_tmp = world.global_needs
				print('global_needs_tmp:', global_needs_tmp)
				world.global_needs = world.create_needs()
				print('world.global_needs:', world.global_needs)
				if world.global_needs is not global_needs_tmp:
					for individual in self.factory.get(Individual):
						individual.setup_needs()
				if args.jones:
					# TODO Maybe turn this into a function
					# Get list of businesses from items data
					new_businesses = []
					for index, producers in world.items['producer'].items():#.iteritems():
						if producers is not None:
							if isinstance(producers, str):
								producers = [x.strip() for x in producers.split(',')]
							new_businesses += producers
					new_businesses = list(collections.OrderedDict.fromkeys(filter(None, new_businesses)))
					if 'Individual' in new_businesses:
						new_businesses.remove('Individual')
					if 'Bank' in new_businesses:
						new_businesses.remove('Bank')
					new_businesses = [x for x in new_businesses if x not in world.businesses]
					for business in new_businesses:
						new_business = world.gov.incorporate(name=business)
						# TODO Spawn newly added items for existing businesses
						new_business.maintain_inv()
		if external:
			# break
			return 'end'


class Individual(Entity):
	def __init__(self, name, items, needs, government, founder, hours=12, current_need=None, parents=(None, None), user=None, entity_id=None):# Individual(Entity)
		super().__init__(name) # TODO Is this needed?
		if isinstance(parents, str):
			parents = parents.replace('(', '').replace(')', '')
			parents = tuple(None if x.strip() == 'None' else int(x.strip()) for x in parents.split(','))
		# print('Parents Start: {}'.format(parents))

		max_need = []
		decay_rate = []
		threshold = []
		for i in enumerate(needs):
			max_need.append(100)
			decay_rate.append(1)
			threshold.append(100)
		if current_need is None:
			current_need = []
			for i in enumerate(needs):
				current_need.append(100)
		max_need = ', '.join(map(str, max_need))
		decay_rate = ', '.join(map(str, decay_rate))
		threshold = ', '.join(map(str, threshold))
		if not isinstance(current_need, str):
			current_need = ', '.join(map(str, current_need))
		needs = ', '.join(needs)

		# Note: The 4th to 8th values are for another program
		entity_data = [ (name, 'CAD', 'IFRS', 0.0, 1, 100, 0.5, 'iex', self.__class__.__name__, government, founder, hours, needs, max_need, decay_rate, threshold, current_need, str(parents), user, None, None, items, None) ] # TODO Maybe add dead or active bool field
		# print('Entity Data: {}'.format(entity_data))

		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		self.government = government
		self.founder = founder
		if user is None:
			gov = self.factory.get_by_id(self.government)
			if gov is None:
				user = False
			else:
				user = gov.user
		elif user == 'True' or user == '1' or user == 1:
			user = True
		elif user == 'False' or user == '0' or user == 0:
			user = False
		self.user = user
		self.other_hire = False
		self.pin = None
		self.dead = False
		self.auto_address = False
		self.auto_wip = True
		self.auto_done = False
		self.saved = False
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		# if self.produces is not None:
		# 	self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		# else:
		# 	self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		self.parents = parents
		self.hours = hours
		print('Create Individual: {} | User: {} | entity_id: {}'.format(self.name, self.user, self.entity_id))
		print('Citizen of Government: {}'.format(self.government))
		print('Parents: {}'.format(self.parents))
		print('Current Hours:', self.hours)
		self.pregnant = None
		self.hold_event_ids = []
		self.prod_hold = []
		if args.jones:
			self.lose_time = False
		self.setup_needs(entity_data)
		for need in self.needs:
			print('{} {} need start: {}'.format(self.name, need, self.needs[need]['Current Need']))

	def __str__(self):
		return 'Indv: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Indv: {} | {}'.format(self.name, self.entity_id)

	def set_hours(self, hours_delta=0, v=False):
		if v: print(f'Set Hours Before for {self.name}: {self.hours}')
		self.hours = round(max(self.hours - hours_delta, 0), 3)
		cur = self.ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET hours = ?
			WHERE entity_id = ?;
		'''
		values = (self.hours, self.entity_id)
		cur.execute(set_need_query, values)
		self.ledger.conn.commit()
		cur.close()
		if v: print(f'Set Hours After  for {self.name}: {self.hours}')
		return self.hours

	def reset_hours(self):
		self.hours = MAX_HOURS
		if args.jones:
			if self.lose_time:
				print(f'{self.name} lost time due to not satisfying immediate needs!')
				self.hours = MAX_HOURS / 2
			self.lose_time = True
		return self.hours

	def setup_needs(self, entity_data=None):
		# self.needs = collections.defaultdict(dict)
		self.needs = collections.OrderedDict()
		if entity_data:
			needs_names = [x.strip() for x in entity_data[0][12].split(',')]
			needs_max = [x.strip() for x in str(entity_data[0][13]).split(',')]
			decay_rate = [x.strip() for x in str(entity_data[0][14]).split(',')]
			threshold = [x.strip() for x in str(entity_data[0][15]).split(',')]
			current_need = [x.strip() for x in str(entity_data[0][16]).split(',')]
		else:
			needs_names = list(world.global_needs.keys())
			needs_max = [100] * len(needs_names)
			decay_rate = [1] * len(needs_names)
			threshold = [100] * len(needs_names)
			current_need = [100] * len(needs_names)
		print('needs_names:', needs_names)
		if not needs_names or needs_names[0] == '':
			return
		for need in needs_names:
			self.needs[need] = {}
			for i in range(len(needs_names)): # TODO Fix pointless looping over all needs when not all needs are in dict
				self.needs[need]['Max Need'] = int(needs_max[i])
				self.needs[need]['Decay Rate'] = int(decay_rate[i])
				self.needs[need]['Threshold'] = int(threshold[i])
				self.needs[need]['Current Need'] = int(float(current_need[i]))
		# print(self.needs)
		return self.needs

	def set_need(self, need, need_delta, forced=False, attacked=False, seppuku=False, v=False):
		if v: print('{} sets need {} down by {}'.format(self.name, need, need_delta))
		if self not in self.factory.registry[Individual]:
			print('{} is already deceased.'.format(self.name))
			return
		self.needs[need]['Current Need'] += need_delta
		if self.needs[need]['Current Need'] < 0:
			self.needs[need]['Current Need'] = 0
		current_need_all = world.entities.loc[world.entities['entity_id'] == self.entity_id, 'current_need'].values[0]
		# if v: print('Current Need Start: {}'.format(current_need_all))
		current_need_all = [x.strip() for x in str(current_need_all).split(',')]
		# if v: print('Current Needs: {}'.format(current_need_all))
		for i, need_spot in enumerate(self.needs):
			# if v: print('Need Spot: {} | {}'.format(i, need_spot))
			if need == need_spot:
				break
		current_need_all[i] = self.needs[need]['Current Need']
		current_need_all = ', '.join(str(x) for x in current_need_all)
		# if v: print('Current Need All After: {}'.format(current_need_all))
		cur = self.ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET current_need = ?
			WHERE entity_id = ?;
		'''
		values = (current_need_all, self.entity_id)
		cur.execute(set_need_query, values)
		self.ledger.conn.commit()
		cur.close()
		if self.needs[need]['Current Need'] <= 0:
			self.reset_hours()
			self.inheritance(bequeath=not seppuku)
			self.factory.destroy(self)
			if forced:
				print('{} died due to natural causes.'.format(self.name))
			elif attacked:
				print('{} died due to attack.'.format(self.name))
			elif seppuku:
				print('{} died from seppuku.'.format(self.name))
			else:
				print('{} died due to {}.'.format(self.name, need))
			self.dead = True
		world.entities = self.accts.get_entities().reset_index()
		return self.needs[need]['Current Need']

	def birth_check(self):
		if self.pregnant:
			self.pregnant -= 1
			self.set_hours(MAX_HOURS)
			print(f'{self.name} gave birth or was born recently and has used up all their time ({self.hours}) for the day with {self.pregnant} days left.\n')
		if self.pregnant == 0:
			self.pregnant = None
		return self.pregnant

	def birth(self, counterparty=None, amount_1=None, amount_2=None):
		if self.dead:
			print(f'{self.name} is dead and cannot give birth.')
			return
		# if self.hours == 0:
		# 	print(f'{self.name} has no hours left and cannot give birth.')
		# 	return
		if self.pregnant is not None:
			print(f'{self.name} is pregnant already and cannot give birth.')
			return
		if args.max_pop is not None:
			population = len(self.factory.registry[Individual])
			if population >= args.max_pop:
				print(f'{self.name} cannot give birth because the population is at {population} and the max population is {args.max_pop}.')
				return
		if amount_1 is None and amount_2 is None:
			amount_1 = INIT_CAPITAL / 2
			amount_2 = INIT_CAPITAL / 2
		entities = self.accts.get_entities()
		if counterparty is None:
			individuals = self.factory.get(Individual, users=False)
			individuals = [individual for individual in individuals if individual != self]
			# print('Individuals for birth: {}'.format(individuals))
			if not individuals:
				print('No one else is left to have a child with {}.'.format(self.name))
				print('{} clones themselves.'.format(self.name))
				counterparty = self
			else:
				counterparty = individuals[-1]
		elif not isinstance(counterparty, Individual):
			print('{} can only give birth with Individuals and {} is a {}.'.format(self.name, counterparty.name, type(counterparty).__name__))
			return
		# TODO Use get relatives function to check if counterparty is external, if so cannot get cash from them or maybe use them
		gift_event = []
		self.ledger.set_entity(self.entity_id)
		cash1 = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		if amount_1 is None:
			amount_1 = 0
		if cash1 >= amount_1:
			gift_entry1 = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Gift cash to child', '', '', '', 'Gift Expense', 'Cash', amount_1 ] # TODO Get proper cp_id
		else:
			print('{} does not have ${} in cash to give birth with {}.'.format(self.name, amount_1, counterparty.name))
			return
		self.ledger.set_entity(counterparty.entity_id)
		cash2 = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		if amount_2 is None:
			amount_2 = 0
		if cash2 >= amount_2:
			gift_entry2 = [ self.ledger.get_event(), counterparty.entity_id, '', world.now, '', 'Gift cash to child', '', '', '', 'Gift Expense', 'Cash', amount_2 ] # TODO Get proper cp_id
		else:
			print('{} does not have ${} in cash to have child with {}.'.format(counterparty.name, amount_2, self.name))
			return
			# TODO Support looping through counterparties if first does not have enough cash
		gift_event += [gift_entry1, gift_entry2]

		self.indiv_items_produced = list(world.items[world.items['producer'].str.contains('Individual', na=False)].index.values) # TODO Move to own function
		self.indiv_items_produced = ', '.join(self.indiv_items_produced)
		#print('Individual Production: {}'.format(self.indiv_items_produced))
		last_entity_id = entities.reset_index()['entity_id'].max() # TODO Maybe a better way of doing this
		#print('Last Entity ID: {}'.format(last_entity_id))
		self.factory.create(Individual, 'Person-' + str(last_entity_id + 1), self.indiv_items_produced, world.global_needs, self.government, founder=self.entity_id, parents=(self.entity_id, counterparty.entity_id), user=self.user)
		individual = self.factory.get_by_id(last_entity_id + 1)
		# world.prices = pd.concat([world.prices, individual.prices])
		if self.user and USE_PIN:
			while True:
				try:
					pin = getpass.getpass('{} enter a 4 digit pin number or enter "exit": '.format(individual.name))
					if pin.lower() == 'exit':
						exit()
					pin = int(pin)
				except ValueError:
					print('Not a valid entry. Must be a 4 digit number.')
					continue
				else:
					if len(str(pin)) != 4 or int(pin) < 0:
						print('Not a valid entry. Must be a 4 digit number.')
						continue
					break
			individual.pin = pin
		world.set_table(world.prices, 'prices')

		gift_event += individual.capitalize(amount=amount_1 + amount_2, buffer=True)
		individual.hours = 0
		print('\nPerson-' + str(last_entity_id + 1) + ' is born!')
		self.ledger.journal_entry(gift_event)
		self.pregnant = GESTATION
		individual.pregnant = GESTATION + 1
		return individual

	def emancipation(self, parents=(None, None), v=True):
		orig_parents = self.parents
		self.parents = parents
		cur = self.ledger.conn.cursor()
		set_parents_query = '''
			UPDATE entities
			SET parents = ?
			WHERE entity_id = ?;
		'''
		values = (str(self.parents), self.entity_id)
		cur.execute(set_parents_query, values)
		self.ledger.conn.commit()
		cur.close()
		if v: print('{} set parents to be {} from {}. User status: {}'.format(self.name, self.parents, orig_parents, self.user))
		return self.parents

	def inheritance(self, counterparty=None, bequeath=True):
		# Remove any items that exist on the demand table for this entity
		demand_items = world.demand[world.demand['entity_id'] == self.entity_id]
		if not demand_items.empty:
			to_drop = demand_items.index.tolist()
			world.demand = world.demand.drop(to_drop).reset_index(drop=True)
			world.set_table(world.demand, 'demand')
			print('{} removed {} indexes for items from demand list.\n'.format(self.name, to_drop))
			with pd.option_context('display.max_rows', None):
				print('World Demand: {} \n{}'.format(world.now, world.demand))

		# Quit any current jobs
		self.ledger.set_entity(self.entity_id)
		current_jobs = self.ledger.get_qty(accounts=['Start Job', 'Quit Job'])
		self.ledger.reset()
		print('Jobs at death: \n{}'.format(current_jobs)) # 1986-11-29
		current_jobs = current_jobs.groupby(['item_id']).sum().reset_index() # TODO Use credit=True in get_qty() and 'Worker Info' account
		# print('Grouped Jobs at death: \n{}'.format(current_jobs))
		for index, job in current_jobs.iterrows():
			item = job['item_id']
			worker_state = job['qty']
			if worker_state >= 1: # Should never be greater than 1 for the same counterparty
				worker_state = int(worker_state)
				self.ledger.set_entity(self.entity_id)
				rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				hire_txns = self.ledger.gl[( (self.ledger.gl['debit_acct'] == 'Start Job') & (self.ledger.gl['credit_acct'] == 'Worker Info') ) & (self.ledger.gl['item_id'] == item) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
				self.ledger.reset()
				cp_job, event_id = self.get_counterparty(hire_txns, rvsl_txns, item, 'Worker Info')
				for _ in range(worker_state): # TODO This for loop shouldn't be necessary
					self.fire_worker(item, cp_job, quit=True)

		# Cancel any current subscriptions
		self.ledger.set_entity(self.entity_id)
		current_subs = self.ledger.get_qty(accounts=['Subscription Info'])
		self.ledger.reset()
		for index, sub in current_subs.iterrows():
			item = sub['item_id']
			sub_state = sub['qty']
			if sub_state >= 1:
				sub_state = int(sub_state)
				self.ledger.set_entity(self.entity_id)
				rvsl_txns = self.ledger.gl[self.ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				sub_txns = self.ledger.gl[( (self.ledger.gl['debit_acct'] == 'Subscription Info') & (self.ledger.gl['credit_acct'] == 'Order Subscription') ) & (self.ledger.gl['item_id'] == item) & (~self.ledger.gl['event_id'].isin(rvsl_txns))]
				self.ledger.reset()
				cp_sub, event_id = self.get_counterparty(sub_txns, rvsl_txns, item, 'Sell Subscription')
				for _ in range(sub_state):
					self.cancel_subscription(item, cp_sub)
		
		world.prices = world.prices.loc[world.prices['entity_id'] != self.entity_id]
		print('{} removed their prices for items from the price list.\n'.format(self.name))

		if not bequeath:
			return
		# Get the counterparty to inherit to
		if counterparty is None:
			counterparty = self.factory.get_by_id(self.parents[0])
			if counterparty not in self.factory.registry[Individual]:
				counterparty = None
			#print('First Parent: {}'.format(counterparty))
		if counterparty is None:
			individuals = itertools.cycle(world.gov.get(Individual))
			nextindv = next(individuals) # Prime the pump
			while True:
				individual, nextindv = nextindv, next(individuals)
				# print('Individual: {}'.format(individual.name))
				# print('Next Individual: {}'.format(nextindv.name))
				if individual.entity_id == self.entity_id:
					counterparty = nextindv
					break
		print('Inheritance bequeathed from {} to {}'.format(self.name, counterparty.name))

		self.ledger.set_entity(self.entity_id)
		# Remove all job and subscription info entries
		consolidated_gl = self.ledger.gl
		consolidated_gl = consolidated_gl.loc[self.ledger.gl['credit_acct'] != 'Worker Info']
		consolidated_gl = consolidated_gl.loc[self.ledger.gl['debit_acct'] != 'Subscription Info']
		consolidated_gl.fillna(0, inplace=True)
		consolidated_gl = consolidated_gl.drop(['date', 'post_date'], axis=1)
		# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		# 	print(f'consolidated_gl: {consolidated_gl}')
		consolidated_gl = consolidated_gl.groupby(['item_id','debit_acct','credit_acct']).sum()
		self.ledger.reset()
		inherit_event = []
		for index, entry in consolidated_gl.iterrows():
			# print('Index: \n{}'.format(index))
			# print('Entry: \n{}'.format(entry))
			bequeath_entry = [ self.ledger.get_event(), self.entity_id, counterparty.entity_id, world.now, '', 'Bequeath to ' + counterparty.name, index[0], entry[5], entry[6], index[2], index[1], entry[7] ]
			inherit_entry = [ self.ledger.get_event(), counterparty.entity_id, self.entity_id, world.now, '', 'Inheritance from ' + self.name, index[0], entry[5], entry[6], index[1], index[2], entry[7] ]
			inherit_event += [bequeath_entry, inherit_entry]
		self.ledger.journal_entry(inherit_event)

	def get_children(self, founder=False, ids=False, v=False):
		# TODO Replace this function with a self.founder check
		if founder:
			founder_id = self.get_founder()
			entity = self.factory.get_by_id(founder_id)
		else:
			entity = self
		children = []
		to_check = self.factory.get(Individual, ids=True)
		children = entity.check_parent(to_check, children, v=v)
		# if len(children) == 2: # TODO Not needed
		# 	children = children[0] + children[1]
		if v: print('Children Before: {}'.format(children))
		children = list(collections.OrderedDict.fromkeys(filter(None, children))) # Remove dupes
		if not ids:
			children = [self.factory.get_by_id(entity_id) for entity_id in children]
		return children

	def check_parent(self, to_check, children, parent=None, lineage=None, v=False):
		if v: print('To Check Start: {}'.format(to_check))
		if v: print('Children Start: {}'.format(children))
		if lineage is None:
			lineage = []
		else:
			if v: print('Lineage: {}'.format(lineage))
		if not to_check:
			return children
		if parent:
			entity_id = parent
			if v: print('Parent: {}'.format(entity_id))
		else:
			entity_id = to_check[0]
		if v: print('Checking: {}'.format(entity_id))
		if isinstance(entity_id, int):
			entity = self.factory.get_by_id(entity_id)
		if v: print('Parents: {}'.format(entity.parents))
		if entity.parents[0] is None and entity.parents[1] is None:
			if v: print('Case 1')
			if self.entity_id == entity.entity_id:
				if v: print('Case 1.1')
				children.append(entity.entity_id)
				if lineage:
					children += lineage
			if lineage:
				to_check = [x for x in to_check if x not in lineage]
			if not parent:
				to_check.remove(entity.entity_id)
			if v: print('To Check: {}'.format(to_check))
			if v: print('Children: {}'.format(children))
			return self.check_parent(to_check, children, v=v)
		elif entity.parents[0] == entity_id or entity.parents[1] == entity_id:
			if v: print('Case 2')
			children.append(entity.entity_id)
			to_check.remove(entity.entity_id)
			if lineage:
				if v: print('Case 2.1')
				children += lineage
				to_check = [x for x in to_check if x not in lineage]
			if v: print('To Check: {}'.format(to_check))
			if v: print('Children: {}'.format(children))
			return self.check_parent(to_check, children, v=v)
		else:
			if v: print('Case 3')
			lineage.append(entity.entity_id)
			if v: print('To Check: {}'.format(to_check))
			if v: print('Children: {}'.format(children))
			return self.check_parent(to_check, children, entity.parents[0], lineage, v=v)#, self.check_parent(to_check, children, entity.parents[1], lineage, v=v)

	def get_founder(self, entity_id=None):
		if entity_id is None:
			entity_id = self.entity_id
		if isinstance(entity_id, int):
			entity = self.factory.get_by_id(entity_id)
		else:
			entity = entity_id
		if entity.parents[0] is None and entity.parents[1] is None:
			return entity.entity_id
		else:
			return entity.get_founder(entity.parents[0])
			#, entity.get_founder(entity.parents[1])

	def change_allegiance(self, gov_id):
		# TODO Change allegiance of all children and companies owned also
		orig_gov = self.factory.get_by_id(self.government)
		gov = self.factory.get_by_id(gov_id)
		if not isinstance(gov, Government):
			print(f'{gov.name} is not a Government. It is a {gov.__class__.__name__}.')
			return
		cur = self.ledger.conn.cursor()
		set_parents_query = '''
			UPDATE entities
			SET government = ?
			WHERE entity_id = ?;
		'''
		values = (str(gov_id), self.entity_id)
		cur.execute(set_parents_query, values)
		self.ledger.conn.commit()
		cur.close()
		print(f'{self.name} switch allegiance from {orig_gov.name} to {gov.name}')
		return gov

	def found_gov(self):
		print('current gov:', self.government)
		self.emancipation()
		world.entities = self.accts.get_entities()
		last_entity_id = world.entities.reset_index()['entity_id'].max()
		gov_id = last_entity_id + 1
		self.factory.create(Government, 'Government-' + str(gov_id), items=None, user=self.user)
		self.change_allegiance(gov_id)
		return gov_id

	def seppuku(self, v=True):
		for need in self.needs:
			self.set_need(need, -100, seppuku=True)
			break
		if v: print(f'{self.name} has performed seppuku.')
		return self

	def add_person(self, name=None, user=True):
		if name is None:
			name = 'Person'
		entities = self.accts.get_entities()
		indiv_items_produced = list(world.items[world.items['producer'].str.contains('Individual', na=False)].index.values) # TODO Move to own function
		indiv_items_produced = ', '.join(indiv_items_produced)
		last_entity_id = entities.reset_index()['entity_id'].max() # TODO Maybe a better way of doing this
		self.factory.create(Individual, name + '-' + str(last_entity_id + 1), indiv_items_produced, world.global_needs, world.gov.entity_id, founder=last_entity_id + 1, parents=(None, None), user=user)
		new_indiv = self.factory.get_by_id(last_entity_id + 1)
		start_capital = args.capital / args.population
		world.gov.bank.print_money(start_capital)
		new_indiv.loan(amount=start_capital, roundup=False)
		if user:
			print(f'New human player added as: {new_indiv.name}')
		else:
			print(f'New AI player added as: {new_indiv.name}')
		return new_indiv

	def needs_decay(self, decay_rate=1):
		priority_needs = {}
		for need in self.needs:
			priority_needs[need] = self.needs[need]['Current Need']
		priority_needs = {k: v for k, v in sorted(priority_needs.items(), key=lambda item: item[1])}
		priority_needs = collections.OrderedDict(priority_needs)
		for need in priority_needs:
			self.need_decay(need, decay_rate=decay_rate)

	def need_decay(self, need, decay_rate=1):
		rand = 1
		# if args.random:
		# 	rand = random.randint(1, 3)
		decay_rate = self.needs[need]['Decay Rate'] * -1 * rand
		current_need = max(self.needs[need]['Current Need'] + decay_rate, 0)
		print(f'{self.name} {need} need decayed by {decay_rate} to: {current_need}')
		self.set_need(need, decay_rate)
		return decay_rate

	def threshold_check(self, need, threshold=100, priority=False):
		# TODO No longer needed
		threshold = self.needs[need]['Threshold']
		if self.needs[need]['Current Need'] < threshold:
			print('\n{} {} need threshold met at: {}'.format(self.name, need, self.needs[need]['Current Need']))
			self.address_need(need, priority=priority)

	def address_needs(self, obtain=True, prod=False, priority=False, method=None, v=True):
		if v: print(f'address_needs method: {method} | obtain: {obtain} | prod: {prod} | priority: {priority}')
		priority_needs = {}
		for need in self.needs:
			if method is not None:
				if world.global_needs[need] != method:
					continue
			priority_needs[need] = self.needs[need]['Current Need']
		priority_needs = {k: v for k, v in sorted(priority_needs.items(), key=lambda item: item[1])}#, reverse=priority)}
		priority_needs = collections.OrderedDict(priority_needs)
		if priority:
			priority_needs = reversed(priority_needs)
		for need in priority_needs:
			self.address_need(need, obtain=obtain, prod=prod, priority=priority, v=v)

	def address_need(self, need, obtain=True, prod=False, priority=False, v=True):
		if need is None:
			return
		outcome = None
		items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs

		need_satisfy_rate = []
		for index, item_row in items_info.iterrows():
			needs = [x.strip() for x in item_row['satisfies'].split(',')]
			for i, need_item in enumerate(needs):
				if need_item == need:
					break
			satisfy_rates = [x.strip() for x in item_row['satisfy_rate'].split(',')]
			satisfy_rate = float(satisfy_rates[i])
			need_satisfy_rate.append(satisfy_rate)
		need_satisfy_rate = pd.Series(need_satisfy_rate)
		#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
		items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)
		# Add price column and use min price of all entities for now
		item_prices = []
		for item, _ in items_info.iterrows():
			min_price = world.prices.loc[world.prices.index == item].min()['price']
			if pd.isna(min_price):
				raw_mats = self.get_raw(item, base=True)
				min_price = raw_mats.iloc[-1]['qty'] * INIT_PRICE
				# min_price = INIT_PRICE # TODO Old method
			if v: print(f'Address {need} with {item} for min price of: {min_price}')
			item_prices.append(min_price)
		item_prices = pd.Series(item_prices)
		items_info = items_info.assign(price=item_prices.values)
		price_rate = items_info['price'] / items_info['need_satisfy_rate']
		items_info = items_info.assign(price_rate=price_rate.values)
		items_info = items_info.sort_values(by='price_rate', ascending=True)
		# print('Items Info: \n{}'.format(items_info))
		# items_info = items_info.sort_values(by='need_satisfy_rate', ascending=False) # Old method of sorting
		items_info.reset_index(inplace=True)
		# If first item is not available, try the next one
		for index, item in items_info.iterrows():
			item_choosen = items_info['item_id'].iloc[index]
			# print(f'{need} item_choosen: {item_choosen}')
			if not self.check_eligible(item_choosen):
				continue
			# TODO Support multiple satisfies
			satisfy_rate = float(items_info['need_satisfy_rate'].iloc[index])
			#print('Item Choosen: {}'.format(item_choosen))
			item_type = world.get_item_type(item_choosen)
			#print('Item Type: {}'.format(item_type))
			if item_type != 'Commodity' and item_type != 'Components' and obtain:
				if v: print('\nSatisfy {} need for {} by purchasing: {}'.format(need, self.name, item_choosen))

			if item_type == 'Subscription':
				self.ledger.set_entity(self.entity_id)
				subscription_state = self.ledger.get_qty(items=item_choosen, accounts=['Subscription Info'])
				self.ledger.reset()
				if subscription_state:
					self.needs[need]['Current Need'] = self.needs[need]['Max Need']
					if v: print('{} need satisfied with {} and set to max value.'.format(need, item_choosen))
				else:
					# counterparty = self.subscription_counterparty(item_choosen) # TODO Move this into order_subscription()
					# if counterparty is None:
					# 	self.item_demanded(item_choosen, 1)
					# 	continue
					if obtain:
						outcome = self.order_subscription(item_choosen, priority=priority, reason_need=True, v=v)#, counterparty=counterparty)#, price=world.get_price(item_choosen, counterparty.entity_id))
				# qty_purchase = 1 # TODO Remove as was needed for demand call below
				break

			elif item_type == 'Buildings': # TODO Test this with examples
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				self.ledger.set_entity(self.entity_id)
				qty_held = self.ledger.get_qty(items=item_choosen, accounts=['Buildings'])
				qty_in_use = self.ledger.get_qty(items=item_choosen, accounts=['Buildings In Use'])
				self.ledger.reset()
				qty_owned = qty_held + qty_in_use
				event = []
				if qty_owned == 0 and obtain:
					outcome = self.purchase(item_choosen, qty=1, priority=priority, reason_need=True, v=v)#, acct_buy='Equipment') # TODO Support buildings by sqft units
				if qty_owned:
					if (qty_held > 0 and qty_in_use == 0) or outcome:
						entries = self.in_use(item_choosen, buffer=True)
					if not entries:
						entries = []
					if entries is True:
						entries = []
					if entries:
						self.needs[need]['Current Need'] = self.needs[need]['Max Need']
					event += entries
					self.ledger.journal_entry(event)
					return event
				break

			elif item_type == 'Service':
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_purchase = int(math.ceil(need_needed / satisfy_rate))
				#print('QTY Needed: {}'.format(qty_needed))
				if obtain:
					outcome = self.purchase(item_choosen, qty_purchase, priority=priority, reason_need=True, v=v)
				else:
					if v: print(f'Produce or purchase {qty_purchase} {item_choosen} service to satisfy {need_needed} {need} need.')
				break

			elif (item_type == 'Commodity') or (item_type == 'Component'):
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_needed = int(math.ceil(need_needed / satisfy_rate))
				#print('QTY Needed: {}'.format(qty_needed))
				self.ledger.set_entity(self.entity_id)
				qty_held = self.ledger.get_qty(items=item_choosen, accounts=['Inventory'])
				self.ledger.reset()
				if v: print(f'{self.name} has {qty_held} {item_choosen} out of {qty_needed} qty needed to address {need_needed} {need} need.')
				# TODO Check all valid items if they are onhand and attempt to use consume before aquiring some
				if qty_held < qty_needed and obtain:
					qty_wanted = qty_needed - qty_held
					# TODO Is the below needed?
					qty_avail = self.ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					if qty_avail == 0:
						qty_avail = qty_wanted # Prevent purchase for 0 qty
					qty_purchase = min(qty_wanted, qty_avail)
					# TODO Is the above needed?
					if v: print(f'\nSatisfy {need} need for {self.name} by purchasing: {qty_purchase} {item_choosen}')
					outcome = self.purchase(item_choosen, qty_purchase, priority=priority, reason_need=True, v=v)
					self.ledger.set_entity(self.entity_id)
					qty_held = self.ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					self.ledger.reset()
					#print('QTY Held: {}'.format(qty_held))
					if prod and qty_held < qty_wanted:
						outcome, time_required, max_qty_possible, incomplete = self.produce(item_choosen, qty_wanted - qty_held)
						if not outcome:
							if (qty_wanted - qty_held) != 1:
								if v: print(f'Trying to address {need} need again for 1 qty of {item_choosen}.')
								outcome, time_required, max_qty_possible, incomplete = self.produce(item_choosen, qty=1, v=v)
						self.ledger.set_entity(self.entity_id)
						qty_held = self.ledger.get_qty(items=item_choosen, accounts=['Inventory'])
						self.ledger.reset()
						#print('QTY Held: {}'.format(qty_held))
				if qty_held:
					result = self.consume(item_choosen, min(qty_needed, qty_held), need)
					if args.jones:
						if result:
							self.lose_time = False
				break

			elif item_type == 'Equipment':
				# TODO Decide how qty will work with time spent using item
				self.ledger.set_entity(self.entity_id)
				qty_held = self.ledger.get_qty(items=item_choosen, accounts=['Equipment'])
				self.ledger.reset()
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				uses_needed = int(math.ceil(need_needed / satisfy_rate))
				if v: print(f'{self.name} has {qty_held} {item_choosen} to use {uses_needed} times to address {need_needed} {need} need.')
				event = []
				if qty_held == 0 and obtain:
					qty_purchase = 1
					metrics = items_info['metric'].iloc[index]
					if isinstance(metrics, str):
						metrics = [x.strip() for x in metrics.split(',')]
						metrics = list(filter(None, metrics))
					if metrics is None:
						metrics = ''
					lifespans = items_info['lifespan'].iloc[index]
					if isinstance(lifespans, str):
						lifespans = [x.strip() for x in lifespans.split(',')]
						lifespans = list(filter(None, lifespans))
					if lifespans is None:
						lifespans = ''
					for i, metric in enumerate(metrics):
						lifespan = int(lifespans[i])
						#print('{} Metric: {} | Lifespan: {}'.format(item, metric, lifespan))
						if metric == 'usage':
							qty_purchase = int(math.ceil(uses_needed / lifespan))
							break
					outcome = self.purchase(item_choosen, qty_purchase, priority=priority, reason_need=True, v=v)#, acct_buy='Equipment')
					# TODO Should update qty_held again
				if qty_held > 0 or outcome:
					entries = self.use_item(item_choosen, uses_needed, buffer=True)
					if not entries:
						entries = []
					if entries is True:
						entries = []
					event += entries
					self.ledger.journal_entry(event)
					return event
				break
			if self.needs[need]['Current Need'] == self.needs[need]['Max Need']:
				break

	def adj_needs(self, item, qty=1):
		indiv_needs = list(self.needs.keys())
		# print('Indiv Needs: \n{}'.format(indiv_needs))
		satisfies = world.items.loc[item, 'satisfies']
		satisfies = [x.strip() for x in satisfies.split(',')]
		#print('Satisfies: \n{}'.format(satisfies))
		satisfy_rates = world.items.loc[item, 'satisfy_rate']
		satisfy_rates = [x.strip() for x in satisfy_rates.split(',')]
		#print('Satisfy Rates: \n{}'.format(satisfy_rates))
		needs = list(set(indiv_needs) & set(satisfies))
		if needs is None:
			return
		for need in needs:
			for i, satisfy_need in enumerate(satisfies):
				if satisfy_need == need:
					break
			new_need = self.needs[need]['Current Need'] + (float(satisfy_rates[i]) * qty)
			if new_need < self.needs[need]['Max Need']:
				self.needs[need]['Current Need'] = new_need
			else:
				self.needs[need]['Current Need'] = self.needs[need]['Max Need']
			if args.jones:
				if world.global_needs[need] == 'consumption':
					self.lose_time = False
			print('{} {} need adjusted by: {} | Current {} Need: {}'.format(self.name, need, (float(satisfy_rates[i]) * qty), need, self.needs[need]['Current Need']))

	def is_shareholder(self, corps):
		if not isinstance(corps, (list, tuple)):
			corps = [corps]
		invested = [corp for corp in corps if corp.is_owner(self)] # TODO Try to make this a generator
		return invested

class Environment(Entity):
	def __init__(self, name, entity_id=None):# Environment(Entity)
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 'CAD', 'IFRS', None, None, None, None, None, self.__class__.__name__, None, None, None, None, None, None, None, None, None, None, None, None, None, None) ] # Note: The 2nd to 5th values are for another program
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		self.government = None
		self.user = None
		self.hold_event_ids = []
		self.produces = None
		self.saved = False
		self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Environment: {} | entity_id: {}'.format(self.name, self.entity_id))

	def __str__(self):
		return 'Env: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Env: {} | {}'.format(self.name, self.entity_id)

	def create_land(self, item, qty, date=None):
		if date is None:
			date = world.now
		price = 0 #world.get_price(item, self.entity_id)
		land_entry = [ self.ledger.get_event(), self.entity_id, '', date, '', item + ' created', item, price, qty, 'Land', 'Natural Wealth', price * qty ]
		land_event = [land_entry]
		self.ledger.journal_entry(land_event)

class Organization(Entity):
	def __init__(self, name):# Organization(Entity)
		super().__init__(name)

class Corporation(Organization):
	def __init__(self, name, items, government, founder, auth_shares=1000000, entity_id=None):# Corporation(Organization)
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 'CAD', 'IFRS', 0.0, 1, 100, 0.5, 'iex', self.__class__.__name__, government, founder, None, None, None, None, None, None, None, None, auth_shares, None, items, None) ] # Note: The 2nd to 5th values are for another program
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		self.government = government
		self.founder = founder
		self.user = None
		self.hold_event_ids = []
		self.prod_hold = []
		self.auto_wip = True
		self.auto_done = False
		self.saved = False
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Organization: {} | entity_id: {} \nProduces: {}'.format(self.name, self.entity_id, self.produces))

	def __str__(self):
		return 'Corp: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Corp: {} | {}'.format(self.name, self.entity_id)

	def list_shareholders(self, largest=False, v=True):
		self.ledger.reset()
		shareholders = self.ledger.get_qty(items=self.name, accounts='Investments', by_entity=True)
		if shareholders.empty:
			print('No shareholders listed for {}. Try again the next day.\n'.format(self.name))
			return
		# print('{} shareholders: \n{}'.format(self.name, shareholders))
		if largest:
			largest_shareholder = shareholders.loc[shareholders['qty'] == shareholders['qty'].max()]['entity_id'].values[0] # TODO Fix multiple Corporations with the same name
			# if len(largest_shareholder) >= 2:
			# 	largest_shareholder = largest_shareholder[0]
			if v: print('{} largest shareholder Entity ID: {}'.format(self.name, largest_shareholder))
			return largest_shareholder
		else:
			if v: print('{} shareholders: \n{}'.format(self.name, shareholders))
			return shareholders

	def is_owner(self, counterparty):
		shareholders = self.list_shareholders(v=False)
		shareholder_ids = shareholders['entity_id'].values
		if counterparty.entity_id in shareholder_ids:
			return True
		else:
			return False

	def is_shareholder(self, corps):
		if not isinstance(corps, (list, tuple)):
			corps = [corps]
		invested = [corp for corp in corps if corp.is_owner(self)] # TODO Try to make this a generator
		return invested

	def declare_div(self, div_rate): # TODO Move this to corporation subclass
		item = self.name
		shareholders = self.ledger.get_qty(items=item, accounts='Investments', by_entity=True)
		if shareholders.empty:
			return
		total_shares = shareholders['qty'].sum()
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		self.ledger.reset()
		#print('{} cash: {}'.format(self.name, cash))
		if cash < total_shares * div_rate:
			print('{} does not have enough cash to pay dividend at a rate of {}. Cash: {}'.format(self.name, div_rate, cash))
			return
		div_event = []
		for index, shareholder in shareholders.iterrows():
			shares = shareholder['qty']
			counterparty_id = shareholder['entity_id']
			# TODO Add div accrual entries and payments
			div_rev_entry = [ self.ledger.get_event(), counterparty_id, self.entity_id, world.now, '', 'Dividend received for ' + item, item, div_rate, shares, 'Cash', 'Dividend Income', shares * div_rate ]
			div_event += [div_rev_entry]
		# TODO This should book against Retained Earnings
		div_exp_entry = [ self.ledger.get_event(), self.entity_id, counterparty_id, world.now, '', 'Dividend payment for ' + item, item, div_rate, total_shares, 'Dividend Expense', 'Cash', total_shares * div_rate ]
		div_event += [div_exp_entry]
		self.ledger.journal_entry(div_event)

	def dividend(self, div_rate=1):
		self.ledger.set_entity(self.entity_id)
		cash = self.ledger.balance_sheet(['Cash'])
		# print('{} cash: {}'.format(self.name, cash))
		funding = self.ledger.balance_sheet(accounts=['Shares'], item=self.name)
		# print('{} funding: {}'.format(self.name, funding))
		self.ledger.reset()
		if cash >= funding * 2: # TODO Make 2 a global constant
			self.declare_div(div_rate=div_rate)

	def raise_capital(self, qty=None, price=None, investors=None):
		if price is None:
			price = 1 # TODO Fix this to get a dynamic price
		if qty is None and investors is None:
			qty = 5000 # TODO Fix temp defaults
		if investors is None:
			largest_shareholder = self.list_shareholders(largest=True)
			largest_shareholder = self.factory.get_by_id(largest_shareholder)
			investors = {largest_shareholder: qty}
		if qty is None:
			qty = sum(investors.values())
		for investor, investor_qty in investors.items():
			self.ledger.set_entity(investor.entity_id)
			investor_cash = self.ledger.balance_sheet(['Cash'])
			self.ledger.reset()
			#print('Cash: {}'.format(cash))
			if price * investor_qty > investor_cash:
				print('{} does not have enough cash to invest in {}. Cash: {} | Required: {}'.format(investor.name, investor.entity_id, name, investor_cash, price * investor_qty))
				return
		for investor, qty in investors.items():
			investor.buy_shares(self.name, price, qty, self)

	# TODO Maybe move to Entity class
	def maintain_inv(self, buffer_qty=1, v=False):
		if v: print('maintain_inv:')
		for item_id in self.produces:
			if v: print(item_id)
			if not self.check_eligible(item_id):
				continue
			qty = buffer_qty #10
			item_type = world.get_item_type(item_id)
			if v: print('item_type:', item_type)
			if item_type not in ['Commodity', 'Components', 'Equipment', 'Buildings', 'Subscription']:
				_ = world.get_price(item_id, self.entity_id)
				continue
			if item_type in ['Commodity', 'Components']:
				qty = qty * 100 #1000
			self.ledger.set_entity(self.entity_id)
			inv_qty = self.ledger.get_qty(items=item_id, accounts=['Inventory'])
			if inv_qty < qty * 0.8: # Buffer of 20%
				qty = qty - inv_qty
				if args.jones:
					self.spawn_item(item_id, qty)
				else:
					self.produce(item_id, qty, v=v)

class Government(Organization):
	def __init__(self, name, items=None, user=False, entity_id=None):# Government(Organization)
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 'CAD', 'IFRS', None, None, None, None, None, self.__class__.__name__, None, None, None, None, None, None, None, None, None, user, None, None, items, None) ] # Note: The 2nd to 5th values are for another program
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		if user == 'True' or user == '1' or user == 1:
			user = True
		elif user == 'False' or user == '0' or user == 0:
			user = False
		self.user = user
		self.government = self.entity_id
		if args.jones:
			self.founder = self.entity_id # TODO Clean up
		self.hold_event_ids = []
		self.auto_wip = True
		self.auto_done = False
		self.saved = False
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Government: {} | User: {} | entity_id: {}'.format(self.name, self.user, self.entity_id))
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			self.bank = self.create_bank()

	def get(self, typ=None, users=True, computers=True, ids=False, envs=True):
		entities = []
		if envs:
			entities = [entity for entity in self.factory.get(typ) if (entity.government == self.entity_id) or (entity.government is None)]
		else:
			entities = [entity for entity in self.factory.get(typ) if entity.government == self.entity_id]
		if not computers:
			entities = [entity for entity in entities if entity.user]
		if not users:
			entities = [entity for entity in entities if not entity.user]
		if ids:
			entities = [e.entity_id for e in entities]
		return entities

	def is_shareholder(self, corps):
		if not isinstance(corps, (list, tuple)):
			corps = [corps]
		invested = [corp for corp in corps if corp.is_owner(self)] # TODO Try to make this a generator
		return invested

	def create_bank(self):#, bank_items_produced=None):
		# if bank_items_produced is None:
		# 	bank_items_produced = world.items[world.items['producer'].str.contains('Individual', na=False)].reset_index()
		# 	bank_items_produced = bank_items_produced['item_id'].tolist()
		# 	bank_items_produced = ', '.join(bank_items_produced)
		# world.entities = self.accts.get_entities()
		last_entity_id = self.accts.get_entities().reset_index()['entity_id'].max()
		# print('last_entity_id: {}'.format(last_entity_id))
		bank = self.factory.create(Bank, 'Bank-' + str(last_entity_id + 1), government=self.entity_id)#, items=bank_items_produced)
		return bank

	def __str__(self):
		return 'Gov: {} | {}'.format(self.name, self.entity_id)

	# def __repr__(self):
	# 	return 'Gov: {} | {}'.format(self.name, self.entity_id)

class Governmental(Organization):
	def __init__(self, name, government, items=None, entity_id=None):# Governmental(Organization)
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 'CAD', 'IFRS', None, None, None, None, None, self.__class__.__name__, government, None, None, None, None, None, None, None, None, None, None, None, items, None) ] # Note: The 2nd to 5th values are for another program
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		self.government = government
		self.user = None
		self.hold_event_ids = []
		self.prod_hold = []
		self.auto_wip = True
		self.auto_done = False
		self.saved = False
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Governmental Org: {} | entity_id: {}'.format(self.name, self.entity_id))

	def is_shareholder(self, corps):
		if not isinstance(corps, (list, tuple)):
			corps = [corps]
		invested = [corp for corp in corps if corp.is_owner(self)] # TODO Try to make this a generator
		return invested

	def __str__(self):
		return 'Govn: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Govn: {} | {}'.format(self.name, self.entity_id)

class Bank(Organization):#Governmental): # TODO Subclassing Governmental creates a Governmental entity also
	# TODO Can the below be omitted for inheritance
	def __init__(self, name, government, interest_rate=None, items=None, user=None, entity_id=None):# Bank(Organization)
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 'CAD', 'IFRS', None, None, None, None, None, self.__class__.__name__, government, None, None, None, None, None, None, None, None, user, None, interest_rate, items, None) ] # Note: The 2nd to 5th values are for another program
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		self.government = government
		if user is None:
			gov = self.factory.get_by_id(self.government)
			if gov is None:
				user = False
			else:
				user = gov.user
		elif user == 'True' or user == '1' or user == 1:
			user = True
		elif user == 'False' or user == '0' or user == 0:
			user = False
		self.user = user
		self.hold_event_ids = []
		self.auto_wip = True
		self.auto_done = False
		self.saved = False
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Central Bank: {} | User: {} | entity_id: {}'.format(self.name, self.user, self.entity_id))
		if interest_rate is None:
			self.interest_rate = 0.0

	def print_money(self, amount=None):
		if amount is None:
			amount = INIT_CAPITAL
		capital_entry = [ self.ledger.get_event(), self.entity_id, '', world.now, '', 'Create capital', '', '', '', 'Cash', 'Nation Wealth', amount ]
		capital_event = [capital_entry]
		self.ledger.journal_entry(capital_event)

	def adj_rate(self, change):
		self.interest_rate += change
		return self.interest_rate

	def __str__(self):
		return 'Bank: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Bank: {} | {}'.format(self.name, self.entity_id)

class NonProfit(Organization):
	def __init__(self, name, items, government, founder, auth_qty=0, entity_id=None):# NonProfit(Organization)
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 'CAD', 'IFRS', None, None, None, None, None, self.__class__.__name__, government, founder, None, None, None, None, None, None, None, None, None, None, items, None) ] # Note: The 2nd to 5th values are for another program
		# if not os.path.exists('db/' + args.database) or args.reset:
		if new_db or args.reset:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			if entity_id is None:
				self.entity_id = self.accts.add_entity(entity_data)
			else:
				self.entity_id = entity_id
		self.name = name
		self.government = government
		self.founder = founder
		self.user = None
		self.hold_event_ids = []
		self.prod_hold = []
		self.auto_wip = True
		self.auto_done = False
		self.saved = False
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Non-Profit: {} | entity_id: {}'.format(self.name, self.entity_id))

	def __str__(self):
		return 'Non-Profit: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Non-Profit: {} | {}'.format(self.name, self.entity_id)


class EntityFactory:
	_instance = None  # Singleton instance
	_initialized = False  # Prevent multiple inits
	
	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			print('Creating new EntityFactory instance via __new__')
			cls._instance = super().__new__(cls)
		else:
			print('Returning existing EntityFactory instance via __new__')
		return cls._instance

	def __init__(self):# EntityFactory
		# print(f'{repr(self)} Create factory with __init__.')
		if self._initialized:
			return  # Skip re-initializing the singleton

		self.registry = collections.OrderedDict()
		self.registry[Individual] = []
		self.registry[Environment] = []
		self.registry[Organization] = []
		self.registry[Corporation] = []
		self.registry[Government] = []
		self.registry[NonProfit] = []
		self.registry[Governmental] = []
		# self.registry[Environment] = []

		self._initialized = True

	_accts = None
	_ledger = None

	@classmethod
	def get_factory(cls):
		# '''Returns the existing factory instance, or creates one if none exists.'''
		# print(f'cls: {cls} | {repr(cls)} | {cls._instance}')
		# if cls._instance is None:
		# 	cls._instance = EntityFactory()  # Create if none exists
		# return cls._instance
		return cls()

	@staticmethod
	def init(database, econ_accts):
		if EntityFactory._ledger is None:
			EntityFactory._accts = acct.create_accounts(database, econ_accts)
			EntityFactory._ledger = acct.create_ledger(EntityFactory._accts)

	@staticmethod
	def get_accts():
		if EntityFactory._accts is None:
			raise RuntimeError('Accts has not been initialized. Call Registry.init() first.')
		return EntityFactory._accts

	@staticmethod
	def get_ledger():
		if EntityFactory._ledger is None:
			raise RuntimeError('Ledger has not been initialized. Call Registry.init() first.')
		return EntityFactory._ledger

	# def get_accts(self):
	# 	return self.accts

	# def get_ledger(self):
	#     return self.ledger

	def create(self, cls, *args, **kwargs):
		# print(f'Create cls: {repr(self)} | {cls}')
		entity = cls(*args, **kwargs)  # create the instance
		self.register_instance(entity) # add to registry
		return entity

	def register_instance(self, entity):
		# print(f'Regi: {repr(self)} | {entity}')
		typ = type(entity)
		if typ not in self.registry:
			self.registry[typ] = []
		self.registry[typ].append(entity)

	def destroy(self, entity):
		typ = type(entity)
		index = self.get_pos(entity)
		return self.registry[typ].pop(index)

	def get(self, typ=None, users=True, computers=True, ids=False):
		# TODO Maybe convert all for loops to list comprehensions
		if typ is None:
			typ = [*self.registry.keys()]
		if not isinstance(typ, (list, tuple)):
			typ = [typ]
		entities = []
		# print(f'Registry: {repr(self)} | {self} | {typ} | {self.registry}')
		for el in typ:
			entities += self.registry[el]
		if not computers:
			entities = [entity for entity in entities if entity.user]
		if not users:
			entities = [entity for entity in entities if not entity.user]
			# print('Include users, {}: \n{}'.format(users, entities))
		if ids:
			entities = [e.entity_id for e in entities]
		# print(f'Factory get entities from {self}: {entities}')
		return entities

	def get_all(self): # TODO No longer needed
		org_types = [*self.registry.keys()]
		return self.get(org_types)

	def get_all_ids(self):
		# ids = []
		# for entity in self.get():
		# 	ids.append(entity.entity_id)
		# return ids
		return self.get(ids=True)

	def get_pos(self, entity):
		typ = type(entity)
		for index, el in enumerate(self.get(typ)):
			if el.entity_id == entity.entity_id:
				return index

	def get_by_id(self, entity_id):
		for typ in self.registry.keys():
			for entity in self.get(typ):
				if entity.entity_id == entity_id:
					#print('Entity by ID: {} | {}'.format(entity, entity.entity_id))
					#print('Entity Name by ID: {}'.format(entity.name))
					return entity

	def get_by_name(self, name, generic=False):
		for typ in self.registry.keys():
			for entity in self.get(typ):
				if generic:
					if name == entity.name.rsplit('-', 1)[0]:
						# print('Entity by Name: {}'.format(entity))
						# print('Entity Name by Name: {}'.format(entity.name))
						return entity
				else:
					if name == entity.name:
						#print('Entity by Name: {}'.format(entity))
						#print('Entity Name by Name: {}'.format(entity.name))
						return entity

	def list_entities(self, typ=None):
		if typ is None:
			for entity in self.get():
				print(entity)
		else:
			for entity in self.get(typ):
				print(entity)

	def __str__(self):
		counts = {typ.__name__: len(reg) for typ, reg in self.registry.items()}
		return 'EntityFactory: ' + str(counts)


def create_entityfactory():
	print('EntityFactory object created.')
	return EntityFactory()

def create_world(accts=None, ledger=None, factory=None, governments=1, population=2, new_db=True, database=None):#, args=None):
	if factory is None:
		factory = create_entityfactory()
	EntityFactory.init(database, econ_accts)
	if accts is None:
		accts = EntityFactory.get_accts()
	if ledger is None:
		ledger = EntityFactory.get_ledger()
	global world
	world = World(factory, accts, ledger, governments, population, new_db)#, args)
	return world

def timed_input(prompt, timeout=10, v=False):
	import threading
	user_input = [None]

	def get_input():
		user_input[0] = input(prompt)

	thread = threading.Thread(target=get_input)
	thread.daemon = True
	thread.start()
	thread.join(timeout)

	if thread.is_alive():
		if v: print(f'\nNo input received in {timeout} seconds. Continuing...')
		return None
	else:
		if v: print(f'\nReceived user input. Will ask for a player ID to toggle.')# {user_input[0]}')# |  {type(user_input[0])}')
		return user_input[0]

def parse_args(conn=None, command=None, external=False):
	global args
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-c', '--command', type=str, help='A command for the program.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='Add a delay for a chance to take over the econ sim.')
	parser.add_argument('-r', '--reset', action='store_true', help='Reset the sim!')
	parser.add_argument('-rand', '--random', action='store_false', help='Remove randomness from the sim.') # TODO Is this still needed?
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
	parser.add_argument('-t', '--time', type=int, help='The number of days the sim will run for.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital each player to start with.')
	parser.add_argument('-g', '--governments', type=int, default=1, help='The number of governments in the econ sim.')
	parser.add_argument('-P', '--players', type=int, nargs='?', const=-1, help='Play the sim as a government!')
	parser.add_argument('-p', '--population', type=int, default=1, help='The number of people in the econ sim per government.')
	parser.add_argument('-mp', '--max_pop', type=int, help='The maximum number of people in the econ sim per government.')
	parser.add_argument('-u', '--users', type=int, nargs='?', const=-1, help='Play the sim as an individual!')
	parser.add_argument('-win', '--win', action='store_true', help='Set win conditions for the sim.')
	parser.add_argument('-pin', '--pin', action='store_true', help='Enable pin for turn protection.')
	parser.add_argument('-early', '--early', action='store_true', help='Automatically end the turn when no hours left when not in user mode.')
	parser.add_argument('-j', '--jones', action='store_true', help='Enable game mode like Jones in the Fast Lane.')
	parser.add_argument('-inf', '--inf_time', action='store_true', help='Toggles infinite time for labour and turns off waiting requirements.')
	parser.add_argument('-v', '--verbose', action='store_false', help='Turn off verbosity for running the sim in auto mode.')
	# TODO Add argparse for setting win conditions
	# User would choose one or more goals for Wealth, Tech, Population, Land
	# Or a time limit, with the highest of one or more of the above
	# With ability to keep playing
	args = parser.parse_args()

	if args.database is not None:
		conn = args.database
	elif args.database is None:
		conn = 'econ01.db'
		# args.database = 'econ01.db'
	# command = None
	if command is None:
		command = args.command
	USE_PIN = args.pin # TODO Fix this?

	if args.inf_time:
		MAX_HOURS = float('inf')
		print('Labour hours inf: ', MAX_HOURS)

	print(time_stamp() + str(sys.argv))
	print(time_stamp() + 'Start Econ Sim | Governments: {} | Population per Gov: {}'.format(args.governments, args.population))
	if args.players:
		print(time_stamp() + 'Play the sim as a government by entering commands. Type "help" for more info.')
		if args.players == -1:
			print(time_stamp() + 'Number of players not specified. Will assume same number as number of governments: {}'.format(args.governments))
			args.players = args.governments
		elif args.players > args.governments:
			args.players = args.governments
	else: # TODO Could use a default=0 argument
		args.players = 0
	if args.users:
		print(time_stamp() + 'Play the sim as one or more individuals by entering commands. Type "help" for more info.')
		if args.users == -1:
			print(time_stamp() + 'Number of users not specified. Will assume single player.')
			args.users = 1
		elif args.users > args.population:
			args.population = args.users
	else: # TODO Could use a default=0 argument
		args.users = 0
	if args.capital is None:
		if args.jones:
			args.capital = 300 * args.population
		else:
			args.capital = 1000000
	if (args.delay is not None) and (args.delay != 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
	if args.random:
		if args.seed:
			print(time_stamp() + 'Randomness turned on with a seed of {}.'.format(args.seed))
			random.seed(args.seed)
		else:
			print(time_stamp() + 'Randomness turned on with no seed provided.')
			random.seed()
	if not args.verbose:
		print(time_stamp() + 'Verboseness turned off.')
	if args.time is not None:
		global END_DATE
		END_DATE = (datetime.datetime(1986,10,1).date() + datetime.timedelta(days=args.time)).strftime('%Y-%m-%d')
	if args.early:
		print(time_stamp() + 'Econ Sim will end turns early if no hours available')
	if END_DATE is None:
		print(time_stamp() + 'Econ Sim has no end date and will end if everyone dies.')
	else:
		print(time_stamp() + 'Econ Sim has an end date of {} or if everyone dies.'.format(END_DATE))
	print(time_stamp() + 'Database file: {}'.format(conn))
	global new_db
	new_db = True
	# print('Existing DB Check: {}'.format(os.path.exists('db/' + conn)))
	if os.path.exists('db/' + conn):
		new_db = False
	if args.reset:
		delete_db(conn)
	return args, conn

def main(conn=None, command=None, external=False):
	t0_start = time.perf_counter()
	args, conn = parse_args(conn, command, external)
	# accts = acct.Accounts(conn, econ_accts)
	# ledger = acct.Ledger(accts)
	# factory = EntityFactory()
	# world = World(factory, args.governments, args.population, new_db)

	# accts = acct.create_accounts(conn, econ_accts)
	# ledger = acct.create_ledger(accts)
	# factory = create_entityfactory()
	global world
	EntityFactory.init(conn, econ_accts)  # Initialize Ledger
	world = create_world(governments=args.governments, population=args.population, new_db=new_db, database=conn)#, args=args)
	
	# pr = cProfile.Profile()
	# pr.enable()
	while True:
		# world.handle_events()
		world.update_econ()
		if world.end:
			break
		if args.delay:
			response = timed_input(f'Press any key (except enter) and then enter, to chose an entity to control ({args.delay} sec to respond): ', timeout=args.delay)
			if response:
				world.toggle_user()

	# pr.disable()
	# pr.print_stats(sort='time')

	t0_end = time.perf_counter()
	print(time_stamp() + 'End of Econ Sim! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))


if __name__ == '__main__':
	main()

# source ./venv/bin/activate

# nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/econ.py -db econ_2025-06-20.db -s 11 -p 4 -mp 10 --early -i items.csv >> /home/robale5/becauseinterfaces.com/acct/logs/econ_2025-06-20.log 2>&1 &

# nohup /home/pi/dev/venv/bin/python3.6 -u /home/pi/dev/acct/econ.py -db econ01.db -s 11 -p 4 >> /home/pi/dev/acct/logs/econ01.log 2>&1 &

# (python econ.py -db econ_2024-12-07.db -s 11 -p 4 -r -t 4 >> logs/econ_2024-12-07.log && say done) || say error
# python econ.py -db econ_2024-12-07.db -s 11 -p 4 -mp 5 -r -t 1 >> logs/econ_2024-12-07.log

# (python econ.py -s 11 -p 4 -r -t 4 && say done) || say error
# python econ.py -u

# TODO
# Add a new column to items called fulfill
# If it is None, then take the item name
# Otherwise it allows you to specific what it fulfills, similar to how productivity items work
# This will allow multiple items to fulfill the same requirement
# Such as having a Stone Forge and an Electric Forge
# Or Drift Wood and Lumber both fulfilling Wood

# scp data/items.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp econ.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct