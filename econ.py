from acct import Accounts
from acct import Ledger
import pandas as pd
import collections
import argparse
import datetime
import random
import time
import os

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

random.seed()

def time_stamp():
	time = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time

def delete_db(db_name=None): # TODO Test and fix this for long term
	if db_name is None:
		db_name = 'econ02.db'
	db_path = 'db/'
	if os.path.exists(db_path + db_name):
		os.remove(db_path + db_name)
		print(time_stamp() + 'Database file removed: {}'.format(db_path + db_name))
	else:
		print(time_stamp() + 'The database file does not exist at {}.'.format(db_path + db_name))

class World(object):
	def __init__(self, player=False):
		self.clear_ledger()
		print(('=' * 42) + ' Create World ' + ('=' * 42))
		self.items = accts.load_items('data/items.csv')
		self.end = False
		self.player = player
		self.now = datetime.datetime(1986,10,1).date()
		print(self.now)

		self.farmer = self.create_indv('Farmer', self) # TODO Make this general
		self.farm = self.create_org('Farm', self) # TODO Make this general
		self.farmer.auth_shares('Farm', 1000000, 2) # TODO Pull shares authorized from entities table

		self.farmer.capitalize(amount=10000)
		self.farmer.buy_shares(item='Farm', price=5, qty=1000, counterparty=2) # TODO Maybe 'Farm shares'
		self.farm.claim_land(4000, 5, 'Arable Land') # TODO Need a way to determine price and qty of land

		self.food_price = 10 # TODO Fix how prices work
		self.price = self.food_price

		self.farm.order_service('Water', 1, 3)

		print(ledger.gl.columns.values.tolist()) # For verbosity

	def clear_ledger(self):
		tables = [
			'gen_ledger',
			'entities',
			'items'
		]

		cur = ledger.conn.cursor()
		for table in tables:
			clear_table_query = '''
				DELETE FROM ''' + table + ''';
			'''
			try:
				cur.execute(clear_table_query)
				print('Clear ' + table + ' table.')
			except:
				continue
		ledger.conn.commit()
		cur.close()
		#print('Clear tables.')

	def ticktock(self, ticks=1):
		self.now += datetime.timedelta(days=ticks)
		print(self.now)
		return self.now

	def create_org(self, name, world):
		return Organization(name, world)

	def create_indv(self, name, world):
		return Individual(name, world)

	def update_econ(self):
		print(('=' * 42) + ' Econ Updated ' + ('=' * 42))
		self.ticktock()
		for need in self.farmer.needs:
			self.farmer.need_decay(need)
			print('{} {} Need: {}'.format(self.farmer.name, need, self.farmer.needs[need]['Current Need']))

		self.farmer.depreciation_check() # Should something depreciate the first day it is bought?
		self.farm.depreciation_check() # TODO Add all entities to a register and then loop through objects and run method

		self.farm.pay_service('Water', 1, 3) # TODO Make into service check # TODO Get price and counterparty from service order

		if not self.player:
			self.farm.pay_salary(counterparty=1, job='Cultivator') # TODO Pull parameters from farmer object properties that are set at init
			self.farm.produce(item='Food', price=self.food_price, qty=10) # TODO Fix how much is produced

			# print('Farmer:')
			# self.farmer.collect_material(item='Wood', qty=20, price=1)
			# self.farmer.collect_material(item='Metal', qty=10, price=3)
			# self.farmer.produce(item='Plow', price=100, qty=1)

			# print('Farm:')
			# self.farm.collect_material(item='Wood', qty=20, price=1)
			# self.farm.collect_material(item='Metal', qty=10, price=3)
			# self.farm.produce(item='Plow', price=100, qty=1)

			ledger.set_entity(2)
			self.food = ledger.get_qty(items='Food', accounts=['Inventory'])
			ledger.reset()
			print('Farm Food: {}'.format(self.food))

			for need in self.farmer.needs:
				self.farmer.threshold_check(need)

			ledger.set_entity(2)
			plow_qty = ledger.get_qty(items='Plow', accounts=['Equipment'])
			ledger.reset()
			if plow_qty < 1:
				self.farm.make_item(item='Plow', qty=1, price=100)

		hours = 0
		while hours < 8 and self.player: # TODO Need to test hours to be used before executing function
			print('Player Hours Remaining: {}'.format(hours))
			action = input('\nType one of the following actions:\nHarvest, Forage, Purchase, Consume, Make, exit\n')
			if action.lower() == 'harvest':
				hours += self.farm.pay_salary(counterparty=1, job='Cultivator')
				self.farm.produce(item='Food', price=self.food_price, qty=10)
				print(hours)
			elif action.lower() == 'forage':
				item = input('Which item? (wood, metal) ').title()
				hours += self.farmer.collect_material(item, qty=2, price=1, account='Raw Materials')
			elif action.lower() == 'purchase':
				qty = int(input('How much food? '))
				hours += self.farmer.purchase(item='Food', price=world.food_price, qty=qty, counterparty=2)
			elif action.lower() == 'consume':
				qty = int(input('How much food? '))
				hours += self.farmer.consume(item='Food', qty=qty)
			elif action.lower() == 'make':
				hours += self.farmer.make_item(item='Plow', qty=1, price=100, account='Equipment')
			elif action.lower() == 'exit':
				exit()
			else:
				print('Not a valid action. Type exit to close.')


		#if str(self.now) == '1986-10-15': # Temp
			#world.end = True # Temp

	# TODO Maybe an update_world method to change the needs

