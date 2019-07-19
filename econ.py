import acct
import pandas as pd
import collections
import itertools
import argparse
import datetime
import warnings
import random
import time
import math
import os
import re
import cProfile

DISPLAY_WIDTH = 98
pd.set_option('display.width', None)
pd.options.display.float_format = '${:,.2f}'.format
warnings.filterwarnings('ignore')

END_DATE = None
MAX_CORPS = 2
MAX_HOURS = 12
WORK_DAY = 8
INIT_PRICE = 10.0
INIT_CAPITAL = 2000
EXPLORE_TIME = 400

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
		print(time_stamp() + 'Database file reset: {}'
			.format(db_path + db_name))
	else:
		print(time_stamp() + 'The database file does not exist at {}.'
			.format(db_path + db_name))

econ_accts = [
	('Cash','Asset'),
	('Info','Admin'),
	('Natural Wealth','Wealth'),
	('Investments','Asset'),
	('Shares','Wealth'),
	('Land','Asset'),
	('Buildings','Asset'),
	('Building Produced','Revenue'),
	('Equipment Produced','Revenue'),
	('Equipment','Asset'),
	('Machine','Equipment'),
	('Tools','Equipment'),
	('Furniture','Equipment'),
	('Inventory','Asset'),
	('WIP Inventory','Asset'),
	('WIP Equipment','Asset'),
	('Building Under Construction','Asset'),
	('In Use','Asset'),
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
	('Depreciation Expense','Expense'),
	('Accumulated Depreciation','Asset'),
	('Loss on Impairment','Expense'),
	('Accumulated Impairment Losses','Asset'),
	('Spoilage Expense','Expense'),
	('Worker Info','Info'),
	('Hire Worker','Info'),
	('Fire Worker','Info'),
	('Start Job','Info'),
	('Quit Job','Info'),
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
	('Technology','Asset'),
	('Researching Technology','Asset'),
	('Technology Expense','Expense'),
	('Technology Produced','Revenue'),
	('Deposits','Liability'),
	('Bank','Asset'),
	('Loan','Liability'),
	('Loans Receivable','Asset'),
	('Gift','Revenue'),
	('Gift Expense','Expense'),
] # TODO Remove div exp once retained earnings is implemented

class World:
	def __init__(self, factory, players=1, population=2):
		self.factory = factory
		if not os.path.exists('db/' + args.database) or args.reset:
			self.clear_ledger()
			print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Create World ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))
			self.now = datetime.datetime(1986,10,1).date()
			self.set_table(self.now, 'date')
			print(self.now)
			if args.items is None:
				items_file = 'data/items.csv'
			self.items = accts.load_items(items_file) # TODO Change config file to JSON
			self.global_needs = self.create_needs()
			print(time_stamp() + 'Loading items from: {}'.format(items_file))
			self.demand = pd.DataFrame(columns=['date','entity_id','item_id','qty','reason'])
			self.set_table(self.demand, 'demand')
			self.delay = pd.DataFrame(columns=['txn_id','delay']) # TODO Create table in db and save df to it after each edit
			self.set_table(self.delay, 'delay')
			self.players = players
			self.population = population
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Items Config: \n{}'.format(self.items))
			self.env = self.create_world(date=self.now)
			self.setup_prices()
			self.produce_queue = pd.DataFrame(columns=['item_id', 'entity_id','qty', 'freq', 'last'])
			print('Initial Produce Queue: \n{}'.format(self.produce_queue))
			self.set_table(self.produce_queue, 'produce_queue')
			self.end = False
			# Create gov for each player
			for player in range(1, self.players + 1):
				self.entities = accts.get_entities()
				last_entity_id = self.entities.reset_index()['entity_id'].max()
				factory.create(Government, 'Player-' + str(last_entity_id + 1), items=None)
			for gov in factory.get(Government):
				gov.bank = None
				print('Bank: {}'.format(gov.bank))
				self.indiv_items_produced = self.items[self.items['producer'].str.contains('Individual', na=False)].reset_index() # TODO Move to own function
				self.indiv_items_produced = self.indiv_items_produced['item_id'].tolist()
				self.indiv_items_produced = ', '.join(self.indiv_items_produced)
				print('\nCreate founding population for government {}.'.format(gov.entity_id))
				for person in range(1, self.population + 1):
					# print('Person: {}'.format(person))
					self.entities = accts.get_entities()
					last_entity_id = self.entities.reset_index()['entity_id'].max()
					factory.create(Individual, 'Person-' + str(last_entity_id + 1), self.indiv_items_produced, self.global_needs, gov.entity_id)
					entity = factory.get_by_id(person)
					self.prices = pd.concat([self.prices, entity.prices])
			self.gov = factory.get(Government)[0]
			print('Start Government: {}'.format(self.gov))
			self.selection = None
		else:
			continue_date = self.get_table('date').values[0][0]
			self.now = datetime.datetime.strptime(continue_date[:10], '%Y-%m-%d').date()
			# self.now += datetime.timedelta(days=-1)
			print(time_stamp() + 'Continuing sim from {} file as of {}.'.format(args.database, self.now))
			self.items = accts.get_items()
			self.global_needs = self.create_needs()
			self.demand = self.get_table('demand')
			self.delay = self.get_table('delay')
			self.entities = accts.get_entities().reset_index()
			individuals = self.entities.loc[self.entities['entity_type'] == 'Individual']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Individuals: \n{}'.format(individuals))
			alive_individuals = []
			for index, row in individuals.iterrows():
				current_need_all = [int(x.strip()) for x in str(row['current_need']).split(',')]
				if not any(n <= 0 for n in current_need_all):
					alive_individuals.append(row)
			self.population = len(alive_individuals)
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Items Config: \n{}'.format(self.items))
			self.entities = accts.get_entities().reset_index()
			# TODO Reload env and govs
			envs = self.entities.loc[self.entities['entity_type'] == 'Environment']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Environments: \n{}'.format(envs))
			for index, env in envs.iterrows():
				factory.create(Environment, env['name'], env['entity_id'])
			self.env = factory.get(Environment)[0]
			self.setup_prices()
			self.produce_queue = self.get_table('produce_queue')
			self.end = False
			govs = self.entities.loc[self.entities['entity_type'] == 'Government']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Governments: \n{}'.format(govs))
			for index, gov in govs.iterrows():
				factory.create(Government, gov['name'], gov['entity_id'], items=None)
			self.players = len(govs)
			for gov in factory.get(Government):
				gov.bank = None
				# TODO Check if Bank entities exist and assign them to the correct play based on the shareholders
			for index, indiv in individuals.iterrows():
				current_need_all = [int(x.strip()) for x in str(indiv['current_need']).split(',')]
				if not any(n <= 0 for n in current_need_all):
					factory.create(Individual, indiv['name'], indiv['outputs'], self.global_needs, int(indiv['government']), indiv['hours'], indiv['current_need'], indiv['parents'], indiv['entity_id'])
			corps = self.entities.loc[self.entities['entity_type'] == 'Corporation']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('Corporations: \n{}'.format(corps))	
			for index, corp in corps.iterrows():
				legal_form = self.org_type(corp['name'])
				factory.create(legal_form, corp['name'], corp['outputs'], int(corp['government']), corp['auth_shares'], corp['entity_id'])
			self.gov = factory.get(Government)[0]
			print('Start Government: {}'.format(self.gov))
			self.selection = None
		print()
		self.cols = ledger.gl.columns.values.tolist()
		print(self.cols) # For verbosity

	def clear_ledger(self):
		tables = [
			'gen_ledger',
			'entities',
			'items'
		]

		cur = ledger.conn.cursor()
		for table in tables:
			clear_table_query = '''
				DELETE FROM ''' + table + ''';
			'''
			try:
				cur.execute(clear_table_query)
				print('Clear ' + table + ' table.')
			except:
				continue
		ledger.conn.commit()
		cur.close()
		#print('Clear tables.')

	def set_table(self, table, table_name):
		if not isinstance(table, (pd.DataFrame, pd.Series)):
			if not isinstance(table, collections.Iterable):
				table = [table]
			table = pd.DataFrame(data=table, index=None)
		# print('Set Table: \n{}'.format(table))
		table.to_sql(table_name, ledger.conn, if_exists='replace', index=False)
		return table

	def get_table(self, table):
		table = pd.read_sql_query('SELECT * FROM ' + table + ';', ledger.conn)
		return table

	def setup_prices(self):
		# TODO Make self.prices a multindex with item_id and entity_id
		self.prices = pd.DataFrame(data={'item_id': self.items.index,'entity_id': self.env.entity_id,'price': INIT_PRICE}) # TODO Clean this up
		self.prices = self.prices[14:]
		self.prices['item_type'] = self.prices.apply(lambda x: self.get_item_type(x['item_id']), axis=1)
		self.prices = self.prices.set_index('item_id')
		clear_prices = self.prices.loc[self.prices['item_type'].isin(['Technology','Education','Land'])].reset_index()
		for i, item in clear_prices['item_id'].iteritems():
			self.prices.at[item, 'price'] = 0
		self.prices.at['Study','price'] = 0
		self.prices.drop(columns=['item_type'], inplace=True)
		print('Prices Setup: \n{}\n'.format(self.prices))
		return self.prices

	def create_world(self, lands=None, date=None):
		print(time_stamp() + 'Creating world.')
		# TODO Create environment instance first
		env = factory.create(Environment, 'Earth')#, entity_id=0)
		if lands is None:
			lands = [
				['Land', 100000],
				['Arable Land', 150000],
				['Forest', 10000],
				['Rocky Land', 1000],
				['Mountain', 10]
			]
		for land in lands:
			env.create_land(land[0], land[1], date) # TODO Call from env instance
		return env

	def ticktock(self, ticks=1, v=True):
		self.now += datetime.timedelta(days=ticks)
		self.set_table(self.now, 'date')
		if v: print(self.now)
		return self.now

	def get_hours(self):
		self.hours = collections.OrderedDict()
		entities = world.gov.get(Individual)
		for individual in entities:
			self.hours[individual.name] = individual.hours
		return self.hours

	def check_end(self, v=False):
		population = len(factory.registry[Individual])
		if v: print('Population: {}'.format(population))
		industry = len(factory.registry[Corporation])
		if v: print('Industry: {}'.format(industry))
		if population <= 0:
			print('Econ Sim ended due to human extinction.')
			self.end = True
		return self.end

	def valid_corp(self, ticker):
		if not isinstance(ticker, str):
			return False
		ticker = ticker.title()
		tickers = []
		for index, producers in self.items['producer'].iteritems():
			if producers is not None:
				if isinstance(producers, str):
					producers = [x.strip() for x in producers.split(',')]
				producers = list(collections.OrderedDict.fromkeys(filter(None, producers)))
				tickers += producers
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
			items_typ = self.items.reset_index()
			items_typ['item_type'] = items_typ.apply(lambda x: x['item_id'] if x['child_of'] is None else self.get_item_type(x['item_id']), axis=1)
			items_typ = items_typ.loc[items_typ['item_type'] == typ]
			# print('Items Typ: {} | {} \n{}'.format(item, typ, items_typ))
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

	def get_item_type(self, item):
		if item in ['Land','Labour','Job','Equipment','Buildings','Subscription','Service','Commodity','Components','Technology','Education','Government','Non-Profit','Time','Loan','None']:
			return item
		else:
			return self.get_item_type(self.items.loc[item, 'child_of'])

	def org_type(self, name):
		if name == 'Government':
			return Government
		elif name == 'Non-Profit':
			return NonProfit
		else:
			try:
				return self.org_type(self.items.loc[name, 'child_of'])
			except KeyError:
				return Corporation

	def get_price(self, item, entity_id=None):
		if not isinstance(entity_id, int) and entity_id is not None:
			entity_id = entity_id.entity_id # Incase an entity object is passed instead
		if entity_id:
			#print('Entity ID: {}'.format(entity_id))
			item_prices = self.prices.loc[item]
			if isinstance(item_prices, pd.Series):
				item_prices = item_prices.to_frame().transpose()
			#print('Item Prices: \n{}'.format(item_prices))
			current_prices = item_prices.loc[item_prices['entity_id'] == entity_id]
			if current_prices.empty:
				current_prices = self.prices.loc[item]
		else:
			current_prices = self.prices.loc[item]
		#print('Current Prices: \n{}'.format(current_prices))
		price = current_prices['price'].min()
		# price = self.items.loc[item, 'price']
		#print('Price for {}: {}'.format(item, price))
		return price

	def create_needs(self):
		global_needs = []
		for _, item_satifies in self.items['satisfies'].iteritems():
			if item_satifies is None:
				continue
			item_needs = [x.strip() for x in item_satifies.split(',')]
			global_needs += item_needs
		global_needs = list(collections.OrderedDict.fromkeys(global_needs))
		print('Global Needs: \n{}'.format(global_needs))
		return global_needs

	def update_econ(self):
		t1_start = time.perf_counter()
		if str(self.now) == '1986-10-01':
			# TODO Consider a better way to do this
			for individual in factory.get(Individual):
				capital = args.capital / self.population
				individual.capitalize(amount=capital)#25000 # Hardcoded for now

		# TODO Maybe an update_world() method to adjust the needs and time
		print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Econ Updated ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))

		# self.ticktock()
		self.entities = accts.get_entities().reset_index()
		#prices_disp = self.entities[['entity_id','name']].merge(self.prices.reset_index(), on=['entity_id']).set_index('item_id')
		print(time_stamp() + 'Current Date: {}'.format(self.now))
		if END_DATE is not None: # For debugging
			if self.now >= datetime.datetime.strptime(END_DATE, '%Y-%m-%d').date():
				world.end = True # TODO User
		self.check_end(v=True)
		if self.end:
			return
		for individual in factory.get(Individual):
				individual.reset_hours()
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print('\nPrices: \n{}\n'.format(self.prices))

		demand_items = self.demand.drop_duplicates(['item_id'])
		self.set_table(self.demand, 'demand')

		print(time_stamp() + 'Current Date: {}'.format(self.now))
		t3_start = time.perf_counter()
		for entity in factory.get():
			#print('Entity: {}'.format(entity))
			t3_1_start = time.perf_counter()
			entity.depreciation_check()
			t3_1_end = time.perf_counter()
			print(time_stamp() + '3.1: Dep check took {:,.2f} sec for {}-{}.'.format((t3_1_end - t3_1_start), entity.name, entity.entity_id))
			t3_2_start = time.perf_counter()
			entity.wip_check()
			t3_2_end = time.perf_counter()
			print(time_stamp() + '3.2: WIP check took {:,.2f} sec for {}-{}.'.format((t3_2_end - t3_2_start), entity.name, entity.entity_id))
			t3_3_start = time.perf_counter()
			entity.check_interest()
			t3_3_end = time.perf_counter()
			print(time_stamp() + '3.3: Int check took {:,.2f} sec for {}-{}.'.format((t3_3_end - t3_3_start), entity.name, entity.entity_id))
			t3_4_start = time.perf_counter()
			entity.check_subscriptions()
			t3_4_end = time.perf_counter()
			print(time_stamp() + '3.4: Sub check took {:,.2f} sec for {}-{}.'.format((t3_4_end - t3_4_start), entity.name, entity.entity_id))
			t3_5_start = time.perf_counter()
			entity.check_salary()
			t3_5_end = time.perf_counter()
			print(time_stamp() + '3.5: Sal check took {:,.2f} sec for {}-{}.'.format((t3_5_end - t3_5_start), entity.name, entity.entity_id))
			t3_6_start = time.perf_counter()
			entity.pay_wages()
			t3_6_end = time.perf_counter()
			print(time_stamp() + '3.6: Wag check took {:,.2f} sec for {}-{}.'.format((t3_6_end - t3_6_start), entity.name, entity.entity_id))
		t3_end = time.perf_counter()
		print(time_stamp() + '3: Entity check took {:,.2f} min.'.format((t3_end - t3_start) / 60))
		print()

		# User mode
		if args.user:
			for player in factory.get(Government):
				print('~' * DISPLAY_WIDTH)
				print('Player: {}'.format(player))
				print('Citizen Entities: \n{}'.format(player.get(envs=False)))
				self.selection = None
				ledger.default = player.get(ids=True)
				ledger.reset()
				self.gov = player
				for entity in player.get():
					entity.auto_produce()
				while sum(self.get_hours().values()) > 0:
					if self.selection is None:
						self.selection = player.get(Individual)[0]
					if isinstance(self.selection, Individual):
						print('\nEntity Selected: {} | Hours: {}'.format(self.selection.name, self.selection.hours))
					else:
						print('\nEntity Selected: {}'.format(self.selection))
					result = self.selection.action()
					if result == 'end':
						break
			ledger.default = None

		else:
			print(time_stamp() + 'Current Date: {}'.format(self.now))
			t2_start = time.perf_counter()
			for individual in factory.get(Individual):
				print('Individual: {} | {}'.format(individual.name, individual.entity_id))
				for need in individual.needs:
					#print('Need: {}'.format(need))
					individual.corp_needed(need=need)
					individual.item_demanded(need=need)
				for index, item in demand_items.iterrows():
					#print('Corp Check Demand Item: {}'.format(item['item_id']))
					individual.corp_needed(item=item['item_id'], demand_index=index)
			t2_end = time.perf_counter()
			print(time_stamp() + '2: Individual check took {:,.2f} min.'.format((t2_end - t2_start) / 60))
			print()
			print('World Demand Start: \n{}'.format(world.demand))
			print()

			print(time_stamp() + 'Current Date: {}'.format(self.now))
			t4_start = time.perf_counter()
			print('Check Demand List:')
			for entity in factory.get():#(Corporation):
				#print('\nDemand check for: {} | {}'.format(entity.name, entity.entity_id))
				entity.tech_motivation()
				entity.set_price()
				entity.auto_produce()
				entity.check_demand()
				entity.check_inv()
			t4_end = time.perf_counter()
			print(time_stamp() + '4: Demand list check took {:,.2f} min.'.format((t4_end - t4_start) / 60))
			print()

			print(time_stamp() + 'Current Date: {}'.format(self.now))
			t5_start = time.perf_counter()
			print('Check Optional Items:')
			for entity in factory.get():#(Corporation):
				#print('\nOptional check for: {} | {}'.format(entity.name, entity.entity_id))
				entity.check_optional()
				entity.check_inv()
				if type(entity) == Corporation:
					# entity.list_shareholders(largest=True)
					entity.dividend()
			t5_end = time.perf_counter()
			print(time_stamp() + '5: Optional check took {:,.2f} min.'.format((t5_end - t5_start) / 60))
			print()

		print(time_stamp() + 'Current Date: {}'.format(self.now))
		t6_start = time.perf_counter()
		print('Check Prices:')
		for entity in factory.get():
			print('\nPrices check for: {} | {}'.format(entity.name, entity.entity_id))
			entity.check_prices()
		t6_end = time.perf_counter()
		print(time_stamp() + '6: Prices check took {:,.2f} min.'.format((t6_end - t6_start) / 60))
		print()

		print(time_stamp() + 'Current Date: {}'.format(self.now))
		t7_start = time.perf_counter()
		 # TODO Fix assuming all individuals have the same needs
		for need in self.global_needs:#individual.needs:
			for individual in factory.get(Individual):
				#print('Individual Name: {} | {}'.format(individual.name, individual.entity_id))
				if not args.user:
					individual.threshold_check(need)
				individual.need_decay(need)
				print('{} {} Need: {}'.format(individual.name, need, individual.needs[need]['Current Need']))
				if individual.dead:
					break
		t7_end = time.perf_counter()
		print(time_stamp() + '7: Needs check took {:,.2f} min.'.format((t7_end - t7_start) / 60))
		print()

		print(time_stamp() + 'Current Date: {}'.format(self.now))
		if self.check_end():
			return
		t8_start = time.perf_counter()
		for typ in factory.registry.keys():
			for entity in factory.get(typ):
				if isinstance(entity, Corporation): # TODO Temp fix for negative balances
					entity.negative_bal()
				ledger.set_entity(entity.entity_id)
				entity.cash = ledger.balance_sheet(['Cash'])
				if isinstance(entity, Individual):
					print('{} Cash: {}'.format(entity.name, entity.cash))
				else:
					print('{}-{} Cash: {}'.format(entity.name, entity.entity_id, entity.cash))
				ledger.reset()
			print()
			for entity in factory.get(typ):
				ledger.set_entity(entity.entity_id)
				entity.nav = ledger.balance_sheet()
				if isinstance(entity, Individual):
					print('{} NAV: {}'.format(entity.name, entity.nav))
				else:
					print('{}-{} NAV: {}'.format(entity.name, entity.entity_id, entity.nav))
				ledger.reset()

			# To switch things up
			if len(factory.registry[typ]) != 0:
				print('\nPre Entity Sort by NAV: {} \n{}'.format(typ, factory.registry[typ]))
				factory.registry[typ].sort(key=lambda x: x.nav)
				print('Post Entity Sort by NAV: {} \n{}\n'.format(typ, factory.registry[typ]))
				# if args.random:
				# 	print('\nPre Entity Shuffle: {} \n{}'.format(typ, factory.registry[typ]))
				# 	random.shuffle(factory.registry[typ])
				# 	print('Post Entity Shuffle: {} \n{}\n'.format(typ, factory.registry[typ]))
				# else:
				# 	lst = factory.get(typ)
				# 	lst.append(lst.pop(0))

		t8_end = time.perf_counter()
		print(time_stamp() + '8: Cash check took {:,.2f} min.'.format((t8_end - t8_start) / 60))
		print()

		t9_start = time.perf_counter()
		individual = factory.registry[Individual][-1] # TODO Check for full time
		print('Last Individual: {}'.format(individual))
		if str(self.now) == '1986-10-31': # For testing impairment
			individual.use_item('Rock', uses=1, counterparty=factory.get_by_name('Farm', generic=True), target='Plow')

		if args.random:
			birth_roll = random.randint(1, 20)
			print('Birth Roll: {}'.format(birth_roll))
			if birth_roll == 20:# or (str(self.now) == '1986-10-02'):
				individual.birth()

		# if args.random:
		# 	death_roll = random.randint(1, 40)
		# 	print('Death Roll: {}'.format(death_roll))
		# 	if death_roll == 40:# or (str(self.now) == '1986-10-03'):
		# 		print('{} randomly dies!'.format(individual.name))
		# 		individual.set_need('Hunger', -100, forced=True)

		print()
		print(time_stamp() + 'Current Date: {}'.format(self.now))
		print()
		print('World Demand End: \n{}'.format(world.demand))
		print()
		self.entities = accts.get_entities().reset_index()
		self.inventory = ledger.get_qty(items=None, accounts=['Inventory','Equipment','Buildings','In Use'], show_zeros=False, by_entity=True)
		self.inventory = self.entities[['entity_id','name']].merge(self.inventory, on=['entity_id'])
		print('Global Items: \n{}'.format(self.inventory))
		print()
		t9_end = time.perf_counter()
		print(time_stamp() + '9: Birth and misc checks took {:,.2f} min.'.format((t9_end - t9_start) / 60))

		# if END_DATE is not None: # For debugging
		# 	if self.now >= datetime.datetime.strptime(END_DATE, '%Y-%m-%d').date():
		# 		world.end = True # TODO User remove

		t1_end = time.perf_counter()
		print('\n' + time_stamp() + 'End of Econ Update for {}. It took {:,.2f} min.'.format(self.now, (t1_end - t1_start) / 60))
		self.ticktock() # TODO User

