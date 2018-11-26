import unittest
import os
import acct
import trade_platform
import pandas as pd
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.INFO) #filename='logs/output.log')

db_name = 'test.db'
db_path = 'db/'

class TestAcct(unittest.TestCase):
	def set_up(self):
		logging.warning('Setup started.')
		self.ledger = ledger
		self.gl = ledger.gl
		self.ledger_name = ledger.ledger_name
		self.entity = ledger.entity
		self.date = ledger.date
		self.start_date = ledger.start_date
		self.txn = ledger.txn

		#try:
			#accts.load_accts('accounts.csv') # Load accounts
		#except:
			#accts.load_accts('trading') # If error from iOS SSH app
		ledger.load_gl('data/ledger_test_2.csv') # Load sample transactions
		logging.warning('Setup complete.')

	def test_bs(self):
		logging.warning('Testing balance_sheet function.')
		self.assertEqual(ledger.balance_sheet(), 99980.1, 'Net Asset Value')

	def test_qty(self, item=None):
		logging.warning('Testing qty function.')
		if item is None:
			item = input('Which ticker? ').lower()
		self.assertEqual(ledger.get_qty(item, 'Investments'), 10, 'Quantity')

	def test_hist(self, date=None, qty=None, item=None):
		ledger.set_date(date)
		ledger.print_gl()
		print('Date: {}'.format(date))
		cost = ledger.hist_cost(qty, item, 'Investments')
		ledger.reset()
		return cost

	def tear_down(self):
		if os.path.exists(db_path + db_name):
			os.remove(db_path + db_name)
			logging.warning('Test database file removed: {}'.format(db_path + db_name))
		else:
			logging.error('The database file does not exist at {}.'.format(db_path + db_name))

if __name__ == '__main__':
	logging.warning('Starting testing of acct.py and trading_platform.py')
	accts = acct.Accounts(db_name)
	ledger = acct.Ledger(accts, ledger_name='test_1')
	trade = trade_platform.Trading(ledger)
	test = TestAcct()

	try:
		test.set_up()

		cost = test.test_hist('2018-07-21', 34, 'xmpl')
		print('Cost: {}'.format(cost))

		#test.test_bs()
		#ledger.print_bs()
		test.test_qty('abc')
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(ledger.get_qty(accounts='Investments'))

	finally:
		test.tear_down()

	logging.warning('Exiting testing of acct.py and trading_platform.py')
