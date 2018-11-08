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

		self.farmer.buy_shares('Farm', 5, 100000, 2)

		self.food_price = 2 # TODO Fix how prices work
		self.price = self.food_price

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

		self.farm.produce('Food', self.food_price, 1)
		ledger.set_entity(2)
		self.food = ledger.get_qty(item='Food', acct='Inventory')
		ledger.reset()
		print('Farm Food: {}'.format(self.food))

		self.farmer.threshold_check()

	# TODO Maybe an update_world method to change the needs

class Entity(object):
	def __init__(self, name, world):
		self.world = world
		#print('Entity created')

	def transact(self, item, acct_buy, acct_sell, price, qty, counterparty):
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		ledger.set_entity(counterparty)
		qty_avail = ledger.get_qty(item=item, acct=acct_sell)
		ledger.reset()
		if cash > (qty * price):
			if qty <= qty_avail:
				print('Purchase: {} {}'.format(qty, item))

				purchase_entry = [ ledger.get_event(), self.entity, self.world.now, item + ' purchased', item, price, qty, acct_buy, 'Cash', price * qty ]
				sell_entry = [ ledger.get_event(), counterparty, self.world.now, item + ' sold', item, price, qty, 'Cash', acct_sell, price * qty ]
				purchase_event = [purchase_entry, sell_entry]
				ledger.journal_entry(purchase_event)
			else:
				print('Not enough units on hand to sell {} units of {}.'.format(qty, item))

		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, item))

	# TODO Maybe replace with transact method
	def purchase(self, item, price, qty, counterparty):
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		print('Cash: {}'.format(cash))
		if cash > (qty * price):
			sell_entry = self.sell(item, price, qty, counterparty)
			if sell_entry is not None:
				print('Purchase: {} {}'.format(qty, item))

				purchase_entry = [ ledger.get_event(), self.entity, world.now, item + ' purchased', item, price, qty, 'Inventory', 'Cash', price * qty ]
				purchase_event = [purchase_entry, sell_entry]
				ledger.journal_entry(purchase_event)

		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, item))

	def sell(self, item, price, qty, counterparty):
		ledger.set_entity(counterparty)
		qty_avail = ledger.get_qty(item=item, acct='Inventory')
		ledger.reset()
		if qty <= qty_avail:
			print('Sell: {} {}'.format(qty, item))

			sell_entry = [ ledger.get_event(), counterparty, world.now, item + ' sold', item, price, qty, 'Cash', 'Inventory', price * qty ]

			return sell_entry
		else:
			print('Not enough on hand to sell {} units of {}.'.format(qty, item))

	# TODO Use historical price
	def consume(self, item, qty):
		ledger.set_entity(self.entity)
		qty_held = ledger.get_qty(item='Food', acct='Inventory')
		ledger.reset()
		if qty_held > 0:
			print('Consume: {} {}'.format(qty, item))

			consume_entry = [ ledger.get_event(), self.entity, world.now, item + ' consumed', 'Food', self.world.price, qty, item + ' Consumed', 'Inventory', self.world.price * qty ]
			consume_event = [consume_entry]
			ledger.journal_entry(consume_event)

			self.need += (10 * qty)
			print('Farmer Need: {}'.format(self.need))
		else:
			print('Not enough on hand to consume {} units of {}.'.format(qty, item))

	# TODO Proper costing
	def produce(self, item, price, qty):
		produce_entry = [ ledger.get_event(), self.entity, world.now, item + ' produced', item, price, qty, 'Inventory', item + ' Produced', price * qty ]
		produce_event = [produce_entry]
		ledger.journal_entry(produce_event)

	# TODO Fix this
	def purchase_asset(self, asset, price, qty, counterparty):
		price = 100
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash > (qty * price):
			print('Purchase: {} {}'.format(qty, asset))

			purchase_asset_entry = [ ledger.get_event(), self.entity, world.now, asset + ' purchased', asset, price, qty, asset, 'Cash', price * qty ]
			purchase_asset_event = [purchase_asset_entry]
			ledger.journal_entry(purchase_asset_event)

			self.sell_asset(asset, qty, counterparty)
		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, asset))

	def capitalize(self, amount):
		capital_entry = [ ledger.get_event(), self.entity, self.world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', amount ]
		capital_event = [capital_entry]
		ledger.journal_entry(capital_event)

	def auth_shares(self, ticker, amount):
		auth_shares_entry = [ ledger.get_event(), self.entity, self.world.now, 'Authorize shares', ticker, '', amount, 'Shares', 'Info', 0 ]
		auth_shares_event = [auth_shares_entry]
		ledger.journal_entry(auth_shares_event)

	def buy_shares(self, item, price, qty, counterparty):
		self.transact(item, 'Investments', 'Shares', price, qty, counterparty)

	def claim_land(self, qty, price): # QTY in square meters
		claim_land_entry = [ ledger.get_event(), self.entity, self.world.now, 'Claim land', 'Land', price, qty, 'Land', 'Wealth', qty * price ]
		claim_land_event = [claim_land_entry]
		ledger.journal_entry(claim_land_event)

	def pay_wages(self):
		pass

class Individual(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		self.name = name
		print('Create Indv: {}'.format(name))
		self.entity = 1 # TODO Have this read from the entities table
		self.max_need = 100
		self.need =  50
		print('Initial Need: {}'.format(self.need))
		# TODO Make entry in entities table upon creation

		self.capitalize(500100)

	def need_decay(self, need):
		self.need -= 1

	def threshold_check(self):
		if self.need <= 40:
			print('Threshold met!')
			self.purchase('Food', world.food_price, 10, 2)
			self.consume('Food', 5) # TODO Make random int between 5 and 15

class Organization(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		self.name = name
		print('Create Org: {}'.format(name))
		self.entity = 2 # TODO Have this read from the entities table
		self.auth_shares(name, 1000000)
		self.claim_land(4000, 5) # TODO Need some way to determine price of land
		ledger.set_entity(2)
		self.food = ledger.get_qty(item='Food', acct='Inventory')
		ledger.reset()
		print('Starting Farm Food: {}'.format(self.food))


if __name__ == '__main__':
	print('Start Econ Sim')
	accts = Accounts(conn='econ01.db') #TODO Fix init of accounts
	ledger = Ledger(accts) # TODO Move this into init for World() # TODO Fix generalization of get_qty() and hist_cost()
	accts.load_accts('econ')
	world = World()
	#exit()
	#while True:
	for _ in range(20):
		world.update_econ()

	print('End of Econ Sim')


exit()

# Magically start with capital
# Incorporate farm
# Deposit capital in farm
# Farm claims land
# Produce food
# Farmer draws wages
# Farmer buys food from other farms

# Buying land, Incorporation, buying equipment, equipment depreciation, buying services, paying wages


# Notes for factory functions
def g():
    return B()

def f(): # Singleton
    if f.obj is None:
        f.obj = A()
    return f.obj

f.obj = None