class Entity:
	def __init__(self, name):
		self.name = name
		#print('Entity created: {}'.format(name))

	def adj_price(self, item, qty=1, rate=None, direction=None):
		if rate is None:
			if direction == 'up':
				rate = 1.1 #1.01
			elif direction == 'down':
				rate = 0.9 #0.99
			elif direction == 'up_low':
				rate = 1.02 #1.002
			elif direction == 'down_high':
				rate = 0.8 #0.98
			else:
				rate = 1.1 #1.01
		# rate = 1 + rate
		if item == self.name:
			print('{}-{} cannot get a price for shares of {}.'.format(self.name, self.entity_id, item))
			return 5 # TODO Fix how prices for corporate entities work. Could have a price column on the entities table
		price = world.get_price(item, self.entity_id)
		orig_price = price
		item_type = world.get_item_type(item)
		if item_type in ['Technology','Education']:
			if price != 0:
				world.prices.at[item, 'price'] = 0
				print('{}-{} sets price for {} from {} to {}.'.format(self.name, self.entity_id, item, price, 0))
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
		entity_prices = world.prices.loc[world.prices['entity_id'] == self.entity_id]
		#print('Entity Prices Before: \n{}'.format(entity_prices))
		try:
			target_item = entity_prices.loc[item]
			#print('Target Item: \n{}'.format(target_item))
		except KeyError as e:
			#print('Error Catch: {} | {}'.format(e, repr(e)))
			new_row = pd.DataFrame({'entity_id': self.entity_id, 'price': INIT_PRICE}, [item])#.set_index('item_id')
			#print('New Row: \n{}'.format(new_row))
			entity_prices = entity_prices.append(new_row)
		#print('Entity Prices Mid: \n{}'.format(entity_prices))
		entity_prices.at[item, 'price'] = price
		#print('Entity Prices After: \n{}'.format(entity_prices))
		world.prices = world.prices.loc[world.prices['entity_id'] != self.entity_id]
		world.prices = pd.concat([world.prices, entity_prices])
		#world.prices.at[item, 'price'] = price # Old method
		print('{}-{} adjusts {} price by a rate of {} from ${} to ${}.'.format(self.name, self.entity_id, item, rate, orig_price, price))
		return price

	def set_price(self, item=None, qty=0, price=None, mark_up=0.1, at_cost=False):
		if item is None:
			if self.produces is None:
				print('{}-{} produces no items.'.format(self.name, self.entity_id))
				return
			for item in self.produces:
				price = world.get_price(item, self.entity_id)
				item_type = world.get_item_type(item)
				if item_type in ['Technology','Education','Land']: # TODO Support creating types of land like planting trees to make forest
					if price != 0:
						world.prices.at[item, 'price'] = 0
						#print('{}-{} sets price for {} from {} to {}.'.format(self.name, self.entity_id, item, price, 0))
					return
				cost = 0
				ledger.set_entity(self.entity_id)
				cost_entries = ledger.gl.loc[(ledger.gl['item_id'] == item) & (ledger.gl['credit_acct'] == 'Cost Pool')]
				if not cost_entries.empty:
					cost_entries.sort_values(by=['date'], ascending=False, inplace=True)
					#print('Cost Entries: \n{}'.format(cost_entries))
					cost = cost_entries.iloc[0]['price']
				qty_held = ledger.get_qty(items=item, accounts=['Inventory'])
				#print('Qty held by {}-{} when setting price for {}: {}'.format(self.name, self.entity_id, item, qty_held))
				ledger.reset()
				#print('{}-{}\'s current price for {}: {}'.format(self.name, self.entity_id, item, price))
				if price < cost and qty_held <= qty:
					if at_cost:
						world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost
						print('{}-{} sets price for {} from {} to cost at {}.'.format(self.name, self.entity_id, item, price, cost))
					else:
						world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost * (1 + mark_up)
					print('{}-{} sets price for {} from {} to {}.'.format(self.name, self.entity_id, item, price, cost * (1 + mark_up)))
		else:
			if price is not None:
				orig_price = world.get_price(item, self.entity_id)
				world.prices.at[item, 'price'] = price
				print('{}-{} manually sets price for {} from {} to {}.'.format(self.name, self.entity_id, item, orig_price, price))
				return
			price = world.get_price(item, self.entity_id)
			item_type = world.get_item_type(item)
			if item_type in ['Technology','Education','Land']: # TODO Support creating types of land like planting trees to make forest
				if price != 0:
					world.prices.at[item, 'price'] = 0
					#print('{}-{} sets price for {} from {} to {}.'.format(self.name, self.entity_id, item, price, 0))
				return
			cost = 0
			ledger.set_entity(self.entity_id)
			cost_entries = ledger.gl.loc[(ledger.gl['item_id'] == item) & (ledger.gl['credit_acct'] == 'Cost Pool')]
			if not cost_entries.empty:
				cost_entries.sort_values(by=['date'], ascending=False, inplace=True)
				#print('Cost Entries: \n{}'.format(cost_entries))
				cost = cost_entries.iloc[0]['price']
			qty_held = ledger.get_qty(items=item, accounts=['Inventory'])
			print('Qty held by {}-{} when setting price for {}: {}'.format(self.name, self.entity_id, item, qty_held))
			ledger.reset()
			print('{}-{}\'s current price for {}: {}'.format(self.name, self.entity_id, item, price))
			if price < cost and qty_held <= qty:
				if at_cost:
					world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost
					print('{}-{} sets price for {} from {} to cost at {}.'.format(self.name, self.entity_id, item, price, cost))
				else:
					world.prices.loc[(world.prices['entity_id'] == self.entity_id) & (world.prices.index == item), 'price'] = cost * (1 + mark_up)
					print('{}-{} sets price for {} from {} to {}.'.format(self.name, self.entity_id, item, price, cost * (1 + mark_up)))
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	print(world.prices)

	def transact(self, item, price, qty, counterparty, acct_buy='Inventory', acct_sell='Inventory', acct_rev='Sales', desc_pur=None, desc_sell=None, item_type=None, buffer=False):
		if qty == 0:
			return [], False
		purchase_event = []
		cost = False
		if desc_pur is None:
			desc_pur = item + ' purchased'
		if desc_sell is None:
			desc_sell = 'Sale of ' + item
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		#print('Cash: {}'.format(cash))
		ledger.set_entity(counterparty.entity_id)
		qty_avail = ledger.get_qty(items=item, accounts=[acct_sell])
		print('Qty Available to purchase from {}-{}: {}'.format(counterparty.name, counterparty.entity_id, qty_avail))
		ledger.reset()
		if cash >= (qty * price):
			#print('Transact Item Type: {}'.format(item_type))
			if (qty <= qty_avail or item_type == 'Service'):
				if item_type is not None and item_type != 'Service':
					print('{}-{} transacted with {} for {} {}'.format(self.name, self.entity_id, counterparty.name, qty, item))
					ledger.set_entity(counterparty.entity_id)
					print('{} getting historical cost of {} {}.'.format(counterparty.name, qty, item))
					cost_amt = ledger.hist_cost(qty, item, 'Inventory')#, v=True)
					ledger.reset()
					#print('Cost: {}'.format(cost_amt))
					avg_price = cost_amt / qty
					cogs_entry = [ ledger.get_event(), counterparty.entity_id, world.now, desc_sell, item, avg_price, qty, 'Cost of Goods Sold', acct_sell, cost_amt ]
					sale_entry = [ ledger.get_event(), counterparty.entity_id, world.now, desc_sell, item, price, qty, 'Cash', acct_rev, price * qty ]
					purchase_entry = [ ledger.get_event(), self.entity_id, world.now, desc_pur, item, price, qty, acct_buy, 'Cash', price * qty ]
					purchase_event += [cogs_entry, sale_entry, purchase_entry]
					if buffer:
						counterparty.adj_price(item, qty, direction='up')
						return purchase_event, cost
					ledger.journal_entry(purchase_event)
					counterparty.adj_price(item, qty, direction='up')
					return purchase_event, cost
				else:
					if item_type is None:
						print('{}-{} transacted with {}-{} for {} {} shares.'.format(self.name, self.entity_id, counterparty.name, counterparty.entity_id, qty, item))
					sell_entry = [ ledger.get_event(), counterparty.entity_id, world.now, desc_sell, item, price, qty, 'Cash', acct_sell, price * qty ]
					purchase_entry = [ ledger.get_event(), self.entity_id, world.now, desc_pur, item, price, qty, acct_buy, 'Cash', price * qty ]
					purchase_event += [sell_entry, purchase_entry]
					if buffer:
						counterparty.adj_price(item, qty, direction='up')
						return purchase_event, cost
					ledger.journal_entry(purchase_event)
					counterparty.adj_price(item, qty, direction='up')
					return purchase_event, cost
			else:
				print('{}-{} does not have enough {} on hand to sell {} units of {}.'.format(self.name, self.entity_id, item, qty, item))
				return purchase_event, cost
		else:
			print('{}-{} does not have enough cash to purchase {} units of {}.'.format(self.name, self.entity_id, qty, item))
			cost = True
			# counterparty.adj_price(item, qty, direction='down')
			return purchase_event, cost

	def purchase(self, item, qty, acct_buy='Inventory', acct_sell='Inventory', acct_rev='Sales', wip_acct='WIP Inventory', buffer=False):
		# TODO Clean up
		if qty == 0:
			return
		qty = int(math.ceil(qty))
		qty_wanted = qty
		# TODO Add support for purchasing from multiple entities
		outcome = None
		item_type = world.get_item_type(item)
		if item_type == 'Service':
			# Check if producer exists and get their ID
			# TODO Support multiple of the same producer
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
			if not serv_prices:
				print('No {} to offer {} service. Will add it to the demand table for {}-{}.'.format(producers, item, self.name, self.entity_id))
				self.item_demanded(item, qty)
				return
			counterparty_id = min(serv_prices, key=lambda k: serv_prices[k])
			counterparty = factory.get_by_id(counterparty_id)
			if counterparty is None:
				print('No {} to offer {} service. Will add it to the demand table for {}-{}.'.format(producer, item, self.name, self.entity_id))
				self.item_demanded(item, qty)
				return
			print('{}-{} choose {}-{} for the {} service counterparty.'.format(self.name, self.entity_id, counterparty.name, counterparty.entity_id, item))
			acct_buy = 'Service Expense'
			acct_sell = 'Service Revenue'
		ledger.reset()
		# TODO Consider if want to purchase none inventory assets by replacing Inventory below with acct_buy
		global_inv = ledger.get_qty(item, ['Inventory'], by_entity=True)
		prices_tmp = world.prices.reset_index()
		prices_tmp.rename(columns={'index': 'item_id'}, inplace=True)
		global_inv = global_inv.merge(prices_tmp, on=['entity_id','item_id'])
		global_inv.sort_values(by=['price'], ascending=True, inplace=True)
		if global_inv.shape[0] >= 2:
			print('Global Purchase Inventory for {}: \n{}'.format(item, global_inv))
		if global_inv.empty:
			global_qty = 0
		else:
			global_qty = global_inv['qty'].sum()
		print('Global qty of {} available for purchase: {} {}-{} looking for: {}'.format(item, global_qty, self.name, self.entity_id, qty))
		wip_global_qty = ledger.get_qty(items=item, accounts=wip_acct)
		print('{} WIP qty globally: {}'.format(item, wip_global_qty))

		# Check which entity has the goods for the cheapest
		if item_type != 'Service':
			i = 0
			result = []
			cost = False
			purchased_qty = 0
			while qty > 0:
				#print('Purchase Qty Loop: {} | {}'.format(qty, i))
				try:
					purchase_qty = global_inv.iloc[i].loc['qty']
				except IndexError as e:
					print('No other entities hold {} to purchase the remaining qty of {}.'.format(item, qty))
					break
				if purchase_qty > qty:
					purchase_qty = qty
				counterparty_id = global_inv.iloc[i].loc['entity_id']
				#print('Counterparty ID: {}'.format(counterparty_id))
				counterparty = factory.get_by_id(counterparty_id)
				#print('Purchase Counterparty: {}'.format(counterparty.name))
				if counterparty.entity_id == self.entity_id:
					print('{}-{} attempting to transact with themselves for {} {}.'.format(self.name, self.entity_id, purchase_qty, item))
					price = 0
					ledger.set_entity(self.entity_id)
					cost_entries = ledger.gl.loc[(ledger.gl['item_id'] == item) & (ledger.gl['credit_acct'] == 'Cost Pool')]
					if not cost_entries.empty:
						cost_entries.sort_values(by=['date'], ascending=False, inplace=True)
						#print('Cost Entries: \n{}'.format(cost_entries))
						price = cost_entries.iloc[0]['price']
					ledger.reset()
					#return
				else:
					price = world.get_price(item, counterparty.entity_id)
				#print('Purchase QTY: {}'.format(purchase_qty))
				result_tmp, cost = self.transact(item, price=price, qty=purchase_qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=buffer)
				if not result_tmp:
					break
				result += result_tmp
				purchased_qty += purchase_qty
				qty -= purchase_qty
				i += 1
			if qty_wanted > purchased_qty and item_type != 'Land':
				qty_wanted = qty_wanted - wip_global_qty
				if qty_wanted > 0:
					if cost:
						#self.item_demanded(item, qty_wanted - purchased_qty, cost=cost)
						pass
					else:
						self.item_demanded(item, qty_wanted - purchased_qty)
		elif item_type == 'Service':
			print('{}-{} trying to purchase Service: {}'.format(self.name, self.entity_id, item))
			result, req_time_required = counterparty.produce(item, qty, buffer=buffer)
			#print('Service purchase produce result: \n{}'.format(result))
			if not result:
				return
			try:
				self.adj_needs(item, qty)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				pass
			outcome, cost = self.transact(item, price=world.get_price(item, counterparty.entity_id), qty=qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=buffer)
			if outcome is None:
				outcome = []
			result += outcome
		#print('Purchase Result: {} {} \n{}'.format(qty, item, result))
		return result

	def gift(self, item, qty, counterparty, account=None):
		if item == 'Cash':
			price = 1
			# TODO Check if enough cash
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if cash >= price * qty:
				giftee_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Cash gift received from {}'.format(self.name), '', '', '', 'Cash', 'Gift', price * qty ]
				giftor_entry = [ ledger.get_event(), self.entity_id, world.now, 'Cash gift given to {}'.format(counterparty.name), '', '', '', 'Gift Expense', 'Cash', price * qty ]
				gift_event = [giftee_entry, giftor_entry]
				ledger.journal_entry(gift_event)
			else:
				print('{}-{} does not have enough cash to gift ${} to {}.'.format(self.name, self.entity_id, qty, counterparty.name))
		else:
			# TODO Fix accounting to not be at cost
			price = 1
			if account is None:
				account = 'Inventory' # TODO Support other accounts
			ledger.set_entity(self.entity_id)
			qty_held = ledger.get_qty(item, account)
			ledger.reset()
			if qty_held >= qty:
				ledger.set_entity(self.entity_id)
				print('{} getting historical cost of {} {} to gift.'.format(self.name, qty, item))
				cost_amt = ledger.hist_cost(qty, item, 'Inventory')#, v=True)
				ledger.reset()
				giftee_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Gift received from {}'.format(self.name), item, cost_amt / qty, qty, account, 'Gift', cost_amt ]
				giftor_entry = [ ledger.get_event(), self.entity_id, world.now, 'Gift given to {}'.format(counterparty.name), item, cost_amt / qty, qty, 'Gift Expense', account, cost_amt ]
				gift_event = [giftee_entry, giftor_entry]
				ledger.journal_entry(gift_event)
			else:
				print('{}-{} does not have enough {} to gift {} units to {}.'.format(self.name, self.entity_id, item, qty, counterparty.name))

	def consume(self, item, qty, need=None, buffer=False):
		if qty == 0:
			return
		ledger.set_entity(self.entity_id)
		qty_held = ledger.get_qty(items=item, accounts=['Inventory'])#, v=True)
		ledger.reset()
		print('{}-{} holds {} qty of {} and is looking to consume {} units.'.format(self.name, self.entity_id, qty_held, item, qty))
		# qty_held_orig = qty_held
		# if buffer:
		# 	qty_held = qty
		if qty_held >= qty:# or buffer:
			print('{}-{} consumes: {} {}'.format(self.name, self.entity_id, qty, item))
			# if qty_held_orig == 0 and buffer:
			# 	price = world.get_price(item)
			# 	cost = price * qty
			# else: # TODO Remove
			ledger.set_entity(self.entity_id)
			print('{}-{} getting historical cost of {} {}.'.format(self.name, self.entity_id, qty, item))
			cost = ledger.hist_cost(qty, item, 'Inventory')#, v=True)
			ledger.reset()
			#print('Cost: {}'.format(cost))
			price = cost / qty
			consume_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' consumed', item, price, qty, 'Goods Consumed', 'Inventory', cost ]
			consume_event = [consume_entry]
			if buffer:
				return consume_event
			ledger.journal_entry(consume_event)
			self.adj_needs(item, qty) # TODO Add error checking
			return
		else:
			print('{}-{} does not have enough {} on hand to consume {} units of {}.'.format(self.name, self.entity_id, item, qty, item))

	def in_use(self, item, qty, price, account, buffer=False):
		ledger.set_entity(self.entity_id)
		qty_held = ledger.get_qty(items=item, accounts=[account])
		ledger.reset()
		if (qty_held >= qty) or buffer:
			in_use_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' in use', item, price, qty, 'In Use', account, price * qty ]
			in_use_event = [in_use_entry]
			if buffer:
				return in_use_event
			ledger.journal_entry(in_use_event)
			try:
				self.adj_needs(item, qty)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				return True
		else:
			print('{}-{} does not have enough {} available to use.'.format(self.name, self.entity_id, item))

	def use_item(self, item, uses=1, counterparty=None, target=None, buffer=False, check=False):
		# TODO Add check to ensure entity has item they are using
		# TODO Add check to ensure counterparty has item being attacked
		if counterparty is not None and target is not None:
			if self.hours < MAX_HOURS:
				print('{} cannot attack this turn. Attacking requires {} full hours time.'.format(self.name, MAX_HOURS))
				return
			dmg = world.items['dmg'][item]
			if dmg is None:
				dmg = 0
			dmg = float(dmg)
			try:
				target = int(target)
			except ValueError:
				print('{} attempting to attack {} item held by {}'.format(self.name, target, counterparty.name))
			if isinstance(target, int):
				print('{} attempting to attack Entity ID: {}'.format(self.name, target))
				target = factory.get_by_id(target)
			if world.valid_item(target):
				dmg_type = world.items['dmg_type'][item] # Does not support more than one dmg_type on the attack
				if dmg_type is not None:
					res_types = [x.strip() for x in world.items['res_type'][target].split(',')]
					for i, res_type in enumerate(res_types):
						if res_type == dmg_type:
							break
					res = [x.strip() for x in world.items['res'][target].split(',')]
					res = list(map(float, res))
					resilience = res[i]
				else:
					resilience = world.items['res'][target]
				if resilience is None:
					resilience = 0
				resilience = float(resilience)
				print('{}-{} attacks with {} for {} damage against {} with resilience of {}.'.format(self.name, self.entity_id, item, dmg, target, resilience))
				reduction = dmg / resilience
				if reduction > 1:
					reduction = 1
				for n in range(uses):
					#target_type = world.get_item_type(target)
					ledger.set_entity(counterparty.entity_id)
					target_bal = ledger.balance_sheet(accounts=['Buildings','Equipment','Accumulated Depreciation','Accumulated Impairment Losses'], item=target)
					asset_cost = ledger.balance_sheet(accounts=['Buildings','Equipment'], item=target)
					print('Target Balance: {}'.format(target_bal))
					ledger.reset()
					impairment_amt = asset_cost * reduction
					if target_bal < impairment_amt:
						impairment_amt = target_bal
					counterparty.impairment(target, impairment_amt) # TODO Damage shouldn't be booked until fulfillment and depreciation is passed
				self.set_hours(MAX_HOURS)
			elif isinstance(target, Individual):
				ledger.default = None
				ledger.set_entity(target.entity_id)
				armour_qty = ledger.get_qty(items='Armour', accounts=['Equipment']) # TODO Fix this, only returning 0
				ledger.default = world.gov.get(ids=True)
				ledger.reset()
				print('Target Armour: {}'.format(armour_qty))
				if armour_qty < 0:
					resilience = world.items.loc['Armour', 'res']
					print('Target Armour: {} Resilience: {}'.format(armour_qty, resilience))
				else:
					resilience = 1
				need_delta = -( dmg / resilience )
				for need in world.global_needs:
					target.set_need(need, need_delta, attacked=True, v=True)
				print('{}-{} attacks with {} for {} damage against {}.'.format(self.name, self.entity_id, item, dmg, target))
			else:
				print('Cannot attack a {}.'.format(target))
				return

		# In both cases using the item still uses existing logic
		incomplete, use_event, time_required = self.fulfill(item, qty=uses, reqs='usage_req', amts='use_amount', check=check)
		# TODO Book journal entries within function and add buffer argument
		if incomplete or check: # TODO Exit early on check after depreciation
			return
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
						print('{}-{} could not use {} {} as requested; was used {} times.'.format(self.name, self.entity_id, item, orig_uses, uses))
				else:
					incomplete = True
		if incomplete or check: # TODO Add check to depreciation() to exit early on this check
			return
		try:
			self.adj_needs(item, uses)
		except AttributeError as e:
			#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
			pass
		if not use_event and not incomplete:
			#print('{} has no requirements in order to be used by {}-{}.'.format(item, self.name, self.entity_id))
			return True
		return use_event

	def check_productivity(self, item, v=False):
		ledger.set_entity(self.entity_id)
		equip_list = ledger.get_qty(accounts=['Equipment'])
		ledger.reset()
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
			print('{}-{} used {} equipment to do {} task better by {}.'.format(self.name, self.entity_id, equip_info['item_id'].iloc[0], item, modifier))
			return modifier, equip_info
		return None, None

	def fulfill(self, item, qty, reqs='requirements', amts='amount', man=False, check=False): # TODO Maybe add buffer=True
		v = False
		# TODO Determine the min amount possible to produce when incomplete
		try:
			if not self.gl_tmp.empty:
				# if item == 'Hydroponics' or item == 'Wire':
				# 	print('Tmp GL: \n{}'.format(self.gl_tmp.tail(10)))
				ledger.gl = self.gl_tmp
		except AttributeError as e:
			# if item == 'Hydroponics' or item == 'Wire':
			# 	print('No Tmp GL Error: {}'.format(repr(e)))
			pass
		incomplete = False
		if qty == 0:
			return None, [], None
		event = []
		time_required = False
		orig_hours = world.get_hours()
		if v: print('Orig Hours: \n{}'.format(orig_hours))
		item_info = world.items.loc[item]
		item_type = world.get_item_type(item)
		if v: print('Item Info: \n{}'.format(item_info))
		if item_info[reqs] is None or item_info[amts] is None:
			return None, [], None
		requirements = [x.strip() for x in item_info[reqs].split(',')]
		if v: print('Requirements: {}'.format(requirements))
		requirement_types = [world.get_item_type(requirement) for requirement in requirements]
		if v: print('Requirement Types: {}'.format(requirement_types))
		amounts = [x.strip() for x in item_info[amts].split(',')]
		amounts = list(map(float, amounts))
		if v: print('Requirement Amounts: {}'.format(amounts))
		requirements_details = list(itertools.zip_longest(requirements, requirement_types, amounts))
		if v: print('Requirements Details: {}'.format(requirements_details))
		# TODO Sort so requirements with a capacity are first after time
		for requirement in requirements_details:
			ledger.set_entity(self.entity_id)
			req_item = requirement[0]
			req_item_type = requirement[1]
			req_qty = requirement[2]
			if req_qty is None:
				req_qty = 1
			if v: print('Requirement: {}'.format(requirement))

			if req_item_type == 'Time':
				# TODO Consider how Equipment could reduce time requirements
				time_required = True
				if v: print('Time Required: {}'.format(time_required))

			elif req_item_type == 'Land':
				modifier, items_info = self.check_productivity(req_item)
				ledger.set_entity(self.entity_id)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl.loc[ledger.gl['entity_id'] == self.entity_id]
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
				else:
					modifier = 0
				try:
					if not self.gl_tmp.empty:
						# print('Tmp GL land: \n{}'.format(self.gl_tmp.tail()))
						ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
				except AttributeError as e:
					# print('No Tmp GL Error land: {}'.format(repr(e)))
					pass
				land = ledger.get_qty(items=req_item, accounts=['Land'])
				print('{}-{} requires {} {} to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty * (1-modifier) * qty, req_item, qty, item, land))
				if land < (req_qty * (1-modifier) * qty):
					needed_qty = (req_qty * (1-modifier) * qty) - land
					print('{}-{} requires {} m^2 more {} to produce {} on.'.
						format(self.name, self.entity_id, needed_qty, req_item, item))
					# Attempt to purchase land
					if not man:
						result = self.purchase(req_item, needed_qty, 'Land')#, buffer=True)
						if not result:
							ledger.set_entity(world.env.entity_id) # Only try to claim land that is remaining
							try:
								if not self.gl_tmp.empty:
									# print('Tmp GL land claim: \n{}'.format(self.gl_tmp.tail()))
									ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
							except AttributeError as e:
								# print('No Tmp GL Error land claim: {}'.format(repr(e)))
								pass
							land_avail = ledger.get_qty(items=req_item, accounts=['Land'])
							# print('Land Available: {}'.format(land_avail))
							ledger.reset()
							ledger.set_entity(self.entity_id)
							qty_claim = int(min(needed_qty, land_avail))
							result = self.claim_land(qty_claim, price=world.get_price(req_item, world.env.entity_id), item=req_item)#, buffer=True)
							# print('Land Claim Result: \n{}'.format(result))
							if not result:
								incomplete = True
					else:
						incomplete = True
				if (time_required or item_type == 'Buildings' or item_type == 'Equipment') and not incomplete: # TODO Handle land in use during one tick
					entries = self.in_use(req_item, req_qty * (1-modifier) * qty, world.get_price(req_item, self.entity_id), 'Land', buffer=True)
					#print('Land In Use Entries: \n{}'.format(entries))
					if not entries:
						entries = []
						incomplete = True
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))

			elif req_item_type == 'Buildings':
				modifier, items_info = self.check_productivity(req_item)
				ledger.set_entity(self.entity_id)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
				else:
					modifier = 0
				building = ledger.get_qty(items=req_item, accounts=['Buildings'])
				# Get capacity amount
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None:
					capacity = 1
				capacity = float(capacity)
				print('{}-{} requires {} {} building (Capacity: {}) to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty, req_item, capacity, qty, item, building))
				if ((building * capacity) / (qty * (1-modifier) * req_qty)) < 1:
					ledger.reset()
					building_wip = ledger.get_qty(items=req_item, accounts=['Building Under Construction'])
					ledger.set_entity(self.entity_id)
					print('{} building under construction: {}'.format(req_item, building_wip))
					building += building_wip
					if ((building * capacity) / (qty * (1-modifier) * req_qty)) < 1:
						remaining_qty = max((qty * (1-modifier) * req_qty) - (building * capacity), 0)
						required_qty = int(math.ceil(remaining_qty / capacity))
						if building == 0:
							print('{}-{} does not have any {} building and requires {}.'.format(self.name, self.entity_id, req_item, required_qty))
						else:
							print('{}-{} does not have enough capacity in {} building and requires {}.'.format(self.name, self.entity_id, req_item, required_qty))
						if not man:
							# Attempt to purchase before producing self if makes sense
							result = self.purchase(req_item, required_qty, acct_buy='Buildings')#, wip_acct='Building Under Construction')
							req_time_required = False
							if not result:
								print('{}-{} will attempt to produce {} {} itself.'.format(self.name, self.entity_id, required_qty, req_item))
								result, req_time_required = self.produce(req_item, required_qty, debit_acct='Buildings')#, buffer=True)
							if not result or req_time_required:
								if req_time_required:
									print('{}-{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, self.entity_id, item, req_item))
								incomplete = True
						else:
							incomplete = True
					else:
						print('{}-{} cannot complete {} now due to requiring time to produce {}.'.format(self.name, self.entity_id, item, req_item))
						incomplete = True
				building = ledger.get_qty(items=req_item, accounts=['Buildings'])
				qty_to_use = 0
				if building != 0:
					qty_to_use = int(min(building, int(math.ceil((qty * (1-modifier) * req_qty) / (building * capacity)))))
					print('{}-{} needs to use {} {} times to produce {}.'.format(self.name, self.entity_id, req_item, qty_to_use, item))
				if time_required: # TODO Handle building in use during one tick and handle building capacity
					entries = self.in_use(req_item, qty_to_use, world.get_price(req_item, self.entity_id), 'Buildings', buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
				for _ in range(qty_to_use):
					entries = self.use_item(req_item, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))

			elif req_item_type == 'Equipment': # TODO Make generic for process
				modifier, items_info = self.check_productivity(req_item)
				ledger.set_entity(self.entity_id)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
				else:
					modifier = 0
				equip_qty = ledger.get_qty(items=req_item, accounts=['Equipment'])
				# Get capacity amount
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None:
					capacity = 1
				capacity = float(capacity)
				print('{}-{} requires {} {} equipment (Capacity: {}) to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty, req_item, capacity, qty, item, equip_qty))
				if ((equip_qty * capacity) / (qty * (1-modifier) * req_qty)) < 1: # TODO Test item with capacity
					ledger.reset()
					equip_qty_wip = ledger.get_qty(items=req_item, accounts=['WIP Equipment'])
					ledger.set_entity(self.entity_id)
					print('{} equipment being manufactured: {}'.format(req_item, equip_qty_wip))
					equip_qty += equip_qty_wip
					if ((equip_qty * capacity) / (qty * (1-modifier) * req_qty)) < 1: # TODO Fix this
						remaining_qty = max((qty * (1-modifier) * req_qty) - (equip_qty * capacity), 0)
						required_qty = int(math.ceil(remaining_qty / capacity))
						if equip_qty == 0:
							print('{}-{} does not have any {} equipment and requires {}.'.format(self.name, self.entity_id, req_item, required_qty))
						else:
							print('{}-{} does not have enough capacity on {} equipment and requires {}.'.format(self.name, self.entity_id, req_item, required_qty))
						if not man:
							# Attempt to purchase before producing self if makes sense
							result = self.purchase(req_item, required_qty, acct_buy='Equipment')#, wip_acct='WIP Equipment')
							req_time_required = False
							if not result:
								print('{}-{} will attempt to produce {} {} itself.'.format(self.name, self.entity_id, required_qty, req_item))
								result, req_time_required = self.produce(req_item, required_qty, debit_acct='Equipment')#, buffer=True)
							if not result or req_time_required:
								if req_time_required:
									print('{}-{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, self.entity_id, item, req_item))
								incomplete = True
						else:
							incomplete = True
					else:
						print('{}-{} cannot complete {} now due to requiring time to produce {}.'.format(self.name, self.entity_id, item, req_item))
						incomplete = True
				equip_qty = ledger.get_qty(items=req_item, accounts=['Equipment'])
				qty_to_use = 0
				if equip_qty != 0:
					qty_to_use = int(min(equip_qty, int(math.ceil((qty * (1-modifier) * req_qty) / (equip_qty * capacity)))))
				if time_required: # TODO Handle equipment in use during only one tick
					entries = self.in_use(req_item, qty_to_use, world.get_price(req_item, self.entity_id), 'Equipment', buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
				for _ in range(qty_to_use):
					entries = self.use_item(req_item, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))

			elif req_item_type == 'Components':
				modifier, items_info = self.check_productivity(req_item)
				ledger.set_entity(self.entity_id)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
				else:
					modifier = 0
				try:
					if not self.gl_tmp.empty:
						# print('Tmp GL components: \n{}'.format(self.gl_tmp.tail()))
						ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
				except AttributeError as e:
					# print('No Tmp GL Error components: {}'.format(repr(e)))
					pass
				component_qty = ledger.get_qty(items=req_item, accounts=['Components'])
				print('{}-{} requires {} {} components to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty * (1-modifier) * qty, req_item, qty, item, component_qty))
				if component_qty < (req_qty * (1-modifier) * qty):
					print('{}-{} does not have enough {} components. Will attempt to aquire some.'.format(self.name, self.entity_id, req_item))
					if not man:
						# Attempt to purchase before producing self if makes sense
						result = self.purchase(req_item, req_qty * qty, 'Inventory')#, buffer=True)
						req_time_required = False
						if not result:
							print('{}-{} will attempt to produce {} {} itself.'.format(self.name, self.entity_id, req_qty * qty, req_item))
							result, req_time_required = self.produce(req_item, req_qty * qty)#, buffer=True)
						if not result or req_time_required:
							if req_time_required:
								print('{}-{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, self.entity_id, item, req_item))
							incomplete = True
					else:
						incomplete = True
				if not check:
					entries = self.consume(req_item, qty=req_qty * qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))

			elif req_item_type == 'Commodity':
				modifier, items_info = self.check_productivity(req_item)
				ledger.set_entity(self.entity_id)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
					if entries is True:
						entries = []
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# if item == 'Hydroponics' or item == 'Wire':
						# 	print('Ledger Temp commodity: \n{}'.format(ledger.gl.tail(10)))
				else:
					modifier = 0
				try:
					if not self.gl_tmp.empty:
						# if item == 'Hydroponics' or item == 'Wire':
						# 	print('Tmp GL commodity: \n{}'.format(self.gl_tmp.tail(10)))
						ledger.gl = self.gl_tmp.loc[self.gl_tmp['entity_id'] == self.entity_id]
				except AttributeError as e:
					# if item == 'Hydroponics' or item == 'Wire':
					# 	print('No Tmp GL Error commodity: {}'.format(repr(e)))
					pass
				material_qty_held = ledger.get_qty(items=req_item, accounts=['Inventory'])#, v=True)
				print('{}-{} requires {} {} commodity to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty * (1-modifier) * qty, req_item, qty, item, material_qty_held))
				qty_needed = max((req_qty * (1 - modifier) * qty) - material_qty_held, 0)
				if qty_needed > 0:
					print('{}-{} does not have enough {} commodity and requires {} more units.'.format(self.name, self.entity_id, req_item, qty_needed))
					# TODO Maybe add logic so that produces wont try and purchase items they can produce
					if not man:
						# Attempt to purchase before producing
						result = self.purchase(req_item, qty_needed, 'Inventory')#, buffer=True)
						partial = False
						if result:
							purchase_entries = pd.DataFrame(result, columns=world.cols, index=None)
							#print('Purchase Entries: \n{}'.format(purchase_entries))
							purchase_entries = purchase_entries.loc[purchase_entries['entity_id'] == self.entity_id]
							purchased_qty = purchase_entries['qty'].sum()
							if purchased_qty < qty_needed:#result[0][6]
								print('{}-{} could only purchase {} of {} required.'.format(self.name, self.entity_id, purchased_qty, qty_needed))
								#incomplete = True # TODO Decide how best to handle when not enough qty is available to be purchased
								partial = True
								qty_needed = max(qty_needed - purchased_qty, 0)
						req_time_required = False
						if not result or partial:
							print('{}-{} will attempt to produce {} {} itself.'.format(self.name, self.entity_id, qty_needed, req_item))
							result, req_time_required = self.produce(req_item, qty_needed)#, buffer=True)
						if not result or req_time_required:
							if req_time_required:
								print('{}-{} cannot complete {} now due to {} requiring time to produce.'.format(self.name, self.entity_id, item, req_item))
							incomplete = True
					else:
						incomplete = True
				if not check:
					entries = self.consume(req_item, qty=req_qty * qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
					event += entries
					if entries:
						for entry in entries:
							entries_df = pd.DataFrame([entry], columns=world.cols)
							ledger.gl = ledger.gl.append(entries_df)
						self.gl_tmp = ledger.gl
						# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))

			elif req_item_type == 'Service':
				print('{}-{} will attempt to purchase the {} service to produce {} {}.'.format(self.name, self.entity_id, req_item, qty, item))
				entries = self.purchase(req_item, req_qty * qty, buffer=True)
				if not entries:
					print('{}-{} will attempt to produce {} {} itself.'.format(self.name, self.entity_id, req_qty * qty, req_item))
					entries, req_time_required = self.produce(req_item, req_qty * qty, buffer=True) # TODO Consider if man switch needed
				if not entries: # TODO Consider if Time requirement can be handled like above
					entries = []
					incomplete = True
				event += entries
				if entries:
					for entry in entries:
						entries_df = pd.DataFrame([entry], columns=world.cols)
						ledger.gl = ledger.gl.append(entries_df)
					self.gl_tmp = ledger.gl
					# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))

			elif req_item_type == 'Subscription': # TODO Add check to ensure payment has been made recently (maybe on day of)
				subscription_state = ledger.get_qty(items=req_item, accounts=['Subscription Info'])
				print('{}-{} requires {} {} subscription to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty * (1-modifier) * qty, req_item, qty, item, subscription_state))
				if not subscription_state:
					print('{}-{} does not have {} subscription active. Will attempt to activate it.'.format(self.name, self.entity_id, req_item))
					if not man:
						counterparty = self.subscription_counterparty(req_item)
						entries = self.order_subscription(item=req_item, counterparty=counterparty, price=world.get_price(req_item, counterparty.entity_id), qty=1, buffer=True)
						if not entries:
							entries = []
							incomplete = True
						event += entries
						if entries:
							for entry in entries:
								entries_df = pd.DataFrame([entry], columns=world.cols)
								ledger.gl = ledger.gl.append(entries_df)
							self.gl_tmp = ledger.gl
							# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
					else:
						incomplete = True

			elif req_item_type == 'Job':
				if item_type == 'Job' or item_type == 'Labour':
					if type(self) == Individual:
						experience = abs(ledger.get_qty(items=req_item, accounts=['Salary Income']))
						if experience < req_qty:
							incomplete = True
							# TODO Add to demand table
							return incomplete, event, time_required
				else:
					workers = ledger.get_qty(items=req_item, accounts=['Worker Info'])
					if v: print('Workers as {}: {}'.format(req_item, worker_state))
					# Get capacity amount
					capacity = world.items.loc[req_item, 'capacity']
					if capacity is None:
						capacity = 1
					capacity = float(capacity)
					print('{}-{} has {} {} available with {} capacity each to produce {} {}.'.format(self.name, self.entity_id, workers, req_item, capacity, qty, item))
					if ((workers * capacity) / (qty * req_qty)) < 1:
						remaining_qty = (qty * req_qty) - (workers * capacity)
						required_qty = int(math.ceil(remaining_qty / capacity))
						if not man:
							if workers <= 0:
								print('{}-{} does not have a {} available to work. Will attempt to hire {}.'.format(self.name, self.entity_id, req_item, required_qty))
							else:
								print('{}-{} does not have enough capacity for {} jobs. Will attempt to hire {}.'.format(self.name, self.entity_id, req_item, required_qty))
							for _ in range(required_qty):
								entries = self.hire_worker(job=req_item, qty=1, man=man, buffer=True)
								if not entries:
									entries = []
									incomplete = True
								event += entries
								if entries:
									for entry in entries:
										entries_df = pd.DataFrame([entry], columns=world.cols)
										ledger.gl = ledger.gl.append(entries_df)
										self.gl_tmp = ledger.gl
									# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
						else:
							incomplete = True

			elif req_item_type == 'Labour':
				if item_type == 'Job' or item_type == 'Labour':
					if type(self) == Individual:
						experience = abs(ledger.get_qty(items=req_item, accounts=['Wages Income']))
						if experience < req_qty:
							incomplete = True
							# TODO Add to demand table maybe
							return incomplete, event, time_required
				else:
					modifier, items_info = self.check_productivity(req_item)
					ledger.set_entity(self.entity_id)
					if modifier:
						entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
						if not entries:
							entries = []
							incomplete = True
						if entries is True:
							entries = []
						event += entries
						if entries:
							for entry in entries:
								entries_df = pd.DataFrame([entry], columns=world.cols)
								ledger.gl = ledger.gl.append(entries_df)
							self.gl_tmp = ledger.gl
							# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
					else:
						modifier = 0
					ledger.set_start_date(str(world.now))
					labour_done = ledger.get_qty(items=req_item, accounts=['Wages Expense'])
					ledger.reset()
					ledger.set_entity(self.entity_id)
					print('{}-{} requires {} {} labour to produce {} {} and has: {}'.format(self.name, self.entity_id, req_qty * (1-modifier) * qty, req_item, qty, item, labour_done))
					labour_required = (req_qty * (1-modifier) * qty)
					# Labourer does the amount they can, and get that value from the entries. Then add to the labour hours done and try again
					while labour_done < labour_required:
						required_hours = int(math.ceil((req_qty * (1-modifier) * qty) - labour_done))
						if item_type == 'Education':
							print('{}-{} has not studied enough {} today. Will attempt to study for {} hours.'.format(self.name, self.entity_id, req_item, required_hours)) #MAX_HOURS = 12
							required_hours = min(required_hours, MAX_HOURS)
							counterparty = self
							entries = self.accru_wages(job=req_item, counterparty=counterparty, labour_hours=required_hours, wage=0, buffer=True)
						else:
							print('{}-{} has not had enough {} labour done today to produce {} {}.\n{}-{} will attempt to hire a {} for {} hours.'.format(self.name, self.entity_id, req_item, qty, item, self.name, self.entity_id, req_item, required_hours))
							counterparty = self.worker_counterparty(req_item, man=man)
							if isinstance(counterparty, tuple):
								counterparty, entries = counterparty
								event += entries
								if entries:
									for entry in entries:
										entries_df = pd.DataFrame([entry], columns=world.cols)
										ledger.gl = ledger.gl.append(entries_df)
									self.gl_tmp = ledger.gl
									# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
							entries = self.accru_wages(job=req_item, counterparty=counterparty, labour_hours=required_hours, buffer=True)
						if not entries:
							entries = []
							incomplete = True
							if item_type != 'Education':
								#print('World Demand Before: \n{}'.format(world.demand))
								demand_count = world.demand.loc[world.demand['item_id'] == item].shape[0]
								print('Demand Count Buckets for {}: {}'.format(item, demand_count))
								if demand_count:
									qty_possible = max(int(math.floor(labour_done / (req_qty * (1-modifier)))), 1)
									qty_poss_bucket = max(int(math.ceil(qty_possible // demand_count)), 1)
									# TODO Better handle zero remaining when qty_poss_bucket is also 1
									qty_poss_remain = qty_possible % qty_poss_bucket
									print('Labour Done for {}: {} | Qty Possible for {}: {} | '.format(req_item, labour_done, item, qty_possible))
									print('Qty Poss. per Bucket: {} | Qty Poss. Remain: {}'.format(qty_poss_bucket, qty_poss_remain))
									world.demand.loc[world.demand['item_id'] == item, 'qty'] = qty_poss_bucket
									for i, row in world.demand.iterrows():
										if row['item_id'] == item:
											break
									world.demand.at[i, 'qty'] = qty_poss_bucket + qty_poss_remain
									world.demand.loc[world.demand['item_id'] == item, 'reason'] = 'labour'
									world.set_table(world.demand, 'demand')
									print('{}-{} adjusted {} on demand list due to labour constraint.'.format(self.name, self.entity_id, item))
									#print(time_stamp() + 'World Demand After: \n{}'.format(world.demand))
							break
						event += entries
						if entries:
							for entry in entries:
								entries_df = pd.DataFrame([entry], columns=world.cols)
								ledger.gl = ledger.gl.append(entries_df)
							self.gl_tmp = ledger.gl
							# print('Ledger Temp: \n{}'.format(ledger.gl.tail()))
						if entries:
							labour_done += entries[0][6] # Same as required_hours
							counterparty.set_hours(required_hours)
							if item_type == 'Education':
								break

			elif req_item_type == 'Education':
				if item_type == 'Job' or item_type == 'Labour':
					if type(self) == Individual:
						edu_status = ledger.get_qty(items=req_item, accounts=['Education'])
						edu_status_wip = ledger.get_qty(items=req_item, accounts=['Studying Education'])
						req_qty = int(req_qty)
						print('{}-{} has {} education hours for {} and requires {} to learn {}.'.format(self.name, self.entity_id, edu_status, req_item, req_qty, item))
						if edu_status >= req_qty:
							print('{}-{} has knowledge of {} to create {}.'.format(self.name, self.entity_id, req_item, item))
						elif edu_status + edu_status_wip >= req_qty:
							print('{}-{} is working on knowledge of {} to create {}.'.format(self.name, self.entity_id, req_item, item))
						else:
							if not man:
								print('Studying Education: {}'.format(req_item))
								req_time_required = False
								result, req_time_required = self.produce(req_item, qty=req_qty)#, buffer=True)
								if req_time_required:
									edu_status = ledger.get_qty(items=req_item, accounts=['Studying Education'])
									if edu_status == 0:
										self.item_demanded(req_item, req_qty)
								if not result:
									print('Studying Education not successfull for: {}'.format(req_item))
									#entries = []
									incomplete = True
									edu_status = ledger.get_qty(items=req_item, accounts=['Studying Education'])
									if edu_status == 0 and not req_time_required:
										self.item_demanded(req_item, req_qty)
								else:
									edu_status = ledger.get_qty(items=req_item, accounts=['Education'])
									print('Education Status for {}: {}'.format(req_item, edu_status))
									if edu_status == 0:
										#entries = []
										incomplete = True
							else:
								incomplete = True

			elif req_item_type == 'Technology':
				ledger.reset()
				tech_done_status = ledger.get_qty(items=req_item, accounts=['Technology'])
				tech_status_wip = ledger.get_qty(items=req_item, accounts=['Researching Technology'])
				tech_status = tech_done_status + tech_status_wip
				if tech_done_status >= req_qty:
					print('{}-{} has knowledge of {} technology to create {}.'.format(self.name, self.entity_id, req_item, item))
				elif (tech_done_status + tech_status_wip) >= req_qty:
					print('{}-{} is working on knowledge of {} technology to create {}.'.format(self.name, self.entity_id, req_item, item))
					incomplete = True
				else:
					if not man:
						print('{}-{} attempting to research technology: {}'.format(self.name, self.entity_id, req_item))
						req_time_required = False
						result, req_time_required = self.produce(req_item, qty=req_qty)#, buffer=True)
						if req_time_required:
							tech_status = ledger.get_qty(items=req_item, accounts=['Researching Technology'])
							if tech_status == 0:
								self.item_demanded(req_item, req_qty)
							else:
								print('{}-{} researching technology: {}'.format(self.name, self.entity_id, req_item))
						if not result:
							print('{}-{} technology researching not successfull for: {}'.format(self.name, self.entity_id, req_item))
							#entries = []
							incomplete = True
							tech_status = ledger.get_qty(items=req_item, accounts=['Researching Technology'])
							if tech_status == 0 and not req_time_required:
								self.item_demanded(req_item, req_qty)
						else:
							tech_status = ledger.get_qty(items=req_item, accounts=['Technology'])
							print('{}-{} technology status for {}: {}'.format(self.name, self.entity_id, req_item, tech_status))
							if tech_status == 0:
								#entries = []
								incomplete = True
					else:
						incomplete = True

			ledger.reset()
		if incomplete:
			for individual in world.gov.get(Individual):
				if v: print('Reset hours for {} from {} to {}.'.format(individual.name, individual.hours, orig_hours[individual.name]))
				individual.hours = orig_hours[individual.name]
			print('{}-{} cannot produce {} {} at this time.\n'.format(self.name, self.entity_id, qty, item))
		self.gl_tmp = pd.DataFrame()
		return incomplete, event, time_required

	def produce(self, item, qty, debit_acct=None, credit_acct=None, desc=None , price=None, man=False, buffer=False, v=False):
		if not args.user:
			if item not in self.produces: # TODO Should this be kept long term?
				return [], False
		incomplete, produce_event, time_required = self.fulfill(item, qty, man=man)
		if incomplete:
			return [], time_required
		item_type = world.get_item_type(item)
		#print('Item Type: {}'.format(item_type))
		if debit_acct is None:
			if item_type == 'Technology':
				debit_acct = 'Technology'
			elif item_type == 'Education':
				debit_acct = 'Education'
			elif item_type == 'Equipment':
				debit_acct = 'Inventory'
			elif item_type == 'Buildings':
				debit_acct = 'Inventory'#'Buildings'
			else:
				debit_acct = 'Inventory'
			if time_required:
				if item_type == 'Technology':
					debit_acct = 'Researching Technology'
				elif item_type == 'Education':
					debit_acct='Studying Education'
				elif item_type == 'Equipment':
					debit_acct = 'WIP Inventory'#'WIP Equipment'
				elif item_type == 'Buildings':
					debit_acct = 'WIP Inventory'#'Building Under Construction'
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
				desc = item + ' manufactured'
				if time_required:
					desc = 'Manufacturing ' + item
			elif item_type == 'Buildings':
				desc = item + ' constructed'
				if time_required:
					desc = 'Constructing ' + item
			else:
				desc = item + ' produced'
				if time_required:
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
			ledger.set_entity(self.entity_id)
			# Find last Cost Pool entry
			cost_pool_gls = ledger.gl.loc[ledger.gl['debit_acct'] == 'Cost Pool']
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	if v: print('Cost Pool TXNs: \n{}'.format(cost_pool_gls))
			if not cost_pool_gls.empty and type(self) != Individual:
				last_txn = cost_pool_gls.index.values[-1]
				# if v: print('Last Cost Pool TXN: {}'.format(last_txn))
				# Filter for all entries since then
				ledger.set_start_txn(last_txn)
				recent_gls = ledger.gl
				recent_gls['debit_acct_type'] = recent_gls.apply(lambda x: ledger.get_acct_elem(x['debit_acct']), axis=1)
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	if v: print('Recent GLs Acct Type: \n{}'.format(recent_gls))
				# Filter for expense entries
				indirect_costs = recent_gls.loc[recent_gls['debit_acct_type'] == 'Expense']
				indirect_costs = indirect_costs.loc[indirect_costs['debit_acct'] != 'Cost of Goods Sold']
				indirect_costs = indirect_costs.loc[indirect_costs['debit_acct'] != 'Dividend Expense'] # TODO Divs should not be an expense
				# Do logic like below
				cost += indirect_costs['amount'].sum()
				indirect_costs.drop('debit_acct_type', axis=1, inplace=True)
				#print('Cost DF: \n{}'.format(indirect_costs))
				# if v: print('Indirect Cost: {}'.format(cost))
				indirect_costs = indirect_costs[['event_id', 'entity_id', 'date', 'description', 'item_id', 'price', 'qty', 'credit_acct', 'debit_acct', 'amount']]
				#print('Cost DF After Swap: \n{}'.format(indirect_costs))
				indirect_costs.rename({'debit_acct': 'credit_acct', 'credit_acct': 'debit_acct'}, axis='columns', inplace=True)
				#print('Cost DF After Rename: \n{}'.format(indirect_costs))
				indirect_costs.debit_acct = 'Cost Pool'
				indirect_costs['qty'] = indirect_costs['qty'].fillna('')
				indirect_costs['price'] = indirect_costs['price'].fillna('')
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	if v: print('Indirect Cost DF End: \n{}'.format(indirect_costs))
				indirect_cost_entries = indirect_costs.values.tolist()
				# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				# 	if v: print('Indirect Cost Entries: \n{}'.format(indirect_cost_entries))
				if item_type != 'Service':
					produce_event += indirect_cost_entries
			ledger.reset()

			cost_df = pd.DataFrame(produce_event, columns=world.cols)
			cost_df = cost_df.loc[cost_df['entity_id'] == self.entity_id]
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				if v: print('Cost DF Start: \n{}'.format(cost_df))
			if not cost_df.empty:
				cost_df['debit_acct_type'] = cost_df.apply(lambda x: ledger.get_acct_elem(x['debit_acct']), axis=1)
				with pd.option_context('display.max_rows', None, 'display.max_columns', None):
					if v: print('Cost DF Acct Type: \n{}'.format(cost_df))
				cost_df = cost_df.loc[cost_df['debit_acct_type'] == 'Expense']
				if not cost_df.empty:
					cost += cost_df['amount'].sum()
					cost_df.drop('debit_acct_type', axis=1, inplace=True)
					#print('Cost DF: \n{}'.format(cost_df))
					#print('Cost Price: {}'.format(cost))
					cost_df = cost_df[['event_id', 'entity_id', 'date', 'description', 'item_id', 'price', 'qty', 'credit_acct', 'debit_acct', 'amount']]
					#print('Cost DF After Swap: \n{}'.format(cost_df))
					cost_df.rename({'debit_acct': 'credit_acct', 'credit_acct': 'debit_acct'}, axis='columns', inplace=True)
					#print('Cost DF After Rename: \n{}'.format(cost_df))
					cost_df.debit_acct = 'Cost Pool'
					with pd.option_context('display.max_rows', None, 'display.max_columns', None):
						if v: print('Cost DF End: \n{}'.format(cost_df))
					cost_entries = cost_df.values.tolist()
					with pd.option_context('display.max_rows', None, 'display.max_columns', None):
						if v: print('Cost Entries: \n{}'.format(cost_entries))
					if item_type != 'Service':
						produce_event += cost_entries
					if v: print('Cost 1: {}'.format(cost))
			price = cost / qty
			if price == 0: # No cost
				price = world.get_price(item, self.entity_id)
				cost = price * qty
		else:
			cost = price * qty
		if item_type != 'Service':
			if cost_entries[0]:
				credit_acct = 'Cost Pool'
			produce_entry = [ ledger.get_event(), self.entity_id, world.now, desc, item, price, qty, debit_acct, credit_acct, cost ]
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
				byproduct_entry = [ ledger.get_event(), self.entity_id, world.now, desc, byproduct, by_price, byproduct_amt * qty, debit_acct, credit_acct, by_price * byproduct_amt * qty ]
				if byproduct_entry:
					produce_event += [byproduct_entry]

		if item_type == 'Technology':
			current_demand = world.demand[(world.demand['item_id'] == item) & (world.demand['qty'] == qty)]
		else:
			current_demand = world.demand[(world.demand['entity_id'] == self.entity_id) & (world.demand['item_id'] == item) & (world.demand['qty'] == qty)]
		if not current_demand.empty:
			to_drop = current_demand.index.tolist()
			world.demand = world.demand.drop(to_drop).reset_index(drop=True)
			world.set_table(world.demand, 'demand')
			print('{} exists on the demand table will drop index items {}.'.format(item, to_drop))
		if buffer:
			return produce_event, time_required
		ledger.journal_entry(produce_event)
		if produce_event[-1][-3] == 'Inventory':
			self.set_price(item, qty)
		else:
			self.set_price(item, qty, at_cost=True)
		return True, time_required

	def set_produce(self, item, qty, freq=0):
		# TODO Maybe make multindex with item_id and entity_id
		current_pro_queue = world.produce_queue.loc[(world.produce_queue['item_id'] == item) & (world.produce_queue['entity_id'] == self.entity_id)]
		if not current_pro_queue.empty:
			print('This item exists on the production queue as: \n{}'.format(current_pro_queue))
			print('It will be replaced with the new values below: ')
		world.produce_queue = world.produce_queue.append({'item_id':item, 'entity_id':self.entity_id, 'qty':qty, 'freq':freq, 'last':freq}, ignore_index=True)
		world.produce_queue = pd.concat([world.produce_queue, current_pro_queue]).drop_duplicates(keep=False) # TODO There may be a better way to get the difference between two dfs
		world.set_table(world.produce_queue, 'produce_queue')
		print('Set Produce Queue by {}: \n{}'.format(self.name, world.produce_queue))

	def auto_produce(self):
		if world.produce_queue.empty:
			return
		entity_pro_queue = world.produce_queue.loc[world.produce_queue['entity_id'] == self.entity_id]
		for index, que_item in entity_pro_queue.iterrows():
			if que_item['last'] == 0:
				result, time_required = self.produce(que_item['item_id'], que_item['qty'])
				if result:
					world.produce_queue.loc[(world.produce_queue['item_id'] == que_item['item_id']) & (world.produce_queue['entity_id'] == que_item['entity_id']), 'last'] = que_item['freq']
			else:
				world.produce_queue.loc[(world.produce_queue['item_id'] == que_item['item_id']) & (world.produce_queue['entity_id'] == que_item['entity_id']), 'last'] -= 1
		world.set_table(world.produce_queue, 'produce_queue')

	def wip_check(self, check=False, v=False):
		ledger.refresh_ledger()
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of WIP txns for different item types
		wip_txns = ledger.gl[(ledger.gl['debit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (ledger.gl['entity_id'] == self.entity_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		if v: print('WIP TXNs: \n{}'.format(wip_txns))
		if not wip_txns.empty:
			#print('WIP Transactions: \n{}'.format(wip_txns))
			# Compare the gl dates to the WIP time from the items table
			#items_time = world.items[world.items['requirements'].str.contains('Time', na=False)]
			items_continuous = world.items[world.items['freq'].str.contains('continuous', na=False)]
			for index, wip_lot in wip_txns.iterrows():
				wip_event = []
				item = wip_lot.loc['item_id']
				# item_type = world.get_item_type(item)
				# if item == 'Food':
				# 	v = True
				if v: print('WIP Item Check: {}'.format(item))
				#if v: print('Continuous Items: \n{}'.format(items_continuous))
				requirements = world.items.loc[item, 'requirements']
				if isinstance(requirements, str):
					requirements = [x.strip() for x in requirements.split(',')]
				requirements = list(filter(None, requirements))
				if v: print('WIP Requirements for {}: {}'.format(item, requirements))
				# if v: print('WIP Requirements for {}: {}'.format(item, requirements))
				for i, requirement in enumerate(requirements):
					requirement_type = world.get_item_type(requirement)
					if v: print('Requirement Timespan: {} | {}'.format(requirement, i))
					if requirement_type == 'Time':
						break
				if v: print('Time Requirement: {}'.format(requirement))
				#amounts = [x.strip() for x in items_time['amount'][item].split(',')]
				amounts = world.items.loc[item, 'amount']
				if isinstance(amounts, str):
					amounts = [x.strip() for x in amounts.split(',')]
				amounts = list(map(float, amounts))
				if v: print('Amounts: {}'.format(amounts))
				timespan = amounts[i]
				date_done = (datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=timespan)).date()
				days_left = (date_done - world.now).days
				if days_left < 0:
					continue
				for equip_requirement in requirements:
					if v: print('Requirement: {}'.format(equip_requirement))
					if equip_requirement in items_continuous.index.values:
						result = self.use_item(equip_requirement, check=check)
						if not result and not check:
							print('{}-{} WIP Progress for {} was not successfull.'.format(self.name, self.entity_id, item))
							if world.delay.empty:
								world.delay = world.delay.append({'txn_id':index, 'delay': 1}, ignore_index=True)
								world.set_table(world.delay, 'delay')
							elif index in world.delay['txn_id'].values:
								world.delay.loc[world.delay['txn_id'] == index, 'delay'] += 1
								world.set_table(world.delay, 'delay')
							else:
								world.delay = world.delay.append({'txn_id':index, 'delay': 1}, ignore_index=True)
								world.set_table(world.delay, 'delay')
							return
				start_date = datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d').date()
				if v: print('Start Date: {}'.format(start_date))
				ledger.set_date(str(start_date))
				modifier, items_info = self.check_productivity(requirement)
				if v: print('Modifier: {}'.format(modifier))
				ledger.reset()
				ledger.set_entity(self.entity_id)
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
				ledger.reset()
				if v: print('Modifier End: {}'.format(modifier))
				timespan = timespan * (1 - modifier)
				if check:
					continue
				delay = 0
				if not world.delay.empty:
					try:
						delay = world.delay.loc[world.delay['txn_id'] == index, 'delay'].values[0]
						print('{} delayed by {} days.'.format(item, delay))
					except KeyError as e:
						delay = 0
				if v: print('WIP lifespan for {}: {}'.format(item, timespan))
				timespan += delay
				if v: print('WIP lifespan with delay of {} for {}: {}'.format(item, delay, timespan))
				date_done = (datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=timespan)).date()
				if v: print('WIP date done for {}: {} Today is: {}'.format(item, date_done, world.now))
				days_left = abs(date_done - world.now).days
				if days_left < timespan:
					print('{}-{} has {} WIP days left for {}.'.format(self.name, self.entity_id, days_left, item))
				# If the time elapsed has passed
				if date_done == world.now:
					if v: print('WIP date is done for {}: {} Today is: {}'.format(item, date_done, world.now))
					# Undo "in use" entries for related items
					release_txns = ledger.gl[(ledger.gl['credit_acct'] == 'In Use') & (ledger.gl['entity_id'] == self.entity_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
					#print('Release TXNs: \n{}'.format(release_txns))
					in_use_txns = ledger.gl[(ledger.gl['debit_acct'] == 'In Use') & (ledger.gl['entity_id'] == self.entity_id) & (ledger.gl['date'] <= wip_lot[2]) & (~ledger.gl['event_id'].isin(release_txns['event_id'])) & (~ledger.gl['event_id'].isin(rvsl_txns))] # Ensure only captures related items, perhaps using date as a filter
					#print('In Use TXNs: \n{}'.format(in_use_txns))
					for index, in_use_txn in in_use_txns.iterrows():
						release_entry = [ in_use_txn[0], in_use_txn[1], world.now, in_use_txn[4] + ' released', in_use_txn[4], in_use_txn[5], in_use_txn[6], in_use_txn[8], 'In Use', in_use_txn[9] ]
						release_event = [release_entry]
						ledger.journal_entry(release_event)
					# Book the entry to move from WIP to Inventory
					if v: print('WIP account for {}: {}'.format(item, wip_lot[7]))
					if v: print('WIP Lot: \n{}'.format(wip_lot))
					if wip_lot[7] == 'Researching Technology':
						debit_acct = 'Technology'
						desc = wip_lot[4] + ' researched'
					elif wip_lot[7] == 'Studying Education':
						debit_acct = 'Education'
						desc = wip_lot[4] + ' learned'
					elif wip_lot[7] == 'WIP Equipment':
						debit_acct = 'Equipment' # TODO Test Equipment that takes Time to produce
						desc = wip_lot[4] + ' manufactured'
					elif wip_lot[7] == 'Building Under Construction':
						debit_acct = 'Buildings'
						desc = wip_lot[4] + ' constructed'
					elif wip_lot[7] == 'WIP Inventory':
						debit_acct = 'Inventory'
						desc = wip_lot[4] + ' produced'
					else:
						debit_acct = 'Inventory'
						desc = wip_lot[4] + ' produced'
					wip_entry = [ wip_lot[0], wip_lot[1], world.now, desc, wip_lot[4], wip_lot[5], wip_lot[6] or '', debit_acct, wip_lot[7], wip_lot[9] ]
					wip_event += [wip_entry]
					if v: print('WIP Event: \n{}'.format(wip_event))
					ledger.journal_entry(wip_event)

	def check_inv(self, v=False):
		if type(self) == Corporation:
			v = False
		if v: print('{}-{} running inventory check.'.format(self.name, self.entity_id))
		self.check_salary(check=True)
		self.check_subscriptions(check=True)
		self.wip_check(check=True)
		if v: print('{}-{} finished inventory check.\n'.format(self.name, self.entity_id))

	def check_prices(self):
		if self.produces is None:
			return
		ledger.set_entity(self.entity_id)
		for item in self.produces:
			if not self.check_eligible(item): # TODO Maybe cache this
				continue
			item_type = world.get_item_type(item)
			if item_type in ('Education', 'Technology', 'Land'): # TODO Support creating types of land like planting trees to make forest
				continue
			elif item_type in ('Subscription', 'Service'):
				ledger.set_date(str(world.now - datetime.timedelta(days=1)))
				hist_bal = ledger.balance_sheet(['Subscription Revenue','Service Revenue'], item, v=True)
				ledger.reset()
				ledger.set_entity(self.entity_id)
				print('Serv and Sub Hist Bal of {} for {}-{}: {}'.format(item, self.name, self.entity_id, hist_bal))
				if hist_bal:
					ledger.set_start_date(str(world.now - datetime.timedelta(days=1)))
					ledger.set_date(str(world.now - datetime.timedelta(days=1)))
					cur_bal = ledger.balance_sheet(['Subscription Revenue','Service Revenue'], item)
					ledger.reset()
					ledger.set_entity(self.entity_id)
					print('Cur Bal of {} for {}-{}: {}'.format(item, self.name, self.entity_id, cur_bal))
					if not cur_bal:
						self.adj_price(item, direction='down')
			else:
				qty_inv = ledger.get_qty(item, ['Inventory'])
				print('Qty of {} for {}-{}: {}'.format(item, self.name, self.entity_id, qty_inv))
				if qty_inv > 0:
					self.adj_price(item, direction='down')
				else:
					# If the entity has made the item in the past, and someone else has or is making the item, and they dont have and are not making the item
					wip_qty_inv = ledger.get_qty(item, ['WIP Inventory']) # Must be zero, qty in inv already known to be zero
					ledger.set_date(str(world.now - datetime.timedelta(days=1)))
					hist_bal = ledger.balance_sheet(['Sales','Goods Produced','Building Produced','Equipment Produced','Spoilage Expense'], item) # Must not be zero
					ledger.reset()
					global_qty_inv = ledger.get_qty(item, ['Inventory','WIP Inventory']) # Must be greater than zero
					ledger.set_entity(self.entity_id)
					print('Inv Hist Bal of {} for {}-{}: {} | WIP Inv: {} | Global qty: {}'.format(item, self.name, self.entity_id, hist_bal, wip_qty_inv, global_qty_inv))
					if hist_bal != 0 and global_qty_inv > 0 and wip_qty_inv == 0:
						self.adj_price(item, direction='down')
			ledger.reset()

	def negative_bal(self):
		for item in self.produces:
			qty_inv = ledger.get_qty(item, ['Inventory'])
			if qty_inv < 0:
				print('{}-{} has a negative item balance of {} {}. Will attempt to produce {} units'.format(self.name, self.entity_id, qty_inv, item, abs(qty_inv)))
				self.produce(item, abs(qty_inv))


	def capitalize(self, amount=None, buffer=False):
		if amount is None:
			amount = INIT_CAPITAL
		capital_entry = [ ledger.get_event(), self.entity_id, world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', amount ]
		capital_event = [capital_entry]
		if buffer:
			return capital_event
		ledger.journal_entry(capital_event)
		#return capital_event

	def auth_shares(self, ticker, qty=None, counterparty=None):
		if counterparty is None:
			counterparty = self
		if qty is None:
			qty = 100000
		auth_shares_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Authorize shares', ticker, '', qty, 'Shares', 'Info', 0 ]
		auth_shares_event = [auth_shares_entry]
		ledger.journal_entry(auth_shares_event)

	def buy_shares(self, ticker, price, qty, counterparty):
		desc_pur = ticker + ' shares purchased'
		desc_sell = ticker + ' shares sold'
		result, cost = self.transact(ticker, price, qty, counterparty, 'Investments', 'Shares', desc_pur=desc_pur, desc_sell=desc_sell)
		return result

	# Allow individuals to incorporate organizations without human input
	def incorporate(self, name=None, item=None, qty=None, price=None, auth_qty=None, founders=None):
		if self.hours < MAX_HOURS:
			print('Not enough time to incorporate. Requires a full day of {} hours time.'.format(MAX_HOURS))
			return
		if price is None:
			price = 1
		if qty is None and founders is None:
			qty = 5000 # TODO Fix temp defaults
		if auth_qty is None:
			auth_qty = 100000 # TODO Determine dynamically
		if founders is None:
			founders = {self: qty}
		if qty is None:
			qty = sum(founders.values())
		entities = accts.get_entities()
		if name is None and item is not None:
			names = world.items.loc[item, 'producer']
			if isinstance(names, str):
				names = [x.strip() for x in names.split(',')]
			# names = list(set(filter(None, names)))
			names = list(collections.OrderedDict.fromkeys(filter(None, names)))
			name = names[0]
			#print('Ticker: {}'.format(name))
		if name == 'Bank' and world.gov.bank is not None:
			print('{} already has a bank. Only one bank per government is allowed.'.format(world.gov))
			return
		legal_form = world.org_type(name)
		# print('Legal Form: {}'.format(legal_form))
		if legal_form == Corporation:
			for founder, founder_qty in founders.items():
				ledger.set_entity(founder.entity_id)
				founder_cash = ledger.balance_sheet(['Cash'])
				ledger.reset()
				#print('Cash: {}'.format(cash))
				if price * founder_qty > founder_cash:
					print('{}-{} does not have enough cash to incorporate {}. Cash: {} | Required: {}'.format(founder.name, founder.entity_id, name, founder_cash, price * founder_qty))
					return
		items_produced = world.items[world.items['producer'].str.contains(name, na=False)].reset_index()
		items_produced = items_produced['item_id'].tolist()
		items_produced = ', '.join(items_produced)
		# print('Items Produced: {}'.format(items_produced))
		last_entity_id = entities.reset_index()['entity_id'].max()
		name = name + '-' + str(last_entity_id + 1)
		#print('Corp Name: \n{}'.format(name))
		corp = factory.create(legal_form, name, items_produced, self.government, auth_qty)
		world.prices = pd.concat([world.prices, corp.prices])
		if name.split('-')[0] == 'Bank':
			world.gov.bank = corp
			print('{}\'s central bank created.'.format(world.gov))
		counterparty = corp
		if legal_form == Corporation:
			self.auth_shares(name, auth_qty, counterparty)
			for founder, qty in founders.items():
				founder.buy_shares(name, price, qty, counterparty)
		self.set_hours(MAX_HOURS)
		return corp

	def corp_needed(self, item=None, need=None, ticker=None, demand_index=None):
		# Choose the best item
		#print('Need Demand: {}'.format(need))
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
			#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
			items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)

			items_info = items_info.sort_values(by='satisfy_rate', ascending=False).reset_index()
			#items_info.reset_index(inplace=True)
			item = items_info['item_id'].iloc[0]
			#print('Item Choosen: {}'.format(item))
		if ticker is None:
			tickers = world.items.loc[item, 'producer']
			if tickers is None:
				return
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			# tickers = list(set(filter(None, tickers))) # Use set to ensure no dupes
			tickers = list(collections.OrderedDict.fromkeys(filter(None, tickers)))
			#print('Tickers: {}'.format(tickers))
			# TODO Recursively check required items and add their producers to the ticker list
		# Check if item is produced or being produced
		# TODO How to handle service qty check
		qty = ledger.get_qty(item, ['Inventory','WIP Inventory'])
		#print('QTY of {} existing: {}'.format(item, qty))
		# If not being produced incorporate and produce item
		if qty == 0: # TODO Fix this for when Food stops being produced
			for ticker in tickers:
				count = 0
				#print('Ticker: {}'.format(ticker))
				if ticker == 'Individual':
					#print('{} produced by individuals, no corporation needed.'.format(item))
					continue
				for corp in world.gov.get([Corporation, NonProfit]): # TODO Check Non-Profits also
					# print('Corp: {}'.format(corp))
					if ticker == corp.name.split('-')[0]:
						count += 1
						if count >= MAX_CORPS:
							#print('{} {} corporation already exists.'.format(count, corp.name))
							return
				corp = self.incorporate(name=ticker, item=item)
				# TODO Have the demand table item cleared when entity gets the subscription
				item_type = world.get_item_type(item)
				if item_type == 'Subscription' and demand_index is not None:
					world.demand = world.demand.drop([demand_index]).reset_index(drop=True)
					world.set_table(world.demand, 'demand')
				return corp

	def tech_motivation(self):
		tech_info = world.items[world.items['child_of'] == 'Technology']
		tech_info.reset_index(inplace=True)
		#print('Tech Info: \n{}'.format(tech_info))
		# ledger.reset()
		for index, tech_row in tech_info.iterrows():
			tech = tech_row['item_id']
			#print('Tech Check: {}'.format(tech))
			tech_done_status = ledger.get_qty(items=tech, accounts=['Technology'])
			tech_research_status = ledger.get_qty(items=tech, accounts=['Researching Technology'])
			tech_status = tech_done_status + tech_research_status
			if tech_status == 0:
				#print('Tech Needed: {}'.format(tech))
				outcome = self.item_demanded(tech, qty=1)
				if outcome:
					return tech

	def check_eligible(self, item, v=False):
		if v: print('Eligible Item Check: {}'.format(item))
		if world.items.loc[item, 'requirements'] is None: # Base case
			return True
		requirements = [x.strip() for x in world.items.loc[item, 'requirements'].split(',')]
		if v: print('Eligible Item Requirements: {} | {}'.format(item, requirements))
		for requirement in requirements:
			item_type = world.get_item_type(requirement)
			if v: print('Check {} Eligible Requirement: {} | {}'.format(item, requirement, item_type))
			if item_type == 'Technology':
				tech_status = ledger.get_qty(items=requirement, accounts=['Technology'])
				if tech_status == 0:
					if v: print('Do not have {} tech for item: {}'.format(requirement, item))
					return False
				elif tech_status >= 0:
					if v: print('Have {} tech for item: {}'.format(requirement, item))
					return True
			else:
				if self.check_eligible(requirement):
					continue
				else:
					return False
		if v: print('No tech needed for item: {}'.format(item))
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
			print('{}-{} cannot add {} to demand list as it is constrained by {}.'.format(self.name, self.entity_id, item, constraint))
			return True

	def item_demanded(self, item=None, qty=None, need=None, cost=False):
		need_reason = False
		if item is None and need is not None:
			need_reason = True
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
			print('Do not have tech for {} so it cannot be added to the demand list.'.format(item))
			return
		# Check if entity already has item on demand list
		if not world.demand.empty: # TODO Commodity replaces existing commodity if qty is bigger
			#if item_type != 'Commodity': # TODO No longer needed
			temp_df = world.demand[['entity_id','item_id']]
			#print('Temp DF: \n{}'.format(temp_df))
			#temp_new_df = pd.DataFrame({'entity_id': self.entity_id, 'item_id': item}, index=[0]) # Old
			temp_new_df = pd.DataFrame(columns=['entity_id','item_id'])
			temp_new_df = temp_new_df.append({'entity_id': self.entity_id, 'item_id': item}, ignore_index=True)
			#print('Temp New DF: \n{}'.format(temp_new_df))
			#check = temp_df.intersection(temp_new_df)
			check = pd.merge(temp_df, temp_new_df, how='inner', on=['entity_id','item_id'])
			#print('Check: \n{}'.format(check))
			if not check.empty:
				if item_type != 'Commodity': # TODO Maybe add Components
					print('{} already on demand list for {}-{}.'.format(item, self.name, self.entity_id))
				return
		if item_type == 'Service':
			#print('Current Demand : \n{}'.format(world.demand['item_id']))
			qty = 1
			if item in world.demand['item_id'].values:
				print('{} service already on the demand table for {}-{}.'.format(item, self.name, self.entity_id)) # TODO Finish this
				return
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			# tickers = list(set(filter(None, tickers)))
			tickers = list(collections.OrderedDict.fromkeys(filter(None, tickers)))
			#print('Tickers: {}'.format(tickers))
			for ticker in tickers: # TODO Check to entity register
				corp_shares = ledger.get_qty(ticker, ['Investments'])
				if corp_shares != 0:
					return
		if qty is None:
			qty = self.qty_demand(item, need, item_type)
		#print('Demand QTY: {}'.format(qty))
		if qty != 0 and not self.check_constraint(item):
			if cost:
				world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'cost'}, ignore_index=True)
				world.set_table(world.demand, 'demand')
			elif need_reason:
				world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'need'}, ignore_index=True)
				world.set_table(world.demand, 'demand')
			else:
				world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty, 'reason': 'existance'}, ignore_index=True)
				world.set_table(world.demand, 'demand')
			if qty == 1:
				print('{} added to demand list for {} unit by {}-{}.'.format(item, qty, self.name, self.entity_id))
			else:
				print('{} added to demand list for {} units by {}-{}.'.format(item, qty, self.name, self.entity_id))
			#print('Demand after addition: \n{}'.format(world.demand))
			return item, qty

	def check_demand(self, v=False):
		if self.produces is None:
			return
		if v: print('{}-{} demand check for items: \n{}'.format(self.name, self.entity_id, self.produces))
		for item in self.produces:
			if v: print('Check Demand Item for {}-{}: {}'.format(self.name, self.entity_id, item))
			item_type = world.get_item_type(item)
			if item_type == 'Subscription':
				continue
			#print('World Demand: \n{}'.format(world.demand))
			to_drop = []
			qty = 0
			qty_existance = 0
			# Filter for item and add up all qtys to support multiple entries
			for index, demand_row in world.demand.iterrows():
				if item_type == 'Education':
					if demand_row['entity_id'] == self.entity_id: # TODO Could filter df for entity_id first
						if demand_row['item_id'] == item:
							qty = demand_row['qty']
							qty = int(math.ceil(qty))
							break
				else:
					if demand_row['item_id'] == item:
						qty += demand_row['qty']
						qty = int(math.ceil(qty))
						to_drop.append(index)
			if qty == 0:
				continue
			print('\n{}-{} attempting to produce {} {} from the demand table.'.format(self.name, self.entity_id, qty, item))
			item_demand = world.demand[world.demand['item_id'] == item]
			if 'existance' in item_demand['reason'].values:
				self.adj_price(item, qty, direction='up')
			outcome, time_required = self.produce(item, qty)
			if v: print('Outcome: {} \n{}'.format(time_required, outcome))
			if outcome:
				if item_type == 'Education':
					edu_hours = int(math.ceil(qty - MAX_HOURS))
					#print('Edu Hours: {} | {}'.format(edu_hours, index))
					if edu_hours > 0:
						world.demand.at[index, 'qty'] = edu_hours
						world.set_table(world.demand, 'demand')
					#print('Demand After: \n{}'.format(world.demand))
				if item_type == 'Technology':
					return
				else:
					try:
						world.demand = world.demand.drop(to_drop).reset_index(drop=True)
						world.set_table(world.demand, 'demand')
					except KeyError as e:
						#print('Error: {}'.format(repr(e)))
						pass
					print('{} removed from demand list for {} units by {}-{}.\n'.format(item, qty, self.name, self.entity_id))

	def check_optional(self):
		if self.produces is None:
			return
		items_list = world.items[world.items['producer'] != None]
		#print('Items List: \n{}'.format(items_list))
		for item in self.produces:
			if not self.check_eligible(item): # TODO Maybe cache this
				continue
			#print('Produces Item: {}'.format(item))
			requirements = world.items.loc[item, 'requirements']
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
					productivity_items = productivity_items.append({'item_id': prod_item.name, 'efficiency': efficiency}, ignore_index=True)
				productivity_items = productivity_items.sort_values(by='efficiency', ascending=True)
				#print('Productivity Items: \n{}'.format(productivity_items))
				if not productivity_items.empty:
					for index, prod_item in productivity_items.iterrows():
						if self.check_eligible(prod_item['item_id']):
							item_type = world.get_item_type(prod_item['item_id'])
							ledger.set_entity(self.entity_id)
							current_qty = ledger.get_qty(prod_item['item_id'], [item_type])
							ledger.reset()
							#print('Current Qty of {}: {}'.format(item['item_id'], current_qty))
							if current_qty == 0:
								result = self.purchase(prod_item['item_id'], qty=1, acct_buy=item_type) # TODO More than 1 qty?
								if result:
									break

	def claim_land(self, qty, price=0, item='Land', counterparty=None, buffer=False): # QTY in square meters
		if qty <= 0:
			return
		if counterparty is None:
			counterparty = world.env.entity_id
			print('{}-{} claiming {} {} from entity ID: {}.'.format(self.name, self.entity_id, qty, item, counterparty))
		if args.user: # TODO Add support for non-user claim time requirement
			time_required = qty / EXPLORE_TIME
			if isinstance(self, Corporation):
				largest_shareholder = self.list_shareholders(largest=True)
				if largest_shareholder is None:
					return
				largest_shareholder = factory.get_by_id(largest_shareholder)
				if largest_shareholder.hours < time_required:
					print('{} does not have enough time to claim {} units of {}.'.format(largest_shareholder.name, qty, item))
					return
				else:
					largest_shareholder.set_hours(time_required)
			else:
				if self.hours < time_required:
					print('{} does not have enough time to claim {} units of {}.'.format(self.name, qty, item))
					return
				else:
					self.set_hours(time_required)
		# TODO Decide if fulfill() is required when claiming land from other entity
		incomplete, claim_land_event, time_required = self.fulfill(item, qty)
		if incomplete:
			return
		claim_land_entry = []
		yield_land_entry = []
		# TODO Add WIP Time component
		if counterparty == world.env.entity_id or counterparty is None:
			ledger.set_entity(world.env.entity_id)
		else:
			ledger.set_entity(counterparty.entity_id) # TODO Support claiming land from other Individuals
		unused_land = ledger.get_qty(items=item, accounts=['Land'])
		ledger.reset()
		print('{} available to claim by {}-{}: {}'.format(item, self.name, self.entity_id, unused_land))
		if unused_land >= qty:
			claim_land_entry = [ ledger.get_event(), self.entity_id, world.now, 'Claim land', item, price, qty, 'Land', 'Natural Wealth', qty * price ]
			if counterparty == world.env.entity_id:
				yield_land_entry = [ ledger.get_event(), world.env.entity_id, world.now, 'Bestow land', item, price, qty, 'Natural Wealth', 'Land', qty * price ]
			else:
				yield_land_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Lose land', item, price, qty, 'Natural Wealth', 'Land', qty * price ]
			# claim_land_event = [yield_land_entry, claim_land_entry]
			if claim_land_entry and yield_land_entry:
				claim_land_event += [yield_land_entry, claim_land_entry]
			if buffer:
				print('{}-{} claims {} square meters of {}.'.format(self.name, self.entity_id, qty, item))
				return claim_land_event
			# if not claim_land_event:
			# 	return
			ledger.journal_entry(claim_land_event)
			return True
		else:
			unused_land = ledger.get_qty(items=item, accounts=['Land'])
			if unused_land < qty:
				print('{}-{} cannot claim {} square meters of {} because there is only {} square meters available.'.format(self.name, self.entity_id, qty, item, unused_land))
			unused_land = ledger.get_qty(items=item, accounts=['Land'], by_entity=True)
			print('Unused Land claimed by the following entities: \n{}'.format(unused_land))

	def get_counterparty(self, txns, rvsl_txns, item, account, n=0, allowed=None, v=False):
		if v: print('Get Counterparty for {}-{} | Item: {}'.format(self.name, self.entity_id, item))
		if allowed is None:
			allowed = factory.registry.keys()
		else:
			if not isinstance(allowed, (list, tuple)):
				allowed = [allowed]
		if v: print('Allowed: {}'.format(allowed))
		txn = txns.loc[txns['item_id'] == item]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('TXN: \n{}'.format(txn))
		if txn.empty:
			print('No counterparty exists for {}.'.format(item))
			return None, None
		event_id = txn.iloc[0].loc['event_id']
		if v: print('Event ID: {}'.format(event_id))
		event_txns = ledger.gl[(ledger.gl['event_id'] == event_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('Event TXNs: \n{}'.format(event_txns))
		item_txn = event_txns.loc[event_txns['item_id'] == item] # If there are multiple items in same event
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('Item TXN: \n{}'.format(item_txn))
		counterparty_txn = item_txn.loc[item_txn['debit_acct'] == account]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('Counterparty TXN: {} \n{}'.format(account, counterparty_txn))
		if v: print('n: {}'.format(n))
		counterparty_id = counterparty_txn.iloc[n].loc['entity_id']
		counterparty = factory.get_by_id(counterparty_id)
		if v: print('Counterparty Type: {}'.format(type(counterparty)))
		while True:
			if counterparty is not None:
				break
			if type(counterparty) not in allowed:
				counterparty_id += 1
				counterparty = factory.get_by_id(counterparty_id)
		if v: print('Counterparty: {}'.format(counterparty))
		return counterparty, event_id

	def pay_wages(self, jobs=None, counterparty=None, v=False):
		if jobs is None:
			# Get list of jobs
			# TODO Get list of jobs that have accruals only
			ledger.set_entity(self.entity_id)
			wages_payable_list = ledger.get_qty(accounts=['Wages Expense'])
			ledger.reset()
			#print('Wages Payable List: \n{}'.format(wages_payable_list))
			jobs = wages_payable_list['item_id']
		# Ensure jobs is a list
		if isinstance(jobs, str):
			jobs = [x.strip() for x in jobs.split(',')]
		jobs = list(filter(None, jobs))
		for job in jobs:
			ledger.set_entity(self.entity_id)
			wages_payable = abs(ledger.balance_sheet(accounts=['Wages Payable'], item=job))
			labour_hours = abs(ledger.get_qty(items=job, accounts=['Wages Payable']))
			ledger.reset()
			#print('Wages Payable: {}'.format(wages_payable))
			#print('Labour Hours: {}'.format(labour_hours))
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if not wages_payable:
				#print('No wages payable to pay for {} work.'.format(job))
				return
			elif cash >= wages_payable:
				# Get counterparty
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				wages_paid_txns = ledger.gl[( (ledger.gl['entity_id'] == self.entity_id) & (ledger.gl['debit_acct'] == 'Wages Payable') & (ledger.gl['credit_acct'] == 'Cash') & (ledger.gl['item_id'] == job) ) & (~ledger.gl['event_id'].isin(rvsl_txns))]['event_id']
				#print('Wages Paid TXN Event IDs: \n{}'.format(wages_paid_txns))
				wages_pay_txns = ledger.gl[( (ledger.gl['entity_id'] == self.entity_id) & (ledger.gl['debit_acct'] == 'Wages Expense') & (ledger.gl['credit_acct'] == 'Wages Payable') ) & (~ledger.gl['event_id'].isin(wages_paid_txns)) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				with pd.option_context('display.max_rows', None, 'display.max_columns', None):
					if v: print('Wages Pay TXNs: \n{}'.format(wages_pay_txns))
				job_wages_pay_txns = wages_pay_txns.loc[wages_pay_txns['item_id'] == job]
				with pd.option_context('display.max_rows', None, 'display.max_columns', None):
					if v: print('Wages Job Pay TXNs: \n{}'.format(job_wages_pay_txns))
				counterparties = job_wages_pay_txns.shape[0]
				if v: print('Number of Counterparties for {}: {}'.format(job, counterparties))
				pay_wages_event = []
				for n in range(counterparties):
					counterparty, event_id = self.get_counterparty(wages_pay_txns, rvsl_txns, job, 'Wages Receivable', n=n, allowed=Individual, v=v)
					wages_pay_entry = [ event_id, self.entity_id, world.now, job + ' wages paid', job, wages_payable / labour_hours, labour_hours, 'Wages Payable', 'Cash', wages_payable ]
					wages_chg_entry = [ event_id, counterparty.entity_id, world.now, job + ' wages received', job, wages_payable / labour_hours, labour_hours, 'Cash', 'Wages Receivable', wages_payable ]
					pay_wages_event += [wages_pay_entry, wages_chg_entry]
				ledger.journal_entry(pay_wages_event)
			else:
				print('{}-{} does not have enough cash to pay wages for {} work. Cash: {}'.format(self.name, self.entity_id, job, cash))
				# TODO Fix counterparty
				#counterparty.adj_price(job, labour_hours, direction='down')
				return

	def check_wages(self, job):
		TWO_PAY_PERIODS = 32 #datetime.timedelta(days=32)
		ledger.set_entity(self.entity_id)
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of Wages Payable txns
		payable = ledger.gl[(ledger.gl['credit_acct'] == 'Wages Payable') & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Payable: \n{}'.format(payable))
		paid = ledger.gl[(ledger.gl['debit_acct'] == 'Wages Payable') & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Paid: \n{}'.format(paid))
		ledger.reset()
		if not payable.empty:
			latest_payable = payable['date'].iloc[-1]
			latest_payable = datetime.datetime.strptime(latest_payable, '%Y-%m-%d').date()
			#print('Latest Payable: \n{}'.format(latest_payable))
		else:
			latest_payable = 0
		if not paid.empty:
			latest_paid = paid['date'].iloc[-1]
			latest_paid = datetime.datetime.strptime(latest_paid, '%Y-%m-%d').date()
			#print('Latest Paid: \n{}'.format(latest_paid))
		else:
			latest_paid = 0
			return True
		#print('Latest Payable: \n{}'.format(latest_payable))
		#print('Latest Paid: \n{}'.format(latest_paid))
		last_paid = latest_payable - latest_paid
		if isinstance(last_paid, datetime.timedelta):
			last_paid = last_paid.days
		#print('Last Paid: \n{}'.format(last_paid))
		if last_paid < TWO_PAY_PERIODS:
			return True

	def accru_wages(self, job, counterparty, labour_hours, wage=None, buffer=False, check=False):
		desc_exp = job + ' wages to be paid'
		desc_rev = job + ' wages to be received'
		if counterparty is None:
			print('No workers available to do {} job for {} hours.'.format(job, labour_hours))
			return
		#print('Labour Counterparty: {}'.format(counterparty.name))
		if job == 'Study':
			desc_exp = 'Record study hours'
			desc_rev = 'Record study hours'
		if wage is None:
			wage = world.get_price(job, counterparty.entity_id)
		recently_paid = self.check_wages(job)
		incomplete, accru_wages_event, time_required = self.fulfill(job, qty=labour_hours, reqs='usage_req', amts='use_amount', check=check)
		if check:
			return
		if recently_paid and not incomplete:
			if counterparty.hours > 0:
				hours_worked = min(labour_hours, counterparty.hours)
				wages_exp_entry = [ ledger.get_event(), self.entity_id, world.now, desc_exp, job, wage, hours_worked, 'Wages Expense', 'Wages Payable', wage * hours_worked ]
				wages_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, desc_rev, job, wage, hours_worked, 'Wages Receivable', 'Wages Income', wage * hours_worked ]
				accru_wages_event += [wages_exp_entry, wages_rev_entry]
			else:
				if not incomplete:
					print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
				else:
					print('{}-{} cannot fulfill the requirements to allow {} to work.'.format(self.name, self.entity_id, job))
				return
			if buffer:
				print('{}-{} hired {} as a {} for {} hours.'.format(self.name, self.entity_id, counterparty.name, job, hours_worked))
				if job != 'Study':
					counterparty.adj_price(job, labour_hours, direction='up_low')
				return accru_wages_event
			ledger.journal_entry(accru_wages_event)
			if job != 'Study':
				counterparty.adj_price(job, labour_hours, direction='up_low')
			counterparty.set_hours(hours_worked)
		else:
			print('Wages have not been paid for {} recently by {}-{}.'.format(job, self.name, self.entity_id))
			counterparty.adj_price(job, labour_hours, direction='down')
			return

	def worker_counterparty(self, job, only_avail=True, man=False):
		print('{}-{} looking for worker for job: {}'.format(self.name, self.entity_id, job))
		item_type = world.get_item_type(job)
		workers_exp = collections.OrderedDict()
		workers_price = collections.OrderedDict()
		# Get list of all individuals
		#world.entities = accts.get_entities()
		# Get list of eligible individuals
		worker_event = []
		individuals = []
		for individual in world.gov.get(Individual):
			incomplete, entries, time_required = individual.fulfill(job, qty=1)
			# TODO Capture entries
			if not incomplete:
				# This will cause all available workers to attempt to become qualified even if they don't get the job in the end
				individuals.append(individual)
				worker_event += entries
		#print('Eligible Individuals: \n{}'.format(individuals))
		# Check total wages receivable for that job for each individual
		for individual in individuals:
			experience_wages = 0
			experience_salary = 0
			ledger.set_entity(individual.entity_id)
			experience_wages = abs(ledger.get_qty(accounts=['Wages Income'], items=job))
			experience_salary = abs(ledger.get_qty(accounts=['Salary Income'], items=job))
			experience = experience_wages + experience_salary
			print('Experience for {}: {:g} | Hours Left: {}'.format(individual.name, experience, individual.hours))
			ledger.reset()
			workers_exp[individual] = experience
		for individual in individuals:
			price = world.get_price(job, individual.entity_id)
			workers_price[individual] = price
			print('Price for {}: {} | Hours Left: {}'.format(individual.name, price, individual.hours))
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
			# TODO Combine dicts to one structure
			if man:
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
						break
				worker_choosen = factory.get_by_id(worker_choosen)
				return worker_choosen
		else:
			workers_avail_exp = workers_exp
			workers_avail_price = workers_price
			if man:
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
						break
				worker_choosen = factory.get_by_id(worker_choosen)
				return worker_choosen
		if not workers_avail_price:
			return None, []
		# Choose the worker with the most experience
		worker_choosen_exp = max(workers_avail_exp, key=lambda k: workers_avail_exp[k])
		# Choose the worker for the lowest price
		worker_choosen = min(workers_avail_price, key=lambda k: workers_avail_price[k])
		print('Worker Choosen for {}: {}'.format(job, worker_choosen.name))
		if worker_event:
			return worker_choosen, worker_event
		return worker_choosen

	def hire_worker(self, job, counterparty=None, price=0, qty=1, man=False, buffer=False):
		entries = []
		if counterparty is None:	
			counterparty = self.worker_counterparty(job, only_avail=False, man=man)
			if isinstance(counterparty, tuple):
				counterparty, entries = counterparty
		if counterparty is None:
			print('No workers available to do {} job for {}-{}.'.format(job, self.name, self.entity_id))
			return
		price = world.get_price(job, counterparty.entity_id)
		incomplete, hire_worker_event, time_required = self.fulfill(job, qty)
		if incomplete:
			return
		if entries:
			hire_worker_event += entries
		# hire_worker_entry = [] # TODO Test if not needed
		# start_job_entry = [] # TODO Test if not needed
		hire_worker_entry = [ ledger.get_event(), self.entity_id, world.now, 'Hired ' + job, job, price, qty, 'Worker Info', 'Hire Worker', 0 ]
		start_job_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Started job as ' + job, job, price, qty, 'Start Job', 'Worker Info', 0 ]
		# if hire_worker_entry and start_job_entry: # TODO Test if not needed
		hire_worker_event += [hire_worker_entry, start_job_entry]
		first_pay = self.pay_salary(job, counterparty, buffer=buffer, first=True)
		if not first_pay:
			hire_worker_event = []
			first_pay = []
		else:
			hire_worker_event += first_pay
		if buffer:
			if hire_worker_event:
				print('{}-{} hired {} as a fulltime {}.'.format(self.name, self.entity_id, counterparty.name, job))
				if first_pay:
					self.adj_price(job, qty=1, direction='up')
			else:
				print('{}-{} could not hire {} as a fulltime {}.'.format(self.name, self.entity_id, counterparty.name, job))
			return hire_worker_event
		ledger.journal_entry(hire_worker_event)
		if first_pay:
			self.adj_price(job, qty=1, direction='up')

	def fire_worker(self, job, counterparty, price=0, qty=-1, quit=False, buffer=False):
		ent_id = self.entity_id
		cp_id = counterparty.entity_id
		if quit:
			ent_id, cp_id = cp_id, ent_id
		fire_worker_entry = [ ledger.get_event(), ent_id, world.now, 'Fired ' + job, job, price, qty, 'Worker Info', 'Fire Worker', 0 ]
		quit_job_entry = [ ledger.get_event(), cp_id, world.now, 'Quit job as ' + job, job, price, qty, 'Quit Job', 'Worker Info', 0 ]
		fire_worker_event = [fire_worker_entry, quit_job_entry]
		if buffer:
			counterparty.adj_price(job, qty=1, direction='down')
			return fire_worker_event
		ledger.journal_entry(fire_worker_event)
		counterparty.adj_price(job, qty=1, direction='down')

	def check_salary(self, job=None, counterparty=None, check=False):
		if job is not None:
			ledger.set_entity(self.entity_id)
			worker_state = ledger.get_qty(items=job, accounts=['Worker Info'])
			ledger.reset()
			if worker_state:
				worker_state = int(worker_state)
			#print('Worker State: {}'.format(worker_state))
			if not worker_state: # If worker_state is zero
				return
			for _ in range(worker_state):
				self.pay_salary(job, counterparty, check=check)
		elif job is None:
			ledger.set_entity(self.entity_id)
			worker_states = ledger.get_qty(accounts=['Worker Info'])
			ledger.reset()
			#print('Worker States: \n{}'.format(worker_states))
			rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			salary_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Worker Info') & (ledger.gl['credit_acct'] == 'Hire Worker') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
			#print('Worker TXNs: \n{}'.format(salary_txns))
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
				counterparty, event_id = self.get_counterparty(salary_txns, rvsl_txns, job, 'Start Job', allowed=Individual)
				# Check is fulltime job is still required
				items_req = world.items[world.items['requirements'].str.contains(job, na=False)].reset_index()
				qty_active = ledger.get_qty(items=list(items_req['item_id'].values))
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
		if type(counterparty) != Individual: # TODO Shouldn't be needed now, this was due to error from inheritance going to a Corporation
			print('Counterparty is not an Individual, it is {} | {}'.format(counterparty.name, counterparty.entity_id))
			return
		if first: # TODO Required due to not using db rollback in fulfill
			pay_salary_event = []
			incomplete = False
			time_required = False
		else:
			incomplete, pay_salary_event, time_required = self.fulfill(job, qty=1, reqs='usage_req', amts='use_amount', check=check)
		if check:
			if pay_salary_event and not incomplete:
				ledger.journal_entry(pay_salary_event)
				return True
			return
		if salary is None:
			salary = world.get_price(job, counterparty.entity_id)
		if labour_hours is None:
			labour_hours = WORK_DAY
		if counterparty.hours < labour_hours:
			print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= (salary * labour_hours) and not incomplete:
			# TODO Add check if enough cash, if not becomes salary payable
			salary_exp_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' salary paid', job, salary, labour_hours, 'Salary Expense', 'Cash', salary * labour_hours ]
			salary_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' salary received', job, salary, labour_hours, 'Cash', 'Salary Income', salary * labour_hours ]
			pay_salary_event += [salary_exp_entry, salary_rev_entry]
			# TODO Don't set hours if production is not possible
			counterparty.set_hours(labour_hours)
			if buffer:
				counterparty.adj_price(job, labour_hours, direction='up_low')
				return pay_salary_event
			ledger.journal_entry(pay_salary_event)
			counterparty.adj_price(job, labour_hours, direction='up_low')
			return True
		else:
			if not incomplete:
				print('{}-{} does not have enough cash to pay for {} salary. Cash: {}'.format(self.name, self.entity_id, job, cash))
			else:
				print('{}-{} cannot fulfill the requirements to keep {} working.'.format(self.name, self.entity_id, job))
			if not first:
				self.fire_worker(job, counterparty)

	def subscription_counterparty(self, subscription, v=False):
		# Get entity that produces the subscription
		if v: print('Subscription Requested: {}'.format(subscription))
		producers = world.items.loc[subscription, 'producer']
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
		serv_prices = {k:world.get_price(subscription, k) for k in producer_entities}
		if not serv_prices:
			print('No {} exists that can provide the {} subscription for {}-{}.'.format(producers, subscription, self.name, self.entity_id))
			return
		counterparty_id = min(serv_prices, key=lambda k: serv_prices[k])
		counterparty = factory.get_by_id(counterparty_id)
		if counterparty is None:
			print('No {} exists that can provide the {} subscription for {}-{}.'.format(producer, subscription, self.name, self.entity_id))
			return
		print('{}-{} choose {}-{} for the {} subscription counterparty.'.format(self.name, self.entity_id, counterparty.name, counterparty.entity_id, subscription))
		return counterparty

	def order_subscription(self, item, counterparty, price, qty=1, buffer=False):
		if counterparty is None:
			self.item_demanded(item, qty)
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= price:
			order_subscription_event = []
			incomplete, entries, time_required = counterparty.fulfill(item, qty)
			if incomplete:
				return
			if entries:
				order_subscription_event += entries
			order_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Ordered ' + item, item, price, qty, 'Subscription Info', 'Order Subscription', 0 ]
			sell_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Sold ' + item, item, price, qty, 'Sell Subscription', 'Subscription Info', 0 ]
			order_subscription_event += [order_subscription_entry, sell_subscription_entry]
			first_payment = self.pay_subscription(item, counterparty, buffer=buffer, first=True)
			if not first_payment:
				order_subscription_event = []
				first_payment = []
			elif buffer:
				order_subscription_event += first_payment
				print('{}-{} ordered {} subscription service from {}.'.format(self.name, self.entity_id, item, counterparty.name))
				return order_subscription_event
			ledger.journal_entry(order_subscription_event)
			return True
		else:
			print('{}-{} does not have enough cash to pay for {} subscription. Cash: {}'.format(self.name, self.entity_id, item, cash))
			#self.item_demanded(item, qty, cost=True) # TODO Decide how to handle
			counterparty.adj_price(item, qty=1, direction='down')

	def cancel_subscription(self, item, counterparty, price=0, qty=-1):
		cancel_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Cancelled ' + item, item, price, qty, 'Subscription Info', 'Cancel Subscription', 0 ]
		end_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'End ' + item, item, price, qty, 'End Subscription', 'Subscription Info', 0 ]
		cancel_subscription_event = [cancel_subscription_entry, end_subscription_entry]
		ledger.journal_entry(cancel_subscription_event)
		counterparty.adj_price(item, qty=1, direction='down')
		return cancel_subscription_event

	def check_subscriptions(self, counterparty=None, check=False):
		ledger.set_entity(self.entity_id)
		subscriptions_list = ledger.get_qty(accounts=['Subscription Info'])
		#print('Subscriptions List: \n{}'.format(subscriptions_list))
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		subscriptions_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Subscription Info') & (ledger.gl['credit_acct'] == 'Order Subscription') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Subscriptions TXNs: \n{}'.format(subscriptions_txns))
		ledger.reset()
		if not subscriptions_list.empty:
			for index, subscription in subscriptions_list.iterrows():
				item = subscription['item_id']
				counterparty, event_id = self.get_counterparty(subscriptions_txns, rvsl_txns, item, 'Sell Subscription')
								# Check is fulltime job is still required
				items_req = world.items[world.items['requirements'].str.contains(item, na=False)].reset_index()
				qty_active = ledger.get_qty(items=list(items_req['item_id'].values))
				#print('Qty Active: \n{}'.format(qty_active))
				if isinstance(qty_active, pd.DataFrame):
					if qty_active.empty:
						qty_active = 0
					else:
						qty_active = True
				if not qty_active:
					self.cancel_subscription(item, counterparty)
				else:
					self.pay_subscription(subscription['item_id'], counterparty, world.get_price(subscription['item_id'], counterparty.entity_id), subscription['qty'], check=check)

	def pay_subscription(self, item, counterparty, price=None, qty='', buffer=False, first=False, check=False):
		if price is None:
			price = world.get_price(item, counterparty.entity_id) # TODO Get price from subscription order
		if first:
			subscription_state = 1
		else:
			ledger.set_entity(self.entity_id)
			subscription_state = ledger.get_qty(items=item, accounts=['Subscription Info'])
			ledger.reset()
			if subscription_state:
				subscription_state = int(subscription_state)
		#print('Subscription State: {}'.format(subscription_state))
		if not subscription_state:
			return
		pay_subscription_event = []
		for _ in range(subscription_state):
			incomplete, entries, time_required = self.fulfill(item, qty=1, reqs='usage_req', amts='use_amount', check=check)
			pay_subscription_event += entries
			if check:
				continue
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if cash >= price and not incomplete:
				pay_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Payment for ' + item, item, price, qty, 'Subscription Expense', 'Cash', price ]
				charge_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Received payment for ' + item, item, price, qty, 'Cash', 'Subscription Revenue', price ]
				pay_subscription_event += [pay_subscription_entry, charge_subscription_entry]
				if buffer:
					counterparty.adj_price(item, qty=1, direction='up_low')
					continue
				ledger.journal_entry(pay_subscription_event)
				counterparty.adj_price(item, qty=1, direction='up_low')
			else:
				if not incomplete:
					print('{}-{} does not have enough cash to pay for {} subscription. Cash: {}'.format(self.name, self.entity_id, item, cash))
				else:
					print('{}-{} cannot fulfill the requirements to keep {} subscription.'.format(self.name, self.entity_id, item))
				if not first:
					self.cancel_subscription(item, counterparty)
		if not incomplete:
			return pay_subscription_event

	 # For testing
	def collect_material(self, item, qty=1, price=None, account='Inventory'):
		if price is None:
			price = world.get_price(item, 0)
		collect_mat_entry = [ ledger.get_event(), self.entity_id, world.now, 'Forage ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		collect_mat_event = [collect_mat_entry]
		ledger.journal_entry(collect_mat_event)
		return collect_mat_event

	 # For testing
	def find_item(self, item, qty=1, price=None, account='Equipment'):
		if price is None:
			price = world.get_price(item, 0)
		find_item_entry = [ ledger.get_event(), self.entity_id, world.now, 'Find ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		find_item_event = [find_item_entry]
		ledger.journal_entry(find_item_event)
		return find_item_event

	def deposit(self, amount, counterparty=None):
		# TODO Make only one bank allowed per gov and auto select that bank entity as the counter party
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= amount:
			bank_entry = [ ledger.get_event(), self.entity_id, world.now, 'Deposit cash with {}'.format(counterparty.name), '', '', '', 'Bank', 'Cash', amount ]
			deposit_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Deposit cash from {}'.format(self.name), '', '', '', 'Cash', 'Deposits', amount ]
			deposit_event = [bank_entry, deposit_entry]
			ledger.journal_entry(deposit_event)
			return deposit_event
		else:
			print('{} does not have {} to deposit with {}. Cash held: {}'.format(self.name, amount, counterparty.name, cash))

	def withdrawal(self, amount, counterparty=None):
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Bank']) # TODO Fix that this assumes only one bank
		ledger.reset()
		if cash >= amount:
			bank_entry = [ ledger.get_event(), self.entity_id, world.now, 'Withdraw cash from {}'.format(counterparty.name), '', '', '', 'Cash', 'Bank', amount ]
			withdrawal_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Withdraw cash to {}'.format(self.name), '', '', '', 'Deposits', 'Cash', amount ]
			withdrawal_event = [bank_entry, withdrawal_entry]
			ledger.journal_entry(withdrawal_event)
			return withdrawal_event
		else:
			print('{} does not have {} to withdraw from {}. Cash held in bank: {}'.format(self.name, amount, counterparty.name, cash))

	def loan(self, amount, counterparty=None, item=None):
		if item is None:
			item = 'Credit Line'
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		ledger.set_entity(counterparty.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		qty = 1
		if cash >= amount:
			loan_entry = [ ledger.get_event(), self.entity_id, world.now, 'Loan cash from {}'.format(counterparty.name), item, '', '', 'Cash', 'Loan', amount ]
			lend_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Lend cash to {}'.format(self.name), item, '', '', 'Loans Receivable', 'Cash', amount ]
			loan_event = [loan_entry, lend_entry]
			ledger.journal_entry(loan_event)
			return loan_event
		else:
			print('{} does not have {} to loan to {}. Cash held by bank: {}'.format(counterparty.name, amount, self.name, cash))

	def repay(self, amount, counterparty=None, item=None):
		if item is None:
			item = 'Credit Line'
		if counterparty is None:
			counterparty = world.gov.bank
		if counterparty is None:
			print('{} has not founded their central bank yet. Incorporate a Bank to do so.'.format(world.gov))
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		qty = 1
		if cash >= amount:
			loan_repay_entry = [ ledger.get_event(), self.entity_id, world.now, 'Repay loan to {}'.format(counterparty.name), item, '', '', 'Loan', 'Cash', amount ]
			lend_repay_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Lend repayment from {}'.format(self.name), item, '', '', 'Cash', 'Loans Receivable', amount ]
			loan_repay_event = [loan_repay_entry, lend_repay_entry]
			ledger.journal_entry(loan_repay_event)
			return loan_repay_event
		else:
			print('{} does not have {} to repay loan to {}. Cash held by bank: {}'.format(self.name, amount, counterparty.name, cash))

	def check_interest(self, item=None):
		if item is None:
			item = 'Credit Line'
		ledger.set_entity(self.entity_id)
		loan_bal = ledger.balance_sheet(['Loan'])
		ledger.reset()
		if loan_bal:
			# TODO Return bs of items with balance for given accounts
			counterparty = world.gov.bank
			int_rate_fix = world.items.loc[item, 'int_rate_fix']
			int_rate_var = 0 # TODO Add var int logic and support
			rate = int_rate_fix + int_rate_var
			period = 1 / 365 # TODO Add frequency logic
			int_amount = round(loan_bal * rate * period, 2)
			int_exp_entry = [ ledger.get_event(), self.entity_id, world.now, 'Interest expense for {}'.format(item), '', '', '', 'Interest Expense', 'Cash', int_amount ]
			int_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Interest income from {}'.format(item), '', '', '', 'Cash', 'Interest Income', int_amount ]
			# TODO Add bank interest revenue entry
			int_exp_event = [int_exp_entry, int_rev_entry]
			ledger.journal_entry(int_exp_event)

	def depreciation_check(self, items=None): # TODO Add support for explicitly provided items
		if items is None:
			ledger.set_entity(self.entity_id)
			items_list = ledger.get_qty(accounts=['Buildings','Equipment','Inventory','In Use'])
			#print('Dep. Items List: \n{}'.format(items_list))
			ledger.reset()
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

	def depreciation(self, item, lifespan, metric, uses=1, buffer=False, v=False):
		if (metric == 'ticks') or (metric == 'usage'):
			#item_type = world.get_item_type(item)
			asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment','Inventory','In Use'], item=item) # TODO Maybe support other accounts
			if asset_bal == 0:
				return [], None
			depreciation_event = []
			if v: print('Asset Bal for {}: {}'.format(item, asset_bal))
			dep_amount = (asset_bal / lifespan) * uses
			if v: print('Dep. amount for {}: {}'.format(item, dep_amount))
			accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
			if v: print('Accum. Dep. for {}: {}'.format(item, accum_dep_bal))
			remaining_amount = asset_bal - accum_dep_bal
			if dep_amount > remaining_amount:
				uses = remaining_amount / (asset_bal / lifespan)
				dep_amount = remaining_amount
				new_qty = int(math.ceil(uses / lifespan))
				print('The {} breaks for the {}-{}. Another {} are required to use.'.format(item, self.name, self.entity_id, new_qty))
				# Try to purchase a new item if current one breaks
				outcome = self.purchase(item, new_qty)
				if outcome:
					entries, new_uses = self.depreciation(item, lifespan, metric, uses, buffer)
					if entries:
						depreciation_event += entries
						uses += new_uses
			#print('Depreciation: {} {} {}'.format(item, lifespan, metric))
			depreciation_entry = [ ledger.get_event(), self.entity_id, world.now, 'Depreciation of ' + item, item, '', '', 'Depreciation Expense', 'Accumulated Depreciation', dep_amount ]
			depreciation_event = [depreciation_entry]
			if buffer:
				return depreciation_event, uses
			if metric == 'usage':
				print('{}-{} uses {} {} times.'.format(self.name, self.entity_id, item, uses))
			ledger.journal_entry(depreciation_event)
			return depreciation_event, uses

		if (metric == 'spoilage') or (metric == 'obsolescence'):
			#print('Spoilage: {} {} days {}'.format(item, lifespan, metric))
			ledger.refresh_ledger()
			#print('GL: \n{}'.format(ledger.gl.tail()))
			rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			# Get list of Inventory txns
			inv_txns = ledger.gl[(ledger.gl['debit_acct'] == 'Inventory')
				& (ledger.gl['item_id'] == item)
				& (~ledger.gl['event_id'].isin(rvsl_txns))]
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
					date_done = (datetime.datetime.strptime(inv_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=lifespan)).date()
					#print('Date Done: {}'.format(date_done))
					# If the time elapsed has passed
					if date_done == world.now:
						ledger.set_entity(self.entity_id)
						qty = ledger.get_qty(item, 'Inventory')
						if qty == 0:
							print('{}-{} spoilage TXNs for {} {} returning zero.'.format(self.name, self.entity_id, qty, item))
							return
						txns = ledger.hist_cost(qty, item, 'Inventory', remaining_txn=True)
						ledger.reset()
						if not isinstance(txns, pd.DataFrame):
							print('{}-{} spoilage TXNs for {} {} returning zero.'.format(self.name, self.entity_id, qty, item))
							return
						# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
						# 	print('{}-{} spoilage TXNs for {} {}: \n{}'.format(self.name, self.entity_id, qty, item, txns)) # Debug
							# print('Looking fo TXN ID: {}'.format(txn_id))
						#print('Spoilage QTY: {}'.format(qty))
						if txn_id in txns.index:
							txn_qty = txns[txns.index == txn_id]['qty'].iloc[0]
							#print('Spoilage TXN QTY: {}'.format(txn_qty))
							# Book thes spoilage entry
							if qty < txn_qty:
								spoil_entry = [[ inv_lot[0], inv_lot[1], world.now, inv_lot[4] + ' spoilage', inv_lot[4], inv_lot[5], qty or '', 'Spoilage Expense', 'Inventory', inv_lot[5] * qty ]]
							else:
								spoil_entry = [[ inv_lot[0], inv_lot[1], world.now, inv_lot[4] + ' spoilage', inv_lot[4], inv_lot[5], inv_lot[6] or '', 'Spoilage Expense', 'Inventory', inv_lot[9] ]]
							ledger.journal_entry(spoil_entry)
							self.adj_price(item, qty, direction='down_high')

	def impairment(self, item, amount):
		# TODO Maybe make amount default to None and have optional impact or reduction parameter
		# item_type = world.get_item_type(item)
		# asset_bal = ledger.balance_sheet(accounts=[item_type], item=item)

		impairment_entry = [ ledger.get_event(), self.entity_id, world.now, 'Impairment of ' + item, item, '', '', 'Loss on Impairment', 'Accumulated Impairment Losses', amount ]
		impairment_event = [impairment_entry]
		ledger.journal_entry(impairment_event)
		return impairment_event

	def derecognize(self, item, qty):
		# TODO Check if item in use
		# TODO Check if item uses land and release that land
		#item_type = world.get_item_type(item)
		asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment'], item=item)# TODO Maybe support other accounts
		if asset_bal == 0:
				return
		accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
		accum_imp_bal = ledger.balance_sheet(accounts=['Accumulated Impairment Losses'], item=item)
		accrum_reduction = abs(accum_dep_bal) + abs(accum_imp_bal)
		if asset_bal == accrum_reduction:
			derecognition_event = []
			item_info = world.items.loc[item]
			if item_info[reqs] is None or item_info[amts] is None:
				return None, [], None
			requirements = [x.strip() for x in item_info[reqs].split(',')]
			amounts = [x.strip() for x in item_info[amts].split(',')]
			amounts = list(map(float, amounts))
			#requirements_details = list(itertools.zip_longest(requirements, requirement_types, amounts))
			for i, requirement in enumerate(requirements):
				requirement_type = world.get_item_type(requirement)
				if requirement_type == 'Land':
					req_qty = amounts[i] # TODO Support modifiers
					req_price = world.get_price(requirement, self.entity_id)
					release_entry = [ ledger.get_event(), self.entity_id, world.now, 'Release ' + requirement + ' used by ' + item, requirement, req_price, req_qty, 'Land', 'In Use', req_price * req_qty ]
					derecognition_event += [release_entry]

			derecognition_entry = [ ledger.get_event(), self.entity_id, world.now, 'Derecognition of ' + item, item, asset_bal / qty, qty, 'Accumulated Depreciation', 'Equipment', asset_bal ]
			derecognition_event += [derecognition_entry]
			ledger.journal_entry(derecognition_event)

	def action(self, command=None, external=False):
		if command is None: # TODO Allow to call bs command from econ.py
			command = args.command
		if command is None and not external:
			command = input('Enter an action or "help" for more info: ')
		# TODO Add help command to list full list of commands
		if command.lower() == 'select':
			for entity in world.gov.get(Individual):
				print('{} Hours: {}'.format(entity, entity.hours))
			print()
			for entity in world.gov.get(Corporation):
				print('{}'.format(entity))
			while True:
				try:
					selection = input('Enter an entity ID number: ')
					if selection == '':
						return
					selection = int(selection)
				except ValueError:
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, world.gov.get(ids=True, envs=False)))
					continue
				if selection not in world.gov.get(ids=True, envs=False):
					print('"{}" is not a valid entity ID selection. Must be one of the following numbers: \n{}'.format(selection, world.gov.get(ids=True, envs=False)))
					continue
				world.selection = factory.get_by_id(selection)
				break
			return world.selection
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
			while True: # TODO Add support for multiple founders
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
						counterparty = factory.get_by_id(counterparty)
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
					if qty <= 0:
						continue
					while True:
						others = input('Any other founders? (Y/N): ')
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
		elif command.lower() == 'claimland':
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
					counterparty = input('Enter an entity ID number to claim from ({} for nature): '.format(world.env.entity_id))
					if counterparty == '':
						return
					counterparty = int(counterparty)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, factory.get_all_ids()))
					continue
				if counterparty not in factory.get_all_ids():
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, factory.get_all_ids()))
					continue
				counterparty = factory.get_by_id(counterparty)
				break
			price = 0
			self.claim_land(qty, price, item.title(), counterparty)
		elif command.lower() == 'hire':
			while True:
				item = input('Enter type of job to hire for: ')
				if item == '':
					return
				if world.valid_item(item, 'Labour') or world.valid_item(item, 'Job'):
					break
				else:
					print('Not a valid entry.')
					continue
			worker = self.worker_counterparty(item.title(), only_avail=True, qualified=True)
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
				self.accru_wages(item.title(), worker, hours)
		elif command.lower() == 'study':
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
					hours = input('Enter number of hours to study {}: '.format(item))
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
			self.produce(item.title(), qty=hours)
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
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, factory.get_all_ids()))
					continue
				if counterparty not in factory.get_all_ids():
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, factory.get_all_ids()))
					continue
				counterparty = factory.get_by_id(counterparty)
				break
			self.gift(item.title(), qty, counterparty)
		elif command.lower() == 'purchase':
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
					qty = input('Enter quantity of {} item to purchase: '.format(item))
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
		elif command.lower() == 'recurproduce':
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
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.produce(item.title(), qty)
		elif command.lower() == 'produce': # TODO Make this default and change other to autoproduce command
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
						return
					qty = int(qty)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if qty <= 0:
						continue
					break
			self.produce(item.title(), qty, man=True)
		elif command.lower() == 'autoproduce':
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
						return
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
					freq = input('Enter number of days between production of {} {} (0 for daily): '.format(qty, item))
					if freq == '':
						return
					freq = int(freq)
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
				else:
					if freq < 0:
						continue
					break
			self.set_produce(item.title(), qty, freq)
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
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, factory.get_all_ids()))
					continue
				if counterparty not in factory.get_all_ids():
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, factory.get_all_ids()))
					continue
				counterparty = factory.get_by_id(counterparty)
				break
			target = input('Enter an item or Individual to attack: ') # TODO Validate item or Individual
			if target == '':
				return
			self.use_item(item.title(), qty, counterparty, target)
		elif command.lower() == 'birth':
			while True:
				try:
					counterparty = input('Enter an entity ID number to conceive with: ')
					if counterparty == '':
						return
					counterparty = int(counterparty)
				except ValueError:
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, world.gov.get(Individual, ids=True)))
					continue
				if counterparty not in world.gov.get(Individual, ids=True):
					print('"{}" is not a valid entry. Must be one of the following numbers: \n{}'.format(counterparty, world.gov.get(Individual, ids=True)))
					continue
				counterparty = factory.get_by_id(counterparty)
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
			self.birth(counterparty, amount_1, amount_2)
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
			self.dividend(div_rate)
		elif command.lower() == 'price':
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
			self.loan(amount, counterparty, item=None)
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
		elif command.lower() == 'demand':
			print('World Demand as of {}: \n{}'.format(world.now, world.demand))
		elif command.lower() == 'auto':
			print('World Auto Produce as of {}: \n{}'.format(world.now, world.produce_queue))
		elif command.lower() == 'items':
			print('World Items Available: \n{}'.format(world.items.index.values))
			while True:
				item = input('\nEnter an item to see all it\'s properties: ')
				if item == '':
					return
				if world.valid_item(item):
					break
				else:
					print('Not a valid entry.')
					continue
			with pd.option_context('display.max_colwidth', 200):
				print('{}: \n{}'.format(item.title(), world.items.loc[[item.title()]].squeeze()))
		elif command.lower() == 'needs':
			print('Global Needs: \n{}'.format(world.global_needs))
			while True:
				need = input('\nEnter a need to see all the items that satisfy it: ')
				if need == '':
					return
				if world.valid_need(need):
					break
				else:
					print('Not a valid entry.')
					continue
			need_items = world.items[world.items['satisfies'].str.contains(need.title(), na=False)].index.values
			print('Items that satisfy {}: \n{}'.format(need.title(), need_items))
		elif command.lower() == 'help':
			commands = {
				'select': 'Choose a different entity (Individual or Corporation.',
				'needs': 'See a list of all needs in the sim and list items that satisfy those needs.',
				'items': 'See a list of all available items and details for specific items.',
				'incorp': 'Incorporate a company to produce items.',
				'claimland': 'Claim land for free, but it must be defended.',
				'produce': 'Produce items.',
				'consume': 'Consume items.',
				'autoproduce': 'Produce items automatically.',
				'purchase': 'Purchase items.',
				'use': 'Use an item.',
				'hire': 'Hire a part-time or full-time worker.',
				'study': 'Study education and skills as an Individual to improve.',
				'attack': 'Attack another Individual or item with an item.',
				'birth': 'Have a child with another Individual.',
				'dividend': 'Declare dividends for a Corporation.',
				'demand': 'See the demand table.',
				'auto': 'See the auto production queue table.',
				'skip': 'Skip an entities turn even if they have hours left.',
				'end': 'End the day even if multiple entities have hours left.',
				'exit': 'Exit out of the sim.'
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
			# for k, v in commands.items():
			# 	print('{}: {}'.format(k, v))
		elif command.lower() == 'more':
			commands = {
				'recurproduce': 'Produce items, this will also attempt to aquire any requirements.',
				'gift': 'Gift cash or items between entities.',
				'deposit': 'Deposit cash with the bank.',
				'withdraw': 'Withdraw cash from the bank.',
				'loan': 'Borrow cash from the bank.',
				'repay': 'Repay cash borrowed from the bank.',
				'price': 'Set the price of items.',
				'exit': 'Exit out of the sim.'
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
		elif command.lower() == 'skip':
			self.set_hours(MAX_HOURS)
		elif command.lower() == 'end':
			# world.end = True
			return 'end'
		elif command.lower() == 'exit':
			exit()
		else:
			print('"{}" is not a valid command. Type "exit" to close or "help" for more options.'.format(command))
		# else:
		# 	acct.main(command, external=True)
		# if external:
		# 	# break
		# 	return 'end'

class Individual(Entity):
	def __init__(self, name, items, needs, government, hours=12, current_need=None, parents=(None, None), entity_id=None):
		super().__init__(name) # TODO Is this needed?
		if isinstance(parents, str):
			parents = parents.replace('(', '').replace(')', '')
			parents = tuple(x.strip() for x in parents.split(','))
		#print('Parents Start: {}\n{}'.format(parents, type(parents)))

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

		# Note: The 2nd to 5th values are for another program
		entity_data = [ (name, 0.0, 1, 100, 0.5, 'iex', self.__class__.__name__, government, hours, needs, max_need, decay_rate, threshold, current_need, str(parents), None, items) ] # TODO Maybe add active bool field	
		# print('Entity Data: {}'.format(entity_data))

		if not os.path.exists('db/' + args.database) or args.reset:
			if entity_id is None:
				self.entity_id = accts.add_entity(entity_data)
			else:
				accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			self.entity_id = entity_id
		self.name = name
		self.dead = False
		self.government = government
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		self.parents = parents
		print('\nCreate Individual: {} | entity_id: {}'.format(self.name, self.entity_id))
		print('Citizen of Government: {}'.format(self.government))
		print('Parents: {}'.format(self.parents))
		self.hours = hours
		self.setup_needs(entity_data)
		for need in self.needs:
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))

	def __str__(self):
		return 'Indv: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Indv: {} | {}'.format(self.name, self.entity_id)

	def set_hours(self, hours_delta=0):
		self.hours -= hours_delta
		if self.hours < 0:
			self.hours = 0
		cur = ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET hours = ?
			WHERE entity_id = ?;
		'''
		values = (self.hours, self.entity_id)
		cur.execute(set_need_query, values)
		ledger.conn.commit()
		cur.close()
		return self.hours

	def reset_hours(self):
		self.hours = MAX_HOURS
		return self.hours

	def setup_needs(self, entity_data):
		# self.needs = collections.defaultdict(dict)
		self.needs = collections.OrderedDict()
		needs_names = [x.strip() for x in entity_data[0][9].split(',')]
		needs_max = [x.strip() for x in str(entity_data[0][10]).split(',')]
		decay_rate = [x.strip() for x in str(entity_data[0][11]).split(',')]
		threshold = [x.strip() for x in str(entity_data[0][12]).split(',')]
		current_need = [x.strip() for x in str(entity_data[0][13]).split(',')]
		for need in needs_names:
			self.needs[need] = {}
			for i in range(len(needs_names)): # TODO Fix pointless looping over all needs when not all needs are in dict
				self.needs[need]['Max Need'] = int(needs_max[i])
				self.needs[need]['Decay Rate'] = int(decay_rate[i])
				self.needs[need]['Threshold'] = int(threshold[i])
				self.needs[need]['Current Need'] = int(current_need[i])
		# print(self.needs)
		return self.needs

	def set_need(self, need, need_delta, forced=False, attacked=False, v=False):
		if v: print('{}-{} sets need {} down by {}'.format(self.name, self.entity_id, need, need_delta))
		if self not in factory.registry[Individual]:
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
		cur = ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET current_need = ?
			WHERE entity_id = ?;
		'''
		values = (current_need_all, self.entity_id)
		cur.execute(set_need_query, values)
		ledger.conn.commit()
		cur.close()
		if self.needs[need]['Current Need'] <= 0:
			self.inheritance()
			factory.destroy(self)
			if forced:
				print('{} died due to natural causes.'.format(self.name))
			elif attacked:
				print('{} died due to attack.'.format(self.name))
			else:
				print('{} died due to {}.'.format(self.name, need))
			self.dead = True
		world.entities = accts.get_entities().reset_index()
		return self.needs[need]['Current Need']

	def birth(self, counterparty=None, amount_1=None, amount_2=None):
		# TODO Have birth take up time
		time_required = 12
		if self.hours < time_required:
			print('{} does not have enough time to give birth.'.format(self.name))
			return
		else:
			self.set_hours(time_required)
		print('\nPerson is born!')
		if amount_1 is None and amount_2 is None:
			amount_1 = INIT_CAPITAL / 2
			amount_2 = INIT_CAPITAL / 2
		entities = accts.get_entities()
		if counterparty is None:
			individuals = factory.registry[Individual]
			# print('Individuals: {}'.format(individuals))
			self.entity_ids = [individual.entity_id for individual in individuals]
			if self.entity_id in self.entity_ids:
				self.entity_ids.remove(self.entity_id)
			# print('Entity IDs Before: {}'.format(self.entity_ids))
			if not self.entity_ids:
				print('No one else is left to have a child with {}.'.format(self.name))
				# return
				print('{} clones themselves.'.format(self.name))
				counterparty = self
			else:
			# random.shuffle(self.entity_ids)
			# print('Entity IDs: {}'.format(self.entity_ids))
			# Choose random partner if none is provided
			# counterparty = factory.get_by_id(random.choice(self.entity_ids))
			# Choose wealthiest individual besides self for partner
				counterparty = factory.get_by_id(self.entity_ids[-1])
		gift_event = []
		ledger.set_entity(self.entity_id)
		cash1 = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if amount_1 is None:
			amount_1 = 0
		if cash1 >= amount_1:
			gift_entry1 = [ ledger.get_event(), self.entity_id, world.now, 'Gift cash to child', '', '', '', 'Gift Expense', 'Cash', amount_1 ]
		else:
			print('{} does not have ${} in cash to give birth with {}.'.format(self.name, amount_1, counterparty.name))
			return
		ledger.set_entity(counterparty.entity_id)
		cash2 = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if amount_2 is None:
			amount_2 = 0
		if cash2 >= amount_2:
			gift_entry2 = [ ledger.get_event(), counterparty.entity_id, world.now, 'Gift cash to child', '', '', '', 'Gift Expense', 'Cash', amount_2 ]
		else:
			print('{} does not have ${} in cash to have child with {}.'.format(counterparty.name, amount_2, self.name))
			return
			# TODO Support looping through counterparties if first does not have enough cash
			# self.entity_ids.remove(counterparty.entity_id)
			# for entity in self.entity_ids:
			# 	counterparty = factory.get_by_id(entity)

		gift_event += [gift_entry1, gift_entry2]

		self.indiv_items_produced = list(world.items[world.items['producer'].str.contains('Individual', na=False)].index.values) # TODO Move to own function
		self.indiv_items_produced = ', '.join(self.indiv_items_produced)
		#print('Individual Production: {}'.format(self.indiv_items_produced))
		last_entity_id = entities.reset_index()['entity_id'].max() # TODO Maybe a better way of doing this
		#print('Last Entity ID: {}'.format(last_entity_id))
		factory.create(Individual, 'Person-' + str(last_entity_id + 1), self.indiv_items_produced, world.global_needs, self.government, parents=(self.entity_id, counterparty.entity_id))
		individual = factory.get_by_id(last_entity_id + 1)
		world.prices = pd.concat([world.prices, individual.prices])

		gift_event += individual.capitalize(amount=amount_1 + amount_2, buffer=True) # TODO Hardcoded amount for now

		ledger.journal_entry(gift_event)

	def inheritance(self, counterparty=None):
		# Remove any items that exist on the demand table for this entity
		demand_items = world.demand[world.demand['entity_id'] == self.entity_id]
		if not demand_items.empty:
			to_drop = demand_items.index.tolist()
			world.demand = world.demand.drop(to_drop).reset_index(drop=True)
			world.set_table(world.demand, 'demand')
			print('{} removed {} indexes for items from demand list.\n'.format(self.name, to_drop))

		# Quit any current jobs
		ledger.set_entity(self.entity_id)
		current_jobs = ledger.get_qty(accounts=['Start Job'])
		ledger.reset()
		for index, job in current_jobs.iterrows():
			item = job['item_id']
			worker_state = job['qty']
			if worker_state >= 1: # Should never be greater than 1 for the same counterparty
				worker_state = int(worker_state)
				ledger.set_entity(self.entity_id)
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				hire_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Start Job') & (ledger.gl['credit_acct'] == 'Worker Info') ) & (ledger.gl['item_id'] == item) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				ledger.reset()
				cp_job, event_id = self.get_counterparty(hire_txns, rvsl_txns, item, 'Worker Info')
				for _ in range(worker_state): # TODO This for loop shouldn't be necessary
					self.fire_worker(item, cp_job, quit=True)

		# Cancel any current subscriptions
		ledger.set_entity(self.entity_id)
		current_subs = ledger.get_qty(accounts=['Subscription Info'])
		ledger.reset()
		for index, sub in current_subs.iterrows():
			item = sub['item_id']
			sub_state = sub['qty']
			if sub_state >= 1:
				sub_state = int(sub_state)
				ledger.set_entity(self.entity_id)
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				sub_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Subscription Info') & (ledger.gl['credit_acct'] == 'Order Subscription') ) & (ledger.gl['item_id'] == item) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				ledger.reset()
				cp_sub, event_id = self.get_counterparty(sub_txns, rvsl_txns, item, 'Sell Subscription')
				for _ in range(sub_state):
					self.cancel_subscription(item, cp_sub)
		
		world.prices = world.prices.loc[world.prices['entity_id'] != self.entity_id]
		print('{} removed their prices for items from the price list.\n'.format(self.name))

		# Get the counterparty to inherit to
		if counterparty is None:
			counterparty = factory.get_by_id(self.parents[0])
			if counterparty not in factory.registry[Individual]:
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

		ledger.set_entity(self.entity_id)
		# Remove all job and subscription info entries
		ledger.gl = ledger.gl.loc[ledger.gl['credit_acct'] != 'Worker Info']
		ledger.gl = ledger.gl.loc[ledger.gl['debit_acct'] != 'Subscription Info']
		ledger.gl.fillna(0, inplace=True)
		consolidated_gl = ledger.gl.groupby(['item_id','debit_acct','credit_acct']).sum()
		ledger.reset()
		inherit_event = []
		for index, entry in consolidated_gl.iterrows():
			#print('Index: \n{}'.format(index))
			#print('Entry: \n{}'.format(entry))
			bequeath_entry = [ ledger.get_event(), self.entity_id, world.now, 'Bequeath to ' + counterparty.name, index[0], entry[2], entry[3], index[2], index[1], entry[4] ]
			inherit_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Inheritance from ' + self.name, index[0], entry[2], entry[3], index[1], index[2], entry[4] ]
			inherit_event += [bequeath_entry, inherit_entry]
		ledger.journal_entry(inherit_event)

	def need_decay(self, need, decay_rate=1):
		rand = 1
		if args.random:
			rand = random.randint(1, 3)
		decay_rate = self.needs[need]['Decay Rate'] * -1 * rand
		#print('{} Decay Rate: {}'.format(need, decay_rate))
		self.set_need(need, decay_rate)
		return decay_rate

	def threshold_check(self, need, threshold=100):
		threshold = self.needs[need]['Threshold']
		if self.needs[need]['Current Need'] < threshold:
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))
			print('{} threshold met for {}!'.format(need, self.name))
			self.address_need(need)

	def address_need(self, need):
		outcome = None
		items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs

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
		#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
		items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)

		items_info = items_info.sort_values(by='need_satisfy_rate', ascending=False)
		items_info.reset_index(inplace=True)
		# If first item is not available, try the next one
		for index, item in items_info.iterrows():
			item_choosen = items_info['item_id'].iloc[index]
			if not self.check_eligible(item_choosen):
				continue
			# TODO Support multiple satisfies
			satisfy_rate = float(items_info['need_satisfy_rate'].iloc[index])
			#print('Item Choosen: {}'.format(item_choosen))
			item_type = world.get_item_type(item_choosen)
			#print('Item Type: {}'.format(item_type))
			if item_type == 'Subscription':
				ledger.set_entity(self.entity_id)
				subscription_state = ledger.get_qty(items=item_choosen, accounts=['Subscription Info'])
				ledger.reset()
				if subscription_state:
					self.needs[need]['Current Need'] = self.needs[need]['Max Need']
				else:
					counterparty = self.subscription_counterparty(item_choosen)
					outcome = self.order_subscription(item_choosen, counterparty=counterparty, price=world.get_price(item_choosen, counterparty.entity_id))
				# qty_purchase = 1 # TODO Remove as was needed for demand call below

			if item_type == 'Service':
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_purchase = int(math.ceil(need_needed / satisfy_rate))
				#print('QTY Needed: {}'.format(qty_needed))
				outcome = self.purchase(item_choosen, qty_purchase)

			elif (item_type == 'Commodity') or (item_type == 'Component'):
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_needed = int(math.ceil(need_needed / satisfy_rate))
				#print('QTY Needed: {}'.format(qty_needed))
				ledger.set_entity(self.entity_id)
				qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
				ledger.reset()
				# TODO Attempt to use item before aquiring some
				if qty_held < qty_needed:
					qty_wanted = qty_needed - qty_held
					qty_avail = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					if qty_avail == 0:
						qty_avail = qty_wanted # Prevent purchase for 0 qty
					qty_purchase = min(qty_wanted, qty_avail)
					print('Satisfy need by purchasing: {} {}'.format(qty_purchase, item_choosen))
					outcome = self.purchase(item_choosen, qty_purchase)
					ledger.set_entity(self.entity_id)
					qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					ledger.reset()
					#print('QTY Held: {}'.format(qty_held))
					if qty_held < qty_wanted:
						outcome, time_required = self.produce(item_choosen, qty_wanted - qty_held)
						ledger.set_entity(self.entity_id)
						qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
						ledger.reset()
						#print('QTY Held: {}'.format(qty_held))
				if qty_held:
					self.consume(item_choosen, qty_held, need)

			elif item_type == 'Equipment':
				# TODO Decide how qty will work with time spent using item
				ledger.set_entity(self.entity_id)
				qty_held = ledger.get_qty(items=item_choosen, accounts=['Equipment'])
				ledger.reset()
				#print('QTY Held: {}'.format(qty_held))
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				uses_needed = int(math.ceil(need_needed / satisfy_rate))
				print('Uses Needed: {}'.format(uses_needed))
				event = []
				if qty_held == 0:
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
					outcome = self.purchase(item_choosen, qty_purchase)
				if qty_held > 0 or outcome:
					entries = self.use_item(item_choosen, uses_needed)
					if not entries:
						entries = []
					if entries is True:
						entries = []
					event += entries
					ledger.journal_entry(event)
					return event

	def adj_needs(self, item, qty=1):
		indiv_needs = list(self.needs.keys())
		#print('Indiv Needs: \n{}'.format(indiv_needs))
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
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))

