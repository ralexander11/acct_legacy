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
			return price
	def com(self):
		com = 9.95
		return com

	def buy_shares(self, symbol, qty=1):
		qty = int(input('How many shares? '))
		price = self.get_price(symbol)
		# TODO Fix Event_ID
		# These are just placeholder entries for testing and not proper accounting treatment
		buy_entry = [ 1, 1, strftime('%Y-%m-%d', localtime()), 'Buy shares', symbol, price, qty, 'Investments', 'Chequing', price * qty]
		com_entry = [ 1, 1, strftime('%Y-%m-%d', localtime()), 'Commission for buy trade', '', trade.com(), 1, 'Commission Expense', 'Chequing', trade.com()]
		buy_event = [buy_entry, com_entry]

		ledger.journal_entry(buy_event)

	def sell_shares(self, symbol, qty=1):
		qty = int(input('How many shares? '))
		price = self.get_price(symbol)
		# TODO Fix Event_ID
		# These are just placeholder entries for testing and not proper accounting treatment
		sell_entry = [ 2, 1, strftime('%Y-%m-%d', localtime()), 'Sell shares', symbol, price, qty, 'Chequing', 'Investments', price * qty]
		com_entry = [ 2, 1, strftime('%Y-%m-%d', localtime()), 'Commission for sell trade', '', trade.com(), 1,'Commission Expense', 'Chequing', trade.com()]
		sell_event = [sell_entry, com_entry]

		ledger.journal_entry(sell_event)

if __name__ == '__main__':
	ledger = Ledger('test_1')
	trade = Trading()

	#trade.buy('tsla', 10)
	#trade.sell('tsla', 10)

	while True:
		command = input('Type one of the following commands:\nbuy, sell, exit\n')
		if command.upper() == "EXIT":
			exit()
		elif command.upper() == "BUY":
			ticker = input('Which ticker? ')
			trade.buy_shares(ticker)
		elif command.upper() == "SELL":
			ticker = input('Which ticker? ')
			trade.sell_shares(ticker)
		else:
			print('Not a valid command. Type exit to close.')