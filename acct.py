import pandas as pd
import sqlite3
from time import strftime, localtime

conn = sqlite3.connect('acct.db')

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)

class Accounts(object):
	def __init__(self):
		try:
			self.refresh_accts()
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
		standard_accts = [
			['Account','None'],
			['Admin','Account'],
			['Asset','Account'],
			['Equity','Account'],
			['Liability','Equity'],
			['Wealth','Equity'],
			['Revenue','Wealth'],
			['Expense','Wealth'],
			['Transfer','Equity']]

		cur = conn.cursor()
		cur.execute(create_accts_query)
		for acct in standard_accts:
				account = str(acct[0])
				child_of = str(acct[1])
				print(acct)
				details = (account,child_of)
				cur.execute('INSERT INTO accounts VALUES (?,?)', details)
		conn.commit()
		cur.close()

	def print_accts(self):
		print (self.df)
		print ('-' * DISPLAY_WIDTH)

	def refresh_accts(self):
		self.df = pd.read_sql_query('SELECT * FROM accounts;', conn, index_col='accounts')

	def add_acct(self, acct_data = None):
		cur = conn.cursor()
		if acct_data is None:
			account = input('Enter the account name: ')
			child_of = input('Enter the parent account: ')
			
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

	def sanitize_accts(self):
		self.df.drop_duplicates() # TODO Implement this

	def load_accts(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			load_df = pd.read_csv(f)
			lol = load_df.values.tolist()
			print (load_df)
			print ('-' * DISPLAY_WIDTH)
			self.add_acct(lol)
			# TODO Add sanitize function to remove dupe accounts

	def export_accts(self):
		outfile = 'accounts' + strftime('_%Y-%m-%d_%H-%M-%S', localtime()) + '.csv'
		save_location = 'data/'
		self.df.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=False)
		print ('File saved as ' + save_location + outfile + '\n')

	def remove_acct(self):
		acct = input('Which account would you like to remove? ')
		cur = conn.cursor()
		cur.execute('DELETE FROM accounts WHERE accounts=?', (acct,))
		conn.commit()
		cur.close()
		self.refresh_accts()

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

	def reversal_entry(self):
		txn = input('Which txn_id to reverse? ')
		rvsl_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';'
		cur = conn.cursor()
		cur.execute(rvsl_query)
		rvsl = cur.fetchone()
		cur.close()
		rvsl_entry = [[ rvsl[1], rvsl[2], rvsl[3], '[RVSL]' + rvsl[4], rvsl[5], rvsl[6], rvsl[7], rvsl[9], rvsl[8], rvsl[10] ]]
		self.journal_entry(rvsl_entry)

	def get_acct_elem(self, acct):
		if acct in ['Asset','Liability','Wealth','Revenue','Expense']:
			return acct
		else:
			return self.get_acct_elem(accts.df.loc[acct, 'child_of'])
		
	def balance_sheet(self): # TODO Needs to be optimized
		debit_accts = pd.unique(self.df['debit_acct'])
		credit_accts = pd.unique(self.df['credit_acct'])
		accts = list( set(debit_accts) | set(credit_accts) )
		accounts = []
		for acct in accts:
			elem = self.get_acct_elem(acct)
			account = (acct, elem)
			accounts.append(account)
		assets = []
		liabilities = []
		wealth = []
		revenues = []
		expenses = []
		for acct in accounts:
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

		print ('Assets:')
		for acct in assets:
			debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			bal = round(debits - credits, 2)
			print (acct + ':	$' + str(bal))
		print ('-' * DISPLAY_WIDTH)

		print ('Liabilities:')
		for acct in liabilities:
			debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			bal = round(credits - debits, 2)
			print (acct + ':	$' + str(bal))
		print ('-' * DISPLAY_WIDTH)

		print ('Revenues:')
		for acct in revenues:
			debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			bal = round(credits - debits, 2)
			print (acct + ':	$' + str(bal))
		print ('-' * DISPLAY_WIDTH)

		print ('Expenses:')
		for acct in expenses:
			debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			bal = round(credits - debits, 2)
			print (acct + ':	$' + str(bal))
		print ('-' * DISPLAY_WIDTH)

		print ('Wealth:')
		for acct in wealth:
			debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			bal = round(credits - debits, 2)
			print (acct + ':	$' + str(bal))
		print ('-' * DISPLAY_WIDTH)
		

if __name__ == '__main__':
	ledger = Ledger('test_1')
	accts = Accounts()

	while True:
		command = input('\nType one of the following commands:\nBS, printGL, JE, RVSL, loadData, exportGL, printAccts, addAcct, exit\n')
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
		elif command.lower() == "removeacct":
			accts.remove_acct()
		elif command.lower() == "loadaccts":
			accts.load_accts()
		elif command.lower() == "exportaccts":
			accts.export_accts()
		elif command.lower() == "je":# or "journalentry":
			ledger.journal_entry()
		elif command.lower() == "sanitize":
			ledger.sanitize_ledger()
		elif command.lower() == "rvsl":# or "reversalentry":
			ledger.reversal_entry()
		elif command.lower() == "bs":# or "balancesheet":
			ledger.balance_sheet()
		else:
			print('Not a valid command. Type exit to close.')