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

	def buy(self, symbol, qty=0):
		qty = int(input('How many shares? '))
		price = self.get_price(symbol)
		# TODO Fix Event_ID
		buy_entry = [ 1, 1, strftime('%Y-%m-%d', localtime()), "Bought " + str(qty) + ' shares of ' + symbol, 'Investments', 'Chequing', qty * price]
		com_entry = [ 1, 1, strftime('%Y-%m-%d', localtime()), 'Commission for buy trade', 'Commission Expense', 'Chequing', 9.95]
		buy_event = [buy_entry, com_entry]

		ledger.journal_entry(buy_event)

	def sell(self, symbol, qty=0):
		qty = int(input('How many shares? '))
		price = self.get_price(symbol)
		# TODO Fix Event_ID
		buy_entry = [ 2, 1, strftime('%Y-%m-%d', localtime()), "Sold " + str(qty) + ' shares of ' + symbol, 'Chequing', 'Investments', qty * price]
		com_entry = [ 2, 1, strftime('%Y-%m-%d', localtime()), 'Commission for buy trade', 'Commission Expense', 'Chequing', 9.95]
		buy_event = [buy_entry, com_entry]

		ledger.journal_entry(buy_event)

if __name__ == '__main__':
	ledger = Ledger('test_1')
	trade = Trading()

	#trade.buy('tsla')
	trade.sell('tsla')