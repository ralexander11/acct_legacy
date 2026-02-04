import pandas as pd
import numpy as np
import sqlite3
import argparse
import datetime
import logging
import warnings
import time
import sys
import yaml
# try:
# 	from rich import print
# except ImportError:
# 	pass
# from contextlib import contextmanager


DISPLAY_WIDTH = 98
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 30)
pd.options.display.float_format = '${:,.2f}'.format
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

acct_cols = {
	'accounts': 'text PRIMARTY KEY',
	'child_of': 'text NOT NULL',
	'acct_role': 'text', # TODO Make this NOT NULL eventually
}

# TODO Move the below to a json file
roles_data = [ # TODO Non-cash data labels are not complete yet
	## Current Assets:
	{'role': 'Cash & Cash Equivalents', 'current': True, 'non-cash': False},
	{'role': 'Accounts Receivable', 'current': True, 'non-cash': False},
	{'role': 'Allowance for Doubtful Accounts', 'current': True, 'non-cash': True},
	{'role': 'Inventory', 'current': True, 'non-cash': False},
	{'role': 'Prepaid Expenses', 'current': True, 'non-cash': True},
	{'role': 'Deferred Tax Current Asset', 'current': True, 'non-cash': True},
	{'role': 'Other Current Assets', 'current': True, 'non-cash': False},

	## Non-Current Assets:
	{'role': 'Property, Plant & Equipment', 'current': False, 'non-cash': False},
	{'role': 'Accumulated Depreciation', 'current': False, 'non-cash': True},
	{'role': 'Intangible Assets', 'current': False, 'non-cash': False},
	{'role': 'Accumulated Amortization', 'current': False, 'non-cash': True},
	{'role': 'Investments', 'current': False, 'non-cash': False},
	{'role': 'Deferred Tax Asset', 'current': False, 'non-cash': True},
	{'role': 'Loans Made', 'current': False, 'non-cash': False},
	{'role': 'Goodwill', 'current': False, 'non-cash': True},
	{'role': 'Other Non-Current Assets', 'current': False, 'non-cash': False},

	## Current Liabilities:
	{'role': 'Accounts Payable', 'current': True, 'non-cash': False},
	{'role': 'Deferred Revenue', 'current': True, 'non-cash': False},
	{'role': 'Short Term Debt', 'current': True, 'non-cash': False},
	{'role': 'VAT/GST Payable', 'current': True, 'non-cash': False},
	{'role': 'Income Tax Liability', 'current': True, 'non-cash': False},
	{'role': 'Deferred Tax Current Liability', 'current': True, 'non-cash': False},
	{'role': 'Other Current Liabilities', 'current': True, 'non-cash': False},

	## Non-Current Liabilities:
	{'role': 'Long Term Debt', 'current': False, 'non-cash': False},
	{'role': 'Deferred Tax Liability', 'current': False, 'non-cash': False},
	{'role': 'Other Non-Current Liabilies', 'current': False, 'non-cash': False},

	## Equity:
	{'role': 'Retained Earnings', 'current': False, 'non-cash': True},
	{'role': 'Current Earnings', 'current': False, 'non-cash': True},
	{'role': 'Common Shares', 'current': False, 'non-cash': True},
	{'role': 'Preference Shares', 'current': False, 'non-cash': True},
	{'role': 'Distributions', 'current': False, 'non-cash': True},
	{'role': 'Non-Controlling Interest Equity', 'current': False, 'non-cash': True},
	{'role': 'Other Equity', 'current': False, 'non-cash': True},

	## Revenue:
	{'role': 'Sales Revenue', 'current': False, 'non-cash': False},
	{'role': 'Other Income', 'current': False, 'non-cash': False},
	{'role': 'Unrealized Gains', 'current': False, 'non-cash': True},
	{'role': 'Interest Income', 'current': False, 'non-cash': False},

	## Expense:
	{'role': 'COGS', 'current': False, 'non-cash': False},
	{'role': 'Labour Expense', 'current': False, 'non-cash': False},
	{'role': 'Fixed Expenses', 'current': False, 'non-cash': False},
	{'role': 'Variable Expenses', 'current': False, 'non-cash': False},
	{'role': 'Depreciation', 'current': False, 'non-cash': True},
	{'role': 'Amortization', 'current': False, 'non-cash': True},
	{'role': 'Impairment Loss', 'current': False, 'non-cash': True},
	{'role': 'Interest Expense', 'current': False, 'non-cash': False},
	{'role': 'Tax Expenses', 'current': False, 'non-cash': False},
	{'role': 'Deferred Tax Expense', 'current': False, 'non-cash': True},
	{'role': 'Unrealized Losses', 'current': False, 'non-cash': True},
	{'role': 'Share Based Compensation', 'current': False, 'non-cash': True},
	{'role': 'Non-Controlling Interest Expense', 'current': False, 'non-cash': False},
	{'role': 'Non-Cash Expenses', 'current': False, 'non-cash': True},
	{'role': 'Other Expenses', 'current': False, 'non-cash': False},
]