class Environment(Entity):
	def __init__(self, name, entity_id=None):
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, None, None, None, None, None, self.__class__.__name__, None, None, None, None, None, None, None, None, None, None) ] # Note: The 2nd to 5th values are for another program
		if not os.path.exists('db/' + args.database) or args.reset:
			if entity_id is None:
				self.entity_id = accts.add_entity(entity_data)
			else:
				accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			self.entity_id = entity_id
		self.name = name
		self.government = None
		self.produces = None
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
		land_entry = [ ledger.get_event(), self.entity_id, date, item + ' created', item, price, qty, 'Land', 'Natural Wealth', price * qty ]
		land_event = [land_entry]
		ledger.journal_entry(land_event)


class Organization(Entity):
	def __init__(self, name):
		super().__init__(name)


class Corporation(Organization):
	def __init__(self, name, items, government, auth_shares=1000000, entity_id=None):
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, 0.0, 1, 100, 0.5, 'iex', self.__class__.__name__, government, None, None, None, None, None, None, None, auth_shares, items) ] # Note: The 2nd to 5th values are for another program
		if not os.path.exists('db/' + args.database) or args.reset:
			if entity_id is None:
				self.entity_id = accts.add_entity(entity_data)
			else:
				accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			self.entity_id = entity_id
		self.name = name
		self.government = government
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

	def list_shareholders(self, largest=False):
		ledger.reset()
		shareholders = ledger.get_qty(items=self.name, accounts='Investments', by_entity=True)
		if shareholders.empty:
			print('No shareholders listed for {}-{}. Try again the next day.\n'.format(self.name, self.entity_id))
			return
		# print('{}-{} shareholders: \n{}'.format(self.name, self.entity_id, shareholders))
		if largest:
			largest_shareholder = shareholders.loc[shareholders['qty'] == shareholders['qty'].max()]['entity_id'].values[0] # TODO Fix multiple Corporations with the same name
			# if len(largest_shareholder) >= 2:
			# 	largest_shareholder = largest_shareholder[0]
			print('{}-{} largest shareholder Entity ID: {}'.format(self.name, self.entity_id, largest_shareholder))
			return largest_shareholder
		else:
			print('{}-{} shareholders: \n{}'.format(self.name, self.entity_id, shareholders))
			return shareholders

	def declare_div(self, div_rate): # TODO Move this to corporation subclass
		item = self.name
		shareholders = ledger.get_qty(items=item, accounts='Investments', by_entity=True)
		if shareholders.empty:
			return
		total_shares = shareholders['qty'].sum()
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		#print('{}-{} cash: {}'.format(self.name, self.entity_id, cash))
		if cash < total_shares * div_rate:
			print('{}-{} does not have enough cash to pay dividend at a rate of {}.'.format(self.name, self.entity_id, div_rate))
			return
		div_event = []
		for index, shareholder in shareholders.iterrows():
			shares = shareholder[2]
			counterparty_id = shareholder[0]
			# TODO Add div accrual entries and payments
			div_rev_entry = [ ledger.get_event(), counterparty_id, world.now, 'Dividend received for ' + item, item, div_rate, shares, 'Cash', 'Dividend Income', shares * div_rate ]
			div_event += [div_rev_entry]
		# TODO This should book against Retained Earnings
		div_exp_entry = [ ledger.get_event(), self.entity_id, world.now, 'Dividend payment for ' + item, item, div_rate, total_shares, 'Dividend Expense', 'Cash', total_shares * div_rate ]
		div_event += [div_exp_entry]
		ledger.journal_entry(div_event)

	def dividend(self, div_rate=1):
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		#print('{}-{} cash: {}'.format(self.name, self.entity_id, cash))
		funding = ledger.balance_sheet(accounts=['Shares'], item=self.name)
		#print('{}-{} funding: {}'.format(self.name, funding))
		ledger.reset()
		if cash >= funding * 2:
			self.declare_div(div_rate=div_rate)

	def raise_capital(self):
		pass

