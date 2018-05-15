import pandas as pd
import sqlite3
from time import strftime, localtime

conn = sqlite3.connect('acct.db')

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)

class Accounts(object):
	def __init__(self):
		try:
			self.df = pd.read_sql_query('SELECT * FROM accounts;', conn)
		except:
			self.df = None
		self.create_accts()
		self.refresh_accts()

	def create_accts(self):
		create_accts_query = '''
			CREATE TABLE IF NOT EXISTS accounts (
				accounts text,
				child_of text
			);
			'''
		# TODO Add creation of default standard accounts

		cur = conn.cursor()
		cur.execute(create_accts_query)
		conn.commit()
		cur.close()

	def print_accts(self):
		print (self.df)
		print ('-' * DISPLAY_WIDTH)

	def refresh_accts(self):
		self.df = pd.read_sql_query('SELECT * FROM accounts;', conn)

	def add_acct(self, acct_data = None):
		cur = conn.cursor()
		if acct_data is None:
			account = input('Enter the account name: ')
			child_of = input('Enter the parent account : ')
			
			details = (account,child_of)
			cur.execute('INSERT INTO accounts VALUES (?,?)', details)
			
		else:
			for acct in acct_data:
				account = str(acct[0])
				child_of = str(acct[1])
				print(acct)

				details = (account,child_of)
				cur.execute('INSERT INTO accounts VALUES (?,?)', details)

		conn.commit()
		cur.close()
		self.refresh_accts()

	def sanitize_accts():
		pass

	def load_accts(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			load_df = pd.read_csv(f)
			lol = load_df.values.tolist()
		#self.df.to_sql('accounts', conn, index=False)
		self.print_accts()
		print ('-' * DISPLAY_WIDTH)
		self.add_acct(lol)
		# TODO Add sanitize function to remove dupe accounts

	def export_accts(self):
		outfile = 'accounts' + strftime('_%Y-%m-%d_%H-%M-%S', localtime()) + '.csv'
		save_location = 'data/'
		self.df.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=False)
		print ('File saved as ' + save_location + outfile + '\n')

class Ledger(object):
	def __init__(self, ledger_name=None):
		if ledger_name == None:
			self.ledger_name = input('Enter a name for the ledger: ')
		else:
			self.ledger_name = ledger_name
		self.create_ledger()
		self.refresh_ledger()
			
	def create_ledger(self):
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

		cur = conn.cursor()
		cur.execute(create_ledger_query)
		conn.commit()
		cur.close()

	def print_gl(self):
		print (self.df)
		print ('-' * DISPLAY_WIDTH)
		#print (self.df.dtypes)

	def refresh_ledger(self):
		self.df = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', conn, index_col='txn_id')

	def get_event(self):
		event_query = 'SELECT event_id FROM '+ self.ledger_name +' ORDER BY event_id DESC LIMIT 1;'
		cur = conn.cursor()
		cur.execute(event_query)
		event_id = cur.fetchone()
		cur.close()
		if event_id == None:
			event_id = 1
			return event_id
		else:
			return event_id[0] + 1

	def get_entity(self):
		entity = 1
		return entity

	def journal_entry(self, journal_data = None):
		cur = conn.cursor()
		if journal_data is None:
			event = input('Enter the event_id or press enter if unknown: ')
			entity = input('Enter the entity_id: ')
			date_raw = input('Enter a date as format yyyy-mm-dd: ')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
			desc = input('Enter a description: ')
			item = input('Enter an optional item_id: ')
			price = input('Enter an optional price: ')
			qty = input('Enter an optional quantity: ')
			debit = input('Enter the account to debit: ')
			credit = input('Enter the account to credit: ')
			amount = input('Enter the amount: ')
			
			values = (event,entity,date,desc,item,price,qty,debit,credit,amount)
			cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)
			
		else:
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
				print(je)

				values = (event,entity,date,desc,item,price,qty,debit,credit,amount)
				cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

		conn.commit()
		cur.close()
		self.refresh_ledger()

	def sanitize_ledger(self):
		self.df.query('Debit_Acct or Credit_Acct != Admin') # TODO Fix this
		self.df.drop_duplicates() # TODO Test this
		
	def load_data(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			load_df = pd.read_csv(f)
			load_df.set_index('txn_id', inplace=True)
			lol = load_df.values.tolist()
			print(load_df)
			print ('-' * DISPLAY_WIDTH)
			self.journal_entry(lol)
			#self.sanitize_ledger()

	def export_gl(self):
		outfile = self.ledger_name + strftime('_%Y-%m-%d_%H-%M-%S', localtime()) + '.csv'
		save_location = 'data/'
		self.df.to_csv(save_location + outfile, date_format='%Y-%m-%d')
		print ('File saved as ' + save_location + outfile + '\n')

	#credits = df.groupby('Credit').sum() # TODO Use this for the B/S and I/S
		
if __name__ == '__main__':
	ledger = Ledger('test_1')
	accts = Accounts()

	while True:
		command = input('Type one of the following commands:\nprintGL, JE, loadData, exportGL, printAccts, loadAccts, exit\n')
		if command.lower() == "exit":
			exit()
		elif command.lower() == "printgl":
			ledger.print_gl()
		elif command.lower() == "exportgl":
			ledger.export_gl()
		elif command.lower() == "loaddata":
			ledger.load_data()
		elif command.lower() == "printaccts":
			accts.print_accts()
		elif command.lower() == "addacct":
			accts.add_acct()
		elif command.lower() == "loadaccts":
			accts.load_accts()
		elif command.lower() == "exportaccts":
			accts.export_accts()
		elif command.lower() == "je":
			ledger.journal_entry()
		elif command.lower() == "sanitize":
			ledger.sanitize_ledger()
		else:
			print('Not a valid command. Type exit to close.')