class Accounts:
	def __init__(self, conn=None, standard_accts=None, entities_table_name=None, items_table_name=None):# Accounts
		if conn is None:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
				self.website = True
				logging.debug('Website: {}'.format(self.website))
			except Exception as e:
				conn = sqlite3.connect('db/acct.db')
				self.website = False
				logging.debug('Website: {}'.format(self.website))
			self.db = 'acct.db'
		elif isinstance(conn, str):
			self.db = conn
			if conn == 'mem':
				conn = ':' + conn + 'ory:'
			elif conn == 'memory':
				conn = ':' + conn + ':'
			if '/' not in conn and conn != ':memory:':
				conn = 'db/' + conn
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/' + conn)
				self.website = True
				logging.debug('Website: {}'.format(self.website))
			except Exception as e:
				conn = sqlite3.connect(conn)
				self.website = False
				logging.debug('Website: {}'.format(self.website))
			self.convert_table(conn, 'accounts', acct_cols)
		# else:
		# 	print('Conn path: {}'.format(conn))
		# 	try:
		# 		conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
		# 		self.website = True
		# 		logging.debug('Website: {}'.format(self.website))
		# 	except Exception as e:
		# 		conn = sqlite3.connect('db/acct.db')
		# 		self.website = False
		# 		logging.debug('Website: {}'.format(self.website))

		# if args.database is not None:
		# 	self.db = args.database
		self.conn = conn

		try:
			self.refresh_accts()
			if entities_table_name is None:
				self.entities_table_name = 'entities'
			else:
				self.entities_table_name = entities_table_name
			if items_table_name is None:
				self.items_table_name = 'items'
			else:
				self.items_table_name = items_table_name
		except Exception as e:
			self.coa = None
			self.create_accts(standard_accts)
			# self.refresh_accts()
			if entities_table_name is None:
				self.entities_table_name = 'entities'
			else:
				self.entities_table_name = entities_table_name
			self.create_entities()
			if items_table_name is None:
				self.items_table_name = 'items'
			else:
				self.items_table_name = items_table_name
			self.create_items()

	def copy_db(self, db_name=None, dest_file=None, v=False):
		if v: print('Copying accounting system database.')
		if db_name is None:
			cur = self.conn.cursor()
			cur.execute('PRAGMA database_list')
			db_path = cur.fetchall()[0][-1]
			if v: print('DB Path:', db_path)
			db_name = db_path.rsplit('/', 1)[-1]
			if db_name == '':
				db_name = 'mem.db'
			cur.close()
			if v: print('DB Name:', db_name)
			if v: print('DB Name type:', type(db_name))
		if '/' not in db_name:
			db_name = 'db/' + db_name
		if dest_file is None:
			dest_file = db_name[:-3] + datetime.datetime.today().strftime('_%Y-%m-%d_%H-%M-%S') + '.db'
		if '/' not in dest_file:
			dest_file = 'db/' + dest_file
		if v: print('dest_file:', dest_file)
		if db_name == 'db/mem.db':
			file_conn = sqlite3.connect(dest_file)
			self.conn.backup(file_conn)
		else:
			import shutil
			shutil.copyfile(db_name, dest_file)
		print(f'Database copied from {db_name} to {dest_file}.')

	def convert_table(self, conn, table_name, schema, v=True):
		cur = conn.execute(f'PRAGMA table_info({table_name})')
		# row format: (cid, name, type, notnull, dflt_value, pk)
		existing_cols = {row[1] for row in cur.fetchall()}
		# if v: print(f'Existing columns of table {table_name}: {existing_cols}')
		if not existing_cols:
			return
		for column, col_type in schema.items():
			if column not in existing_cols:
				sql = f'ALTER TABLE {table_name} ADD COLUMN {column} {col_type}'
				conn.execute(sql)
				print(f'Added column: {column}')
		conn.commit()

	def create_accts(self, standard_accts=None):
		if standard_accts is None:
			standard_accts = []
		cols_sql = ',\n    '.join(f'{column} {col_type}' for column, col_type in acct_cols.items())
		create_accts_query = f'''
			CREATE TABLE IF NOT EXISTS accounts (
				-- acct_code text,
				{cols_sql}
					-- CHECK (status IN (
					-- 	'Fixed Expenses', 'Variable Expenses'
					-- ))
				-- acct_desc text
			);
			'''
		base_accts = [
			('Account','None',''),
			('Admin','Account',''),
			('Asset','Account',''),
			('Liability','Account',''),
			('Equity','Account',''),
			('Revenue','Equity',''),
			('Expense','Equity',''),
			('Transfer','Equity',''),
		]

		personal = [
			('Cash','Asset','Cash & Cash Equivalents'),
			('Chequing','Asset','Cash & Cash Equivalents'),
			('Savings','Asset','Cash & Cash Equivalents'),
			('Investments','Asset','Investments'),
			('Visa','Liability','Accounts Payable'),
			('Student Credit','Liability','Short Term Debt'),
			('Credit Line','Liability','Long Term Debt'),
			('Royal Credit Line','Liability','Long Term Debt'),
			('Uncategorized','Admin',''),
			('Info','Admin',''),
		]

		base_accts = base_accts + standard_accts + personal

		cur = self.conn.cursor()
		cur.execute(create_accts_query)
		self.conn.commit()
		cur.close()
		self.add_acct(base_accts)

	# TODO Maybe make entities a class
	def create_entities(self): # TODO Add command to book more entities
		create_entities_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.entities_table_name + ''' (
				entity_id INTEGER PRIMARY KEY,
				name text,
				currency text,
				framework text,
				comm real DEFAULT 0,
				min_qty INTEGER DEFAULT 1,
				max_qty INTEGER DEFAULT 100,
				liquidate_chance real DEFAULT 0.0,
				ticker_source text DEFAULT 'iex',
				entity_type text,
				government text,
				founder text,
				hours INTEGER,
				needs text,
				need_max INTEGER DEFAULT 100,
				decay_rate INTEGER DEFAULT 1,
				need_threshold INTEGER DEFAULT 100,
				current_need INTEGER DEFAULT 100,
				parents text,
				user text,
				auth_shares INTEGER,
				int_rate real,
				outputs text,
				obj BLOB
			);
			''' # TODO Add needs table?
		default_entities = ['''
			INSERT INTO ''' + self.entities_table_name + ''' (
				name,
				currency,
				framework,
				comm,
				min_qty,
				max_qty,
				liquidate_chance,
				ticker_source,
				entity_type,
				government,
				founder,
				hours,
				needs,
				need_max,
				decay_rate,
				need_threshold,
				current_need,
				parents,
				user,
				auth_shares,
				int_rate,
				outputs,
				obj
				)
				VALUES (
					'Person001',
					'CAD',
					'IFRS',
					0.0,
					1,
					100,
					0.5,
					'iex',
					'Individual',
					1,
					4,
					24,
					'Hunger',
					100,
					1,
					40,
					50,
					'(None,None)',
					'True',
					1000000,
					0.0,
					'Labour',
					NULL
				);
			'''] # TODO Rename outputs to produces
			# TODO Add field for currency and accounting framework

		cur = self.conn.cursor()
		cur.execute(create_entities_query)
		for entity in default_entities:
			print('Entities table created.')
			cur.execute(entity)
		self.conn.commit()
		cur.close()

	# Maybe make items a class
	def create_items(self):# TODO Add command to book more items
		create_items_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.items_table_name + ''' (
				item_id text PRIMARY KEY,
				int_rate_fix real,
				int_rate_var real,
				freq integer DEFAULT 365,
				child_of text,
				requirements text,
				amount text,
				capacity integer,
				hold_req text,
				hold_amount text,
				usage_req text,
				use_amount text,
				fulfill text,
				satisfies text,
				satisfy_rate text,
				productivity text,
				efficiency text,
				lifespan text,
				metric text DEFAULT 'ticks',
				dmg_type text,
				dmg text,
				res_type text,
				res text,
				byproduct text,
				byproduct_amt text,
				start_price text,
				producer text
			);
			''' # Metric can have values of 'ticks' or 'units' or 'spoilage'
		default_item = ['''
			INSERT INTO ''' + self.items_table_name + ''' (
				item_id,
				int_rate_fix,
				int_rate_var,
				freq,
				child_of,
				requirements,
				amount,
				capacity,
				hold_req,
				hold_amount,
				usage_req,
				use_amount,
				fulfill,
				satisfies,
				satisfy_rate,
				productivity,
				efficiency,
				lifespan,
				metric,
				dmg_type,
				dmg,
				res_type,
				res,
				byproduct,
				byproduct_amt,
				start_price,
				producer
				) VALUES (
					'credit_line_01',
					0.0409,
					NULL,
					365,
					'loan',
					'Bank',
					'1',
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					'Capital',
					1,
					NULL,
					NULL,
					3650,
					'ticks',
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					'Bank'
				);
			''']

		cur = self.conn.cursor()
		cur.execute(create_items_query)
		for item in default_item:
			print('Items table created.')
			cur.execute(item)
		self.conn.commit()
		cur.close()

	def refresh_accts(self):
		self.coa = pd.read_sql_query('SELECT * FROM accounts;', self.conn, index_col='accounts')
		return self.coa

	def print_accts(self):
		self.refresh_accts()
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.coa)
		print('-' * DISPLAY_WIDTH)
		return self.coa

	def drop_dupe_accts(self):
		self.coa = self.coa[~self.coa.index.duplicated(keep='first')]
		self.coa.to_sql('accounts', self.conn, if_exists='replace')
		self.refresh_accts()

	def add_acct(self, acct_data=None, v=False):
		if acct_data is not None:
			if isinstance(acct_data, pd.DataFrame):
				acct_data = acct_data.values.tolist()
			elif isinstance(acct_data, pd.Series):
				acct_data = [acct_data.tolist()]
			elif isinstance(acct_data, str):
				acct_data = [[x.strip() for x in acct_data.split(',')]]
			elif not isinstance(acct_data[0], (list, tuple)):
				acct_data = [acct_data]
		cur = self.conn.cursor()
		if acct_data is None:
			account = input('Enter the account name: ')
			child_of = input('Enter the parent account: ')
			acct_role = input('Enter the account role: ')
			# acct_code = 
			# acct_desc = 
			if child_of not in self.coa.index:
				print(f'\n{child_of} is not a valid account.')
				return
			if acct_role not in roles_data:
				print(f'\n{acct_role} is not a valid account role.')
				return
			details = (account, child_of, acct_role)
			cur.execute('INSERT INTO accounts VALUES (?,?,?)', details)
		else:
			for acct in acct_data: # TODO Maybe turn this into a list comprehension
				if len(acct) < len(acct_cols):
					# Convert to new format
					acct = acct + ('',) * max(0, len(acct_cols) - len(acct))
				account = str(acct[0])
				child_of = str(acct[1])
				acct_role = str(acct[2])
				# if acct_role not in roles_data:
				# 	print(f'\n{acct_role} is not a valid account role for account {account}.')
				# 	return
				if v: print(acct)
				details = (account, child_of, acct_role)
				cur.execute('INSERT INTO accounts VALUES (?,?,?)', details)
		self.conn.commit()
		cur.close()
		self.refresh_accts()
		self.drop_dupe_accts()

	def add_entity(self, entity_data=None, v=False): # TODO Cleanup and make nicer
		cur = self.conn.cursor()
		if entity_data is None:
			name = input('Enter the entity name: ')
			currency = input('Enter the currency code for the entity: ')
			framework = input('Enter the accounting framework for the entity: ')
			comm = input('Enter the commission amount: ')
			min_qty = 1 # TODO Remove parameters related to random algo
			max_qty = 100 # TODO Remove parameters related to random algo
			liquidate_chance = 0.5 # TODO Remove parameters related to random algo
			ticker_source = input('Enter the source for tickers: ')
			entity_type = input('Enter the type of the entity: ')
			government = input('Enter the ID for the government the entity belongs to: ')
			founder = input('Enter the ID for the founder the entity belongs to: ')
			hours = input('Enter the number of hours reminaing in their work day: ') # TODO Int validation
			needs = input('Enter the needs of the entity as a list: ')
			need_max = input('Enter the maximum need value as a list: ')
			decay_rate = input('Enter the rates of decay per day for each need: ')
			need_threshold = input('Enter the threshold for the needs as a list: ')
			current_need = input('Enter the starting level for the needs as a list: ')
			parents = input('Enter two IDs for parents as a tuple: ')
			user = input('Enter whether the entity is a user as True or False: ')
			auth_shares = input('Enter the number of shares authorized: ')
			int_rate = input('Enter the interest rate for the bank: ')
			outputs = input('Enter the output names as a list: ') # For corporations
			obj = None

			# if auth_shares == '' or auth_shares == 'None' or auth_shares is None:
			# 	auth_shares = np.nan
			if int_rate == '' or int_rate == 'None' or int_rate is None:
				int_rate = np.nan

			details = (name,currency,framework,comm,min_qty,max_qty,liquidate_chance,ticker_source,entity_type,government,founder,hours,needs,need_max,decay_rate,need_threshold,current_need,parents,user,auth_shares,int_rate,outputs,obj)
			cur.execute('INSERT INTO ' + self.entities_table_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', details)
			
		else:
			for entity in entity_data:
				try:
					entity = entity + ([None] * (23 - len(entity)))
				except TypeError:
					pass
				entity = tuple(map(lambda x: np.nan if x == 'None' else x, entity))
				insert_sql = 'INSERT INTO ' + self.entities_table_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
				cur.execute(insert_sql, entity)

		self.conn.commit()
		entity_id = cur.lastrowid
		cur.close()
		if v: print('Entity Added: {}'.format(entity_id))
		return entity_id

	def add_item(self, item_data=None): # TODO Cleanup and make nicer
		cur = self.conn.cursor()
		if item_data is None:
			item_id = input('Enter the item name: ')
			int_rate_fix = ''#input('Enter the fixed interest rate if there is one: ')
			int_rate_var = ''#input('Enter the variable interest rate or leave blank: ')
			freq = ''#int(input('Enter the frequency of interest payments: '))
			child_of = input('Enter the category the item belongs to: ')
			if child_of == 'Land':
				int_rate_fix = input('Enter the time needed to claim this Land item: ')
				int_rate_var = input('Enter the quantity of this Land item to add to the world: ')
			# if child_of not in self.coa.index: # TODO Ensure item always points to an existing item
			# 	print('\n' + child_of + ' is not a valid account.')
			# 	return
			requirements = input('Enter the list of requirments to produce the item: ')
			amount = input('Enter the list of values for the amounts of each requirements: ')
			capacity = input('Enter the capacity amount if there is one: ')
			hold_req = input('Enter the list of requirements to hold the item: ')
			hold_amount = input('Enter the list of values for the amount of each requirement to hold the item: ')
			usage_req = input('Enter the list of requirements to use the item: ')
			use_amount = input('Enter the list of values for the amount of each requirement to use the item: ')
			fulfill = input('Enter the list of requirements the item satisfies or None if the item name is sufficient: ')
			satisfies = input('Enter the list of needs the item satisfies: ')
			satisfy_rate = input('Enter the list of satisfy rates for the item: ')
			productivity = input('Enter the list of requirements the item makes more efficient: ')
			efficiency = input('Enter the list of ratios that the requirements are made more efficient by: ')
			metric = input('Enter either "ticks" or "units" for how the lifespan is measured: ')
			lifespan = input('Enter how long the item lasts: ')
			dmg_types = input('Enter the list of types of damage (if any) the item can inflict: ')
			dmg = input('Enter the list of amounts of damage (if any) the item can inflict: ')
			res_types = input('Enter the list of types of damage resilience (if any) the item has: ')
			res = input('Enter the list of amounts of damage resilience (if any) the item has: ')
			byproduct = input('Enter the list of byproducts created (if any) when this item is produced: ')
			byproduct_amt = input('Enter the list of amount of byproducts created (if any) when this item is produced: ')
			start_price = input('Enter an optional start price for the item: ')
			producer = input('Enter the producer of the item: ')

			details = [item_id,int_rate_fix,int_rate_var,freq,child_of,requirements,amount,capacity,hold_req,hold_amount,usage_req,use_amount,fulfill,satisfies,satisfy_rate,productivity,efficiency,lifespan,metric,dmg_types,dmg,res_types,res,byproduct,byproduct_amt,start_price,producer]
			details = [None if x == '' else x for x in details]
			cur.execute('INSERT INTO ' + self.items_table_name + ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', details)

		else:
			for item in item_data:
				try:
					item = item + ([None] * (27 - len(item)))
				except TypeError:
					pass
				item = tuple(map(lambda x: np.nan if x == 'None' else x, item))
				insert_sql = 'INSERT INTO ' + self.items_table_name + ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
				cur.execute(insert_sql, item)

		self.conn.commit()
		cur.close()

	def clear_tables(self, tables=None, v=False):
		if tables is None:
			tables = [
				'gen_ledger',
				'entities',
				'items'
			]
		if not isinstance(tables, (list, tuple)):
			tables = [x.strip() for x in tables.split(',')]
		cur = self.conn.cursor()
		for table in tables:
			clear_table_query = '''
				DELETE FROM ''' + table + ''';
			'''
			try:
				cur.execute(clear_table_query)
				if v: print('Cleared ' + table + ' table.')
			except Exception as e:
				continue
		self.conn.commit()
		cur.close()
		return tables

	def load_from_web(self, sheet=None, key=None, tab=None, data_type=None):
		import pygsheets

		if key is None:
			key = input('Enter the key ID: ')
			if key == '':
				key = None
		if sheet is None and key is None:
			sheet = input('Enter the sheet name: ')
			if sheet == '':
				sheet = 'Res GL'
		if tab is None:
			tab = input('Enter the tab name: ')
			if tab == '':
				tab = 'Sheet1'
		if data_type is None:
			data_type = input('Enter the data type [accounts, gl, items, entities]: ')
			if data_type == '':
				data_type = 'accounts'

		print(f'Loading {data_type} data from sheet: {sheet} | key: {key} | tab: {tab}')
		gc = pygsheets.authorize(service_file='service_account.json')
		if key is not None:
			sh = gc.open_by_key(key)
		elif sheet is not None:
			sh = gc.open(sheet)
		else:
			print('Error: Must provide either sheet name or key ID.')
			return

		df = sh.worksheet_by_title(tab).get_as_df()
		print(f'Loaded from {sheet} on tab {tab}:\n{df}')
		if data_type == 'accounts':
			self.add_acct(df)
		elif data_type == 'entities':
			self.add_entity(df)
		elif data_type == 'items':
			self.add_item(df)
		return df

	def load_csv(self, infile=None):
		if infile is None:
			infile = input('Enter a filename: ')
		if '.csv' not in infile:
			infile = infile + '.csv'
		if 'data/' not in infile: # TODO Make this able to handle other locations
			infile = 'data/' + infile
		if isinstance(infile, pd.DataFrame):
			lol = infile.values.tolist()
			return lol
		print(f'Loading csv data from: {infile}')
		try:
			with open(infile, 'r') as f:
				load_csv = pd.read_csv(f, keep_default_na=False, comment='#')
			lol = load_csv.values.tolist()
		except Exception as e:
			print('Error: {}'.format(e))
		# print(load_csv)
		# print(lol)
		# print('-' * DISPLAY_WIDTH)
		return lol

	def load_accts(self, infile=None):
		self.add_acct(self.load_csv(infile), v=True)

	def load_entities(self, infile=None):
		if infile is None:
			infile = input('Enter a filename for the entities csv data [entities.csv]: ')
		elif infile == '':
			infile = 'data/entities.csv'
		self.add_entity(self.load_csv(infile))
		self.entities = pd.read_sql_query('SELECT * FROM ' + self.entities_table_name + ';', self.conn, index_col='entity_id')
		return self.entities

	def load_items(self, infile=None, items=None):
		if items is None:
			if infile is None:
				infile = input('Enter a filename for the items csv data [items.csv]: ')
			elif infile == '':
				infile = 'data/items.csv'
			self.add_item(self.load_csv(infile))
		else:
			self.add_item(items)
		self.items = pd.read_sql_query('SELECT * FROM ' + self.items_table_name + ';', self.conn, index_col='item_id')
		return self.items

	def export_accts(self):
		outfile = 'accounts_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		try:
			self.coa.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
			print('File saved as ' + save_location + outfile)
		except Exception as e:
			print('Error: {}'.format(e))

	def remove_acct(self, acct=None):
		if acct is None:
			acct = input('Which account would you like to remove? ')
		cur = self.conn.cursor()
		cur.execute('DELETE FROM accounts WHERE accounts=?', (acct,))
		self.conn.commit()
		cur.close()
		self.refresh_accts()

	def remove_item(self, item=None):
		if item is None:
			item = input('Which item would you like to remove? ')
		cur = self.conn.cursor()
		cur.execute('DELETE FROM ' + self.items_table_name + ' WHERE item_id=?', (item,))
		self.conn.commit()
		cur.close()
		self.items = self.get_items()

	def get_entities(self, entities_table_name=None):
		if entities_table_name is None:
			entities_table_name = self.entities_table_name
		self.entities = pd.read_sql_query('SELECT * FROM ' + entities_table_name + ';', self.conn, index_col=['entity_id'])
		return self.entities

	def get_items(self, items_table_name=None):
		if items_table_name is None:
			items_table_name=self.items_table_name
		self.items = pd.read_sql_query('SELECT * FROM ' + items_table_name + ';', self.conn, index_col=['item_id'])
		return self.items

	def edit_item(self, item=None, prpty=None, value=None):
		# TODO Make this work
		if item is None:
			item = input('Enter a item: ')
		print('{}: \n{}'.format(item.title(), self.items.loc[[item.title()]].squeeze()))
		if prpty is None:
			prpty = input('Enter a property: ')
		value = input('Enter new value: ')
		self.items.loc[[item.title()], prpty] = value
		return self.items

	def print_entities(self, save=True): # TODO Add error checking if no entities exist
		#self.entities = pd.read_sql_query('SELECT * FROM ' + self.entities_table_name + ';', self.conn, index_col=['entity_id'])
		self.entities = self.get_entities()
		if save:
			self.entities.to_csv('data/entities.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.entities)
		print('-' * DISPLAY_WIDTH)
		return self.entities

	def print_items(self, save=True): # TODO Add error checking if no items exist
		#self.items = pd.read_sql_query('SELECT * FROM items;', self.conn, index_col=['item_id'])
		self.items = self.get_items()
		if save:
			self.items.to_csv('data/items.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.items)
		print('-' * DISPLAY_WIDTH)
		return self.items

	def print_table(self, table_name=None, v=True):
		if table_name is None:
			table_name = input('Enter a table to display: ')
			if table_name == '':
				return
		try:
			table = pd.read_sql_query('SELECT * FROM ' + table_name + ';', self.conn)
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				if v: print('{} table: \n{}'.format(table_name, table))
		except Exception as e:
			print('There exists no table called: {}'.format(table_name))
			print('Error: {}'.format(repr(e)))
			table = table_name
		return table

	def export_table(self, table_name=None):
		if table_name is None:
			table_name = input('Enter a table to export: ')
		try:
			table = pd.read_sql_query('SELECT * FROM ' + table_name + ';', self.conn)
			save_location = 'data/'
			outfile = self.db[:-3] + '_' + table_name + datetime.datetime.today().strftime('_%Y-%m-%d_%H-%M-%S') + '.csv'
			table.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
			print('{} data saved to: {}'.format(table_name, save_location + outfile))
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('{} table export: \n{}'.format(table_name, table))
		except Exception as e:
			print('There exists no table called: {}'.format(table_name))
			print('Error: {}'.format(repr(e)))
			table = table_name
		return table


class Ledger:
	def __init__(self, accts, ledger_name=None, entity=None, date=None, start_date=None, txn=None, start_txn=None):# Ledger
		self.conn = accts.conn
		self.coa = accts.coa
		if ledger_name is None:
			self.ledger_name = 'gen_ledger'
		else:
			self.ledger_name = ledger_name
		if entity is not None:
			if not isinstance(entity, (list, tuple)):
				if isinstance(entity, str):
					if ',' in entity:
						entity = [x.strip() for x in entity.split(',')]
						entity = list(map(int, entity))
					else:
						entity = [int(entity)]
				else:
					entity = [entity]
		self.entity = entity
		self.date = date
		self.start_date = start_date
		self.txn = txn
		self.start_txn = start_txn
		self.default = None
		self.create_ledger()
		self.refresh_ledger() # TODO Maybe make this self.gl = self.refresh_ledger()
		self.balance_sheet()
			
	def create_ledger(self): # TODO Change entity_id to string type maybe
		create_ledger_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.ledger_name + ''' (
				txn_id INTEGER PRIMARY KEY,
				event_id integer NOT NULL,
				entity_id integer NOT NULL,
				cp_id integer NOT NULL,
				date date NOT NULL,
				post_date datetime NOT NULL,
				loc text,
				description text,
				item_id text,
				price real,
				qty integer,
				debit_acct text,
				credit_acct text,
				amount real NOT NULL
			);
			'''

		cur = self.conn.cursor()
		cur.execute(create_ledger_query)
		self.conn.commit()
		cur.close()

	# @contextmanager
	def set_entity(self, entity=None):
		# TODO Maybe this can accept a GL and pass it to refresh_ledger() but use None as default
		if entity is None:
			self.entity = input('Enter an Entity ID: ')
			if self.entity == '':
				self.entity = None
		else:
			self.entity = entity
		if self.entity is not None:
			if not isinstance(self.entity, (list, tuple)):
				if isinstance(self.entity, str):
					if ',' in self.entity:
						self.entity = [x.strip() for x in self.entity.split(',')]
						self.entity = list(map(int, self.entity))
					else:
						self.entity = [int(self.entity)]
				else:
					self.entity = [self.entity]
		self.refresh_ledger()
		self.balance_sheet()
		return self.entity
		# yield self.entity
		# self.reset()

	def set_date(self, date=None):
		if date is None:
			self.date = input('Enter a date in format YYYY-MM-DD: ')
		else:
			self.date = date
		try:
			datetime.datetime.strptime(self.date, '%Y-%m-%d')
		except ValueError:
			raise ValueError('Incorrect data format, should be YYYY-MM-DD.')
		self.refresh_ledger()
		self.balance_sheet()
		return self.date

	def set_start_date(self, start_date=None):
		if start_date is None:
			self.start_date = input('Enter a start date in format YYYY-MM-DD: ')
		else:
			self.start_date = start_date
		try:
			datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
		except ValueError:
			raise ValueError('Incorrect data format, should be YYYY-MM-DD.')
		self.refresh_ledger()
		self.balance_sheet()
		return self.start_date

	def set_txn(self, txn=None):
		if txn is None:
			self.txn = int(input('Enter a TXN ID: '))
		else:
			self.txn = txn
		self.refresh_ledger()
		self.balance_sheet()
		return self.txn

	def set_start_txn(self, start_txn=None):
		if start_txn is None:
			self.start_txn = int(input('Enter a start TXN ID: '))
		else:
			self.start_txn = start_txn
		self.refresh_ledger()
		self.balance_sheet()
		return self.start_txn

	def reset(self):
		# TODO Maybe this can accept a GL and pass it to refresh_ledger() but use None as default
		if self.default is not None and not isinstance(self.default, (list, tuple)):
			self.default = [self.default]
		self.entity = self.default
		self.date = None
		self.start_date = None
		self.txn = None
		self.start_txn = None
		self.refresh_ledger()
		self.balance_sheet() # TODO This makes things very inefficient

	def refresh_ledger(self):
		# TODO Maybe this can accept a GL and if it's None use self.gl
		# print('Refreshing Ledger.')
		self.gl = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', self.conn, index_col='txn_id')
		if self.entity is not None:
			self.gl = self.gl[(self.gl.entity_id.isin(self.entity))]
		if self.date is not None:
			self.gl = self.gl[(self.gl.date <= self.date)]
		if self.start_date is not None:
			self.gl = self.gl[(self.gl.date >= self.start_date)]
		if self.txn is not None:
			self.gl = self.gl[(self.gl.index <= self.txn)]
		if self.start_txn is not None:
			self.gl = self.gl[(self.gl.index >= self.start_txn)] # TODO Add event range
		return self.gl

	def print_gl(self):
		self.refresh_ledger() # Refresh Ledger
		display_gl = self.gl
		display_gl['qty'].replace(np.nan, '', inplace=True)
		display_gl['price'].replace(np.nan, '', inplace=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
			print(display_gl)
		print('-' * DISPLAY_WIDTH)
		return self.gl

	def get_acct_elem(self, acct):
		if acct in ['Asset','Liability','Equity','Revenue','Expense','None']:
			return acct
		else:
			return self.get_acct_elem(self.coa.loc[acct, 'child_of'])

	def balance(self, accounts=None, item=None, nav=False, v=False):
		if accounts == '':
			accounts = None
		if item is not None: # TODO Add support for multiple items maybe
			if v: print('Item: \n{}'.format(item))
			self.gl = self.gl[self.gl['item_id'] == item]
		if accounts is None: # Create a list of all the accounts
			accounts = np.unique(self.gl[['debit_acct', 'credit_acct']].values).tolist()
		else:
			if not isinstance(accounts, (list, tuple)):
				accounts = [x.strip() for x in accounts.split(',')]
		if v: print('Accounts: \n{}'.format(accounts))
		self.gl = self.gl.loc[(self.gl['debit_acct'].isin(accounts)) | (self.gl['credit_acct'].isin(accounts))]
		if v: print('GL Filtered: \n{}'.format(self.gl))

		# TODO Modify tmp gl instead of self.gl
		self.gl['debit_acct_type'] = self.gl.apply(lambda x: self.get_acct_elem(x['debit_acct']), axis=1)
		self.gl['credit_acct_type'] = self.gl.apply(lambda x: self.get_acct_elem(x['credit_acct']), axis=1)
		self.gl['debit_amount'] = self.gl.apply(lambda x: x['amount'] if (x['debit_acct_type'] == 'Asset') | (x['debit_acct_type'] == 'Expense') else x['amount'] * -1, axis=1)
		self.gl['credit_amount'] = self.gl.apply(lambda x: x['amount'] * -1 if (x['credit_acct_type'] == 'Asset') | (x['credit_acct_type'] == 'Expense') else x['amount'], axis=1)
		if v: print('GL Enhanced: \n{}'.format(self.gl))

		debits = self.gl.groupby(['debit_acct','debit_acct_type']).sum()['debit_amount']
		debits.index.rename('acct', level=0, inplace=True)
		debits.index.rename('acct_type', level=1, inplace=True)
		if v: print('\nDebits: \n{}'.format(debits))
		credits = self.gl.groupby(['credit_acct','credit_acct_type']).sum()['credit_amount']
		credits.index.rename('acct', level=0, inplace=True)
		credits.index.rename('acct_type', level=1, inplace=True)
		if v: print('\nCredits: \n{}'.format(credits))
		bal = debits.add(credits, fill_value=0).reset_index()
		# if v: print('Add: \n{}'.format(bal))
		# bal = bal.reset_index()
		if v: print('Add Reset: \n{}'.format(bal))
		bal = bal.loc[(bal['acct'].isin(accounts))]
		if bal.empty:
			bal = 0
			return bal
		bal = bal.groupby(['acct_type']).sum()
		if v: print('New Bal: \n{}'.format(bal))
		try:
			asset_bal = bal.loc['Asset', 0]
		except KeyError as e:
			asset_bal = 0
		try:
			liab_bal = bal.loc['Liability', 0]
		except KeyError as e:
			liab_bal = 0
		try:
			equity_bal = bal.loc['Equity', 0]
		except KeyError as e:
			equity_bal = 0
		try:
			rev_bal = bal.loc['Revenue', 0]
		except KeyError as e:
			rev_bal = 0
		try:
			exp_bal = bal.loc['Expense', 0]
		except KeyError as e:
			exp_bal = 0
		retained_earnings = rev_bal - exp_bal
		net_asset_value = asset_bal - liab_bal
		if net_asset_value == 0: # Two ways to calc NAV depending on accounts
			net_asset_value = equity_bal + retained_earnings
		if v: print('NAV: \n{}'.format(net_asset_value))
		self.refresh_ledger()
		return net_asset_value # TODO This func is slow

		#Option 1 (will be below):
		# Asset  - Debit  bal - Pos : Dr. = pos & Cr. = neg
		# Liab   - Credit bal - Neg : Dr. = pos & Cr. = neg
		# =
		# Equity - Credit bal - Pos : Dr. = neg & Cr. = pos
		# Rev    - Credit bal - Pos : Dr. = neg & Cr. = pos
		# Exp    - Debit  bal - Neg : Dr. = neg & Cr. = pos

		#Option 2 (above):
		# Asset  - Debit  bal - Pos : Dr. = pos & Cr. = neg
		# Liab   - Credit bal - Pos : Dr. = neg & Cr. = pos
		# =
		# Equity - Credit bal - Pos : Dr. = neg & Cr. = pos
		# Rev    - Credit bal - Pos : Dr. = neg & Cr. = pos
		# Exp    - Debit  bal - Pos : Dr. = pos & Cr. = neg

	def balance_sheet(self, accounts=None, item=None, gl=None, v=False): # TODO Needs to be optimized with:
		# t1_start = time.perf_counter()
		#self.gl['debit_acct_type'] = self.gl.apply(lambda x: self.get_acct_elem(x['debit_acct']), axis=1)
		if gl is not None:
			self.gl = gl
		all_accts = False
		if item is not None: # TODO Add support for multiple items maybe
			if v: print('BS Item: {}'.format(item))
			self.gl = self.gl[self.gl['item_id'] == item]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('BS GL: \n{}'.format(self.gl))
		if accounts is None: # Create a list of all the accounts
			all_accts = True
			# debit_accts = pd.unique(self.gl['debit_acct'])
			# credit_accts = pd.unique(self.gl['credit_acct'])
			# accounts = sorted(list(set(debit_accts) | set(credit_accts)))
			accounts = np.unique(self.gl[['debit_acct', 'credit_acct']].values).tolist()
		elif isinstance(accounts, str):
			accounts = [x.strip() for x in accounts.split(',')]
		account_details = []

		# Create a list of tuples for all the accounts with their fundamental accounting element (asset,liab,eq,rev,exp)
		for acct in accounts:
			elem = self.get_acct_elem(acct)
			account_elem = (acct, elem)
			account_details.append(account_elem)

		# print('Account Details: \n{}'.format(account_details))

		# Group all the accounts together in lists based on their fundamental account element
		accounts = None
		assets = []
		liabilities = []
		equity = []
		revenues = []
		expenses = []
		for acct in account_details:
			if acct[1] == 'Asset':
				assets.append(acct[0])
			elif acct[1] == 'Liability':
				liabilities.append(acct[0])
			elif acct[1] == 'Equity':
				equity.append(acct[0])
			elif acct[1] == 'Revenue':
				revenues.append(acct[0])
			elif acct[1] == 'Expense':
				expenses.append(acct[0])
			else:
				continue

		# Create Balance Sheet dataframe to return
		if all_accts:
			self.bs = pd.DataFrame(columns=['line_item','balance']) # TODO Make line_item the index

		# TODO The below repeated sections can probably be handled more elegantly. Maybe by putting the 5 account type lists in a list and using a double loop

		asset_bal = 0
		# if v: print('Asset Accounts: {}'.format(assets))
		for acct in assets:
			if v: print('Asset Account: {}'.format(acct))
			try:
				# debits = self.gl.groupby(['debit_acct'])[['amount']].sum().loc[acct].values[0]
				# debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				debits = self.gl.loc[self.gl.debit_acct == acct, 'amount'].sum()
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Asset Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				# credits = self.gl.groupby(['credit_acct'])[['amount']].sum().loc[acct].values[0]
				# credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				credits = self.gl.loc[self.gl.credit_acct == acct, 'amount'].sum()
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Asset Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = debits - credits
			asset_bal += bal
			if v: print('Balance for {}: {}'.format(acct, bal))
			#if bal != 0: # TODO Not sure if should display empty accounts
			if all_accts:
				# self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
				tmp_df = pd.DataFrame({'line_item':[acct], 'balance':[bal]})
				dfs = [self.bs, tmp_df]
				dfs = [df for df in dfs if not df.empty]
				self.bs = pd.concat(dfs, ignore_index=True)
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Total Assets:', 'balance':asset_bal}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Total Assets:'], 'balance':[asset_bal]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		liab_bal = 0
		for acct in liabilities:
			if v: print('Liability Account: {}'.format(acct))
			try:
				# debits = self.gl.groupby(['debit_acct'])[['amount']].sum().loc[acct].values[0]
				# debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				debits = self.gl.loc[self.gl.debit_acct == acct, 'amount'].sum()
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Liabilities Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				# credits = self.gl.groupby(['credit_acct'])[['amount']].sum().loc[acct].values[0]
				# credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				credits = self.gl.loc[self.gl.credit_acct == acct, 'amount'].sum()
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Liabilities Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			liab_bal += bal
			if all_accts:
				# self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
				tmp_df = pd.DataFrame({'line_item':[acct], 'balance':[bal]})
				dfs = [self.bs, tmp_df]
				dfs = [df for df in dfs if not df.empty]
				self.bs = pd.concat(dfs, ignore_index=True)
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Total Liabilities:', 'balance':liab_bal}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Total Liabilities:'], 'balance':[liab_bal]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		equity_bal = 0
		for acct in equity:
			if v: print('Equity Account: {}'.format(acct))
			try:
				# debits = self.gl.groupby(['debit_acct'])[['amount']].sum().loc[acct].values[0]
				# debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				debits = self.gl.loc[self.gl.debit_acct == acct, 'amount'].sum()
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Equity Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				# credits = self.gl.groupby(['credit_acct'])[['amount']].sum().loc[acct].values[0]
				# credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				credits = self.gl.loc[self.gl.credit_acct == acct, 'amount'].sum()
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Equity Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			equity_bal += bal
			if all_accts:
				# self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
				tmp_df = pd.DataFrame({'line_item':[acct], 'balance':[bal]})
				dfs = [self.bs, tmp_df]
				dfs = [df for df in dfs if not df.empty]
				self.bs = pd.concat(dfs, ignore_index=True)
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Total Equity:', 'balance':equity_bal}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Total Equity:'], 'balance':[equity_bal]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		rev_bal = 0
		for acct in revenues:
			if v: print('Revenue Account: {}'.format(acct))
			try:
				# debits = self.gl.groupby(['debit_acct'])[['amount']].sum().loc[acct].values[0]
				# debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				debits = self.gl.loc[self.gl.debit_acct == acct, 'amount'].sum()
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Revenues Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				# credits = self.gl.groupby(['credit_acct'])[['amount']].sum().loc[acct].values[0]
				# credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				credits = self.gl.loc[self.gl.credit_acct == acct, 'amount'].sum()
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Revenues Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			rev_bal += bal
			if all_accts:
				# self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
				tmp_df = pd.DataFrame({'line_item':[acct], 'balance':[bal]})
				dfs = [self.bs, tmp_df]
				dfs = [df for df in dfs if not df.empty]
				self.bs = pd.concat(dfs, ignore_index=True)
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Total Revenues:', 'balance':rev_bal}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Total Revenues:'], 'balance':[rev_bal]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		exp_bal = 0
		for acct in expenses:
			if v: print('Expense Account: {}'.format(acct))
			try:
				# debits = self.gl.groupby(['debit_acct'])[['amount']].sum().loc[acct].values[0]
				# debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				debits = self.gl.loc[self.gl.debit_acct == acct, 'amount'].sum()
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Expenses Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				# credits = self.gl.groupby(['credit_acct'])[['amount']].sum().loc[acct].values[0]
				# credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				credits = self.gl.loc[self.gl.credit_acct == acct, 'amount'].sum()
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Expenses Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = debits - credits
			exp_bal += bal
			if all_accts:
				# self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
				tmp_df = pd.DataFrame({'line_item':[acct], 'balance':[bal]})
				dfs = [self.bs, tmp_df]
				dfs = [df for df in dfs if not df.empty]
				self.bs = pd.concat(dfs, ignore_index=True)
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Total Expenses:', 'balance':exp_bal}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Total Expenses:'], 'balance':[exp_bal]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		retained_earnings = rev_bal - exp_bal
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Net Income:', 'balance':retained_earnings}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Net Income:'], 'balance':[retained_earnings]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		net_asset_value = asset_bal - liab_bal
		if net_asset_value == 0: # Two ways to calc NAV depending on accounts
			net_asset_value = equity_bal + retained_earnings

		total_equity = net_asset_value + liab_bal
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Equity+NI+Liab.:', 'balance':total_equity}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Equity+NI+Liab.:'], 'balance':[total_equity]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		check = asset_bal - total_equity
		if all_accts:
			# self.bs = self.bs.append({'line_item':'Balance Check:', 'balance':check}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Balance Check:'], 'balance':[check]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs, ignore_index=True)

		if all_accts:
			# self.bs = self.bs.append({'line_item':'Net Asset Value:', 'balance':net_asset_value}, ignore_index=True)
			tmp_df = pd.DataFrame({'line_item':['Net Asset Value:'], 'balance':[net_asset_value]})
			dfs = [self.bs, tmp_df]
			dfs = [df for df in dfs if not df.empty]
			self.bs = pd.concat(dfs)

		if all_accts and gl is None:
			if self.entity is None:
				self.bs.to_sql('balance_sheet', self.conn, if_exists='replace')
			else:
				entities = '_'.join(str(e) for e in self.entity)
				self.bs.to_sql('balance_sheet_' + entities, self.conn, if_exists='replace')
		if item is not None or gl is not None:
			self.refresh_ledger()
		# t1_end = time.perf_counter()
		# print('BS check took {:,.10f} min.'.format((t1_end - t1_start) / 60))
		return net_asset_value

	def print_bs(self):
		self.balance_sheet() # Refresh Balance Sheet
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.bs)
		print('-' * DISPLAY_WIDTH)
		return self.bs

	def sum_role(self, role, v=False):
		# Get list of accounts for role
		accts = self.coa[self.coa['acct_role'] == role].index.tolist()
		if v: print('Accounts for role {}: {}'.format(role, accts))
		# Get balance for those accounts
		amount = self.balance_sheet(accts)
		if v: print('Amount for role {}: {:,.2f}'.format(role, amount))
		return amount

	def get_qty_txns(self, item=None, acct=None):
		# TODO Maybe make acct accept a list of accounts
		rvsl_txns = self.gl[self.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of txns
		qty_txns = self.gl[(self.gl['item_id'] == item) & ((self.gl['debit_acct'] == acct) | (self.gl['credit_acct'] == acct)) & pd.notnull(self.gl['qty']) & (~self.gl['event_id'].isin(rvsl_txns))]
		#print('QTY TXNs:')
		#print(qty_txns)
		return qty_txns

	def get_qty(self, items=None, accounts=None, gl=None, show_zeros=False, by_entity=False, single_item=False, always_df=False, credit=False, ignore_cash=True, v=False):
		# if items == 'Wild Leather':
		# 	if v: print('Get Qty GL: \n{}'.format(self.gl))
		if gl is not None:
			self.gl = gl
		if not credit:
			acct_side = 'debit_acct'
		else:
			acct_side = 'credit_acct'
		all_accts = False
		no_item = False
		if v: print('Get Qty for Items Given: {}'.format(items))
		if (items is None) or (items == '') or (not items):
			items = None
			no_item = True
		if isinstance(items, str):
			items = [x.strip() for x in items.split(',')]
			items = list(filter(None, items))
			if v: print('Select Items: {}'.format(items))
		if items is not None and len(items) == 1:
			single_item = True
			if v: print('Single Item: {}'.format(single_item))
		if isinstance(accounts, (list, tuple)):
			if all([x is None for x in accounts]):
				accounts = None
		if accounts is None or accounts == '':
			if v: print('No account given.')
			all_accts = True
			if no_item:
				accounts = pd.unique(self.gl[acct_side])
				if v: print('Accounts Before Filter: \n{}'.format(accounts))
				# Filter for only Asset and Liability accounts
				accounts = [acct for acct in accounts if self.get_acct_elem(acct) == 'Asset' or self.get_acct_elem(acct) == 'Liability']
			else:
				item_txns = self.gl.loc[self.gl['item_id'].isin(items)]
				accounts = pd.unique(item_txns[acct_side])
			if ignore_cash:
				accounts = [acct for acct in accounts if acct != 'Cash']
			#credit_accts = pd.unique(self.gl['credit_acct']) # Not needed
			#accounts = list( set(accounts) | set(credit_accts) ) # Not needed
		if v: print('Accounts: {}\n'.format(accounts))
		if isinstance(accounts, str):
			accounts = [x.strip() for x in accounts.split(',')]
		accounts = list(filter(None, accounts))
		accounts = [x for x in accounts if x != 'Accum. Depr.']
		if by_entity:
			inventory = pd.DataFrame(columns=['entity_id','item_id','account','qty'])
		else:
			inventory = pd.DataFrame(columns=['item_id','account','qty'])
		if single_item:
			total_qty = 0
		for acct in accounts:
			#if v: print('GL: \n{}'.format(self.gl))
			if v: print('Acct: {}'.format(acct))
			if no_item: # Get qty for all items
				if v: print('No item given.')

				items = pd.unique(self.gl[self.gl[acct_side] == acct]['item_id'].dropna()).tolist() # Assuming you can't have a negative inventory
				#credit_items = pd.unique(self.gl[self.gl['credit_acct'] == acct]['item_id'].dropna()).tolist() # Causes issues
				#items = list( set(items) | set(credit_items) ) # Causes issues
				items = list(filter(None, items))
				if v: print('All Items: {}'.format(items))
			for item in items:
				if v: print('Item: {}'.format(item))
				if by_entity:
					entities = pd.unique(self.gl[self.gl['item_id'] == item]['entity_id'])
					if v: print('Entities: {}'.format(entities))
					for entity_id in entities:
						if v: print('Entity ID: {}'.format(entity_id))
						self.set_entity(entity_id)
						qty_txns = self.get_qty_txns(item, acct)
						if v: print('QTY TXNs by entity: \n{}'.format(qty_txns))
						try:
							debits = qty_txns.groupby(['debit_acct'])[['qty']].sum().loc[acct].values[0]
							# debits = qty_txns.groupby(['debit_acct']).sum()['qty'][acct]
							if v: print('Debits: \n{}'.format(debits))
						except KeyError as e:
							if v: print('Error Debits: {} | {}'.format(e, repr(e)))
							debits = 0
						try:
							credits = qty_txns.groupby(['credit_acct'])[['qty']].sum().loc[acct].values[0]
							# credits = qty_txns.groupby(['credit_acct']).sum()['qty'][acct]
							if v: print('Credits: \n{}'.format(credits))
						except KeyError as e:
							if v: print('Error Credits: {} | {}'.format(e, repr(e)))
							credits = 0
						qty = round(debits - credits, 0)
						if v: print('QTY: {}\n'.format(qty))
						# inventory = inventory.append({'entity_id':entity_id, 'item_id':item, 'account':acct, 'qty':qty}, ignore_index=True)
						tmp_df = pd.DataFrame({'entity_id':[entity_id], 'item_id':[item], 'account':[acct], 'qty':[qty]})
						dfs = [inventory, tmp_df]
						dfs = [df for df in dfs if not df.empty]
						inventory = pd.concat(dfs, ignore_index=True)
						inventory = inventory.sort_values(by='entity_id', ascending=True)
						#if v: print(inventory)
						self.reset()
					inventory['entity_id'] = pd.to_numeric(inventory['entity_id'])
				else:
					qty_txns = self.get_qty_txns(item, acct)
					if v: print('Qty TXNs: \n{}'.format(qty_txns))
					try:
						debits = qty_txns.groupby(['debit_acct'])[['qty']].sum().loc[acct].values[0]
						# debits = qty_txns.groupby(['debit_acct']).sum()['qty'][acct]
						if v: print('Debits: {}'.format(debits))
					except KeyError as e:
						if v: print('Error Debits: {} | {}'.format(e, repr(e)))
						debits = 0
					try:
						credits = qty_txns.groupby(['credit_acct'])[['qty']].sum().loc[acct].values[0]
						# credits = qty_txns.groupby(['credit_acct']).sum()['qty'][acct]
						if v: print('Credits: {}'.format(credits))
					except KeyError as e:
						if v: print('Error Credits: {} | {}'.format(e, repr(e)))
						credits = 0
					qty = debits - credits
					if v: print('QTY: {}\n'.format(qty))
					if single_item and not always_df:
						total_qty += qty
					else:
						# inventory = inventory.append({'item_id':item, 'account':acct, 'qty':qty}, ignore_index=True)
						tmp_df = pd.DataFrame({'item_id':[item], 'account':[acct], 'qty':[qty]})
						dfs = [inventory, tmp_df]
						dfs = [df for df in dfs if not df.empty]
						inventory = pd.concat(dfs, ignore_index=True)
						#if v: print(inventory)
		if single_item and not by_entity and not always_df:
			if v: print('Return Total Qty: ', total_qty)
			return total_qty
		if not show_zeros:
			inventory = inventory[(inventory.qty != 0)] # Ignores items completely sold
		if all_accts and no_item and gl is None:
			if self.entity is None:
				inventory.to_sql('inventory', self.conn, if_exists='replace')
			else:
				entities = '_'.join(str(e) for e in self.entity)
				inventory.to_sql('inventory_' + entities, self.conn, if_exists='replace')
		if gl is not None:
			self.refresh_ledger()
		return inventory

	def get_util(self, entity_id=None, items=None, accounts=None, desc=None, gl=None, ex_rvsl=True, mob=True, save=None, v=True):
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
			gl = self.gl.copy(deep=True)

		if not entity_id:
			entity_id = None
		if entity_id is not None:
			if isinstance(entity_id, str):
				entity_id = [int(x.strip()) for x in entity_id.split(',')]
		if not items:
			items = None
		if items is not None:
			if isinstance(items, str):
				items = [x.strip() for x in items.split(',')]
		if not accounts:
			accounts = None
		if accounts is not None:
			if isinstance(accounts, str):
				accounts = [x.strip() for x in accounts.split(',')]
		
		if ex_rvsl:
			rvsl_txns = gl[gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			gl = gl[(~gl['event_id'].isin(rvsl_txns))]

		if entity_id is not None:
			if v: print('entity_id:', entity_id)
			gl = gl[(gl['entity_id'].isin(entity_id))]
			if gl.empty:
				print('The GL is empty with the entity filter.')
				return
		if items is not None:
			if v: print('items:', items)
			gl = gl[(gl['item_id'].isin(items))]
			if gl.empty:
				print('The GL is empty with the item filter.')
				return
		if accounts is not None:
			if v: print('accounts:', accounts)
			gl = gl[((gl['debit_acct'].isin(accounts)) | (gl['credit_acct'].isin(accounts)))]
			if gl.empty:
				print('The GL is empty with the account filters.')
				return
		if desc is not None and desc != '':
			if v: print('desc contains:', desc)
			gl= gl[gl['description'].str.contains(desc)]

		if gl.empty:
			print('The GL is empty.')
			return
		gl['parties'] = gl['entity_id'].astype(str) + '|' + gl['cp_id'].astype(str)
		gl['accts'] = gl['debit_acct'] + '|' + gl['credit_acct']
		gl['debit_acct_type'] = gl.apply(lambda x: self.get_acct_elem(x['debit_acct']), axis=1)
		gl['credit_acct_type'] = gl.apply(lambda x: self.get_acct_elem(x['credit_acct']), axis=1)
		gl['types'] = gl['debit_acct_type'] + '|' + gl['credit_acct_type']

		gl['dir'] = 0
		if accounts is None:
			gl['dir'] = gl.apply(lambda x: 1 if x['debit_acct_type'] == 'Asset' else x['dir'], axis=1)
			gl['dir'] = gl.apply(lambda x: -1 if x['credit_acct_type'] == 'Asset' else x['dir'], axis=1)
			gl['dir'] = gl.apply(lambda x: 0 if (x['debit_acct_type'] == 'Asset' and x['credit_acct_type'] == 'Asset') else x['dir'], axis=1)
		else:
			gl['dir'] = gl.apply(lambda x: 1 if x['debit_acct'] in accounts else x['dir'], axis=1)
			gl['dir'] = gl.apply(lambda x: -1 if x['credit_acct'] in accounts else x['dir'], axis=1)
			gl['dir'] = gl.apply(lambda x: 0 if (x['debit_acct'] in accounts and x['credit_acct'] in accounts) else x['dir'], axis=1)

		gl['delta_qty'] = gl['qty'] * gl['dir']
		gl['run_qty'] = gl['delta_qty'].cumsum()
		gl['delta_amount'] = gl['amount'] * gl['dir']
		gl['run_amount'] = gl['delta_amount'].cumsum()

		if v:
			print(f'GL for {entity_id} entities, for item {items}, for accounts {accounts}, with desc containing "{desc}", returned {gl.shape[0]} rows:') #TODO Improve description logic
			if mob:
				try:
					import rich
					rich.print(gl.to_dict('records'))
				except ImportError:
					pass
			else:
				print(gl)
			print(f'GL for {entity_id} entities, for item {items}, for accounts {accounts}, with desc containing "{desc}", returned {gl.shape[0]} rows:')
		if save:
			# TODO Improve save name logic
			outfile = 'util_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
			save_location = 'data/'
			try:
				gl.to_csv(save_location + outfile, date_format='%Y-%m-%d')
				print('File saved as ' + save_location + outfile)
			except Exception as e:
				print('Error saving: {}'.format(e))
		return gl

	# Used when booking journal entries to match related transactions
	def get_event(self):
		event_query = 'SELECT event_id FROM ' + self.ledger_name +' ORDER BY event_id DESC LIMIT 1;'
		cur = self.conn.cursor()
		cur.execute(event_query)
		event_id = cur.fetchone()
		cur.close()
		if event_id is None:
			event_id = 1
			return event_id
		else:
			return event_id[0] + 1

	def get_entity(self):
		if self.entity is None:
			if self.default is None:
				entity = [1]
			elif isinstance(self.default, int):
				entity = self.default
			else:
				entity = [1]
		else:
			entity = self.entity # TODO Long term solution
		return entity

	def journal_entry(self, journal_data=None):
		'''
			The heart of the whole system; this is how transactions are entered.
			journal_data is a list of transactions. Each transaction is a list
			of datapoints. This means an event with a single transaction
			would be encapsulated in as a single list within a list.
		'''
		if journal_data:
			if isinstance(journal_data, pd.DataFrame):
				journal_data = journal_data.values.tolist()
			elif isinstance(journal_data, pd.Series):
				journal_data = [journal_data.tolist()]
			elif isinstance(journal_data, str):
				journal_data = [[x.strip() for x in journal_data.split(',')]]
			elif not isinstance(journal_data[0], (list, tuple)):
				journal_data = [journal_data]
		post_date = datetime.datetime.utcnow() # TODO Finish this
		cur = self.conn.cursor()
		if journal_data is None: # Manually enter a journal entry
			event = input('Enter an optional event_id: ')
			entity = input('Enter the entity_id: ')
			cp = input('Enter the counterparty id (or blank for itself): ')
			while True:
				try:
					date_raw = input('Enter a date as format yyyy-mm-dd: ')
					date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
					if date == 'NaT':
						date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
						date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
					datetime.datetime.strptime(date, '%Y-%m-%d')
					break
				except ValueError:
					print('Incorrect data format, should be YYYY-MM-DD.')
					continue
			loc = input('Enter an optional location: ')
			desc = input('Enter a description: ') + ' [M]'
			item = input('Enter an optional item_id: ')
			price = input('Enter an optional price: ')
			qty = input('Enter an optional quantity: ')
			debit = input('Enter the account to debit: ')
			if debit not in self.coa.index:
				print('\n' + debit + ' is not a valid account. Type "accts" command to view valid accounts.')
				return # TODO Make accounts foreign key constraint
			credit = input('Enter the account to credit: ')
			if credit not in self.coa.index:
				print('\n' + credit + ' is not a valid account. Type "accts" command to view valid accounts.')
				return
			while True:
				amount = input('Enter the amount: ')
				try: # TODO Maybe change to regular expression to prevent negatives
					x = float(amount)
					break
				except ValueError:
					print('Enter a number.')
					continue
			
			if event == '':
				event = str(self.get_event())
			if entity == '':
				entity = self.get_entity()
				if isinstance(entity, (list, tuple)):
					if len(entity) == 1:
						entity = entity[0]
					else:
						entity_str = [str(e) for e in entity]
						while True:
							entity_choice = input('There are multiple entities in this view. Choose from the following {}: '.format(entity))
							if entity_choice in entity_str:
								break
						entity = entity_choice
				else:
					entity = str(entity)
			if cp == '':
				cp = entity

			if qty == '': # TODO No qty and price default needed now
				qty = np.nan
			if price == '':
				price = np.nan

			values = (event, entity, cp, date, loc, desc, item, price, qty, debit, credit, amount) # So the print looks nicer
			print(values)
			values = (event, entity, cp, date, post_date, loc, desc, item, price, qty, debit, credit, amount)
			cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)', values)

		else: # Create journal entries by passing data to the function
			for je in journal_data:
				event = str(je[0])
				entity = je[1]
				if isinstance(entity, (list, tuple)):
					entity = entity[0]
				entity = str(entity)
				cp = je[2]
				if isinstance(cp, (list, tuple)):
					cp = cp[0]
				cp = str(cp)
				date = str(je[3])
				loc = str(je[4])
				desc = str(je[5])
				item  = str(je[6])
				price = str(je[7])
				qty = str(je[8])
				debit = str(je[9])
				credit = str(je[10])
				amount = str(je[11])

				if event == '' or event == 'nan':
					event = str(self.get_event())
				if entity == '' or entity == 'nan':
					entity = self.get_entity()
					if isinstance(entity, (list, tuple)):
						entity = entity[0]
					entity = str(entity)
				if cp == '' or cp == 'nan':
					cp = entity
				if date == 'NaT':
					date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
					date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
				try:
					datetime.datetime.strptime(date, '%Y-%m-%d')
				except ValueError:
					raise ValueError('Incorrect date format, should be YYYY-MM-DD.')

				if qty == '': # TODO No qty and price default needed now
					qty = np.nan
				if price == '':
					price = np.nan

				values = (event, entity, cp, date, loc, desc, item, price, qty, debit, credit, amount) # So the print looks nicer
				print(values)
				# cols = ['event_id', 'entity_id', 'cp_id', 'date', 'loc', 'description', 'item_id', 'price', 'qty', 'debit_acct', 'credit_acct', 'amount']
				# df = pd.DataFrame([values], columns=cols, index=['txn_id'])
				# print(df)
				values = (event, entity, cp, date, post_date, loc, desc, item, price, qty, debit, credit, amount)
				cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)', values)

		self.conn.commit()
		txn_id = cur.lastrowid
		cur.close()
		self.refresh_ledger() # Ensures the gl is in sync with the db
		self.balance_sheet() # Ensures the bs is in sync with the ledger
		self.get_qty() # Ensures the inv is in sync with the ledger
		#return values # TODO Add all entries to list before returning

	def sanitize_ledger(self): # This is not implemented yet
		dupes = self.gl[self.gl.duplicated(['entity_id','date','description','item_id','price','qty','debit_acct','credit_acct','amount'])]
		dupes_to_drop = dupes.index.tolist()
		dupes_to_drop = ', '.join(str(x) for x in dupes_to_drop)
		# Delete dupes from db
		if not dupes.empty:
			cur = self.conn.cursor()
			cur.execute('DELETE FROM ' + self.ledger_name + ' WHERE txn_id IN (' + dupes_to_drop + ')')
			self.conn.commit()
			cur.close()
		self.refresh_ledger()

	def load_gl_from_web(self, sheet=None, key=None, tab=None):
		import pygsheets

		if key is None:
			key = input('Enter the key ID: ')
			if key == '':
				key = None
		if sheet is None and key is None:
			sheet = input('Enter the sheet name: ')
			if sheet == '':
				sheet = 'Res GL'
		if tab is None:
			tab = input('Enter the tab name: ')
			if tab == '':
				tab = 'Sheet1'
				# tab = 'CoA'

		print(f'Loading general ledger data from sheet: {sheet} | key: {key} | tab: {tab}')
		gc = pygsheets.authorize(service_file='service_account.json')
		if key is not None:
			sh = gc.open_by_key(key)
		elif sheet is not None:
			sh = gc.open(sheet)
		else:
			print('Error: Must provide either sheet name or key ID.')
			return

		df = sh.worksheet_by_title(tab).get_as_df()
		print(f'Loaded from {sheet} on tab {tab}:\n{df}')
		self.load_gl(data=df)
		return df

	def load_gl(self, infile=None, flag=None, data=None):
		if infile is None and data is None:
			infile = input('Enter a filename: ')
			#infile = 'data/rbc_sample_2019-01-27.csv' # For testing
			#infile = 'data/legacy_ledger_2019-01-25.csv' # For testing
		if flag is None and data is None:
			flag = input('Enter a flag (rbc, legacy, or none): ')
			#flag = 'rbc' # For testing
			#flag = 'legacy' # For testing
		try:
			with open(infile, 'r') as f:
				if flag == 'legacy':
					load_gl = pd.read_csv(f, header=1, keep_default_na=False)
				else:
					load_gl = pd.read_csv(f, keep_default_na=False)
		except Exception as e:
			if isinstance(data, pd.DataFrame):
				print(f'Load data directly from df:')
				load_gl = pd.DataFrame(data)
			else:
				print('Error: {} | {}'.format(e, repr(e)))
				load_gl = pd.DataFrame()
		print(load_gl)
		print('-' * DISPLAY_WIDTH)
		if flag == 'rbc':
			load_gl['dupe'] = load_gl.duplicated(keep=False)
			for index, row in load_gl.iterrows():
				if row['dupe']:
					unique_desc = row['Description 2'] + ' - ' + str(index)
					load_gl.at[index, 'Description 2'] = unique_desc
			load_gl.drop('dupe', axis=1, inplace=True)
			rbc_txn = pd.DataFrame()
			rbc_txn['event_id'] = ''
			rbc_txn['entity_id'] = ''
			rbc_txn['cp_id'] = ''
			rbc_txn['date'] = load_gl['Transaction Date']
			rbc_txn['loc'] = ''
			rbc_txn['desc'] = load_gl['Description 1'] + ' | ' + load_gl['Description 2']
			rbc_txn['item_id'] = ''
			rbc_txn['price'] = ''
			rbc_txn['qty'] = ''
			rbc_txn['debit_acct'] = np.where(load_gl['CAD$'] > 0, load_gl['Account Type'], 'Uncategorized')
			rbc_txn['credit_acct'] = np.where(load_gl['CAD$'] < 0, load_gl['Account Type'], 'Uncategorized')
			rbc_txn['amount'] = abs(load_gl['CAD$'])
			lol = rbc_txn.values.tolist()
			self.journal_entry(lol)
			self.sanitize_ledger()
		elif flag == 'legacy':
			load_gl = load_gl[:-3]
			load_gl['Category 3'] = load_gl['Category 3'].replace(r'^\s*$', np.nan, regex=True)
			load_gl['Category 3'].fillna('Uncategorized', inplace=True)
			load_gl['dupe'] = load_gl.duplicated(keep=False)
			for index, row in load_gl.iterrows():
				if row['dupe']:
					unique_desc = row['Description 2'] + ' - ' + str(index)
					load_gl.at[index, 'Description 2'] = unique_desc
			load_gl.drop('dupe', axis=1, inplace=True)
			load_gl['Amount'] = [float(x.replace('$','').replace(',','').replace(')','').replace('(','-')) if x else 0 for x in load_gl['Amount']]
			leg_txn = pd.DataFrame()
			leg_txn['event_id'] = ''
			leg_txn['entity_id'] = ''
			leg_txn['cp_id'] = ''
			leg_txn['date'] = load_gl['Transaction Date']
			leg_txn['loc'] = ''
			leg_txn['desc'] = load_gl['Description 1'] + ' | ' + load_gl['Description 2']
			leg_txn['item_id'] = ''
			leg_txn['price'] = ''
			leg_txn['qty'] = ''
			leg_txn['debit_acct'] = np.where(load_gl['Amount'] > 0, load_gl['Account Type'], load_gl['Category 3'])
			leg_txn['credit_acct'] = np.where(load_gl['Amount'] < 0, load_gl['Account Type'], load_gl['Category 3'])
			leg_txn['amount'] = abs(load_gl['Amount'])
			lol = leg_txn.values.tolist()
			self.journal_entry(lol)
			self.sanitize_ledger()
		else:
			if 'txn_id' in load_gl.columns.values:
				load_gl.set_index('txn_id', inplace=True)
			lol = load_gl.values.tolist()
			self.journal_entry(lol)	

	def export_gl(self):
		self.reset()
		outfile = self.ledger_name + '_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		try:
			self.gl.to_csv(save_location + outfile, date_format='%Y-%m-%d')
			print('File saved as ' + save_location + outfile)
		except Exception as e:
			print('Error: {}'.format(e))

	def remove_entries(self, txns=None): # TODO Don't keep this long term, only use rvsl instead
		if txns is None:
			txns = input('Which transaction ID would you like to remove? ')
			if txns == '':
				return
		if not isinstance(txns, (list, tuple)):
			txns = [x.strip() for x in txns.split(',')]
		cur = self.conn.cursor()
		for txn in txns:
			cur.execute('DELETE FROM '+ self.ledger_name +' WHERE txn_id=?', (txn,))
		self.conn.commit()
		cur.close()
		print('Removed {} entries.'.format(len(txns)))
		self.refresh_ledger()

	def reversal_entry(self, txns=None, date=None): # This func effectively deletes a transaction
		if txns is None:
			txns = input('Which txn_id to reverse? ') # TODO Add check to ensure valid transaction number
			if txns == '':
				return
		if not isinstance(txns, (list, tuple)):
			txns = [x.strip() for x in txns.split(',')]
		cur = self.conn.cursor()
		rvsl_event = []
		for txn in txns:
			rvsl_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
			cur.execute(rvsl_query)
			rvsl = list(cur.fetchone())
			logging.debug('rvsl: {}'.format(rvsl))
			if '[RVSL]' in rvsl[7]:
				print('Cannot reverse a reversal for txn_id: {}. Enter a new entry instead.'.format(txn))
				continue
			del rvsl[5]
			rvsl = tuple(rvsl)
			if date is None: # rvsl[7] or np.nan
				date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
				date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
			rvsl_entry = [ rvsl[1], rvsl[2], rvsl[3], date, rvsl[5], '[RVSL] ' + rvsl[6], rvsl[7], rvsl[8] or '' if rvsl[8] != 0 else rvsl[8], rvsl[9] or '' if rvsl[9] != 0 else rvsl[9], rvsl[11], rvsl[10], rvsl[12] ]
			rvsl_event += [rvsl_entry]
		cur.close()
		self.journal_entry(rvsl_event)

	def split(self, txn=None, debit_acct=None, credit_acct=None, amount=None, date=None):
		if txn is None:
			txn = input('Enter the transaction number to split: ')
		split_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(split_query)
		split = cur.fetchone()
		cur.close()
		if amount is None:
			split_amt = float(input('How much to split by? '))
			while split_amt > split[12]:
				split_amt = float(input('That is too much. How much to split by? '))
		if debit_acct is None:
			debit_acct = input('Which debit account to split with? ')
			if debit_acct == '':
				debit_acct = split[10]
		if credit_acct is None:
			credit_acct = input('Which credit account to split with? ')
			if credit_acct == '':
				credit_acct = split[11]
		if date is None:
			date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
		orig_split_entry = [ split[1], split[2], split[3], date, split[5], split[6], split[7], split[8] or '' if split[8] != 0 else split[8], split[9] or '' if split[9] != 0 else split[9], split[10], split[11], split[12] - split_amt ]
		new_split_entry = [ split[1], split[2], split[3], date, split[5], split[6], split[7], split[8] or '' if split[8] != 0 else split[8], split[9] or '' if split[9] != 0 else split[9], debit_acct, credit_acct, split_amt ]
		split_event = [orig_split_entry, new_split_entry]
		self.reversal_entry(txn)
		self.journal_entry(split_event)

	def adjust(self, txn=None, price=None, qty=None, item=None):
		if txn is None:
			txn = input('Enter the transaction number to adjust: ') # TODO Add check to ensure valid transaction number
		adj_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = ' + txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(adj_query)
		entry = cur.fetchone()
		print('Entry to Adjust: \n{}'.format(entry))
		# If at least one parameter is provided, don't ask for the others
		if price is not None or qty is not None or item is not None:
			if price is None:
				price = entry[8]
			if qty is None:
				qty = entry[9]
			if item is None:
				item = entry[7]
		if price is None:
			while True:
				try:
					price = input('Enter the new price or hit enter if unchanged: ')
					if price == '':
						price = entry[8]
					price = float(price)
					break
				except ValueError:
					print('Not a valid entry. Must be a number.')
					continue
		if qty is None:
			while True:
				try:
					qty = input('Enter the new qty or hit enter if unchanged: ')
					if qty == '':
						qty = entry[9]
					qty = int(qty)
					break
				except ValueError:
					print('Not a valid entry. Must be a positive whole number.')
					continue
		if item is None:
			while True:
				try:
					item = input('Enter the new item or hit enter if unchanged: ')
					if item == '':
						item = entry[7]
					item = str(item)
					break
				except ValueError:
					print('Not a valid entry. Try again.')
					continue
		if price is not None and qty is not None:
			amount = price * qty
		else:
			amount = entry[12]
		adjusted_entry = [ entry[1], entry[2], entry[3], entry[4], entry[5], '[Adj] ' + entry[6], item, price or '' if price != 0 else price, qty or '' if qty != 0 else qty, entry[10], entry[11], amount ]
		#print('Adjusted Entry: \n{}'.format(adjusted_entry))
		adjusted_event = [adjusted_entry]
		self.reversal_entry(txn)
		self.journal_entry(adjusted_event)

	def uncategorize(self, txn=None, debit_acct=None, credit_acct=None):
		if txn is None:
			txn = input('Enter the transaction number to uncategorize: ') # TODO Add check to ensure valid transaction number
		uncat_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(uncat_query)
		entry = cur.fetchone()
		#print('Entry: \n{}'.format(entry))
		debit_acct = entry[10]
		if entry[10] == 'Uncategorized':
			if debit_acct is None:
				debit_acct = input('Enter the account to debit: ')
			if debit_acct not in self.coa.index:
				print('\n' + debit + ' is not a valid account.')
		credit_acct = entry[11]
		if entry[11] == 'Uncategorized':
			if credit_acct is None:
				credit_acct = input('Enter the account to credit: ')
			if credit_acct not in self.coa.index:
				print('\n' + credit + ' is not a valid account.')
		new_entry = [ entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8] or '', entry[9] or '', debit_acct, credit_acct, entry[12] ]
		#print('New Entry: \n{}'.format(new_entry))
		new_cat_query = 'UPDATE '+ self.ledger_name +' SET debit_acct = \'' + debit_acct + '\', credit_acct = \'' + credit_acct + '\' WHERE txn_id = '+ txn + ';'
		#print('New Cat Query: \n{}'.format(new_cat_query))
		cur.execute(new_cat_query)
		cur.close()
		self.refresh_ledger()
		return new_entry

	def hist_cost(self, qty=None, item=None, acct=None, remaining_txn=False, event_id=False, avg_cost=False, v=False):
		v2 = False
		if qty is None:
			qty = int(input('Enter quantity: '))
		# orig_qty = qty
		if item is None:
			item = input('Enter item: ')
		if acct is None:
			acct = 'Inventory' #input('Enter account: ') # TODO Remove this maybe
		if qty == 0:
			return 0

		if avg_cost: # TODO Test Avg Cost
			if v: print('Getting average historical cost of {} for {} qty.'.format(item, qty))
			total_balance = ledger.balance_sheet([acct], item=item)
			if v: print('Total Balance: {}'.format(total_balance))
			total_qty = ledger.get_qty(items=item, accounts=[acct])
			if v: print('Total Qty: {}'.format(total_qty))
			if v: print('Avg. Cost: {}'.format(total_balance / total_qty))
			amount = qty * (total_balance / total_qty)
			if v: print('Avg. Cost Amount: {}'.format(amount))
			return amount
		else:
			if v: print('Getting historical cost of {} for {} qty.'.format(item, qty))
			orig_qty = qty
			qty_txns = self.get_qty_txns(item, acct)
			if v: print('Qty TXNs Raw: {} \n{}'.format(len(qty_txns), qty_txns))
			m1 = qty_txns.credit_acct == acct
			m2 = qty_txns.credit_acct != acct
			credit_qtys = -qty_txns['qty']
			debit_qtys = qty_txns['qty']
			qty_txns = np.select([m1, m2], [credit_qtys, debit_qtys])
			if v: print('Qty TXNs: {} \n{}'.format(len(qty_txns), qty_txns))

			# Find the first lot of unsold items
			count = 0
			qty_back = self.get_qty(item, [acct]) # TODO Confirm this work when there are multiple different lots of buys and sells in the past
			if v: print('Qty to go back: {}'.format(qty_back))
			qty_change = []
			qty_change.append(qty_back)
			# neg = False
			for txn in qty_txns[::-1]:
				if v2: print('Hist TXN Item: {}'.format(txn))
				# if txn < 0:
				# 	neg = True
				count -= 1
				if v2: print('Hist Count: {}'.format(count))
				qty_back -= txn
				qty_change.append(qty_back)
				if v2: print('Qty Back: {}'.format(qty_back))
				if v: print('Count: {} | TXN: {} | Qty Back: {}'.format(count, txn, qty_back))
				if qty_back == 0:
					break
				# elif qty_back > 0 and neg:
				# 	count += 1
				# 	if v: print('Hist Count Neg: {}'.format(count))
				# 	neg = False

			if v2: print('Qty Back End: {}'.format(qty_back))
			start_qty = qty_txns[count]
			if v: print('Start Qty lot: {}'.format(start_qty))

			qty_txns_gl = self.get_qty_txns(item, acct)
			qty_txns_gl_check = qty_txns_gl.loc[qty_txns_gl['credit_acct'] == acct]
			if not qty_txns_gl_check.empty:
				mask = qty_txns_gl.credit_acct == acct
				#print('Mask: \n{}'.format(mask))
				#qty_txns_gl_flip = qty_txns_gl.loc[mask, 'qty'] # Testing
				#print('qty_txns_gl_flip: \n{}'.format(qty_txns_gl_flip))
				# flip_qty = qty_txns_gl['qty'] * -1
				warnings.filterwarnings('ignore')
				# WithCopyWarning: Warning here
				# qty_txns_gl.loc[mask, 'qty'] = flip_qty
				#qty_txns_gl.loc[mask, 'qty'] = qty_txns_gl['qty'] * -1 # Old
				qty_txns_gl.loc[mask, 'qty'] *= -1

			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				if v: print('QTY TXNs GL: {} \n{}'.format(len(qty_txns_gl), qty_txns_gl))
			if v: print('Hist Count Final: {}'.format(count))
			start_index = qty_txns_gl.index[count]
			if v2: print('Start Index: {} | Len: {}'.format(start_index, len(qty_txns_gl)))
			if remaining_txn:
				avail_txns = qty_txns_gl.loc[start_index:]
				return avail_txns
			if v2: print('Qty Change List: \n{}'.format(qty_change))
			if len(qty_change) >= 3:
				avail_qty = start_qty - qty_change[-1]#-3]# Portion of first lot of unsold items that has not been sold
			else:
				avail_qty = start_qty

			if v: print('Available qty in start lot: {}'.format(avail_qty))
			amount = 0
			if qty <= avail_qty: # Case when first available lot covers the need
				if v2: print('Hist Qty: {}'.format(qty))
				price_chart = pd.DataFrame({'price':[self.gl.loc[start_index]['price']], 'qty':[qty], 'avail_qty':[max(avail_qty, 0)], 'event_id':self.gl.loc[start_index]['event_id']})
				if price_chart.shape[0] >= 2:
					print('Historical Cost Price Chart: \n{}'.format(price_chart))
				if event_id:
					return price_chart
				amount = price_chart.price.dot(price_chart.qty)
				print('Historical Cost Case | One for {} {}: {}'.format(orig_qty, item, amount))
				return amount

			price_chart = pd.DataFrame({'price':[self.gl.loc[start_index]['price']], 'qty':[max(avail_qty, 0)], 'avail_qty':[max(avail_qty, 0)], 'event_id':self.gl.loc[start_index]['event_id']}) # Create a list of lots with associated price
			qty = qty - avail_qty # Sell the remainder of first lot of unsold items
			if v2: print('Historical Cost Price Chart Start: \n{}'.format(price_chart))
			if v2: print('Qty Left to be Sold First: {}'.format(qty))
			count += 1
			if v: print('Count First: {}'.format(count))
			current_index = qty_txns_gl.index[count]
			if v2: print('Current Index First: {}'.format(current_index))
			while qty > 0: # Running amount of qty to be sold
				if v2: print('QTY Check: {}'.format(qty_txns_gl.loc[current_index]['qty']))
				# while qty_txns_gl.loc[current_index]['qty'] < 0: # TODO Confirm this is not needed
				# 	count += 1
				# 	if v: print('Count When Neg: {}'.format(count))
				# 	current_index = qty_txns_gl.index[count]
				current_index = qty_txns_gl.index[count]
				if v2: print('Current Index: {}'.format(current_index))
				if v: print('Qty Left to be Sold 1: {}'.format(qty))
				if v: print('Current TXN Qty: {} | {}'.format(qty_txns_gl.loc[current_index]['qty'], self.gl.loc[current_index]['qty']))
				if qty < self.gl.loc[current_index]['qty']: # Final case when the last sellable lot is larger than remaining qty to be sold
					# price_chart = price_chart.append({'price':self.gl.loc[current_index]['price'], 'qty':max(qty, 0), 'avail_qty':self.gl.loc[current_index]['qty'], 'event_id':self.gl.loc[current_index]['event_id']}, ignore_index=True)
					tmp_df = pd.DataFrame({'price':[self.gl.loc[current_index]['price']], 'qty':[max(qty, 0)], 'avail_qty':[self.gl.loc[current_index]['qty']], 'event_id':[self.gl.loc[current_index]['event_id']]})
					dfs = [price_chart, tmp_df]
					dfs = [df for df in dfs if not df.empty]
					price_chart = pd.concat(dfs, ignore_index=True)
					if price_chart.shape[0] >= 2:
						print('Historical Cost Price Chart: \n{}'.format(price_chart))
					if event_id:
						return price_chart
					amount = price_chart.price.dot(price_chart.qty) # Take dot product
					print('Historical Cost Case | Two for {} {}: {}'.format(orig_qty, item, amount))
					return amount
				
				# price_chart = price_chart.append({'price':self.gl.loc[current_index]['price'], 'qty':max(self.gl.loc[current_index]['qty'], 0), 'avail_qty':self.gl.loc[current_index]['qty'], 'event_id':self.gl.loc[current_index]['event_id']}, ignore_index=True)
				tmp_df = pd.DataFrame({'price':[self.gl.loc[current_index]['price']], 'qty':[max(self.gl.loc[current_index]['qty'], 0)], 'avail_qty':[self.gl.loc[current_index]['qty']], 'event_id':[self.gl.loc[current_index]['event_id']]})
				dfs = [price_chart, tmp_df]
				dfs = [df for df in dfs if not df.empty]
				price_chart = pd.concat(dfs, ignore_index=True)
				qty = qty - self.gl.loc[current_index]['qty']
				if v: print('Qty Left to be Sold 2: {}'.format(qty))
				count += 1
				if v: print('Count: {}'.format(count))

			if price_chart.shape[0] >= 2:
				print('Historical Cost Price Chart: \n{}'.format(price_chart))
			if event_id:
				return price_chart
			amount = price_chart.price.dot(price_chart.qty) # If remaining lot perfectly covers remaining amount to be sold
			print('Historical Cost Case | Three for {} {}: {}'.format(orig_qty, item, amount))
			return amount

	def aggregate_gl(self, v=True):
		# print('aggregate_gl:')
		# print(self.gl)
		gl = self.gl.reset_index()
		# print('reset gl:')
		# print(gl)
		cols = [
				# 'txn_id',
				# 'event_id',
				'entity_id',
				'cp_id',
				# 'date',
				# 'post_date',
				# 'loc',None
				# 'description',None
				'item_id',
				# 'price',
				# 'qty',
				'debit_acct',
				'credit_acct',
				# 'amount',14
		]
		print('cols:', cols)
		# TODO store the txn_id somewhere to continue from there - 
		opening_bals = gl.groupby(cols).agg({'txn_id': 'max', 'event_id': 'max', 'date': 'max', 'post_date': 'max', 'price': 'mean', 'qty': 'sum', 'amount': 'sum'})
		opening_bals.reset_index(inplace=True)
		# if v: print('Opening balances:\n', opening_bals)
		open_bal_event = []
		for i, bal_txn in opening_bals.iterrows():
			# if v: print(f'i: {i} bal_txn:')
			open_bal_entry = [ bal_txn[6], bal_txn[0], bal_txn[1], bal_txn[7], bal_txn[8], '', '', bal_txn[2], bal_txn[9] or '' if bal_txn[9] != 0 else bal_txn[9], bal_txn[10], bal_txn[3], bal_txn[4], bal_txn[11] ]
			# if v: print('open_bal_entry:\n', open_bal_entry)
			open_bal_event += [open_bal_entry]
		if v: print('open_bal_event:\n', open_bal_event)
		# if v: print('count:', len(open_bal_event))
		# self.journal_entry(open_bal_event)
		return open_bal_event

	def roll_over(self, size=10, v=True):
		print('Rolling over GL.')
		gls = self.get_gl_count(v=v)
		if gls < size:
			print(f'{gls} is less than {size} transactions required to roll over the db.')
			return
		# accts.copy_db(v=v) # TODO Fix this scope
		rollover_event = self.aggregate_gl(v=v)
		self.journal_entry(rollover_event)
		print('GL rolled over.')
		# Check if GL count over 100
		# If so, make copy of db
		# Run aggregate
		# Book opening balances
		# Delete prior txn
		# Or try
		# Clear GL
		# Then book opening balances

	def latest_date(self, v=True):
		result = self.gl['date'].max()
		if v: print('Latest Date:', result)
		return result

	def oldest_date(self, v=True):
		result = self.gl['date'].min()
		if v: print('Oldest Date:', result)
		return result

	def latest_item(self, v=True):
		result = self.gl['item_id'].iloc[-1]
		if v: print('Latest Item:', result)
		return result

	def count_days(self, v=True):
		earliest = self.gl['date'].min()
		if v: print('Earliest Date:', earliest)
		earliest = datetime.datetime.strptime(earliest, '%Y-%m-%d')
		latest = self.gl['date'].max()
		if v: print('Latest Date:  ', latest)
		latest = datetime.datetime.strptime(latest, '%Y-%m-%d')
		day_count = latest - earliest
		if v: print('Number of Days:', day_count.days)
		return day_count

	def duration(self, v=True):
		earliest = self.gl['post_date'].min()
		if v: print('Earliest:', earliest)
		earliest = datetime.datetime.strptime(earliest, '%Y-%m-%d %H:%M:%S.%f')
		latest = self.gl['post_date'].max()
		if v: print('Latest:  ', latest)
		latest = datetime.datetime.strptime(latest, '%Y-%m-%d %H:%M:%S.%f')
		dur = latest - earliest
		if v: print('Duration:', dur)
		# if v: print('Duration Days:', dur.days)
		return dur
	
	def get_gl_count(self, v=True):
		count = self.gl.shape[0]
		if v: print('Number of transactions:', count)
		return count

	def bs_hist(self, dates=None, entities=None, v=True): # TODO Optimize this so it does not recalculate each time
	# nohup python -u acct.py -db test01.db -c hist >> logs/hist_test01.log 2>&1
		if entities is None:
			entities = input('Which entity or press enter for all entities? ')
		if entities == '':
			entities = None
		if entities is None:
			entities = pd.unique(self.gl['entity_id'])
		else:
			if not isinstance(entities, (list, tuple)):
				if isinstance(entities, str):
					entities = [x.strip() for x in entities.split(',')]
				else:
					entities = [entities]
		if v: print('Number of entities: {}'.format(len(entities)))
		if dates is None:
			dates = input('Which date or press enter for all dates? ')
			# dates = ['2019-05-27']
		if dates == '':
			dates = None
		if dates is None:
			dates = pd.unique(self.gl['date'])
		else:
			if not isinstance(dates, (list, tuple)):
				if isinstance(dates, str):
					dates = [x.strip() for x in dates.split(',')]
				else:
					dates = [dates]
		if v: print('Number of dates: {}'.format(len(dates)))
		# print(entities)
		# print(dates)
		cur = self.conn.cursor()
		create_bs_hist_query = '''
			CREATE TABLE IF NOT EXISTS hist_bs (
				date date NOT NULL,
				entity text NOT NULL,
				assets real NOT NULL,
				liabilities real NOT NULL,
				equity real NOT NULL,
				revenues real NOT NULL,
				expenses real NOT NULL,
				net_income real NOT NULL,
				equity_ni_liab real NOT NULL,
				bal_check real NOT NULL,
				net_asset_value real NOT NULL
			);
			'''
		cur.execute(create_bs_hist_query)
		cur.execute('DELETE FROM hist_bs')
		for entity in entities:
			# if v: print('Entity:', entity)
			self.set_entity(entity)
			for date in dates:
				self.set_date(date)
				if v: print('Entity: {} | Date: {}'.format(entity, date))
				self.balance_sheet()
				self.bs.set_index('line_item', inplace=True)
				col0 = str(entity)
				col1 = self.bs.loc['Total Assets:'].iloc[0]
				col2 = self.bs.loc['Total Liabilities:'].iloc[0]
				col3 = self.bs.loc['Total Equity:'].iloc[0]
				col4 = self.bs.loc['Total Revenues:'].iloc[0]
				col5 = self.bs.loc['Total Expenses:'].iloc[0]
				col6 = self.bs.loc['Net Income:'].iloc[0]
				col7 = self.bs.loc['Equity+NI+Liab.:'].iloc[0]
				col8 = self.bs.loc['Balance Check:'].iloc[0]
				col9 = self.bs.loc['Net Asset Value:'].iloc[0]
				if isinstance(col1, np.float64):
					data = (date,col0,col1,col2,col3,col4,col5,col6,col7,col8,col9)
				else:
					data = (date,col0,float(col1),float(col2),float(col3),float(col4),float(col5),float(col6),float(col7),float(col8),float(col9))
				logging.info(data)
				cur.execute('INSERT INTO hist_bs VALUES (?,?,?,?,?,?,?,?,?,?,?)', data)
		self.conn.commit()
		cur.execute('PRAGMA database_list')
		db_path = cur.fetchall()[0][-1]
		db_name = db_path.rsplit('/', 1)[-1]
		if v: print('DB Name:', db_name)
		cur.close()
		self.hist_bs = pd.read_sql_query('SELECT * FROM hist_bs;', self.conn, index_col=['date','entity'])
		return self.hist_bs, db_name

		# TODO Add function to book just the current days bs to hist_bs

	def print_hist(self, dates=None, save=True, v=True):
		db_name = self.bs_hist(dates=dates)[1]
		if dates is None:
			dates = [''] # TODO Is this needed?
		if isinstance(dates, str):
			dates = [x.strip() for x in dates.split(',')]
		quirk = '_' if dates else ''
		path = 'data/bs_hist_' + db_name[:-3] + quirk + str(dates[-1]) + '.csv'
		if save:
			self.hist_bs.to_csv(path, index=True)
		if v:
			with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
				print(self.hist_bs)
		print('File saved to: {}'.format(path))
		print('-' * DISPLAY_WIDTH)
		return self.hist_bs

	def fix_qty(self): # Temp qty fix function
		cur = self.conn.cursor()
		qty = np.nan
		#print('QTY: {}'.format(qty))
		value = (qty,)
		#print('Value: {}'.format(value))
		cur.execute('UPDATE ' + self.ledger_name + ' SET qty = (?) WHERE qty = 1', value)
		self.conn.commit()
		cur.close()
		print('QTYs converted.')

	def inv_hist(self, accounts='Inventory', by_entity=False, save=True, v=False):
		start_date = self.oldest_date()
		start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		if v: print('start_date:', start_date)
		# if v: print('start_date type:', type(start_date))
		end_date = self.latest_date()
		end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
		if v: print('end_date:', end_date)
		# if v: print('end_date type:', type(end_date))
		dur = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days)]
		hist_inv = []
		for date in dur:
			date = date.strftime('%Y-%m-%d')
			if v: print('date:', date)
			self.set_date(date)
			inv = self.get_qty(accounts=accounts, by_entity=by_entity)#, v=True)
			inv['date'] = date
			hist_inv.append(inv)
			hist_inv = [df for df in hist_inv if not df.empty]
		hist_inv = pd.concat(hist_inv, ignore_index=True)
		if v: print('hist_inv:')
		if v: print(hist_inv)
		if save:
			save_location = 'data/'
			outfile = 'inv_hist' + datetime.datetime.today().strftime('_%Y-%m-%d_%H-%M-%S') + '.csv'
			hist_inv.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
			print('{} data saved to: {}'.format('inv_hist', save_location + outfile))
		return hist_inv

	def ratio_analysis(self, entity=None, date=None, v=False):
		if date is None or date == '':
			date = self.latest_date(v=False)
		self.set_date(date)
		if entity is not None and date is not '':
			self.set_entity(entity)
		roles = pd.DataFrame(roles_data)
		# print('Roles:', roles)
		ratios = []
		for _, role in roles.iterrows():
			# print('role_name:\n', role[0])
			value = self.sum_role(role[0], v=v)
			ratios.append(pd.DataFrame({'role': [role[0]], 'value': [value]}))
		ratios = pd.concat(ratios, ignore_index=True)

		# Get line items as vars
		cash = ratios[ratios['role'] == 'Cash & Cash Equivalents']['value'].values[0]
		inventory = ratios[ratios['role'] == 'Inventory']['value'].values[0]
		cogs = ratios[ratios['role'] == 'COGS']['value'].values[0]
		ar = ratios[ratios['role'] == 'Accounts Receivable']['value'].values[0]
		ap = ratios[ratios['role'] == 'Accounts Payable']['value'].values[0]
		dep_exp = ratios[ratios['role'] == 'Depreciation']['value'].values[0]
		amort_exp = ratios[ratios['role'] == 'Amortization']['value'].values[0]
		int_exp = ratios[ratios['role'] == 'Interest Expense']['value'].values[0]
		tax_exp = ratios[ratios['role'] == 'Tax Expenses']['value'].values[0] + ratios[ratios['role'] == 'Deferred Tax Expense']['value'].values[0]
		ratios = [ratios]

		# Calc element totals		
		current_assets = ratios[0].loc[0:6,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Current Assets'], 'value': [current_assets]}))
		fixed_assets = ratios[0].loc[7:15,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Fixed Assets'], 'value': [fixed_assets]}))
		total_assets = ratios[0].loc[0:15,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Total Assets'], 'value': [total_assets]}))
		current_liab = ratios[0].loc[16:22,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Current Liabilities'], 'value': [current_liab]}))
		long_term_liab = ratios[0].loc[23:25,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Long-term Liabilities'], 'value': [long_term_liab]}))
		total_liab = ratios[0].loc[16:25,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Total Liabilities'], 'value': [total_liab]}))
		# Calculate working capital
		working_cap = current_assets - current_liab
		ratios.append(pd.DataFrame({'role': ['Working Capital'], 'value': [working_cap]}))
		total_equity = ratios[0].loc[26:32,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Total Equity'], 'value': [total_equity]}))
		total_revenue = ratios[0].loc[33:36,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Total Revenue'], 'value': [total_revenue]}))
		total_expense = ratios[0].loc[37:51,'value'].sum()
		ratios.append(pd.DataFrame({'role': ['Total Expense'], 'value': [total_expense]}))
		gross_margin = total_revenue - cogs
		ratios.append(pd.DataFrame({'role': ['Gross Margin'], 'value': [gross_margin]}))
		ebitda = total_revenue - total_expense + dep_exp + amort_exp + int_exp + tax_exp
		ratios.append(pd.DataFrame({'role': ['EBITDA'], 'value': [ebitda]}))
		op_inc = total_revenue - total_expense + int_exp + tax_exp # Same as EBIT usually
		ratios.append(pd.DataFrame({'role': ['Operating Income'], 'value': [op_inc]}))
		net_income = total_revenue - total_expense
		ratios.append(pd.DataFrame({'role': ['Net Income'], 'value': [net_income]}))

		# Calculate additional avg totals
		## Get prior annual date for averages
		from dateutil.relativedelta import relativedelta
		first_date = self.oldest_date(v=False)
		first_date = datetime.datetime.strptime(first_date, '%Y-%m-%d')
		past_date = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(years=1)
		past_date = max(first_date, past_date)
		past_date = past_date.strftime('%Y-%m-%d')
		self.set_date(past_date)

		priors = []
		# current_roles = roles[roles['current']] # TODO Maybe don't need rev and exp?
		# print(current_roles)
		for _, role in roles.iterrows():
			# print('prior_role_name:\n', role[0])
			prior_value = self.sum_role(role[0], v=v)
			priors.append(pd.DataFrame({'role': ['Prior ' + role[0]], 'value': [prior_value]}))
		priors = pd.concat(priors, ignore_index=True)
		# print('Priors:\n', priors)
		# Avg Working Cap
		prior_current_assets = priors.loc[0:6,'value'].sum()
		prior_current_liab = priors.loc[16:22,'value'].sum()
		prior_working_cap = prior_current_assets - prior_current_liab
		avg_working_cap = (prior_working_cap + working_cap) / 2
		ratios.append(pd.DataFrame({'role': ['Avg Working Capital'], 'value': [avg_working_cap]}))

		# Avg Inv
		try:
			prior_inventory = self.sum_role('Inventory', v=v)
			avg_inventory = (prior_inventory + inventory) / 2
			ratios.append(pd.DataFrame({'role': ['Avg Inventory'], 'value': [avg_inventory]}))
		except KeyError:
			prior_inventory = 0
			avg_inventory = 0
			print('No Inventory for prior date:', past_date)
		# Avg Rec
		try:
			prior_AR = self.sum_role('Accounts Receivable', v=v)
			avg_AR = (prior_AR + ar) / 2
			ratios.append(pd.DataFrame({'role': ['Avg Accounts Receivable'], 'value': [avg_AR]}))
		except KeyError:
			prior_AR = 0
			avg_AR = 0
			print('No AR for prior date:', past_date)
		# Avg Pay
		try:
			prior_AP = self.sum_role('Accounts Payable', v=v)
			avg_AP = (prior_AP + ap) / 2
			ratios.append(pd.DataFrame({'role': ['Avg Accounts Payable'], 'value': [avg_AP]}))
		except KeyError:
			prior_AP = 0
			avg_AP = 0
			print('No AP for prior date:', past_date)
		
		# Avg Fixed Assets (Non-current assets)
		prior_fixed_assets = priors.loc[7:15,'value'].sum()
		avg_fixed_assets = (prior_fixed_assets + fixed_assets) / 2
		ratios.append(pd.DataFrame({'role': ['Avg Fixed Assets'], 'value': [avg_fixed_assets]}))
		# Avg Total Assets
		prior_total_assets = priors.loc[0:15,'value'].sum()
		avg_total_assets = (prior_total_assets + total_assets) / 2
		ratios.append(pd.DataFrame({'role': ['Avg Total Assets'], 'value': [avg_total_assets]}))
		# Avg Total Liab (Not currently needed)
		prior_total_liab = priors.loc[16:25,'value'].sum()
		avg_total_liab = (prior_total_liab + total_liab) / 2
		ratios.append(pd.DataFrame({'role': ['Avg Total Liab'], 'value': [avg_total_liab]}))
		# Avg Total Equity
		prior_total_equity = priors.loc[26:32,'value'].sum()
		avg_total_equity = (prior_total_equity + total_equity) / 2
		ratios.append(pd.DataFrame({'role': ['Avg Total Equity'], 'value': [avg_total_equity]}))
		self.reset()
		self.set_date(date)
		if entity is not None:
			self.set_entity(entity)

		ratios = [pd.concat(ratios, ignore_index=True)]

		# Calculate financial ratios
		with np.errstate(invalid='ignore', divide='ignore'):
			# Activity Ratios
			try:
				inv_turnover = cogs / avg_inventory # COGS / Avg Inv
				ratios.append(pd.DataFrame({'role': ['Inventory Turnover'], 'value': [inv_turnover]}))
			except KeyError:
				# inv_turnover = 0 # TODO Should I do this?
				print('No COGS for Inventory Turnover calculation.')
			try:
				doh = 365 / inv_turnover # 365 / Inv Turnover
				ratios.append(pd.DataFrame({'role': ['Days of Inventory on Hand (DOH)'], 'value': [doh]}))
			except UnboundLocalError:
				# doh = 0
				print('No Inventory Turnover for DoH calculation.')
			try:
				rec_turnover = total_revenue / avg_AR # Rev / Avg Receivables
				ratios.append(pd.DataFrame({'role': ['Receivables Turnover'], 'value': [rec_turnover]}))
			except KeyError:
				# rec_turnover = 0
				print('No COGS for Receivables Turnover calculation.')
			try:
				dso = 365 / rec_turnover # 365 / Rec Turnover
				ratios.append(pd.DataFrame({'role': ['Days of Sales Outstanding (DSO)'], 'value': [dso]}))
			except UnboundLocalError:
				# dso = 0
				print('No Receivables Turnover for DSO calculation.')
			try:
				pay_turnover = cogs / avg_AP # Purchases / Avg Payable # TODO Confirm should this be COGS?
				ratios.append(pd.DataFrame({'role': ['Payables Turnover'], 'value': [pay_turnover]}))
			except KeyError:
				# pay_turnover = 0
				print('No Purchases for Payables Turnover calculation.')
			try:
				dop = 365 / pay_turnover # 365 / Pay Turnover
				ratios.append(pd.DataFrame({'role': ['Number of Days of Payables (DoP)'], 'value': [dop]}))
			except UnboundLocalError:
				# dop = 0
				print('No Payables Turnover for DoP calculation.')
			try:
				wc_turnover = total_revenue / avg_working_cap # Rev / Avg Working Capital
				ratios.append(pd.DataFrame({'role': ['Working Capital Turnover'], 'value': [wc_turnover]}))
				fa_turnover = total_revenue / avg_fixed_assets # Rev / Avg Fix Asset
				ratios.append(pd.DataFrame({'role': ['Fixed Asset Turnover'], 'value': [fa_turnover]}))
				asset_turnover = total_revenue / avg_total_assets # Rev / Avg Total Assets
				ratios.append(pd.DataFrame({'role': ['Total Asset Turnover'], 'value': [asset_turnover]}))
			except KeyError: # TODO Is this needed?
				# wc_turnover = 0
				# fa_turnover = 0
				# asset_turnover = 0
				print('No Total Revenue for Working Capital, Fixed Asset, or Total Asset Turnover calculations.')

			# Liquidity Ratios
			current_ratio = current_assets / current_liab # Cur Assets / Cur Liabilities
			ratios.append(pd.DataFrame({'role': ['Current Ratio'], 'value': [current_ratio]}))
			quick_ratio = (current_assets - inventory) / current_liab # Cur Assets less Inv / Cur Liab
			ratios.append(pd.DataFrame({'role': ['Quick Ratio'], 'value': [quick_ratio]}))
			cash_ratio = cash / current_liab # Cash / Cur Liab
			ratios.append(pd.DataFrame({'role': ['Cash Ratio'], 'value': [cash_ratio]}))
			# 'Defensive Interval Ratio' # Not implemented yet
			ccc = doh + dso - dop # DOH + DSO - No Days of Pay
			ratios.append(pd.DataFrame({'role': ['Cash Conversion Cycle'], 'value': [ccc]}))

			# Solvency Ratios
			debt_to_assets = total_liab / total_assets # Debt / Assets
			ratios.append(pd.DataFrame({'role': ['Debt-to-assets ratio'], 'value': [debt_to_assets]}))
			debt_to_capital = total_liab / (total_liab + total_equity) # Debt / Debt + Shareholder's Eq
			ratios.append(pd.DataFrame({'role': ['Debt-to-capital ratio'], 'value': [debt_to_capital]}))
			debt_to_equity = total_liab / total_equity # Debt / Shareholder's Eq
			ratios.append(pd.DataFrame({'role': ['Debt-to-equity ratio'], 'value': [debt_to_equity]}))
			fin_leverage_ratio = avg_total_assets / avg_total_equity # Avg Assets / Avg Equity
			ratios.append(pd.DataFrame({'role': ['Financial leverage ratio'], 'value': [fin_leverage_ratio]}))
			# 'Interest coverage' # EBIT / Interest Payments
			# 'Fixed charge coverage' # Not implemented yet

			# Profitability Ratios
			gross_profit_margin = gross_margin - total_revenue # Gross Profit / Rev
			ratios.append(pd.DataFrame({'role': ['Gross profit margin'], 'value': [gross_profit_margin]}))
			operating_profit_margin = (net_income + int_exp + tax_exp) / total_revenue # Op Inc / Rev
			ratios.append(pd.DataFrame({'role': ['Operating profit margin'], 'value': [gross_profit_margin]}))
			pretax_margin = (net_income + tax_exp) / total_revenue # EBT / Rev
			ratios.append(pd.DataFrame({'role': ['Pretax margin'], 'value': [pretax_margin]}))
			net_profit_margin = net_income / total_revenue # Net Inc / Rev
			ratios.append(pd.DataFrame({'role': ['Net profit margin'], 'value': [net_profit_margin]}))
			operating_return_on_assets = (net_income + int_exp + tax_exp) / avg_total_assets # Op Inc / Avg Assets
			ratios.append(pd.DataFrame({'role': ['Operating Return on Assets'], 'value': [operating_return_on_assets]}))
			return_on_assets = net_income / avg_total_assets # Net Inc / Avg Assets
			ratios.append(pd.DataFrame({'role': ['Return on Assets'], 'value': [return_on_assets]}))
			return_on_total_capital = (net_income + int_exp + tax_exp) / (total_liab + total_equity) # EBIT / Debt + Equity
			ratios.append(pd.DataFrame({'role': ['Return on total capital'], 'value': [return_on_total_capital]}))
			return_on_equity = net_income / avg_total_equity # Net Inc / Avg Equity
			ratios.append(pd.DataFrame({'role': ['Return on equity'], 'value': [return_on_equity]}))

			dupont_analysis = net_profit_margin * asset_turnover * fin_leverage_ratio # Net profit margin * Total Asset Turnover * Financial leverage ratio
			ratios.append(pd.DataFrame({'role': ['DuPont Analysis'], 'value': [dupont_analysis]}))

		ratios = pd.concat(ratios, ignore_index=True)
		return ratios


def create_accounts(conn=None, standard_accts=None, entities_table_name=None, items_table_name=None):
	print('Accounts object created.')
	return Accounts(conn, standard_accts, entities_table_name, items_table_name)

def create_ledger(accts=None, conn=None, ledger_name=None, entity=None, date=None, start_date=None, txn=None, start_txn=None):
	if accts is None:
		accts = create_accounts(conn)
	print('Ledger object created.')
	return Ledger(accts, ledger_name, entity, date, start_date, txn, start_txn)

def main(conn=None, command=None, external=False):
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-c', '--command', type=str, help='A command for the program.')
	# Dummy args to allow acct.py work with econ.py command loop
	parser.add_argument('-sim', '--simulation', action='store_true', help='Run on historical data.') # For trading sim
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-p', '--population', type=int, default=1, help='The number of people in the econ sim per government.')
	parser.add_argument('-r', '--reset', action='store_true', help='Reset the sim!')
	parser.add_argument('-g', '--governments', type=int, default=1, help='The number of governments in the econ sim.')
	parser.add_argument('-rand', '--random', action='store_false', help='Remove randomness from the sim.') # TODO Is this needed?
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
	parser.add_argument('-t', '--time', type=int, help='The number of days the sim will run for.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital each player to start with.')
	parser.add_argument('-u', '--users', type=int, nargs='?', const=-1, help='Play the sim as an individual!')
	parser.add_argument('-P', '--players', type=int, nargs='?', const=-1, help='Play the sim as a government!')
	parser.add_argument('-win', '--win', action='store_true', help='Set win conditions for the sim.')
	parser.add_argument('-pin', '--pin', action='store_true', help='Enable pin for turn protection.')
	parser.add_argument('-early', '--early', action='store_true', help='Automatically end the turn when no hours left when not in user mode.')
	parser.add_argument('-j', '--jones', action='store_true', help='Enable game mode like Jones in the Fast Lane.')
	parser.add_argument('-inf', '--inf_time', action='store_true', help='Toggles infinite time for labour and turns off waiting requirements.')
	parser.add_argument('-v', '--verbose', action='store_false', help='Turn off verbosity for running the sim in auto mode.')
	args = parser.parse_args()
	print(str(sys.argv))

	if args.database is not None:
		conn = args.database
	# accts = Accounts(conn=conn)
	# ledger = Ledger(accts, ledger_name=args.ledger, entity=args.entity)
	accts = create_accounts(conn=conn)
	ledger = create_ledger(accts, ledger_name=args.ledger, entity=args.entity)
	if command is None:
		command = args.command

	while True: # TODO Make this a function that has the command passed in as an argument
		if args.command is None and not external:
			command = input('\nType one of the following commands:\nBS, GL, JE, RVSL, loadGL, Accts, addAcct, loadAccts, help, exit\n')
		# TODO Add help command to list full list of commands
		if command.lower() == 'gl':
			ledger.print_gl()
			if args.command is not None: exit()
		elif command.lower() == 'exportgl':
			ledger.export_gl()
			if args.command is not None: exit()
		elif command.lower() == 'loadgl':
			ledger.load_gl()
			if args.command is not None: exit()
		elif command.lower() == 'rollover':
			ledger.roll_over(1)
			if args.command is not None: exit()
		elif command.lower() == 'accts':
			accts.print_accts()
			if args.command is not None: exit()
		elif command.lower() == 'acct':
			acct = input('Which account? ').title()
			print(ledger.balance_sheet([acct]))
			if args.command is not None: exit()
		elif command.lower() == 'addacct':
			accts.add_acct()
			if args.command is not None: exit()
		elif command.lower() == 'removeacct':
			accts.remove_acct()
			if args.command is not None: exit()
		elif command.lower() == 'loadaccts':
			accts.load_accts()
			if args.command is not None: exit()
		elif command.lower() == 'exportaccts':
			accts.export_accts()
			if args.command is not None: exit()
		elif command.lower() == 'dupes':
			accts.drop_dupe_accts()
			if args.command is not None: exit()
		elif command.lower() == 'je':
			ledger.journal_entry()
			if args.command is not None: exit()
		elif command.lower() == 'rvsl':
			ledger.reversal_entry()
			if args.command is not None: exit()
		elif command.lower() == 'del':
			# TODO Comment this command out for production
			ledger.remove_entries()
			if args.command is not None: exit()
		elif command.lower() == 'split':
			ledger.split()
			if args.command is not None: exit()
		elif command.lower() == 'adj':
			ledger.adjust()
			if args.command is not None: exit()
		elif command.lower() == 'uncategorize':
			ledger.uncategorize()
			if args.command is not None: exit()
		elif command.lower() == 'aggregate':
			ledger.aggregate_gl()
			if args.command is not None: exit()
		elif command.lower() == 'bs':
			ledger.print_bs()
			if args.command is not None: exit()
		elif command.lower() == 'qty':
			# print('Entity:', ledger.entity)
			item = input('Which item or ticker? ')#.lower()
			acct = input('Which account? ')#.title()
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(ledger.get_qty(item, acct))
			if args.command is not None: exit()
		elif command.lower() == 'inv' or command.lower() == 'ppe':
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				pd.options.display.float_format = '{:,.2f}'.format
				accts = ['Inventory']
				accts += ['Equipment','Buildings','Equipment In Use', 'Buildings In Use', 'Equipped'] # For econ sim
				inv = ledger.get_qty(items=None, accounts=accts, by_entity=True, show_zeros=False)#, v=True))
				print(inv)
				pd.options.display.float_format = '${:,.2f}'.format
			if args.command is not None: exit()
		elif command.lower() == 'invhist':
			ledger.inv_hist()
			if args.command is not None: exit()
		elif command.lower() == 'entity':
			ledger.set_entity()
			# print('Entity:', ledger.entity)
			if args.command is not None: exit()
		elif command.lower() == 'date':
			ledger.set_date()
			if args.command is not None: exit()
		elif command.lower() == 'startdate':
			ledger.set_start_date()
			if args.command is not None: exit()
		elif command.lower() == 'txn':
			ledger.set_txn()
			if args.command is not None: exit()
		elif command.lower() == 'starttxn':
			ledger.set_start_txn()
			if args.command is not None: exit()
		elif command.lower() == 'reset':
			ledger.reset()
			if args.command is not None: exit()
		elif command.lower() == 'hist':
			dates = None
			# dates = ['2019-05-27']
			ledger.print_hist(dates=dates, v=False)
			if args.command is not None: exit()
		elif command.lower() == 'latestdate':
			ledger.latest_date()
			if args.command is not None: exit()
		elif command.lower() == 'oldestdate':
			ledger.oldest_date()
			if args.command is not None: exit()
		elif command.lower() == 'latestitem':
			ledger.latest_item()
			if args.command is not None: exit()
		elif command.lower() == 'role':
			role = input('Which role? ')
			ledger.sum_role(role, v=True)
			if args.command is not None: exit()
		elif command.lower() == 'dur':
			ledger.duration()
			if args.command is not None: exit()
		elif command.lower() == 'countdays':
			ledger.count_days()
			if args.command is not None: exit()
		elif command.lower() == 'count':
			ledger.get_gl_count()
			if args.command is not None: exit()
		elif command.lower() == 'util':
			entity_id = input('Which entitie(s)? ')
			item = input('Which item or ticker (case sensitive)? ')#.lower()
			acct = input('Which account? ')#.title()
			desc = input('Description contains? ')
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				ledger.get_util(entity_id, item, acct, desc, v=True)
			if args.command is not None: exit()
		elif command.lower() == 'demand': # This only works for the econ sim
			demand = accts.print_table('demand', v=False)
			demand['qty'] = demand['qty'].astype(float)
			demand['qty'] = demand['qty'].astype(int)
			demand = demand.groupby(['item_id']).sum()['qty']
			total_demand = demand.sum()
			print(demand)
			print(f'Total demand: {total_demand}')
			if args.command is not None: exit()
		elif command.lower() == 'demanddiff': # This only works for the econ sim
			demand = accts.print_table('hist_demand', v=False)
			demand['qty'] = demand['qty'].astype(float)
			demand['qty'] = demand['qty'].astype(int)
			demand = demand.groupby(['date_saved', 'item_id']).sum()['qty'].reset_index()
			pd.options.display.float_format = '{:,.2f}'.format
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(demand)
			print('=====================================')
			demand['delta_qty'] = demand.groupby('item_id')['qty'].diff()
			demand = demand[demand['delta_qty'] != 0]
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(demand)
			pd.options.display.float_format = '${:,.2f}'.format
			if args.command is not None: exit()
		elif command.lower() == 'invdiff': # This only works for the econ sim
			inv_hist = accts.print_table('hist_inv', v=False)
			inv_hist['qty'] = inv_hist['qty'].astype(float)
			inv_hist['qty'] = inv_hist['qty'].astype(int)
			inv_hist = inv_hist.loc[~inv_hist['account'].isin(['Land'])]
			pd.options.display.float_format = '{:,.2f}'.format
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(inv_hist)
			print('=====================================')
			inv_hist['delta_qty'] = inv_hist.groupby(['item_id', 'account'])['qty'].diff()
			inv_hist = inv_hist[inv_hist['delta_qty'] != 0]
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(inv_hist)
			pd.options.display.float_format = '${:,.2f}'.format
			if args.command is not None: exit()
		# elif command.lower() == 'navhist':
		# 	start_date = ledger.oldest_date(v=False)
		# 	end_date = ledger.latest_date(v=False)
		# 	navhist = pd.DataFrame({'date': pd.date_range(start=start_date, end=end_date)})
		elif command.lower() == 'eutil': # This only works for the econ sim
			eutil = accts.print_table('util', v=False)
			eutil = eutil.head(1)
			print(eutil)
			if args.command is not None: exit()
		elif command.lower() == 'ebigutil': # This only works for the econ sim
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				ebigutil = accts.print_table('big_util', v=False)
				print(ebigutil)
			if args.command is not None: exit()
		elif command.lower() == 'ratio' or command.lower() == 'ratios':
			entity_id = input('Which entitie(s)? ')
			date = input('Which date? ')
			ratios = ledger.ratio_analysis(entity_id, date, v=False)
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(ratios)
			if args.command is not None: exit()
		elif command.lower() == 'entities':
			accts.print_entities()
			if args.command is not None: exit()
		elif command.lower() == 'countentities':
			print(accts.get_entities().shape[0])
			if args.command is not None: exit()
		elif command.lower() == 'items':
			accts.print_items()
			if args.command is not None: exit()
		elif command.lower() == 'addentity':
			accts.add_entity()
			if args.command is not None: exit()
		elif command.lower() == 'additem':
			accts.add_item()
			if args.command is not None: exit()
		elif command.lower() == 'removeitem':
			accts.remove_item()
			if args.command is not None: exit()
		elif command.lower() == 'loadweb':
			accts.load_from_web()
			if args.command is not None: exit()
		elif command.lower() == 'loadwebgl':
			ledger.load_gl_from_web()
			if args.command is not None: exit()
		elif command.lower() == 'loadentities':
			accts.load_entities()
			if args.command is not None: exit()
		elif command.lower() == 'loaditems':
			accts.load_items()
		elif command.lower() == 'tables':
			tables = pd.read_sql_query('SELECT name FROM sqlite_master WHERE type=\'table\';', ledger.conn)
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(f'{tables}\n')
			accts.print_table()
			if args.command is not None: exit()
		elif command.lower() == 'table':
			accts.print_table()
			if args.command is not None: exit()
		elif command.lower() == 'exporttable':
			accts.export_table()
			if args.command is not None: exit()
		elif command.lower() == 'edititem':
			accts.edit_item()
			if args.command is not None: exit()
		elif command.lower() == 'db':
			if args.database is not None:
				db = args.database
			else:
				db = accts.db
			print('Current database: {}'.format(db))
			if args.command is not None: exit()
		elif command.lower() == 'copydb':
			accts.copy_db()
			if args.command is not None: exit()
		elif command.lower() == 'bal':
			acct = input('Which account? ').title()
			tbal_start = time.perf_counter()
			bal = ledger.balance(acct, v=False)
			tbal_end = time.perf_counter()
			print(bal)
			print('Bal took {:,.2f} sec.'.format((tbal_end - tbal_start)))

			tbal_start = time.perf_counter()
			bal = ledger.print_bs()
			tbal_end = time.perf_counter()
			print(bal)
			print('BS took {:,.2f} sec.'.format((tbal_end - tbal_start)))
			if args.command is not None: exit()
		elif command.lower() == 'histcost':
			result = ledger.hist_cost(400, 'Rock', 'Inventory', avg_cost=True, v=True)
			print('Historical cost of {} {}: {}'.format(400, 'Rock', result))
			if args.command is not None: exit()
		elif command.lower() == 'width': # TODO Try and make this work
			DISPLAY_WIDTH = int(input('Enter number for display width: '))
			if args.command is not None: exit()

		elif command.lower() == 'help' or command.lower() == 'accthelp':
			commands = {
				'accts': 'View the Chart of Accounts with their types.',
				'gl': 'View the General Ledger.',
				'bs': 'View the Balance Sheet and Income Statement.',
				'entity': 'View only data related to the entity selected.',
				'date': 'Set the date to view the Balance Sheet up to.',
				'startdate': 'Set the start date to view the Income Statement from.',
				'reset': 'Resets both the entity and dates, to view for all entities and for all dates.',
				'je': 'Book a journal entry to the General Ledger.',
				'addacct': 'Add an account to the Chart of Accounts.',
				'rvsl': 'Reverse a journal entry on the General Ledger.',
				'removeacct': 'Remove an account on the Chart of Accounts.',
				'qty': 'Get the quantity of a particular item or all items if none is specified.',
				'more': 'List more commands... (WIP)',
				'more2': 'List even more commands... (WIP)',
				'exit': 'Exit out of the program.'
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
			if args.command is not None: exit()
		elif command.lower() == 'more' or command.lower() == 'acctmore':
			commands = {
				'split': 'Split a journal entry into more granular entries.',
				'uncategorize': 'For journal entries that are uncategorized, assign them to a new account.',
				'adj': 'Adjust a journal entry to change either the price or qty.',
				'txn': 'Set the date to view the Balance Sheet up to.',
				'starttxn': 'Set the start date to view the Income Statement from.',
				'util': 'Filter and export the General Ledger to csv with some analysis columns added.',
				'exportgl': 'Export the General Ledger to csv.',
				'loadgl': 'Import the General Ledger from csv.',#'Also supports loading trasnactions from RBC online banking and a legacy account system.',
				'exportaccts': 'Export the Chart of Accounts to csv.',
				'loadaccts': 'Import the Chart of Accounts from csv.',
				'table': 'Display any table in the database given its name.',
				'tables': 'Display a list of all tables in the database.',
				'exit': 'Exit out of the program.'
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
			if args.command is not None: exit()
		elif command.lower() == 'more2' or command.lower() == 'acctmore2':
			commands = {
				'rollover': '',
				'dupes': '',
				'del': '',
				'aggregate': '',
				'acct': '',
				'inv': '',
				'invhist': '',
				'hist': '',
				'latestdate': '',
				'oldestdate': '',
				'latestitem': '',
				'dur': '',
				'count': '',
				'entities': '',
				'countentities': '',
				'items': '',
				'addentity': '',
				'additem': '',
				'removeitem': '',
				'loadweb': '',
				'loadentities': '',
				'loaditems': '',
				'exporttable': '',
				'edititem': '',
				'db': '',
				'copydb': '',
				'bal': '',
				'histcost': '',
				'width': '',
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
			if args.command is not None: exit()
		elif command.lower() == 'exit' or args.command is not None:
			exit()
		# elif command == '':
		# 	pass
		else:
			# print('Not a valid command. Type "exit" to close or "help" for more info.')
			print('"{}" is not a valid command. Type "exit" to close or "help" for more options.'.format(command))
		if external:
			break

if __name__ == '__main__':
	main()