from acct import Ledger
from trade_platform import Trading
import pandas as pd
import random
from tqdm import tqdm

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 20)

random.seed()

class RandomAlgo(object):
	def get_symbols(self, flag):
		if flag == 'iex':
			symbols_url = 'https://api.iextrading.com/1.0/ref-data/symbols'
			symbols = pd.read_json(symbols_url, typ='frame', orient='records')
			#symbols.set_index('symbol', inplace=True)
			symbols = symbols.sample(frac=1).reset_index(drop=True) #Randomizes list
			#outfile = flag + '_tickers' + time.strftime('_%Y-%m-%d', time.localtime()) + '.csv'
			#symbols.to_csv(self.save_location + 'tickers/' + outfile)
			return symbols

	def check_capital(self):
		capital_accts = ['Chequing','Cash']
		capital_bal = 0
		#capital_bal = ledger.balance_sheet(capital_accts) # TODO this doesn't work currently

		for acct in capital_accts: # TODO Change this to balance_sheet() function when it can accept specific accounts as arguments
			try:
				debits = ledger.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				debits = 0
			try:
				credits = ledger.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				credits = 0
			bal = round(debits - credits, 2)
			capital_bal += bal
		#	print (acct + ':		$' + str(bal))
		#print ('Total Capital:		$' + str(capital_bal))
		return capital_bal
	
	def get_trade(self, symbols):
		try:
			symbol = symbols.iloc[random.randint(0, len(symbols))-1]['symbol'].lower() # Get random ticker
		except:
			symbol = symbols
			print (symbol)
		try:
			max_qty = portfolio.loc[portfolio['symbol'] == symbol]['qty'].values
			if (random.randint(1, 2) % 2 == 0):
				print ('false')
				qty = random.randint(1, max_qty)
			else:
				print ('true')
				qty = int(max_qty)
		except:
			max_qty = 100
			qty = random.randint(1, max_qty)
			
		#print (qty)
		return symbol, qty
			
if __name__ == '__main__':
	ledger = Ledger('test_1')
	algo = RandomAlgo()
	trade = Trading()
	
	source = 'iex' # input("Which ticker source? ").lower()
	symbols = algo.get_symbols(source) # Get list of all the tickers
	#print (symbols)
	#print ('-' * DISPLAY_WIDTH)
	capital = algo.check_capital() # Check how much capital is available
	print (capital)
	print ('-' * DISPLAY_WIDTH)
	
	#while capital > 1000: # Buy shares until you run out of capital
	#	trade.buy_shares(*algo.get_trade(symbols))
	print (algo.get_trade(symbols))
	print ('-' * DISPLAY_WIDTH)
	
	portfolio = ledger.get_qty() # Get list of currently held tickers
	portfolio.columns = ['symbol','qty']
	portfolio = portfolio.sample(frac=1).reset_index(drop=True) #Randomizes list
	print (portfolio)
	print ('-' * DISPLAY_WIDTH)
	#print (len(portfolio))
	#max_qty = portfolio.loc[portfolio['symbol'] == 'aapl']['qty'].values
	#print (max_qty)
	
	#for _ in range(random.randint(1, len(portfolio))):
	for symbol in portfolio['symbol'][:random.randint(1, len(portfolio))]: # Sell random amounts of currently held shares
		print ('_')
	#	trade.sell_shares(*algo.get_trade(portfolio))
		print (algo.get_trade(symbol))

	print ('-' * DISPLAY_WIDTH) # TODO Add another round of buying shares until you run out of capital