class Government(Organization):
	def __init__(self, name, items=None, entity_id=None):
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, None, None, None, None, None, self.__class__.__name__, None, None, None, None, None, None, None, None, None, items) ] # Note: The 2nd to 5th values are for another program
		if not os.path.exists('db/' + args.database) or args.reset:
			if entity_id is None:
				self.entity_id = accts.add_entity(entity_data)
			else:
				accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			self.entity_id = entity_id
		self.name = name
		self.government = self.entity_id
		self.produces = items
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		if self.produces is not None:
			self.produces = list(filter(None, self.produces))
		if self.produces is not None:
			self.prices = pd.DataFrame({'entity_id': self.entity_id, 'item_id': self.produces,'price': INIT_PRICE}).set_index('item_id')
		else:
			self.prices = pd.DataFrame(columns=['entity_id','item_id','price']).set_index('item_id')
		print('\nCreate Government: {} | entity_id: {}'.format(self.name, self.entity_id))

	def get(self, typ=None, ids=False, envs=True):
		entities = []
		if envs: # TODO Exclude environments
			# for entity in factory.get(typ):
			entities = [entity for entity in factory.get(typ) if entity.government == self.entity_id or entity.government is None]
		else:
			# for entity in factory.get(typ): # TODO Exclude environments
			entities = [entity for entity in factory.get(typ) if entity.government == self.entity_id]
		if ids:
			entities = [e.entity_id for e in entities]
		return entities

	def __str__(self):
		return 'Gov: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Gov: {} | {}'.format(self.name, self.entity_id)

