import unittest
import os
import acct
import trade_platform
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.INFO) #filename='logs/output.log'

db_name = 'test.db'

class TestAcct(unittest.TestCase):
	def set_up(self):
		self.df = trade.df
		self.ledger_name = trade.ledger_name
		self.entity = trade.entity
		self.date = trade.date
		self.start_date = trade.start_date
		self.txn = trade.txn

		accts.load_accts('accounts.csv') # Load accounts
		ledger.load_gl('data/ledger_test_1.csv') # Load sample transactions
		logging.info('Setup complete.')

	def test_bs(self):
		self.assertEqual(ledger.balance_sheet(), 99980.1, 'Net Asset Value' )

	def tear_down(self):
		if os.path.exists(db_name):
			os.remove(db_name)
			logging.info('Test database file removed.')
		else:
			logging.warning('The database file does not exist.')

if __name__ == '__main__':
	logging.info('Starting testing of acct.py and trading_platform.py')
	accts = acct.Accounts(db_name)
	ledger = acct.Ledger('test_1')
	trade = trade_platform.Trading(ledger)
	test = TestAcct()
	test.set_up()

	test.test_bs() # TODO Add finally condition

	test.tear_down()
	logging.info('Exiting testing of acct.py and trading_platform.py')
