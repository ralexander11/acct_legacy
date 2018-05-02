import pandas as pd
import sqlite3

conn = sqlite3.connect('acct.db')

DISPLAY_WIDTH = 98
pd.set_option('display.width',DISPLAY_WIDTH)

def test_je(): # Test
	data = [2,1,'2018-05-02','Test JE 3','Visa','Food',10]
	ledger.journal_entry(data)

class Accounts(object): # TODO Cleanup
	# TODO On load create empty table if it does not exist. Like ledger
	def __init__(self):
		try:
			self.df = pd.read_sql_query('SELECT * FROM accounts;', conn)
		except:
			self.df = None

	def printAccts(self):
		print (self.df)
		print ('-' * DISPLAY_WIDTH+'\n')

	def load_accts(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			self.df = pd.read_csv(f)
		self.df.to_sql('accounts', conn)
		self.printAccts()

class Ledger(object):
	ledger_name = input('Enter a name for the ledger: ')
	#ledger_name = 'test_1'	#debug
	def __init__(self):
		self.create_table()
		self.refresh_data()
			
	def create_table(self):
		create_table_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.ledger_name + ''' (
				txn_id INTEGER PRIMARY KEY,
				event_id integer NOT NULL,
				entity_id integer NOT NULL,
				transaction_date date NOT NULL,
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
		print ('-' * DISPLAY_WIDTH+'\n')
		for column in self.df:
			print (self.df[column].dtype)
		print()

	def refresh_data(self):
		self.df = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', conn, index_col='txn_id')

	def journal_entry(self, journal_data = None):
		if journal_data is None:
			# TODO Validation
			event = str(1) # TODO if blank make copy of rowid value
			entity = input('Enter the Entity_ID: ')
			date = str(pd.to_datetime(input('Enter a date as format yyyy-mm-dd: '), format='%Y-%m-%d').date())
			desc = input('Enter a description: ')
			debit = input('Enter the account to debit: ')
			credit = input('Enter the account to credit: ')
			amount = input('Enter the amount: ')
			
			#event = str(1) # TODO if blank make copy of rowid value
			#entity = str(1) # input('Enter the Entity_ID: ')
			#date = str(pd.to_datetime('2018-04-08', format='%Y-%m-%d')) # pd.to_datetime(input('Enter a date as format yyyy-mm-dd: '), format='%Y-%m-%d')
			#desc = 'Test JE 1' # input('Enter a description: ')
			#debit = 'Savings Expense' # input('Enter the account to debit: ')
			#credit = 'Chequeing' # input('Enter the account to credit: ')
			#amount = str(100.00) # input('Enter the amount: ')
		else:
			event = str(journal_data[0])
			entity = str(journal_data[1])
			date = str(journal_data[2])
			desc = str(journal_data[3])
			debit = str(journal_data[4])
			credit = str(journal_data[5])
			amount = str(journal_data[6])

		print(event+entity+date+desc+debit+credit+amount+'\n')
		values = (event,entity,date,desc,debit,credit,amount)
			
		cur = conn.cursor()
		cur.execute('INSERT INTO '+self.ledger_name+' VALUES (NULL,?,?,?,?,?,?,?)', values)
		conn.commit()
		cur.close()
		self.refresh_data()

	def sanitize_ledger(self):
		self.df.query('Debit_Acct or Credit_Acct != Admin') # Fix this
		self.df.drop_duplicates() # Test this

	def load_data(self): # TODO Finish this
		infile = input('Enter a filename: ')
		ledger_name = input('Enter a name for the ledger: ')
		with open(infile, 'r') as f:
			self.df = pd.read_csv(f)
			self.df.set_index('txn_id', inplace=True)
			#self.sanitize_ledger()
			#self.df.to_sql(ledger_name, conn, if_exists="replace")

		self.printGL()

	def exportGL(self):
		outfile = input('Enter a filename to save as: ')
		save_location = "/data/"
		self.df.to_csv(save_location + outfile)

	# TODO credits = df.groupby('Credit').sum()

if __name__ == '__main__':
	ledger = Ledger()
	accts = Accounts()

	while True:
		command = input('Type one of the following commands:\nprintGL, JE, loadData, printAccts, loadAccts, exit\n')
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
		elif command.upper() == "TESTJE": #debug
			test_je()
		else:
			print('Not a valid command. Type exit to close.')
