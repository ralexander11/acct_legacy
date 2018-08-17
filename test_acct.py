import unittest
import os
import acct
import trade_platform
import pandas as pd
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.INFO) #filename='logs/output.log')

db_name = 'test.db'

class TestAcct(unittest.TestCase):
	def set_up(self):
		logging.warning('Setup started.')
		self.df = trade.df
		self.ledger_name = trade.ledger_name
		self.entity = trade.entity
		self.date = trade.date
		self.start_date = trade.start_date
		self.txn = trade.txn

		accts.load_accts('accounts.csv') # Load accounts
		ledger.load_gl('data/ledger_test_1.csv') # Load sample transactions
		logging.warning('Setup complete.')

	def test_bs(self):
		logging.warning('Testing balance_sheet function.')
		self.assertEqual(ledger.balance_sheet(), 99980.1, 'Net Asset Value')

	def test_qty(self, item=None):
		logging.warning('Testing qty function.')
		if item is None:
			item = input('Which ticker? ').lower()
		self.assertEqual(ledger.get_qty(item), 10, 'Quantity')

	def tear_down(self):
		if os.path.exists(db_name):
			os.remove(db_name)
			logging.warning('Test database file removed: {}'.format(db_name))
		else:
			logging.error('The database file does not exist.')

if __name__ == '__main__':
	logging.warning('Starting testing of acct.py and trading_platform.py')
	accts = acct.Accounts(db_name)
	ledger = acct.Ledger('test_1')
	trade = trade_platform.Trading(ledger)
	test = TestAcct()
	try:
		test.set_up()

		test.test_bs()
		ledger.print_bs()
		test.test_qty('abc')
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print (ledger.get_qty())

	finally:
		test.tear_down()

	logging.warning('Exiting testing of acct.py and trading_platform.py')
