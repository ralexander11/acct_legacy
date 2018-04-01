import pandas as pd
import sqlite3

conn = sqlite3.connect('acct.db')

pd.set_option('display.width', 64)

class Accounts(object):
	def load_accts(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			self.df = pd.read_csv(f)
			print (self.df)
			print ('--------------------------------')
		self.df.to_sql('accounts', conn)

class Ledger(object):
	def __init__(self):
		try:
			self.df = pd.read_sql_query('SELECT * FROM personal_ledger;', conn)
		except:
			self.df = None

	def sanitize_ledger(self):
		# TODO remove Admin txns
		self.df.query('Debit_Acct or Credit_Acct != Admin')
		self.df.drop_duplicates()

	def load_data(self):
		infile = input('Enter a filename: ')
		ledger_name = input('Enter a name for the ledger: ')
		with open(infile, 'r') as f:
			self.df = pd.read_csv(f)
			print (self.df)
			print ('--------------------------------')
		#sanitize_ledger()
		self.df.to_sql(ledger_name, conn)

	def printGL(self):
		print (self.df)
		print ('--------------------------------')

	def exportGL(self):
		outfile = input('Enter a filename to save as: ')
		save_location = "/data/"
		# ledger_name = input('Enter a name for the ledger: ')
		# self.df = pd.read_sql_table(ledger_name, conn)
		self.df.to_csv(save_location + outfile)

		# credits = df.groupby('Credit').sum()

if __name__ == '__main__':
	ledger = Ledger()
	accts = Accounts()

	while True:
		command = input('Type one of the following commands:\nprintGL, exportGL, loadData, loadAccts, exit\n')
		if command.upper() == "EXIT":
			exit()
		elif command.upper() == "PRINTGL":
			ledger.printGL()
		elif command.upper() == "EXPORTGL":
			ledger.exportGL()
		elif command.upper() == "LOADDATA":
			ledger.load_data()
		elif command.upper() == "LOADACCTS":
			accts.load_accts()
		else:
			print('Not a valid command. Type exit to close.')
