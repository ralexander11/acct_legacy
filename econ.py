from acct import Accounts
from acct import Ledger
import pandas as pd

DISPLAY_WIDTH = 97
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

class World(object):
	def __init__(self):
		print('Create World')
		self.farm = self.create_org('Farm', self) # TODO Make this general
		self.farmer = self.create_indv('Farmer', self) # TODO Make this general

	def create_org(self, name, world):
		return Organization(name, world)

	def create_indv(self, name, world):
		return Individual(name, world)

	def update_econ(self):
		print('Econ Updated')
		self.farmer.need_decay(self.farmer.need)
		print('Farmer Need: {}'.format(self.farmer.need))

		self.farm.produce()
		print('Farm Food: {}'.format(self.farm.food))

		self.farmer.threshold_check()

	# TODO Maybe an update_world method

class Entity(object):
	def __init__(self, name, world):
		print('Create Entity')

class Organization(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		print('Create Org: {}'.format(name))
		#self.food = 0 # TODO Use ledger.get_qty() to get starting amount
		self.food = ledger.get_qty(item='Food', acct='Food')
		print('Starting Farm Food: {}'.format(self.food))

	def produce(self):

		price = 1
		qty = 1
		produce_entry = [ ledger.get_event(), ledger.get_entity(), '', 'Food produced', 'Food', price, qty, 'Food', 'Food Produced', price * qty ]
		produce_event = [produce_entry]
		ledger.journal_entry(produce_event)

	def sell(self, qty): # TODO Move into Entity class
		print('Sell: {}'.format(qty))

		price = 1
		qty = 1
		sell_entry = [ ledger.get_event(), ledger.get_entity(), '', 'Food sold', 'Food', price, qty, 'Cash', 'Food', price * qty ]
		sell_event = [sell_entry]
		ledger.journal_entry(sell_event)

class Individual(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		print('Create Indv: {}'.format(name))
		self.max_need = 100
		self.need =  50
		print('Initial Need: {}'.format(self.need))
		# TODO Make entry in entities table upon creation

	def need_decay(self, need):
		self.need -= 1

	def consume(self, qty):
		print('Consume: {}'.format(qty))

		price = 1
		qty = 1
		consume_entry = [ ledger.get_event(), ledger.get_entity(), '', 'Food consumed', 'Food', price, qty, 'Food Consumed', 'Food', price * qty ]
		consume_event = [consume_entry]
		ledger.journal_entry(consume_event)

		self.need += qty

	def purchase(self, qty): # TODO Move into Entity class
		print('Purchase: {}'.format(qty))
		world.farm.sell(qty) # TODO Figure out how to get entities to interact

		price = 1
		qty = 1
		purchase_entry = [ ledger.get_event(), ledger.get_entity(), '', 'Food purchased', 'Food', price, qty, 'Food', 'Cash', price * qty ]
		purchase_event = [purchase_entry]
		ledger.journal_entry(purchase_event)

	def threshold_check(self):
		if self.need <= 40:
			print('Threshold met!')
			self.purchase(10)
			self.consume(5) # TODO Make random int between 5 and 15


if __name__ == '__main__':
	print('Start Econ Sim')
	accts = Accounts(conn='econ01.db') #TODO Fix init of accounts
	ledger = Ledger(accts) # TODO Fix generalization of get_qty() and hist_cost()
	accts.load_accts('econ')
	world = World()
	# TODO Init starting ledger and accounts

	#while True:
	for _ in range(20):
		world.update_econ()

	print('End Econ Sim')


exit()

# Notes for factory functions
def g():
    return B()

def f(): # Singleton
    if f.obj is None:
        f.obj = A()
    return f.obj

f.obj = None
