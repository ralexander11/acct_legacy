from acct import Accounts
from acct import Ledger
import urllib.request
from time import strftime, localtime

class Trading(object):
	def get_price(self, symbol):
		url = 'https://api.iextrading.com/1.0/stock/'
		try:
			price = float(urllib.request.urlopen(url + symbol + '/price').read())
		except:
			print ('Error getting price from: ' + url + symbol + '/price')
		else:
			return price #round(price, 2)

	def date(self):
		return strftime('%Y-%m-%d', localtime())

	def com(self):
		com = 9.95
		return com

	def buy_shares(self, symbol, qty=1):
		if qty == 1:
			qty = int(input('How many shares? '))
		price = self.get_price(symbol)
		capital_accts = ['Cash','Chequing']
		capital_bal = 0
		#capital_bal = ledger.balance_sheet(capital_accts)

		for acct in capital_accts: # TODO Change this to balance_sheet() function when it can accept specific accounts as arguments
			try:
				debits = ledger.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				debits = 0
				print ('Debit error!')
			try:
				credits = ledger.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				credits = 0
				print ('Credit error!')
			bal = round(debits - credits, 2)
			capital_bal += bal
		#	print (acct + ':		$' + str(bal))
		#print ('Total Capital:		$' + str(capital_bal))

		if price * qty > capital_bal:
			print ('\nBuying ' + str(qty) + ' shares of ' + symbol + ' costs $' + str(round(price * qty, 2)) + '.')
			print ('You currently have $' + str(capital_bal) + ' available.\n')
			return

		# TODO Decide whether to display unrealized gains as temp entries with rvsls
		buy_entry = [ ledger.get_event(), ledger.get_entity(), self.date(), 'Shares buy', symbol, price, qty, 'Investments', 'Cash', price * qty]
		com_entry = [ ledger.get_event(), ledger.get_entity(), self.date(), 'Comm. buy', '', trade.com(), 1, 'Commission Expense', 'Cash', trade.com()]
		buy_event = [buy_entry, com_entry]

		ledger.journal_entry(buy_event)

	def sell_shares(self, symbol, qty=1):
		if qty == 1:
			qty = int(input('How many shares? '))
		current_qty = ledger.get_qty(symbol, 'Investments')
		if qty > current_qty:
			print ('You currently have ' + str(current_qty) + ' shares.')
			return

		price = self.get_price(symbol)
		sale_proceeds = qty * price
		hist_cost = ledger.hist_cost(qty, symbol, 'Investments')
		investment_gain = None
		investment_loss = None
		if sale_proceeds >= hist_cost:
			investment_gain = sale_proceeds - hist_cost
		else:
			investment_loss = hist_cost - sale_proceeds

		# TODO Fix price calc
		sell_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Shares sell', symbol, price, qty, 'Cash', 'Investments', hist_cost]
		if investment_gain is not None:
			profit_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Realized gain', symbol, price, qty, 'Cash', 'Investment Gain', investment_gain]
		if investment_loss is not None:
			profit_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Realized loss', symbol, price, qty, 'Investment Loss', 'Cash', investment_loss]
		com_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Comm. sell', '', trade.com(), 1,'Commission Expense', 'Cash', trade.com()]
		sell_event = [sell_entry, profit_entry, com_entry]

		ledger.journal_entry(sell_event)

if __name__ == '__main__':
	accts = Accounts()
	ledger = Ledger('test_1')
	trade = Trading()

	while True:
		command = input('Type one of the following commands:\nbuy, sell, exit\n')
		if command.lower() == "exit":
			exit()
		elif command.lower() == "buy":
			symbol = input('Which ticker? ')
			trade.buy_shares(symbol)
		elif command.lower() == "sell":
			symbol = input('Which ticker? ')
			trade.sell_shares(symbol)
		else:
			print('Not a valid command. Type exit to close.')