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
		qty = int(input('How many shares? '))
		# TODO Add check to ensure there is enough capital to buy shares
		price = self.get_price(symbol)
		# TODO These are just placeholder entries for testing and not proper accounting treatment
		buy_entry = [ ledger.get_event(), ledger.get_entity(), self.date(), 'Shares buy', symbol, price, qty, 'Investments', 'Chequing', price * qty]
		com_entry = [ ledger.get_event(), ledger.get_entity(), self.date(), 'Comm. buy', '', trade.com(), 1, 'Commission Expense', 'Chequing', trade.com()]
		buy_event = [buy_entry, com_entry]

		ledger.journal_entry(buy_event)

	def sell_shares(self, symbol, qty=1):
		qty = int(input('How many shares? '))
		# TODO Add check for available shares > qty
		price = self.get_price(symbol)
		# TODO These are just placeholder entries for testing and not proper accounting treatment
		sale_proceeds = qty * price
		hist_cost = ledger.hist_cost(qty, 'Investments', symbol)
		investment_gain = None
		investment_loss = None
		if sale_proceeds >= hist_cost:
			investment_gain = sale_proceeds - hist_cost
		else:
			investment_loss = hist_cost - sale_proceeds

		# TODO Fix price calc
		sell_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Shares sell', symbol, price, qty, 'Chequing', 'Investments', hist_cost]
		if investment_gain is not None:
			profit_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Realized gain', symbol, price, qty, 'Chequing', 'Investment Gain', investment_gain]
		if investment_loss is not None:
			profit_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Realized loss', symbol, price, qty, 'Investment Loss', 'Chequing', investment_loss]
		com_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Comm. sell', '', trade.com(), 1,'Commission Expense', 'Chequing', trade.com()]
		sell_event = [sell_entry, profit_entry, com_entry]

		ledger.journal_entry(sell_event)

if __name__ == '__main__':
	ledger = Ledger('test_1')
	trade = Trading()

	while True:
		command = input('Type one of the following commands:\nbuy, sell, exit\n')
		if command.lower() == "exit":
			exit()
		elif command.lower() == "buy":
			ticker = input('Which ticker? ')
			trade.buy_shares(ticker)
		elif command.lower() == "sell":
			ticker = input('Which ticker? ')
			trade.sell_shares(ticker)
		else:
			print('Not a valid command. Type exit to close.')