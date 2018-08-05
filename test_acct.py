import unittest
import os
import acct
import trade_platform
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.INFO) #filename='logs/output.log'

db_name = 'test.db'

class TestAcct(unittest.TestCase):
	def setUp(self):
		accts = acct.Accounts(db_name)
		ledger = acct.Ledger('test_1')
		trade = trade_platform.Trading(ledger)
		self.df = trade.df
		self.ledger_name = trade.ledger_name
		self.entity = trade.entity
		self.date = trade.date
		self.start_date = trade.start_date
		self.txn = trade.txn

		# Load accounts
		accts.load_accts('accounts.csv')

		# Load sample transactions


		logging.info('Setup complete.')

	def test_bs(self):
		pass

	def tearDown(self):
		if os.path.exists(db_name):
			os.remove(db_name)
			logging.info('Test database file removed.')
		else:
			logging.warning('The database file does not exist.')

if __name__ == '__main__':
	logging.info('Starting testing of acct.py and trading_platform.py')
	test = TestAcct()

	test.setUp()
	test.tearDown()
	logging.info('Exiting testing of acct.py and trading_platform.py')
