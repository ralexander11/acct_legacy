from acct import Accounts
from acct import Ledger
import urllib.request
import pandas as pd
from time import strftime, localtime

class Trading(Ledger):
	def __init__(self, ledger, comm=0.0):
		self.df = ledger.df
		self.ledger_name = ledger.ledger_name
		self.entity = ledger.entity
		self.date = ledger.date
		self.txn = ledger.txn

		self.comm = comm
		if self.entity is not None:
			cur = ledger.conn.cursor()
			self.comm = cur.execute('SELECT comm FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]

	def get_price(self, symbol):
		url = 'https://api.iextrading.com/1.0/stock/'
		try:
			price = float(urllib.request.urlopen(url + symbol + '/price').read())
		except:
			print ('Error getting price from: ' + url + symbol + '/price')
			return 0
		else:
			return price

	def trade_date(self):
		return strftime('%Y-%m-%d', localtime())

	def com(self): # If I want to add more logic to commissions calculation
		com = self.comm #9.95
		return com

	def buy_shares(self, symbol, qty=None):
		if qty == None:
			qty = int(input('How many shares? '))
		price = self.get_price(symbol)

		# Check if there is enough capital
		capital_accts = ['Cash','Chequing']
		capital_bal = 0
		capital_bal = self.balance_sheet(capital_accts)

		if price * qty > capital_bal or price == 0:
			print ('\nBuying ' + str(qty) + ' shares of ' + symbol + ' costs $' + str(round(price * qty, 2)) + '.')
			print ('You currently have $' + str(round(capital_bal, 2)) + ' available.\n')
			return capital_bal

		# TODO Decide whether to display unrealized gains as temp entries with rvsls or not
		# Journal entries for a buy transaction
		buy_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Shares buy', symbol, price, qty, 'Investments', 'Cash', price * qty]
		if self.com() != 0:
			com_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Comm. buy', '', '', '', 'Commission Expense', 'Cash', self.com()]
		if self.com() != 0:
			buy_event = [buy_entry, com_entry]
		else:
			buy_event = [buy_entry]

		self.journal_entry(buy_event)
		return capital_bal

	def sell_shares(self, symbol, qty=None):
		if qty is None:
			qty = int(input('How many shares? '))
		current_qty = self.get_qty(symbol, 'Investments')
		if qty > current_qty:
			print ('You currently have ' + str(round(current_qty, 2)) + ' shares.')
			return

		# Calculate profit
		price = self.get_price(symbol)
		sale_proceeds = qty * price
		hist_cost = self.hist_cost(qty, symbol, 'Investments')
		investment_gain = None
		investment_loss = None
		if sale_proceeds >= hist_cost:
			investment_gain = sale_proceeds - hist_cost
		else:
			investment_loss = hist_cost - sale_proceeds

		# Journal entries for a sell transaction
		sell_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Shares sell', symbol, hist_cost / qty, qty, 'Cash', 'Investments', hist_cost]
		if investment_gain is not None:
			profit_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Realized gain', '', price, '', 'Cash', 'Investment Gain', investment_gain]
		if investment_loss is not None:
			profit_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Realized loss', '', price, '', 'Investment Loss', 'Cash', investment_loss]
		if self.com() != 0:
			com_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Comm. sell', '', '', '','Commission Expense', 'Cash', self.com()]
		if self.com() != 0:
			sell_event = [sell_entry, profit_entry, com_entry]
		else:
			sell_event = [sell_entry, profit_entry]

		self.journal_entry(sell_event)

		# TODO Handle dividends and stock splits

	def int_exp(self):
		loan_accts = ['Credit Line','Student Credit'] # TODO Get list from accts under liabilities
		loan_bal = 0
		loan_bal = self.balance_sheet(loan_accts)
		if loan_bal < 0:
			print ('Loan exists!')
			cur = ledger.conn.cursor()
			for loan_type in loan_accts:
				loans = pd.unique(self.df.loc[self.df['credit_acct'] == loan_type]['item_id'])
				for loan in loans:
					try:
						debits = self.df.loc[self.df['item_id'] == loan].groupby('debit_acct').sum()['amount'][loan_type]
					except:
						debits = 0
					try:
						credits = self.df.loc[self.df['item_id'] == loan].groupby('credit_acct').sum()['amount'][loan_type]
					except:
						credits = 0
					loan_bal = credits - debits
					if loan_bal > 0:
						int_rate_fix = cur.execute('SELECT int_rate_fix FROM items WHERE item_id = "' + str(loan) + '";').fetchone()[0]
						print (int_rate_fix)
						int_rate_var = cur.execute('SELECT int_rate_var FROM items WHERE item_id = "' + str(loan) + '";').fetchone()[0]
						print (int_rate_var)
						if int_rate_var is None:
							url = 'http://www.rbcroyalbank.com/rates/prime.html'
							rbc_prime_rate = pd.read_html(url)[5].iloc[1,1]
							try:
								int_rate_var = round(float(rbc_prime_rate) / 100, 4)
							except:
								print ('RBC Rates Website structure has changed.')
								int_rate_var = 0
						print (rbc_prime_rate)

					rate = int_rate_fix + int_rate_var
					period = 1 / 365 # TODO Add frequency logic
					int_amount = round(loan_bal * rate * period, 2)
					print (int_amount)
					int_exp_entry = [ self.get_event(), self.get_entity(), self.trade_date(), 'Interest expense', '', '', '', 'Interest Expense', 'Cash', int_amount]
					int_exp_event = [int_exp_entry]
					self.journal_entry(int_exp_event)

	def unrealized(self):
		pass

if __name__ == '__main__':
	# TODO Add argparse to make trades
	accts = Accounts()
	ledger = Ledger()
	trade = Trading(ledger)

	while True:
		command = input('\nType one of the following commands:\nbuy, sell, exit\n')
		if command.lower() == 'exit':
			exit()
		# TODO Allow command to be a single line in any order (i.e. buy tsla 10)
		elif command.lower() == 'buy':
			symbol = input('Which ticker? ')
			trade.buy_shares(symbol)
		elif command.lower() == 'sell':
			symbol = input('Which ticker? ')
			trade.sell_shares(symbol)
		else:
			print('Not a valid command. Type exit to close.')