# TODO Add Governmental org type for govnerment organizations

class NonProfit(Organization):
	def __init__(self, name, items, government, auth_qty=0, entity_id=None):
		super().__init__(name) # TODO Is this needed?
		entity_data = [ (name, None, None, None, None, None, self.__class__.__name__, None, None, None, None, None, None, None, None, None, items) ] # Note: The 2nd to 5th values are for another program
		if not os.path.exists('db/' + args.database) or args.reset:
			if entity_id is None:
				self.entity_id = accts.add_entity(entity_data)
			else:
				accts.add_entity(entity_data)
				self.entity_id = entity_id
		else:
			self.entity_id = entity_id
		self.name = name
		self.government = government
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
	def __init__(self):
		self.registry = collections.OrderedDict()
		self.registry[Individual] = []
		self.registry[Environment] = []
		self.registry[Organization] = []
		self.registry[Corporation] = []
		self.registry[Government] = []
		self.registry[NonProfit] = []
		# self.registry[Environment] = []

	def create(self, cls, *args, **kwargs):
		entity = cls(*args, **kwargs)  # create the instance
		self.register_instance(entity) # add to registry
		return entity

	def register_instance(self, entity):
		typ = type(entity)
		if typ not in self.registry:
			self.registry[typ] = []
		self.registry[typ].append(entity)

	def destroy(self, entity):
		typ = type(entity)
		index = self.get_pos(entity)
		return self.registry[typ].pop(index)

	def get(self, typ=None, ids=False):
		# TODO Maybe convert all for loops to list comprehensions
		if typ is None:
			typ = [*self.registry.keys()]
		if not isinstance(typ, (list, tuple)):
			typ = [typ]
		orgs = []
		for el in typ:
			orgs += self.registry[el]
		if ids:
			orgs = [e.entity_id for e in orgs]
		return orgs

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
					if name == entity.name.split('-')[0]:
						#print('Entity by Name: {}'.format(entity))
						#print('Entity Name by Name: {}'.format(entity.name))
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

