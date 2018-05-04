import pandas as pd
import sqlite3
from time import strftime, localtime

conn = sqlite3.connect('acct.db')

DISPLAY_WIDTH = 98
pd.set_option('display.width',DISPLAY_WIDTH)

class Accounts(object):
	def __init__(self):
		try:
			self.df = pd.read_sql_query('SELECT * FROM accounts;', conn)
		except:
			self.df = None

	def printAccts(self):
		print (self.df)
		print ('-' * DISPLAY_WIDTH)

	def load_accts(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			self.df = pd.read_csv(f)
		self.df.to_sql('accounts', conn)
		self.printAccts()
	
class Ledger(object):
	def __init__(self, ledger_name=None):
		if ledger_name == None:
			self.ledger_name = input('Enter a name for the ledger: ')
		else:
			self.ledger_name = ledger_name
		self.create_table()
		self.refresh_data()
			
	def create_table(self):
		create_table_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.ledger_name + ''' (
				txn_id INTEGER PRIMARY KEY,
				event_id integer NOT NULL,
				entity_id integer NOT NULL,
				date date NOT NULL,
				description text,
				debit_acct text NOT NULL,
				credit_acct text NOT NULL,
				amount real NOT NULL
			);
			'''

		cur = conn.cursor()
		cur.execute(create_table_query)
		conn.commit()
		cur.close()

	def printGL(self):
		print (self.df)
		print ('-' * DISPLAY_WIDTH)

	def refresh_data(self):
		self.df = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', conn, index_col='txn_id')

	def journal_entry(self, journal_data = None):
		cur = conn.cursor()
		if journal_data is None:
			# TODO Validation
			event = input('Enter the Event_ID or press enter if unknown: ')
			#if event == "":
			#	event = last_insert_rowid(conn) + 1 # TODO fix this
			#	print(event) #debug
			entity = input('Enter the Entity_ID: ')
			#while True:
			#	try: # TODO make into while loop
			date_raw = input('Enter a date as format yyyy-mm-dd: ')
			#		if len(date) < 10:
			#			continue
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
			#		break
			#	except:
			#		print('Try again with proper format yyyy-mm-dd: ')
			#		continue
			desc = input('Enter a description: ')
			debit = input('Enter the account to debit: ')
			#while debit not in accts.df['accounts']:
			#	debit = input(debit + ' does not exist. Enter the account to debit: ') # TODO make into while loop
			credit = input('Enter the account to credit: ')
			amount = input('Enter the amount: ')
			
			values = (event,entity,date,desc,debit,credit,amount)
			cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?)', values)
			
		else:
			for je in journal_data:
				event = str(je[0])
				entity = str(je[1])
				date = str(je[2])
				desc = str(je[3])
				debit = str(je[4])
				credit = str(je[5])
				amount = str(je[6])
				print(je)

				values = (event,entity,date,desc,debit,credit,amount)
				cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?)', values)

		conn.commit()
		cur.close()
		self.refresh_data()

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

	def exportGL(self):
		outfile = self.ledger_name + strftime('_%Y-%m-%d', localtime()) + '.csv'
		save_location = 'data/'
		self.df.to_csv(save_location + outfile)
		print('File saved as ' + save_location + outfile + '\n')

	#credits = df.groupby('Credit').sum() # TODO Use this for the B/S and I/S
		
if __name__ == '__main__':
	ledger = Ledger('test_1')
	accts = Accounts()

	while True:
		command = input('Type one of the following commands:\nprintGL, JE, loadData, exportGL, printAccts, loadAccts, exit\n')
		if command.upper() == "EXIT":
			exit()
		elif command.upper() == "PRINTGL":
			ledger.printGL()
		elif command.upper() == "EXPORTGL":
			ledger.exportGL()
		elif command.upper() == "LOADDATA":
			ledger.load_data()
		elif command.upper() == "PRINTACCTS":
			accts.printAccts()
		elif command.upper() == "LOADACCTS":
			accts.load_accts()
		elif command.upper() == "JE":
			ledger.journal_entry()
		elif command.upper() == "SANITIZE":
			ledger.sanitize_ledger()
		else:
			print('Not a valid command. Type exit to close.')