import pandas as pd
import numpy as np
import sqlite3
import argparse
import datetime
import logging

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

class Accounts:
	def __init__(self, conn=None, standard_accts=None):
		if conn is None:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
				website = True
				logging.debug('Website: {}'.format(website))
			except:
				conn = sqlite3.connect('db/acct.db')
				website = False
				logging.debug('Website: {}'.format(website))
		elif isinstance(conn, str):
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/' + conn)
				website = True
				logging.debug('Website: {}'.format(website))
			except:
				conn = sqlite3.connect('db/' + conn)
				website = False
				logging.debug('Website: {}'.format(website))
		else:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
				website = True
				logging.debug('Website: {}'.format(website))
			except:
				conn = sqlite3.connect('db/acct.db')
				website = False
				logging.debug('Website: {}'.format(website))

		self.conn = conn

		try:
			self.refresh_accts()
		except:
			self.coa = None
			self.create_accts(standard_accts)
			# self.refresh_accts()
			self.create_entities()
			self.create_items()

	def create_accts(self, standard_accts=None):
		if standard_accts is None:
			standard_accts = []
		create_accts_query = '''
			CREATE TABLE IF NOT EXISTS accounts (
				accounts text,
				child_of text
			);
			'''
		base_accts = [
			('Account','None'),
			('Admin','Account'),
			('Asset','Account'),
			('Equity','Account'),
			('Liability','Equity'),
			('Wealth','Equity'),
			('Revenue','Wealth'),
			('Expense','Wealth'),
			('Transfer','Wealth')
		]

		personal = [
			('Cash','Asset'),
			('Chequing','Asset'),
			('Savings','Asset'),
			('Investments','Asset'),
			('Visa','Liability'),
			('Student Credit','Liability'),
			('Credit Line','Liability'),
			('Uncategorized','Admin'),
			('Info','Admin'),
			('Royal Credit Line','Liability')
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
			CREATE TABLE IF NOT EXISTS entities (
				entity_id INTEGER PRIMARY KEY,
				name text,
				comm real DEFAULT 0,
				min_qty INTEGER,
				max_qty INTEGER,
				liquidate_chance real,
				ticker_source text DEFAULT 'iex',
				hours INTEGER,
				needs text,
				need_max INTEGER DEFAULT 100,
				decay_rate INTEGER DEFAULT 1,
				need_threshold INTEGER DEFAULT 40,
				current_need INTEGER DEFAULT 50,
				auth_shares INTEGER,
				outputs text
			);
			''' # TODO Add needs table?
		default_entities = ['''
			INSERT INTO entities (
				name,
				comm,
				min_qty,
				max_qty,
				liquidate_chance,
				ticker_source,
				hours,
				needs,
				need_max,
				decay_rate,
				need_threshold,
				current_need,
				auth_shares,
				outputs
				)
				VALUES (
					'Person001',
					0.0,
					1,
					100,
					0.5,
					'iex',
					24,
					'Hunger',
					100,
					1,
					40,
					50,
					1000000,
					'Labour'
				);
			'''] # TODO Rename outputs to produces

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
			CREATE TABLE IF NOT EXISTS items (
				item_id text PRIMARY KEY,
				int_rate_fix real,
				int_rate_var real,
				freq integer DEFAULT 365,
				child_of text,
				requirements text,
				amount text,
				capacity integer,
				usage_req text,
				use_amount text,
				satisfies text,
				satisfy_rate text,
				productivity text,
				efficiency text,
				lifespan integer,
				metric text DEFAULT 'ticks',
				producer text
			);
			''' # Metric can have values of 'ticks' or 'units' or 'spoilage'
		default_item = ['''
			INSERT INTO items (
				item_id,
				int_rate_fix,
				int_rate_var,
				freq,
				child_of,
				requirements,
				amount,
				capacity,
				usage_req,
				use_amount,
				satisfies,
				satisfy_rate,
				productivity,
				efficiency,
				lifespan,
				metric,
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
					'Capital',
					1,
					NULL,
					NULL,
					3650,
					'ticks',
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
		cur = self.conn.cursor()
		if acct_data is None:
			account = input('Enter the account name: ')
			child_of = input('Enter the parent account: ')
			if child_of not in self.coa.index:
				print('\n' + child_of + ' is not a valid account.')
				return
			details = (account, child_of)
			cur.execute('INSERT INTO accounts VALUES (?,?)', details)
		else:
			for acct in acct_data: # TODO Turn this into a list comprehension
				account = str(acct[0])
				child_of = str(acct[1])
				if v: print(acct)
				details = (account,child_of)
				cur.execute('INSERT INTO accounts VALUES (?,?)', details)
		self.conn.commit()
		cur.close()
		self.refresh_accts()
		self.drop_dupe_accts()

	def add_entity(self, entity_data=None): # TODO Cleanup and make nicer
		cur = self.conn.cursor()
		if entity_data is None:
			name = input('Enter the entity name: ')
			comm = input('Enter the commission amount: ')
			min_qty = '' # TODO Remove parameters related to random algo
			max_qty = ''
			liquidate_chance = ''
			ticker_source = input('Enter the source for tickers: ')
			hours = input('Enter the number of hours in a work day: ')
			needs = input('Enter the needs of the entity as a list: ')
			need_max = input('Enter the maximum need value as a list: ')
			decay_rate = input('Enter the rates of decay per day for each need.') # TODO Add int validation
			need_threshold = input('Enter the threshold for the needs as a list: ')
			current_need = input('Enter the starting level for the needs as a list: ')
			auth_shares = input('Enter the number of shares authorized: ')
			outputs = input('Enter the output names as a list: ') # For corporations

			details = (name,comm,min_qty,max_qty,liquidate_chance,ticker_source,hours,needs,need_max,decay_rate,need_threshold,current_need,auth_shares,outputs)
			cur.execute('INSERT INTO entities VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', details)
			
		else:
			for entity in entity_data:
				entity = tuple(map(lambda x: np.nan if x == 'None' else x, entity))
				insert_sql = 'INSERT INTO entities VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
				cur.execute(insert_sql, entity)

		self.conn.commit()
		entity_id = cur.lastrowid
		cur.close()
		return entity_id

	def add_item(self, item_data=None): # TODO Cleanup and make nicer
		cur = self.conn.cursor()
		if item_data is None:
			item_id = input('Enter the item name: ')
			int_rate_fix = ''#input('Enter the fixed interest rate if there is one: ')
			int_rate_var = ''#input('Enter the variable interest rate or leave blank: ')
			freq = ''#int(input('Enter the frequency of interest payments: '))
			child_of = input('Enter the category the item belongs to: ')
			# if child_of not in self.coa.index: # TODO Ensure item always points to an existing item
			# 	print('\n' + child_of + ' is not a valid account.')
			# 	return
			requirements = input('Enter the requirments to produce the item as a list: ')
			amount = input('Enter a value for the amount of each requirement as a list: ')
			capacity = input('Enter the capacity amount if there is one: ')
			usage_req = input('Enter the requirements to use the item as a list: ')
			use_amount = input('Enter a value for the amount of each requirement to use the item as list: ')
			satisfies = input('Enter the needs the item satisfies as a list: ')
			satisfy_rate = input('Enter the rate the item satisfies the needs as a list: ')
			productivity = input('Enter the requirements the item makes more efficient as a list: ')
			efficiency = input('Enter the ratio that the requirement is reduced by as a list: ')
			metric = input('Enter either "ticks" or "units" for how the lifespan is measured: ')
			lifespan = input('Enter how long the item lasts: ')
			producer = input('Enter the producer of the item: ')

			details = (item_id,int_rate_fix,int_rate_var,freq,child_of,requirements,amount,capacity,usage_req,use_amount,satisfies,satisfy_rate,productivity,efficiency,lifespan,metric,producer)
			cur.execute('INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', details)
			
		else:
			for item in item_data:
				item = tuple(map(lambda x: np.nan if x == 'None' else x, item))
				insert_sql = 'INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
				cur.execute(insert_sql, item)

		self.conn.commit()
		cur.close()

	def load_csv(self, infile=None):
		if infile is None:
			infile = input('Enter a filename: ')
		try:
			with open(infile, 'r') as f:
				load_csv = pd.read_csv(f, keep_default_na=False)
			lol = load_csv.values.tolist()
		except Exception as e:
			print('Error: {}'.format(e))
		#print(load_csv)
		#print('-' * DISPLAY_WIDTH)
		return lol

	def load_accts(self, infile=None):
		self.add_acct(self.load_csv(infile), v=True)

	def load_entities(self, infile=None):
		if infile is None:
			infile = 'data/entities.csv'
		self.add_entity(self.load_csv(infile))
		self.entities = pd.read_sql_query('SELECT * FROM entities;', self.conn, index_col='entity_id')
		return self.entities

	def load_items(self, infile=None):
		if infile is None:
			infile = 'data/items.csv'
		self.add_item(self.load_csv(infile))
		self.items = pd.read_sql_query('SELECT * FROM items;', self.conn, index_col='item_id')
		return self.items

	def export_accts(self):
		outfile = 'accounts_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		try:
			self.coa.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
			print('File saved as ' + save_location + outfile + '\n')
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

	def get_entities(self):
		self.entities = pd.read_sql_query('SELECT * FROM entities;', self.conn, index_col=['entity_id'])
		return self.entities

	def get_items(self):
		self.items = pd.read_sql_query('SELECT * FROM items;', self.conn, index_col=['item_id'])
		return self.items

	def print_entities(self, save=True): # TODO Add error checking if no entities exist
		#self.entities = pd.read_sql_query('SELECT * FROM entities;', self.conn, index_col=['entity_id'])
		self.entities = get_entities()
		if save:
			self.entities.to_csv('data/entities.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.entities)
		print('-' * DISPLAY_WIDTH)
		return self.entities

	def print_items(self, save=True): # TODO Add error checking if no items exist
		#self.items = pd.read_sql_query('SELECT * FROM items;', self.conn, index_col=['item_id'])
		self.items = get_items()
		if save:
			self.items.to_csv('data/items.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.items)
		print('-' * DISPLAY_WIDTH)
		return self.items


class Ledger:
	def __init__(self, accts, ledger_name=None, entity=None, date=None, start_date=None, txn=None):
		self.conn = accts.conn
		self.coa = accts.coa
		if ledger_name is None:
			self.ledger_name = 'gen_ledger'
		else:
			self.ledger_name = ledger_name
		self.entity = entity
		self.date = date
		self.start_date = start_date
		self.txn = txn
		self.create_ledger()
		self.refresh_ledger() # TODO Maybe make this self.gl = self.refresh_ledger()
		self.balance_sheet()
			
	def create_ledger(self): # TODO Change entity_id to string type maybe
		create_ledger_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.ledger_name + ''' (
				txn_id INTEGER PRIMARY KEY,
				event_id integer NOT NULL,
				entity_id integer NOT NULL,
				date date NOT NULL,
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

	def set_entity(self, entity=None):
		if entity is None:
			self.entity = int(input('Enter an Entity ID: ')) # TODO Change entity_id to string type
		else:
			self.entity = entity
		self.refresh_ledger()
		self.balance_sheet()
		return self.entity

	def set_date(self, date=None):
		if date is None:
			self.date = input('Enter a date in format YYYY-MM-DD: ')
		else:
			self.date = date
		self.refresh_ledger()
		self.balance_sheet()
		return self.date

	def set_start_date(self, start_date=None):
		if start_date is None:
			self.start_date = input('Enter a date in format YYYY-MM-DD: ')
		else:
			self.start_date = start_date
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

	# TODO Add set_start_txn() function

	def reset(self):
		self.entity = None
		self.date = None
		self.start_date = None
		self.txn = None
		self.refresh_ledger()
		self.balance_sheet()

	def refresh_ledger(self):
		self.gl = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', self.conn, index_col='txn_id')
		if self.entity is not None: # TODO make able to select multiple entities
			self.gl = self.gl[(self.gl.entity_id == self.entity)]
		if self.date is not None:
			self.gl = self.gl[(self.gl.date <= self.date)]
		if self.start_date is not None:
			self.gl = self.gl[(self.gl.date >= self.start_date)]
		if self.txn is not None:
			self.gl = self.gl[(self.gl.index <= self.txn)] # TODO Add start txn and event range
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
		if acct in ['Asset','Liability','Wealth','Revenue','Expense','None']:
			return acct
		else:
			return self.get_acct_elem(self.coa.loc[acct, 'child_of'])

	def balance_sheet(self, accounts=None, item=None): # TODO Needs to be optimized
		all_accts = False
		#print(self.gl)
		if item is not None: # TODO Add support for multiple items maybe
			self.gl = self.gl[self.gl['item_id'] == item]

		if accounts is None: # Create a list of all the accounts
			all_accts = True
			debit_accts = pd.unique(self.gl['debit_acct'])
			credit_accts = pd.unique(self.gl['credit_acct'])
			accounts = list( set(debit_accts) | set(credit_accts) )
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
		wealth = []
		revenues = []
		expenses = []
		for acct in account_details:
			if acct[1] == 'Asset':
				assets.append(acct[0])
			elif acct[1] == 'Liability':
				liabilities.append(acct[0])
			elif acct[1] == 'Wealth':
				wealth.append(acct[0])
			elif acct[1] == 'Revenue':
				revenues.append(acct[0])
			elif acct[1] == 'Expense':
				expenses.append(acct[0])
			else:
				continue

		# Create Balance Sheet dataframe to return
		self.bs = pd.DataFrame(columns=['line_item','balance']) # TODO Make line_item the index

		# TODO The below repeated sections can probably be handled more elegantly

		asset_bal = 0
		for acct in assets:
			#print(self.gl)
			#print('Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
			except KeyError as e:
				#print('Asset Debit Error: {}'.format(e))
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
			except KeyError as e:
				#print('Asset Credit Error: {}'.format(e))
				credits = 0
			bal = debits - credits
			asset_bal += bal
			#print('Bal: {}'.format(bal))
			#if bal != 0: # TODO Not sure if should display empty accounts
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Assets:', 'balance':asset_bal}, ignore_index=True)

		liab_bal = 0
		for acct in liabilities:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Liabilities Debit Error')
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Liabilities Crebit Error')
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			liab_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Liabilities:', 'balance':liab_bal}, ignore_index=True)

		wealth_bal = 0
		for acct in wealth:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Wealth Debit Error')
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Wealth Crebit Error')
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			wealth_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Wealth:', 'balance':wealth_bal}, ignore_index=True)

		rev_bal = 0
		for acct in revenues:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Revenues Debit Error')
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Revenues Crebit Error')
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			rev_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Revenues:', 'balance':rev_bal}, ignore_index=True)

		exp_bal = 0
		for acct in expenses:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Expenses Debit Error')
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
			except KeyError as e:
				logging.debug('Expenses Crebit Error')
				credits = 0
			bal = debits - credits
			exp_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Expenses:', 'balance':exp_bal}, ignore_index=True)

		retained_earnings = rev_bal - exp_bal
		self.bs = self.bs.append({'line_item':'Net Income:', 'balance':retained_earnings}, ignore_index=True)

		net_asset_value = asset_bal - liab_bal
		if net_asset_value == 0: # Two ways to calc NAV depending on accounts
			net_asset_value = wealth_bal + retained_earnings

		total_equity = net_asset_value + liab_bal
		self.bs = self.bs.append({'line_item':'Wealth+NI+Liab.:', 'balance':total_equity}, ignore_index=True)

		check = asset_bal - total_equity
		self.bs = self.bs.append({'line_item':'Balance Check:', 'balance':check}, ignore_index=True)

		self.bs = self.bs.append({'line_item':'Net Asset Value:', 'balance':net_asset_value}, ignore_index=True)

		if all_accts:
			if self.entity is None:
				self.bs.to_sql('balance_sheet', self.conn, if_exists='replace')
			else:
				self.bs.to_sql('balance_sheet_' + str(self.entity), self.conn, if_exists='replace')
		return net_asset_value

	def print_bs(self):
		self.balance_sheet() # Refresh Balance Sheet
		print(self.bs)
		print('-' * DISPLAY_WIDTH)
		return self.bs

	def get_qty_txns(self, item=None, acct=None):
		rvsl_txns = self.gl[self.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of txns
		qty_txns = self.gl[(self.gl['item_id'] == item) & ((self.gl['debit_acct'] == acct) | (self.gl['credit_acct'] == acct)) & pd.notnull(self.gl['qty']) & (~self.gl['event_id'].isin(rvsl_txns))]
		#print('QTY TXNs:')
		#print(qty_txns)
		return qty_txns

	def get_qty(self, items=None, accounts=None, show_zeros=False, by_entity=False, v_qty=False):
		# if items == 'Food':
		# 	v_qty = True
		all_accts = False
		single_item = False
		no_item = False
		if (accounts is None) or (accounts == ''):
			if v_qty: print('No account given.')
			all_accts = True
			accounts = pd.unique(self.gl['debit_acct'])
			#credit_accts = pd.unique(self.gl['credit_acct']) # Not needed
			#accounts = list( set(accounts) | set(credit_accts) ) # Not needed
		if v_qty: print('Accounts: {}'.format(accounts))
		if isinstance(accounts, str):
			accounts = [x.strip() for x in accounts.split(',')]
		accounts = list(filter(None, accounts))
		if v_qty: print('Items Given: {}'.format(items))
		if (items is None) or (items == '') or (not items):
			items = None
			no_item = True
		if isinstance(items, str):
			items = [x.strip() for x in items.split(',')]
			items = list(filter(None, items))
			if v_qty: print('Select Items: {}'.format(items))
		if items is not None and len(items) == 1:
			single_item = True
			if v_qty: print('Single Item: {}'.format(single_item))
		inventory = pd.DataFrame(columns=['item_id','qty'])
		# TODO Finish option to show qtys by entity
		if by_entity:
			inventory = pd.DataFrame(columns=['entity_id','item_id','qty'])
		for acct in accounts:
			#if v_qty: print('GL: \n{}'.format(self.gl))
			if v_qty: print('Acct: {}'.format(acct))
			if no_item: # Get qty for all items
				if v_qty: print('No item given.')
				items = pd.unique(self.gl[self.gl['debit_acct'] == acct]['item_id'].dropna()).tolist() # Assuming you can't have a negative inventory
				#credit_items = pd.unique(self.gl[self.gl['credit_acct'] == acct]['item_id'].dropna()).tolist() # Causes issues
				#items = list( set(items) | set(credit_items) ) # Causes issues
				items = list(filter(None, items))
				if v_qty: print('All Items: {}'.format(items))
			for item in items:
				if v_qty: print('Item: {}'.format(item))
				if by_entity:
					entities = pd.unique(self.gl[self.gl['item_id'] == item]['entity_id'])
					if v_qty: print('Entities: \n{}'.format(entities))
					for entity_id in entities:
						if v_qty: print('Entity ID: \n{}'.format(entity_id))
						self.set_entity(entity_id)
						qty_txns = self.get_qty_txns(item, acct)
						if v_qty: print('QTY TXNs: \n{}'.format(qty_txns))
						try:
							debits = qty_txns.groupby(['debit_acct']).sum()['qty'][acct]
							#print('Debits: \n{}'.format(debits))
						except KeyError as e:
							#print('Error Debits: {} | {}'.format(e, repr(e)))
							debits = 0
						try:
							credits = qty_txns.groupby(['credit_acct']).sum()['qty'][acct]
							#print('Credits: \n{}'.format(credits))
						except KeyError as e:
							#print('Error Credits: {} | {}'.format(e, repr(e)))
							credits = 0
						qty = round(debits - credits, 0)
						if v_qty: print('QTY: {}'.format(qty))
						inventory = inventory.append({'entity_id':entity_id, 'item_id':item, 'qty':qty}, ignore_index=True)
						#if v_qty: print(inventory)
						self.reset()
				else:
					qty_txns = self.get_qty_txns(item, acct)
					if v_qty: print('QTY TXNs: \n{}'.format(qty_txns))
					try:
						debits = qty_txns.groupby(['debit_acct']).sum()['qty'][acct]
						#print('Debits: \n{}'.format(debits))
					except KeyError as e:
						#print('Error Debits: {} | {}'.format(e, repr(e)))
						debits = 0
					try:
						credits = qty_txns.groupby(['credit_acct']).sum()['qty'][acct]
						#print('Credits: \n{}'.format(credits))
					except KeyError as e:
						#print('Error Credits: {} | {}'.format(e, repr(e)))
						credits = 0
					qty = round(debits - credits, 0)
					if v_qty: print('QTY: {}'.format(qty))
					if single_item: # TODO Fix to handle multiple accounts
						return qty # TODO Ensure is int
					inventory = inventory.append({'item_id':item, 'qty':qty}, ignore_index=True)
					#if v_qty: print(inventory)
		if not show_zeros:
			inventory = inventory[(inventory.qty != 0)] # Ignores items completely sold
		if all_accts:
			if self.entity is None:
				inventory.to_sql('inventory', self.conn, if_exists='replace')
			else:
				inventory.to_sql('inventory_' + str(self.entity), self.conn, if_exists='replace')
		return inventory

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
			entity = 1
		else:
			entity = self.entity
		return entity

	def journal_entry(self, journal_data=None):
		'''
			The heart of the whole system; this is how transactions are entered.
			journal_data is a list of transactions. Each transaction is a list
			of datapoints. This means an event with a single transaction
			would be encapsulated in as a single list within a list.
		'''
		if journal_data is not None and not isinstance(journal_data[0], (list, tuple)):
			journal_data = [journal_data]
		cur = self.conn.cursor()
		if journal_data is None: # Manually enter a journal entry
			event = input('Enter an optional event_id: ')
			entity = input('Enter the entity_id: ')
			date_raw = input('Enter a date as format yyyy-mm-dd: ')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
			desc = input('Enter a description: ') + ' [M]'
			item = input('Enter an optional item_id: ')
			price = input('Enter an optional price: ')
			qty = input('Enter an optional quantity: ')
			debit = input('Enter the account to debit: ')
			if debit not in self.coa.index:
				print('\n' + debit + ' is not a valid account.')
				return # TODO Make accounts foreign key constraint
			credit = input('Enter the account to credit: ')
			if credit not in self.coa.index:
				print('\n' + credit + ' is not a valid account.')
				return
			while True:
				amount = input('Enter the amount: ')
				try: # TODO Maybe change to regular expression to prevent negatives
					x = float(amount)
					break
				except ValueError:
					continue
			
			if event == '':
				event = str(self.get_event())
			if entity == '':
				entity = str(self.get_entity())
			if date == 'NaT':
				date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
				date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())

			if qty == '': # TODO No qty and price default needed now
				qty = np.nan
			if price == '':
				price = np.nan

			values = (event, entity, date, desc, item, price, qty, debit, credit, amount)
			print(values)
			cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

		else: # Create journal entries by passing data to the function
			for je in journal_data:
				event = str(je[0])
				entity = str(je[1])
				date = str(je[2])
				desc = str(je[3])
				item  = str(je[4])
				price = str(je[5])
				qty = str(je[6])
				debit = str(je[7])
				credit = str(je[8])
				amount = str(je[9])

				if event == '' or np.isnan:
					event = str(self.get_event())
				if entity == '' or np.isnan:
					entity = str(self.get_entity())
				if date == 'NaT':
					date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
					date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())

				if qty == '': # TODO No qty and price default needed now
					qty = np.nan
				if price == '':
					price = np.nan

				values = (event, entity, date, desc, item, price, qty, debit, credit, amount)
				print(values)
				cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

		self.conn.commit()
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

	def load_gl(self, infile=None, flag=None):
		if infile is None:
			infile = input('Enter a filename: ')
			#infile = 'data/rbc_sample_2019-01-27.csv' # For testing
			#infile = 'data/legacy_ledger_2019-01-25.csv' # For testing
		if flag is None:
			flag = input('Enter a flag: ')
			#flag = 'rbc' # For testing
			#flag = 'legacy' # For testing
		try:
			with open(infile, 'r') as f:
				if flag == 'legacy':
					load_gl = pd.read_csv(f, header=1, keep_default_na=False)
				else:
					load_gl = pd.read_csv(f, keep_default_na=False)
		except Exception as e:
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
			rbc_txn['date'] = load_gl['Transaction Date']
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
			leg_txn['date'] = load_gl['Transaction Date']
			leg_txn['desc'] = load_gl['Description 1'] + ' | ' + load_gl['Description 2']
			leg_txn['item_id'] = ''
			leg_txn['price'] = ''
			leg_txn['qty'] = ''
			leg_txn['debit_acct'] = np.where(load_gl['Amount'] > 0, load_gl['Account Type'], load_gl['Category 3'])
			leg_txn['credit_acct'] = np.where(load_gl['Amount'] < 0, load_gl['Account Type'], load_gl['Category 3'])
			leg_txn['amount'] = abs(load_gl['Amount'])
			lol = leg_txn.values.tolist()
			self.journal_entry(lol)
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

	def reversal_entry(self, txn=None, date=None): # This func effectively deletes a transaction
		if txn is None:
			txn = input('Which txn_id to reverse? ')
		rvsl_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(rvsl_query)
		rvsl = cur.fetchone()
		logging.debug('rvsl: {}'.format(rvsl))
		cur.close()
		if '[RVSL]' in rvsl[4]:
			print('Cannot reverse a reversal. Enter a new entry instead.')
			return
		if date is None: # rvsl[7] or np.nan
			date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
		rvsl_entry = [[ rvsl[1], rvsl[2], date, '[RVSL]' + rvsl[4], rvsl[5], rvsl[6], rvsl[7] or '', rvsl[9], rvsl[8], rvsl[10] ]]
		self.journal_entry(rvsl_entry)

	def hist_cost(self, qty, item=None, acct=None, remain_txn=False):
		v = False
		if acct is None:
			acct = 'Investments' #input('Which account? ') # TODO Remove this maybe

		qty_txns = self.get_qty_txns(item, acct)
		m1 = qty_txns.credit_acct == acct
		m2 = qty_txns.credit_acct != acct
		qty_txns = np.select([m1, m2], [-qty_txns['qty'], qty_txns['qty']])

		if v: print('QTY TXNs:')
		if v: print(qty_txns)

		# Find the first lot of unsold items
		count = 0
		qty_back = self.get_qty(item, [acct]) # TODO Confirm this work when there are multiple different lots of buys and sells in the past
		if v: print('Init QTY Back: {}'.format(qty_back))

		qty_change = []
		qty_change.append(qty_back)
		for txn in qty_txns[::-1]:
			if v: print('Item: {}'.format(txn))
			count -= 1
			if v: print('Count: {}'.format(count))
			qty_back -= txn
			qty_change.append(qty_back)
			if v: print('QTY Back: {}'.format(qty_back))
			if qty_back <= 0:
				break

		if v: print('QTY Change List:')
		if v: print(qty_change)
		if v: print('QTY Back End: {}'.format(qty_back))
		start_qty = qty_txns[count]
		if v: print('Start QTY: {}'.format(start_qty))

		qty_txns_gl = self.get_qty_txns(item, acct)
		mask = qty_txns_gl.credit_acct == acct
		qty_txns_gl.loc[mask, 'qty'] = qty_txns_gl['qty'] * -1
		#qty_txns_gl = qty_txns_gl.loc[mask, 'qty']
		#qty_txns_gl = qty_txns_gl['qty'] * -1

		if v: print('QTY TXNs GL:')
		if v: print(qty_txns_gl)
		start_index = qty_txns_gl.index[count]
		if v: print('Start Index: {}'.format(start_index))
		if len(qty_change) >= 3:
			avail_qty = start_qty - qty_change[-3]# Portion of first lot of unsold items that has not been sold
		else:
			avail_qty = start_qty

		if v: print('Avail qty: {}'.format(avail_qty))
		if remain_txn:
			avail_txns = qty_txns_gl.loc[start_index:]
			return avail_txns
		amount = 0
		if qty <= avail_qty: # Case when first available lot covers the need
			if v: print('QTY: {}'.format(qty))
			price_chart = pd.DataFrame({'price':[self.gl.loc[start_index]['price']],'qty':[qty]})
			if v: print(price_chart)
			amount = price_chart.price.dot(price_chart.qty)
			print('Hist Cost Case: One')
			print(amount)
			return amount

		price_chart = pd.DataFrame({'price':[self.gl.loc[start_index]['price']],'qty':[avail_qty]}) # Create a list of lots with associated price
		qty = qty - avail_qty # Sell the remainder of first lot of unsold items
		if v: print(price_chart)
		if v: print('qty First: {}'.format(qty))
		count += 1
		if v: print('Count First: {}'.format(count))
		#for txn in qty_txns[count::-1]: # TODO Remove this loop
		current_index = qty_txns_gl.index[count]
		if v: print('Current Index First: {}'.format(current_index))
		while qty > 0: # Running amount of qty to be sold
			if v: print('QTY Check: {}'.format(qty_txns_gl.loc[current_index]['qty']))
			while qty_txns_gl.loc[current_index]['qty'] < 0:
				count += 1
				if v: print('Count Check: {}'.format(count))
				current_index = qty_txns_gl.index[count]
			current_index = qty_txns_gl.index[count]
			if v: print('Current Index: {}'.format(current_index))
			if v: print('QTY Left to be Sold: {}'.format(qty))
			if v: print('Current TXN QTY: {}'.format(qty_txns_gl.loc[current_index]['qty']))
			if qty < self.gl.loc[current_index]['qty']: # Final case when the last sellable lot is larger than remaining qty to be sold
				price_chart = price_chart.append({'price':self.gl.loc[current_index]['price'], 'qty':qty}, ignore_index=True)
				if v: print(price_chart)
				amount = price_chart.price.dot(price_chart.qty) # Take dot product
				print('Hist Cost Case: Two')
				print(amount)
				return amount
			
			price_chart = price_chart.append({'price':self.gl.loc[current_index]['price'], 'qty':self.gl.loc[current_index]['qty']}, ignore_index=True)
			if v: print(price_chart)
			qty = qty - self.gl.loc[current_index]['qty']
			count += 1

		amount = price_chart.price.dot(price_chart.qty) # If remaining lot perfectly covers remaining amount to be sold
		print('Hist Cost Case: Three')
		print(amount)
		return amount

	def bs_hist(self): # TODO Optimize this so it does not recalculate each time
		gl_entities = pd.unique(self.gl['entity_id'])
		logging.info(gl_entities)
		dates = pd.unique(self.gl['date'])
		logging.info(dates)

		cur = self.conn.cursor()
		create_bs_hist_query = '''
			CREATE TABLE IF NOT EXISTS hist_bs (
				date date NOT NULL,
				entity text NOT NULL,
				assets real NOT NULL,
				liabilities real NOT NULL,
				wealth real NOT NULL,
				revenues real NOT NULL,
				expenses real NOT NULL,
				net_income real NOT NULL,
				wealth_ni_liab real NOT NULL,
				bal_check real NOT NULL,
				net_asset_value real NOT NULL
			);
			'''
		cur.execute(create_bs_hist_query)
		cur.execute('DELETE FROM hist_bs')
		for entity in gl_entities:
			logging.info(entity)
			self.set_entity(entity)
			for date in dates:
				logging.info(entity)
				self.set_date(date)
				logging.info(date)
				self.balance_sheet()
				self.bs.set_index('line_item', inplace=True)
				col0 = str(entity)
				col1 = self.bs.loc['Total Assets:'][0]
				col2 = self.bs.loc['Total Liabilities:'][0]
				col3 = self.bs.loc['Total Wealth:'][0]
				col4 = self.bs.loc['Total Revenues:'][0]
				col5 = self.bs.loc['Total Expenses:'][0]
				col6 = self.bs.loc['Net Income:'][0]
				col7 = self.bs.loc['Wealth+NI+Liab.:'][0]
				col8 = self.bs.loc['Balance Check:'][0]
				col9 = self.bs.loc['Net Asset Value:'][0]
				
				data = (date,col0,col1,col2,col3,col4,col5,col6,col7,col8,col9)
				logging.info(data)
				cur.execute('INSERT INTO hist_bs VALUES (?,?,?,?,?,?,?,?,?,?,?)', data)
		self.conn.commit()
		cur.execute('PRAGMA database_list')
		db_path = cur.fetchall()[0][-1]
		db_name = db_path.rsplit('/', 1)[-1]
		cur.close()

		self.hist_bs = pd.read_sql_query('SELECT * FROM hist_bs;', self.conn, index_col=['date','entity'])
		return self.hist_bs, db_name

		# TODO Add function to book just the current days bs to hist_bs

	def print_hist(self):
		db_name = self.bs_hist()[1]
		path = 'data/bs_hist_' + db_name[:-3] + '.csv'
		self.hist_bs.to_csv(path, index=True)
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

	def fix_price(self): # Temp price fix function
		cur = self.conn.cursor()
		price = np.nan
		#print('QTY: {}'.format(qty))
		value = (price,)
		#print('Value: {}'.format(value))
		cur.execute('UPDATE ' + self.ledger_name + ' SET price = (?) WHERE price = amount', value)
		self.conn.commit()
		cur.close()
		print('Prices converted.')

def main(command=None, external=False):
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-c', '--command', type=str, help='A command for the program.')
	args = parser.parse_args()

	accts = Accounts(conn=args.database)
	ledger = Ledger(accts, ledger_name=args.ledger, entity=args.entity)
	if command is None:
		command = args.command

	while True: # TODO Make this a function that has the command passed in as an argument
		if args.command is None and not external:
			command = input('\nType one of the following commands:\nBS, GL, JE, RVSL, loadGL, Accts, addAcct, loadAccts, exit\n')
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
		elif command.lower() == 'accts':
			accts.print_accts()
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
		elif command.lower() == 'bs':
			ledger.print_bs()
			if args.command is not None: exit()
		elif command.lower() == 'qty':
			item = input('Which ticker? ')#.lower()
			acct = input('Which account? ')#.title()
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(ledger.get_qty(item, acct))
			if args.command is not None: exit()
		elif command.lower() == 'entity':
			ledger.set_entity()
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
		elif command.lower() == 'reset':
			ledger.reset()
			if args.command is not None: exit()
		elif command.lower() == 'hist':
			ledger.print_hist()
			if args.command is not None: exit()
		elif command.lower() == 'entities':
			accts.print_entities()
			if args.command is not None: exit()
		elif command.lower() == 'items':
			accts.print_items()
		elif command.lower() == 'addentity':
			accts.add_entity()
			if args.command is not None: exit()
		elif command.lower() == 'additem':
			accts.add_item()
		elif command.lower() == 'loadentities':
			accts.load_entities()
			if args.command is not None: exit()
		elif command.lower() == 'loaditems':
			accts.load_items()
			if args.command is not None: exit()
		elif command.lower() == 'width': # TODO Try and make this work
			DISPLAY_WIDTH = int(input('Enter number for display width: '))
			if args.command is not None: exit()
		elif command.lower() == 'fixqty': # Temp qty fix function
			ledger.fix_qty()
			if args.command is not None: exit()
		elif command.lower() == 'fixprice': # Temp price fix function
			ledger.fix_price()
			if args.command is not None: exit()
		elif command.lower() == 'exit' or args.command is not None:
			exit()
		else:
			print('Not a valid command. Type exit to close.')
		if external:
			break

if __name__ == '__main__':
	main()