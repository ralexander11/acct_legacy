from acct import Accounts
from acct import Ledger
import pandas as pd
import datetime
import random

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

class World(object):
	def __init__(self):
		self.clear_ledger()
		print('Create World')
		self.now = datetime.datetime(1986,10,1).date()
		print(self.now)
		self.farm = self.create_org('Farm', self) # TODO Make this general
		self.farmer = self.create_indv('Farmer', self) # TODO Make this general

	def clear_ledger(self):
		clear_ledger_query = '''
			DELETE FROM gen_ledger;
		'''

		cur = ledger.conn.cursor()
		cur.execute(clear_ledger_query)
		ledger.conn.commit()
		cur.close()
		print('Clear Ledger')

	def ticktock(self, ticks=1):
		self.now += datetime.timedelta(days=ticks)
		print(self.now)

	def create_org(self, name, world):
		return Organization(name, world)

	def create_indv(self, name, world):
		return Individual(name, world)

	def update_econ(self):
		print(('=' * 42) + ' Econ Updated ' + ('=' * 42))
		self.ticktock()
		self.farmer.need_decay(self.farmer.need)
		print('Farmer Need: {}'.format(self.farmer.need))

		self.farm.produce()
		ledger.set_entity(2)
		self.food = ledger.get_qty(item='Food', acct='Inventory')
		ledger.reset()
		print('Farm Food: {}'.format(self.food))

		self.farmer.threshold_check()

	# TODO Maybe an update_world method

class Entity(object):
	def __init__(self, name, world):
		#print('Create Entity')
		pass

	def purchase(self, item, qty, counterparty): # TODO Move this into Entity class
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash > (qty * price):
			print('Purchase: {}'.format(qty))

			purchase_entry = [ ledger.get_event(), self.entity, world.now, item + ' purchased', item, price, qty, 'Inventory', 'Cash', price * qty ]
			purchase_event = [purchase_entry]
			ledger.journal_entry(purchase_event)

			world.farm.sell(item, qty, counterparty) # TODO Add parameter for counterparty
		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, item))

	def sell(self, item, qty, counterparty): # TODO Move this into Entity class
		ledger.set_entity(self.entity)
		self.qty_avail = ledger.get_qty(item=item, acct='Inventory')
		ledger.reset()
		if self.qty_avail > 0:
			print('Sell: {}'.format(qty))

			sell_entry = [ ledger.get_event(), counterparty, world.now, item + ' sold', item, price, qty, 'Cash', 'Inventory', price * qty ]
			sell_event = [sell_entry]
			ledger.journal_entry(sell_event)
		else:
			print('Not enough on hand to sell {} units of {}.'.format(qty, item))

	def consume(self, item, qty):
		ledger.set_entity(self.entity)
		qty_held = ledger.get_qty(item='Food', acct='Inventory')
		ledger.reset()
		if qty_held > 0:
			print('Consume: {}'.format(qty))

			consume_entry = [ ledger.get_event(), self.entity, world.now, item + ' consumed', 'Food', price, qty, item + ' Consumed', 'Inventory', price * qty ]
			consume_event = [consume_entry]
			ledger.journal_entry(consume_event)

			self.need += (10 * qty)
			print('Farmer Need: {}'.format(self.need))
		else:
			print('Not enough on hand to consume {} units of {}.'.format(qty, item))

	def produce(self, item=None, qty=None):
		if item is None:
			item = 'Food'
		if qty is None:
			qty = 1
		produce_entry = [ ledger.get_event(), self.entity, world.now, item + ' produced', item, price, qty, 'Inventory', item + ' Produced', price * qty ]
		produce_event = [produce_entry]
		ledger.journal_entry(produce_event)


class Individual(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		print('Create Indv: {}'.format(name))
		self.entity = 1 # TODO Have this read from the entities table
		self.max_need = 100
		self.need =  50
		print('Initial Need: {}'.format(self.need))
		# TODO Make entry in entities table upon creation

		start_entry = [ ledger.get_event(), self.entity, world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', 10000 ]
		start_event = [start_entry]
		ledger.journal_entry(start_event)

	def need_decay(self, need):
		self.need -= 1

	def threshold_check(self):
		if self.need <= 40:
			print('Threshold met!')
			self.purchase('Food', 10, 2)
			self.consume('Food', 5) # TODO Make random int between 5 and 15

class Organization(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		print('Create Org: {}'.format(name))
		self.entity = 2
		ledger.set_entity(2)
		self.food = ledger.get_qty(item='Food', acct='Inventory')
		ledger.reset()
		print('Starting Farm Food: {}'.format(self.food))

		start_entry = [ ledger.get_event(), self.entity, world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', 10000 ]
		start_event = [start_entry]
		ledger.journal_entry(start_event)


if __name__ == '__main__':
	print('Start Econ Sim')
	accts = Accounts(conn='econ01.db') #TODO Fix init of accounts
	ledger = Ledger(accts) # TODO Move this into init for World() # TODO Fix generalization of get_qty() and hist_cost()
	accts.load_accts('econ')
	world = World()
	# TODO Init starting ledger and accounts
	food_price = 1.50
	price = food_price
	#print(world.farm.food)
	#exit()
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
