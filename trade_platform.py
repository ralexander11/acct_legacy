from acct import Accounts
from acct import Ledger
import urllib.request
from time import strftime, localtime

class Trading(Ledger): # Change
	def __init__(self, ledger):
		self.df = ledger.df
		self.ledger_name = ledger.ledger_name

	def get_price(self, symbol):
		url = 'https://api.iextrading.com/1.0/stock/'
		try:
			price = float(urllib.request.urlopen(url + symbol + '/price').read())
		except:
			print ('Error getting price from: ' + url + symbol + '/price')
			return 0
		else:
			return price

	def date(self):
		return strftime('%Y-%m-%d', localtime())

	def com(self):
		com = 0 #9.95
		return com

	def buy_shares(self, symbol, qty=1):
		if qty == 1:
			qty = int(input('How many shares? '))
		price = self.get_price(symbol)

		# Check if there is enough capital
		capital_accts = ['Cash','Chequing']
		capital_bal = 0
		capital_bal = self.balance_sheet(capital_accts) # Change
		#print (capital_bal)

		if price * qty > capital_bal or price == 0:
			print ('\nBuying ' + str(qty) + ' shares of ' + symbol + ' costs $' + str(round(price * qty, 2)) + '.')
			print ('You currently have $' + str(round(capital_bal, 2)) + ' available.\n')
			return capital_bal

		# TODO Decide whether to display unrealized gains as temp entries with rvsls or not
		# Journal entries for a buy transaction
		buy_entry = [ self.get_event(), self.get_entity(), self.date(), 'Shares buy', symbol, price, qty, 'Investments', 'Cash', price * qty]
		if self.com() != 0:
			com_entry = [ self.get_event(), self.get_entity(), self.date(), 'Comm. buy', '', self.com(), 1, 'Commission Expense', 'Cash', self.com()]
		if self.com() != 0:
			buy_event = [buy_entry, com_entry]
		else:
			buy_event = [buy_entry]

		self.journal_entry(buy_event)
		return capital_bal

	def sell_shares(self, symbol, qty=1):
		if qty == 1:
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
		sell_entry = [ self.get_event(), self.get_entity(), self.date(), 'Shares sell', symbol, hist_cost / qty, qty, 'Cash', 'Investments', hist_cost]
		if investment_gain is not None:
			profit_entry = [ self.get_event(), self.get_entity(), self.date(), 'Realized gain', '', price, 1, 'Cash', 'Investment Gain', investment_gain]
		if investment_loss is not None:
			profit_entry = [ self.get_event(), self.get_entity(), self.date(), 'Realized loss', '', price, 1, 'Investment Loss', 'Cash', investment_loss]
		if self.com() != 0:
			com_entry = [ self.get_event(), self.get_entity(), self.date(), 'Comm. sell', '', self.com(), 1,'Commission Expense', 'Cash', self.com()]
		if self.com() != 0:
			sell_event = [sell_entry, profit_entry, com_entry]
		else:
			sell_event = [sell_entry, profit_entry]

		self.journal_entry(sell_event)

		# TODO Handle dividends and stock splits

if __name__ == '__main__':
	# TODO Add argparse to make trades
	accts = Accounts()
	ledger = Ledger('test_1')
	trade = Trading(ledger) # Change

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