class Entity(object):
	def __init__(self, name, world):
		self.world = world
		#print('Entity created: {}'.format(name))

	def transact(self, item, acct_buy, acct_sell, price, qty, counterparty):
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		ledger.set_entity(counterparty)
		qty_avail = ledger.get_qty(items=item, accounts=[acct_sell])
		ledger.reset()
		if cash > (qty * price):
			if qty <= qty_avail:
				print('Purchase: {} {}'.format(qty, item))

				purchase_entry = [ ledger.get_event(), self.entity, self.world.now, item + ' purchased', item, price, qty, acct_buy, 'Cash', price * qty ]
				sell_entry = [ ledger.get_event(), counterparty, self.world.now, item + ' sold', item, price, qty, 'Cash', acct_sell, price * qty ]
				purchase_event = [purchase_entry, sell_entry]
				ledger.journal_entry(purchase_event)
				return 0.5 # TODO Factor in qty for large purchases
			else:
				print('Not enough units on hand to sell {} units of {}.'.format(qty, item))

		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, item))

	# TODO Maybe replace with transact method
	def purchase(self, item, price, qty, counterparty):
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		print('Purchaser Cash: {}'.format(cash))
		if cash > (qty * price):
			sell_entry = self.sell(item, price, qty, counterparty)
			if sell_entry is not None:
				print('Purchase: {} {}'.format(qty, item))
				purchase_entry = [ ledger.get_event(), self.entity, world.now, item + ' purchased', item, price, qty, 'Inventory', 'Cash', price * qty ]
				purchase_event = [purchase_entry, sell_entry]
				ledger.journal_entry(purchase_event)
				return 0.5 # TODO Factor in qty for large purchases
		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, item))

	def sell(self, item, price, qty, counterparty):
		ledger.set_entity(counterparty)
		qty_avail = ledger.get_qty(items=item, accounts=['Inventory'])
		ledger.reset()
		if qty <= qty_avail:
			print('Sell: {} {}'.format(qty, item))
			sell_entry = [ ledger.get_event(), counterparty, world.now, item + ' sold', item, price, qty, 'Cash', 'Inventory', price * qty ]
			return sell_entry
		else:
			print('Not enough on hand to sell {} units of {}.'.format(qty, item))

	# TODO Use historical price
	# TODO Make qty wanting to be consumed smarter (this is to be done in the world)
	def consume(self, item, qty, need=None):
		ledger.set_entity(self.entity)
		qty_held = ledger.get_qty(items=item, accounts=['Inventory'])
		ledger.reset()
		qty = 80 # Temp
		if qty_held > qty:
			print('Consume: {} {}'.format(qty, item))

			consume_entry = [ ledger.get_event(), self.entity, world.now, item + ' consumed', item, self.world.price, qty, 'Goods Consumed', 'Inventory', self.world.price * qty ]
			consume_event = [consume_entry]
			ledger.journal_entry(consume_event)

			if need is not None:
				new_need = self.needs[need]['Current Need'] + (self.world.items.loc[item, 'satisfy_rate'] * qty)
				if new_need < self.needs[need]['Max Need']:
					self.needs[need]['Current Need'] = new_need
				else:
					self.needs[need]['Current Need'] = self.needs[need]['Max Need']
				print('{} Need: {}'.format(self.name, self.needs[need]['Current Need'])) # TODO Get entity name from object data
			return qty * 0.01
		else:
			print('Not enough on hand to consume {} units of {}.'.format(qty, item))

	def get_base_item(self, item):
		if item in ['Land','Labour','Equipment','Building','Service','Raw Material','Components','None']:
			return item
		else:
			return self.get_base_item(self.world.items.loc[item, 'child_of'])

	# TODO Proper costing
	# TODO Make each item take a certain amount of labour hours and have items able to reduce that
	# TODO Add WIP accounting and COGS
	def produce(self, item, price, qty=None):
		v = False
		cur = ledger.conn.cursor()
		requirements_info = cur.execute("SELECT requirements, amount FROM items WHERE item_id = '"+ item +"';").fetchone()
		cur.close()
		if v: print('From Table: {}'.format(requirements_info))
		requirements = [x.strip() for x in requirements_info[0].split(',')]
		requirement_details = []
		for requirement in requirements:
			base_item = self.get_base_item(requirement)
			item_details = (requirement, base_item)
			requirement_details.append(item_details)
		if v: print('Requirements: {}'.format(requirement_details))
		amounts = [x.strip() for x in requirements_info[1].split(',')]
		amounts = list(map(float, amounts))
		if v: print('Amounts: {}'.format(amounts))
		requirement_details = list(zip(requirement_details, amounts))
		if v: print('Requirement Details: {}'.format(requirement_details))
		for requirement in requirement_details:
			ledger.set_entity(self.entity)
			if v: print('Requirement: {}'.format(requirement))
			if requirement[0][1] == 'Land':
				land = ledger.get_qty(items=requirement[0][0], accounts=['Land'])
				if v: print('Land: {}'.format(land))
				if land < (requirement[1] * qty):
					print('Not enough land to produce on.')
					return
			if requirement[0][1] == 'Labour': # TODO How to handle multiple workers
				modifier = 1
				# TODO Get list of all equipment that covers the requirement
				equip_list = ledger.get_qty(accounts=['Equipment'])#, v_qty=True)
				if v: print('Equip List: \n{}'.format(equip_list))
				
				items_data = accts.get_items()
				items_data = items_data[items_data['satisfies'].str.contains(requirement[0][0], na=False)] # If item satisfies multiple needs
				items_data.reset_index(inplace=True)
				if v: print('Items Table: \n{}'.format(items_data))

				if not equip_list.empty:
					equip_info = equip_list.merge(items_data)
					equip_info.sort_values(by='satisfy_rate', ascending=False, inplace=True)
					if v: print('Items Table Merged: \n{}'.format(equip_info))
					modifier = 1 / equip_info['satisfy_rate'].iloc[0]
					if v: print('Modifier: {}'.format(modifier))
				# TODO Factor in equipment capacity

				ledger.set_start_date(str(world.now))
				labour_done = ledger.get_qty(items=requirement[0][0], accounts=['Salary Expense'])
				ledger.reset()
				if v: print('Labour Done: {}'.format(labour_done))
				if labour_done < (requirement[1] * modifier * qty): # TODO Have this call for labour to be done if it hasn't been done
					print('Not enough labour done today for production.')
					return
			if requirement[0][1] == 'Building':
				building = ledger.get_qty(items=requirement[0][0], accounts=['Buildings'])
				if v: print('Building: {}'.format(land))
				if land < (requirement[1] * qty):
					print('Not enough building to produce in.')
					return
			if requirement[0][1] == 'Equipment': # TODO Make generic for process
				equip_qty = ledger.get_qty(items=requirement[0][0], accounts=['Equipment'])
				if v: print('Equipment: {} {}'.format(equip_qty, requirement[0][0]))
				if ((equip_qty * requirement[1]) / qty) < 1: # TODO Test turning requirement into capacity
					print('No required equipment.')
					return
			if requirement[0][1] == 'Components':
				component_qty = ledger.get_qty(items=requirement[0][0], accounts=['Components'])
				if v: print('Land: {}'.format(component_qty))
				if component_qty < (requirement[1] * qty):
					print('Not enough {}.'.format(requirement[0][0]))
					return
			if requirement[0][1] == 'Raw Material':
				material_qty = ledger.get_qty(items=requirement[0][0], accounts=['Raw Materials'])
				if v: print('Land: {}'.format(material_qty))
				if material_qty < (requirement[1] * qty):
					print('Not enough {}.'.format(requirement[0][0]))
					return
			if requirement[0][1] == 'Service': # TODO Add check to ensure payment has been made recently (maybe on day of)
				service_state = ledger.get_qty(items=requirement[0][0], accounts=['Service Info'])
				if not service_state:
					print('{} service is not active.'.format(requirement[0][0]))
					return
		print('Service State: {}'.format(service_state))
			# TODO Add other base requirements
		ledger.reset()
		produce_entry = [ ledger.get_event(), self.entity, world.now, item + ' produced', item, price, qty, 'Inventory', 'Goods Produced', price * qty ]
		produce_event = [produce_entry]
		ledger.journal_entry(produce_event)
		#return labour_done # TODO This shouldn't be needed as it is covered by pay_salary()

	def capitalize(self, amount):
		capital_entry = [ ledger.get_event(), self.entity, self.world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', amount ]
		capital_event = [capital_entry]
		ledger.journal_entry(capital_event)

	def auth_shares(self, ticker, qty, counterparty=None):
		if counterparty is None:
			counterparty = self.entity
		auth_shares_entry = [ ledger.get_event(), counterparty, self.world.now, 'Authorize shares', ticker, '', qty, 'Shares', 'Info', 0 ]
		auth_shares_event = [auth_shares_entry]
		ledger.journal_entry(auth_shares_event)

	def buy_shares(self, item, price, qty, counterparty):
		self.transact(item, 'Investments', 'Shares', price, qty, counterparty)

	def claim_land(self, qty, price, item='Land'): # QTY in square meters
		claim_land_entry = [ ledger.get_event(), self.entity, self.world.now, 'Claim land', item, price, qty, 'Land', 'Natural Wealth', qty * price ]
		claim_land_event = [claim_land_entry]
		ledger.journal_entry(claim_land_event)

	def pay_salary(self, counterparty, job, salary=None, labour_hours=None): # TODO Fix defaults
		if salary is None:
			salary = 5
		if labour_hours is None:
			labour_hours = 4
		ledger.set_entity(self.entity)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= (salary * labour_hours):
			# TODO Add check if enough cash, if not becomes salary payable
			salary_exp_entry = [ ledger.get_event(), self.entity, world.now, job + ' salary paid', job, salary, labour_hours, 'Salary Expense', 'Cash', salary * labour_hours ]
			salary_rev_entry = [ ledger.get_event(), counterparty, self.world.now, job + ' salary received', job, salary, labour_hours, 'Cash', 'Salary Revenue', salary * labour_hours ]
			pay_salary_event = [salary_exp_entry, salary_rev_entry]
			ledger.journal_entry(pay_salary_event)

			ledger.set_entity(self.entity)
			print('{} Cash: {}'.format(self.name, ledger.balance_sheet(['Cash'])))
			ledger.set_entity(counterparty)
			print('{} Cash: {}'.format('Farmer', ledger.balance_sheet(['Cash']))) # TOTO Pull counterparty name from counterparty object
			ledger.reset()
			return labour_hours
		else:
			print('Not enough cash to pay for ' + job + ': {}'.format(cash))

	def order_service(self, item, counterparty, price, qty=1):
		order_service_entry = [ ledger.get_event(), self.entity, self.world.now, 'Ordered ' + item, item, price, qty, 'Service Info', 'Order Service', 0 ]
		order_service_event = [order_service_entry]
		ledger.journal_entry(order_service_event)
		return 1

	def cancel_service(self, item, counterparty, price=0, qty=-1):
		order_service_entry = [ ledger.get_event(), self.entity, self.world.now, 'Cancelled ' + item, item, price, qty, 'Service Info', 'Cancel Service', 0 ]
		order_service_event = [order_service_entry]
		ledger.journal_entry(order_service_event)
		return 1

	def pay_service(self, item, counterparty, price, qty=''):
		 # TODO Get price and counterparty from service order
		ledger.set_entity(self.entity)
		service_state = ledger.get_qty(items=item, accounts=['Service Info'])
		ledger.reset()
		#print('Service State: {}'.format(service_state))
		if service_state:
			pay_service_entry = [ ledger.get_event(), self.entity, self.world.now, 'Payment for ' + item, item, price, qty, 'Service Expense', 'Cash', price ]
			charge_service_entry = [ ledger.get_event(), counterparty, self.world.now, 'Received payment for ' + item, item, price, qty, 'Cash', 'Service Revenue', price ]
			pay_service_event = [pay_service_entry, charge_service_entry]
			ledger.journal_entry(pay_service_event)
			return 0

	def collect_material(self, item, qty, price=1, account=None): # TODO Make cost based on time spent and salary
		if account is None:
			account = 'Raw Materials'
		collect_mat_entry = [ ledger.get_event(), self.entity, self.world.now, 'Forage ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		collect_mat_event = [collect_mat_entry]
		ledger.journal_entry(collect_mat_event)
		return qty * 1 # TODO Spend time collecting food, wood, ore

	def make_item(self, item, qty, price=1, account=None): # Assuming all materials found
		if account is None:
			account = 'Equipment'
		make_item_entry = [ ledger.get_event(), self.entity, self.world.now, 'Make ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		make_item_event = [make_item_entry]
		ledger.journal_entry(make_item_event)
		return qty * 10

	def depreciation_check(self, items=None): # TODO Add support for explicitly provided items
		if items is None:
			ledger.set_entity(self.entity)
			items_list = ledger.get_qty(accounts=['Buildings','Equipment','Furniture','Inventory'])#, v_qty=False)# TODO Add other account types for base items such as Raw Materials
			#print('Dep. Items List: \n{}'.format(items_list))
		for index, item in items_list.iterrows():
			#print(item)
			qty = item['qty']
			item = item['item_id']
			cur = ledger.conn.cursor()
			lifespan = cur.execute('SELECT lifespan FROM items WHERE item_id = ?;', (item,)).fetchone()[0]
			metric = cur.execute('SELECT metric FROM items WHERE item_id = ?;', (item,)).fetchone()[0]
			cur.close()
			#lifespan = 10 # Temp
			self.derecognize(item, qty)
			self.depreciation(item, lifespan, metric)
		ledger.reset()

	def depreciation(self, item, lifespan, metric):
		if (metric == 'depreciation') or (metric == 'ticks'):
			asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment','Furniture'], item=item) # TODO Support other accounts like Tools
			if asset_bal == 0:
				return
			#print('Asset Bal: {}'.format(asset_bal))
			dep_amount = asset_bal / lifespan
			#print('Depreciation: {} {} {}'.format(item, lifespan, metric))
			depreciation_entry = [ ledger.get_event(), self.entity, self.world.now, 'Depreciation on ' + item, item, '', '', 'Depreciation Expense', 'Accumulated Depreciation', dep_amount ]
			depreciation_event = [depreciation_entry]
			ledger.journal_entry(depreciation_event)

		if (metric == 'spoilage') or (metric == 'obsolescence'):
			print('Spoilage: {} {} day {} to be implemented'.format(item, lifespan, metric))
			return

	def derecognize(self, item, qty):
		asset_bal = ledger.balance_sheet(accounts=['Equipment'], item=item)# TODO Support other accounts
		if asset_bal == 0:
				return
		accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
		if asset_bal == abs(accum_dep_bal):
			derecognition_entry = [ ledger.get_event(), self.entity, self.world.now, 'Derecognition of ' + item, item, asset_bal / qty, qty, 'Accumulated Depreciation', 'Equipment', asset_bal ]
			derecognition_event = [derecognition_entry]
			ledger.journal_entry(derecognition_event)


class Individual(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		entity_data = [ (name,0.0,1,100,0.5,'iex','Hunger,Thirst','100,100','1,2','40,60','50,100',None,'Labour') ] # TODO Change to proper values
		# TODO Add entity skills (Cultivator)
		self.entity = accts.add_entity(entity_data)
		self.name = entity_data[0][0]
		#self.entity = 1 # TODO Have this read from the entities table
		print('Create Individual: {} | entity_id: {}'.format(self.name, self.entity))
		self.setup_needs(entity_data)
		for need in self.needs:
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))

	def setup_needs(self, entity_data):
		self.needs = collections.defaultdict(dict)
		needs_names = [x.strip() for x in entity_data[0][6].split(',')]
		needs_max = [x.strip() for x in str(entity_data[0][7]).split(',')]
		decay_rate = [x.strip() for x in str(entity_data[0][8]).split(',')]
		threshold = [x.strip() for x in str(entity_data[0][9]).split(',')]
		current_need = [x.strip() for x in str(entity_data[0][10]).split(',')]
		for i, name in enumerate(needs_names):
			self.needs[name]['Max Need'] = int(needs_max[i])
			self.needs[name]['Decay Rate'] = int(decay_rate[i])
			self.needs[name]['Threshold'] = int(threshold[i])
			self.needs[name]['Current Need'] = int(current_need[i])
		#print(self.needs)
		return self.needs

	def set_need(self, need, need_delta):
		#self.need += need_delta
		self.needs[need]['Current Need'] += need_delta
		cur = ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET current_need = ?
			WHERE entity_id = ?;
		'''
		values = (self.needs[need]['Current Need'], self.entity)
		cur.execute(set_need_query, values)
		ledger.conn.commit()
		cur.close()
		if self.needs[need]['Current Need'] <= 0:
			world.end = True
		return self.needs[need]['Current Need']

	def need_decay(self, need):
		#cur = ledger.conn.cursor()
		#decay_rate = cur.execute('SELECT decay_rate FROM entities WHERE entity_id = ?;', str(self.entity)).fetchone()[0]
		#cur.close()
		decay_rate = self.needs[need]['Decay Rate'] * -1
		#print('{} Decay Rate: {}'.format(need, decay_rate))
		self.set_need(need, decay_rate)
		return decay_rate

	def threshold_check(self, need):
		#cur = ledger.conn.cursor()
		#self.need_threshold = cur.execute('SELECT need_threshold FROM entities WHERE entity_id = ?;', str(self.entity)).fetchone()[0]
		#cur.close()
		#print('Need Threshold: {}'.format(need_threshold))
		if self.needs[need]['Current Need'] <= self.needs[need]['Threshold']:
			print('{} Threshold met!'.format(need))
			self.address_need(need)

	def address_need(self, need): # TODO This needs a demand system
		if need == 'Hunger':
			self.purchase(item='Food', price=world.food_price, qty=100, counterparty=2) # TODO Change to transact() function
			qty = random.randint(40, 80)
			self.consume('Food', qty, need) # TODO Make random int between 50 and 150 and if not enough food try again
		else:
			print('Trying to address {} need.'.format(need))

class Organization(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		entity_data = [ (name,0.0,1,100,0.5,'iex',None,None,None,None,None,1000000,'Food') ]
		self.entity = accts.add_entity(entity_data)
		self.name = entity_data[0][0] # TODO Change this to pull from entities table
		print('Create Organization: {} | entity_id: {}'.format(self.name, self.entity))
		ledger.set_entity(self.entity)
		self.food = ledger.get_qty(items='Food', accounts=['Inventory'])
		ledger.reset()
		print('Starting Farm Food: {}'.format(self.food))


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-p', '--player', action="store_true", help='Turn on player interaction.')
	args = parser.parse_args()
	if args.database is None:
		args.database = 'econ01.db'

	print(time_stamp() + 'Start Econ Sim')
	if (args.delay is not None) and (args.delay is not 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
	delete_db(args.database)
	accts = Accounts(conn=args.database) #TODO Fix init of accounts
	ledger = Ledger(accts) # TODO Move this into init for World() # TODO Fix generalization of get_qty() and hist_cost()
	world = World(args.player)

	while True:
		world.update_econ()
		if world.end:
			break
		time.sleep(args.delay)

	print(time_stamp() + 'End of Econ Sim')


exit()

# Add entity
# Add item

# Buying land, Incorporation, buying raw materials, buying equipment, equipment depreciation, buying services, paying wages


# Notes for factory functions
def g():
    return B()

def f(): # Singleton
    if f.obj is None:
        f.obj = A()
    return f.obj

f.obj = None