#def main():
	# TODO Ledger gives a not defined error
	#pass

if __name__ == '__main__':
	t0_start = time.perf_counter()
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-c', '--command', type=str, help='A command for the program.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-P', '--players', type=int, default=1, help='The number of players in the econ sim.')
	parser.add_argument('-p', '--population', type=int, default=2, help='The number of people in the econ sim.')
	parser.add_argument('-r', '--reset', action="store_true", help='Reset the sim!')
	parser.add_argument('-rand', '--random', action="store_false", help='Remove randomness from the sim!')
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
	parser.add_argument('-t', '--time', type=int, help='The number of days the sim will run for.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital each player to start with.')
	parser.add_argument('-u', '--user', action="store_true", help='Play the sim!')
	args = parser.parse_args()

	if args.database is None:
		args.database = 'econ01.db'
	if args.capital is None:
		args.capital = 100000
	# command = None
	# if command is None:
	# 	command = args.command

	print(time_stamp() + 'Start Econ Sim | Players: {} | Population: {}'.format(args.players, args.population))
	if args.user:
		print(time_stamp() + 'Play the sim by entering commands. Type "help" for more info.')
	if (args.delay is not None) and (args.delay is not 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
	if args.random:
		if args.seed:
			print(time_stamp() + 'Randomness turned on with a seed of {}.'.format(args.seed))
			random.seed(args.seed)
		else:
			print(time_stamp() + 'Randomness turned on with no seed provided.')
			random.seed()
	if args.time is not None:
		END_DATE = (datetime.datetime(1986,10,1).date() + datetime.timedelta(days=args.time)).strftime('%Y-%m-%d')
	if END_DATE is None:
		print(time_stamp() + 'Econ Sim has no end date and will end if everyone dies.')
	else:
		print(time_stamp() + 'Econ Sim has an end date of {} or if everyone dies.'.format(END_DATE))
	if args.reset:
		delete_db(args.database)
	accts = acct.Accounts(args.database, econ_accts)
	ledger = acct.Ledger(accts)
	factory = EntityFactory()
	world = World(factory, args.players, args.population)
	
	# pr = cProfile.Profile()
	# pr.enable()
	
	while True:
		world.update_econ()
		if world.end:
			break
		time.sleep(args.delay)

	# pr.disable()
	# pr.print_stats(sort='time')

	t0_end = time.perf_counter()
	print(time_stamp() + 'End of Econ Sim! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))