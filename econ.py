from acct import Accounts
from acct import Ledger
import pandas as pd
import collections
import argparse
import datetime
import random
import time
import math
import os

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

random.seed()

def time_stamp():
	time_stamp = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def delete_db(db_name=None): # TODO Test and fix this for long term
	if db_name is None:
		db_name = 'econ02.db'
	db_path = 'db/'
	if os.path.exists(db_path + db_name):
		os.remove(db_path + db_name)
		print(time_stamp() + 'Database file removed: {}'
			.format(db_path + db_name))
	else:
		print(time_stamp() + 'The database file does not exist at {}.'
			.format(db_path + db_name))

class World(object):
	def __init__(self, player=False):
		self.clear_ledger()
		print(('=' * 42) + ' Create World ' + ('=' * 42))
		self.items = accts.load_items('data/items.csv')
		self.end = False
		self.player = player
		self.now = datetime.datetime(1986,10,1).date()
		print(self.now)
		self.create_land('Land', 100000)
		self.create_land('Arable Land', 10000)
		self.create_land('Forest', 1000)
		self.create_land('Rocky Land', 1000)
		self.create_land('Mountain', 1000)

		# TODO Set amounts of land world has on init

		self.farmer = self.create_indv('Farmer', self) # TODO Make this general
		self.farm = self.create_org('Farm', self) # TODO Make this general

		# TODO Pull shares authorized from entities table
		self.farmer.auth_shares('Farm', 1000000, self.farm.entity)
		self.farmer.claim_land(100, 2, 'Land')
		self.farmer.capitalize(amount=10000)
		# TODO Maybe 'Farm shares'
		self.farmer.buy_shares(ticker='Farm', price=5, qty=1000
								, counterparty=self.farm.entity)
		# TODO Need a way to determine price and qty of land
		self.farm.claim_land(4000, 5, 'Arable Land')
		self.farm.hire_worker('Cultivator', self.farmer.entity)

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

	def create_land(self, item, qty):
		land_entry = [ ledger.get_event(), 0, self.now, item + ' created', item, '', qty, 'Natural Wealth', 'Land', 0 ]
		land_event = [land_entry]
		ledger.journal_entry(land_event)

	def ticktock(self, ticks=1):
		self.now += datetime.timedelta(days=ticks)
		print(self.now)
		return self.now

	def create_org(self, name, world):
		return Organization(name, world)

	def create_indv(self, name, world):
		return Individual(name, world)

	def price(self, item):
		if item == 'Food':
			price = 10
		elif item == 'Water':
			price = 3
		else:
			price = 5
		print('Price: {}'.format(price))
		return price

	def update_econ(self):
		print(('=' * 42) + ' Econ Updated ' + ('=' * 42))
		self.ticktock()

		#for entity in registry:
		for need in self.farmer.needs:
			self.farmer.need_decay(need)
			print('{} {} Need: {}'
				.format(self.farmer.name, need
						, self.farmer.needs[need]['Current Need']))

		# Should something depreciate the first day it is bought?
		self.farmer.depreciation_check()
		# TODO Add all entities to a register and then loop to run method
		self.farm.depreciation_check()

		self.farm.wip_check()

		# TODO Convert to Salary Payable and make payment only on 15th and last day of month
		self.farm.check_salary('Cultivator', self.farmer.entity)
		# TODO Make payment only on 15th and last day of month
		self.farm.pay_wages('Cultivator', self.farmer.entity)

		# TODO Make into service check
		# TODO Get price and counterparty from service order
		self.farm.pay_service('Water', 1, 3)

		if not self.player:
			# TODO Pull parameters from farmer object that are set at init
			#self.farm.pay_salary(job='Cultivator'
			#					, counterparty=self.farmer.entity)
			# TODO Fix how much is produced
			#if str(self.now) == '1986-10-02': # Temp
			#self.farm.produce(item='Food', qty=10, price=self.food_price)
			#if str(self.now) == '1986-10-04': # Temp
			rand_food = random.randint(0, 20)
			#rand_food = 20 #Temp
			self.farm.produce(item='Food', qty=rand_food, price=self.food_price)

			ledger.set_entity(self.farm.entity)
			self.farm.food = ledger.get_qty(items='Food', accounts=['Inventory'])
			ledger.reset()
			print('Farm Food: {}'.format(self.farm.food))
			ledger.set_entity(self.farmer.entity)
			self.farmer.food = ledger.get_qty(items='Food', accounts=['Inventory'])
			ledger.reset()
			print('Farmer Food: {}'.format(self.farmer.food))

			#self.farmer.produce(item='Plow', qty=1, price=100)
			ledger.set_entity(self.farm.entity)
			plow_qty = ledger.get_qty(items='Plow', accounts=['Equipment'])
			ledger.reset()
			if plow_qty < 1:
				self.farm.produce(item='Plow', qty=1, price=100, account='Equipment')#find_item

		hours = 0
		# TODO Need to test hours to be used before executing function
		while hours < 8 and self.player:
			print('Player Hours Remaining: {}'.format(hours))
			action = input('\nType one of the following actions:\nHarvest, Forage, Purchase, Consume, Make, exit\n')
			if action.lower() == 'harvest':
				hours += self.farm.pay_salary(job='Cultivator', counterparty=1)
				self.farm.produce(item='Food', qty=10, price=self.food_price)
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
				hours += self.farmer.find_item(item='Plow', qty=1, price=100, account='Equipment')
			elif action.lower() == 'incorp':
				hours += self.farmer.incorporate(item='Farm', price=5, qty=1000, counterparty=2)
			elif action.lower() == 'exit':
				exit()
			else:
				print('Not a valid action. Type exit to close.')

		for need in self.farmer.needs:
			self.farmer.threshold_check(need)

		#if str(self.now) == '1986-10-15': # Temp
			#world.end = True # Temp

	# TODO Maybe an update_world method to change the needs

class Entity(object):
	def __init__(self, name, world):
		self.world = world
		#print('Entity created: {}'.format(name))

	def transact(self, item, price, qty, counterparty, acct_buy='Inventory', acct_sell='Inventory'):
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
				print('Not enough {} on hand to sell {} units of {}.'.format(item, qty, item))

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
		#print('QTY Held: {} {}'.format(qty_held, item))
		if qty_held >= qty:
			#print('Consume: {} {}'.format(qty, item))
			price = 5 #self.world.price(item)

			consume_entry = [ ledger.get_event(), self.entity, world.now, item + ' consumed', item, price, qty, 'Goods Consumed', 'Inventory', price * qty ]
			consume_event = [consume_entry]
			ledger.journal_entry(consume_event)

			if need is not None:
				new_need = self.needs[need]['Current Need'] + (self.world.items.loc[item, 'satisfy_rate'] * qty)
				if new_need < self.needs[need]['Max Need']:
					self.needs[need]['Current Need'] = new_need
				else:
					self.needs[need]['Current Need'] = self.needs[need]['Max Need']
				print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need'])) # TODO Get entity name from object data
			return qty * 0.01
		else:
			print('Not enough {} on hand to consume {} units of {}.'.format(item, qty, item))

	def get_base_item(self, item):
		if item in ['Land','Labour','Equipment','Building','Service','Raw Material','Components','Time','None']:
			return item
		else:
			return self.get_base_item(self.world.items.loc[item, 'child_of'])

	# TODO Proper costing
	# TODO Make each item take a certain amount of labour hours and have items able to reduce that
	# TODO Add WIP accounting and COGS
	def produce(self, item, qty, price, account=None):
		v = False
		if qty == 0:
			return
		time_required = False
		cur = ledger.conn.cursor()
		requirements_info = cur.execute("SELECT requirements, amount FROM items WHERE item_id = '"+ item +"';").fetchone() # TODO Maybe get from items dataframe
		cur.close()
		if v: print('From Table: {}'.format(requirements_info))
		requirements = [x.strip() for x in requirements_info[0].split(',')]
		if v: print('Requirements Split: {}'.format(requirements))
		requirement_details = []
		for requirement in requirements:
			if v: print('Requirement: {}'.format(requirement))
			base_item = self.get_base_item(requirement)
			item_details = (requirement, base_item)
			requirement_details.append(item_details)
		if v: print('Requirements: {}'.format(requirement_details))
		amounts = [x.strip() for x in requirements_info[1].split(',')]
		amounts = list(map(float, amounts))
		if v: print('Amounts: {}'.format(amounts))
		requirement_details = list(zip(requirement_details, amounts))
		if v: print('Requirement Details: {}'.format(requirement_details))
		# TODO Sort so requirements with a capacity are first
		for requirement in requirement_details:
			ledger.set_entity(self.entity)
			if v: print('Requirement: {} {}'.format(requirement, requirement[0][1]))
			if requirement[0][1] == 'Land':
				land = ledger.get_qty(items=requirement[0][0], accounts=['Land'])
				if v: print('Land: {}'.format(land))
				if land < (requirement[1] * qty):
					print('Not enough {} to produce on.'.format(requirement[0][0]))
					required_qty = (requirement[1] * qty) - land
					# TODO Attempt to purchase land
					self.claim_land(required_qty, price=5, item=requirement[0][0])#world.price(requirement[0][0])
					#return
			if requirement[0][1] == 'Building':
				building = ledger.get_qty(items=requirement[0][0], accounts=['Buildings'])
				if v: print('Building: {}'.format(land))
				if building < (requirement[1] * qty): # TODO FIx qty required
					if building == 0:
						print('No {} building to produce in. Will attempt to aquire some.'.format(requirement[0][0]))
					print('Not enough capacity in {} building to produce in. Will attempt to aquire some.'.format(requirement[0][0]))
					# TODO Attempt to purchase before producing self if makes sense
					self.produce(requirement[0][0], qty=requirement[1] * qty, price=1)
					#return
			if requirement[0][1] == 'Equipment': # TODO Make generic for process
				equip_qty = ledger.get_qty(items=requirement[0][0], accounts=['Equipment'])
				if v: print('Equipment: {} {}'.format(equip_qty, requirement[0][0]))
				if ((equip_qty * requirement[1]) / qty) < 1: # TODO Test turning requirement into capacity
					if equip_qty == 0:
						print('No {} equipment to use. Will attempt to aquire some.'.format(requirement[0][0]))
					print('Not enough capacity on {} equipment. Will attempt to aquire some.'.format(requirement[0][0]))
					remaining_qty = qty - (equip_qty * requirement[1])
					required_qty = math.ceil(remaining_qty / requirement[1])
					# TODO Attempt to purchase before producing self if makes sense
					self.produce(requirement[0][0], required_qty, world.price(requirement[0][0]))
					#return
			if requirement[0][1] == 'Components':
				component_qty = ledger.get_qty(items=requirement[0][0], accounts=['Components'])
				if v: print('Land: {}'.format(component_qty))
				if component_qty < (requirement[1] * qty):
					print('Not enough {} components. Will attempt to aquire some.'.format(requirement[0][0]))
					# TODO Attempt to purchase before producing self if makes sense
					self.produce(requirement[0][0], qty=requirement[1] * qty, price=1)
					#return
				self.consume(requirement[0][0], qty=requirement[1] * qty)
			# TODO Add consumption calls for the raw materials and components
			if requirement[0][1] == 'Raw Material':
				material_qty = ledger.get_qty(items=requirement[0][0], accounts=['Raw Materials'])
				if v: print('Land: {}'.format(material_qty))
				if material_qty < (requirement[1] * qty):
					print('Not enough raw material: {}. Will attempt to aquire some.'.format(requirement[0][0]))
					# TODO Attempt to purchase before producing self if makes sense
					self.produce(requirement[0][0], qty=requirement[1] * qty, price=1)
					#return
				self.consume(requirement[0][0], qty=requirement[1] * qty)
			if requirement[0][1] == 'Service': # TODO Add check to ensure payment has been made recently (maybe on day of)
				service_state = ledger.get_qty(items=requirement[0][0], accounts=['Service Info'])
				if v: print('Service State for {}: {}'.format(requirement[0][0], service_state))
				if not service_state:
					print('{} service is not active. Will attempt to activate it.'.format(requirement[0][0]))
					self.order_service(item=requirement[0][0], counterparty=1, price=world.price(requirement[0][0]), qty=1) # TODO Fix counterparty
					#return
			if requirement[0][1] == 'Labour': # TODO How to handle multiple workers
				modifier = 1
				# TODO Get list of all equipment that covers the requirement
				equip_list = ledger.get_qty(accounts=['Equipment'])#, v_qty=True)
				if v: print('Equip List: \n{}'.format(equip_list))
				
				items_data = accts.get_items()
				items_data = items_data[items_data['satisfies'].str.contains(requirement[0][0], na=False)] # Supports if item satisfies multiple needs
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
					required_hours = int(math.ceil((requirement[1] * modifier * qty) - labour_done))
					print('Not enough {} labour done today for production. Will attempt to hire a worker for {} hours.'.format(requirement[0][0], required_hours))
					#print('Price: {}'.format(world.price('Cultivator'))) # TODO Fix error this gives
					self.accru_wages(job=requirement[0][0], counterparty=1, wage=5, labour_hours=required_hours) # TODO Fix counterparty and price
					#return
			if requirement[0][1] == 'Time':
				time_required = True
				if v: print('Time Required: {}'.format(time_required))
		ledger.reset()
		if time_required:
			produce_entry = [ ledger.get_event(), self.entity, world.now, item + ' in process', item, price, qty, 'WIP Inventory', 'Goods Produced', price * qty ]
		else:
			if account is None:
				account = 'Inventory'
			produce_entry = [ ledger.get_event(), self.entity, world.now, item + ' produced', item, price, qty, account, 'Goods Produced', price * qty ]
		produce_event = [produce_entry]
		ledger.journal_entry(produce_event)
		#return labour_done # TODO This shouldn't be needed as it is covered by pay_salary()

	def wip_check(self):
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of WIP Inventory txns
		wip_txns = ledger.gl[(ledger.gl['debit_acct'] == 'WIP Inventory') & (~ledger.gl['event_id'].isin(rvsl_txns))]
		if not wip_txns.empty:
			# Compare the gl dates to the WIP time from the items table
			items_time = world.items[world.items['requirements'].str.contains('Time', na=False)]
			for index, wip_lot in wip_txns.iterrows():
				item = wip_lot.loc['item_id']
				requirements = [x.strip() for x in items_time['requirements'][item].split(',')]
				for i, requirement in enumerate(requirements):
					if requirement == 'Time':
						break
				amounts = [x.strip() for x in items_time['amount'][item].split(',')]
				amounts = list(map(float, amounts))
				lifespan = amounts[i]
				date_done = (datetime.datetime.strptime(wip_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=lifespan)).date()
				# If the time elapsed has passed
				if date_done == world.now:
					# Book the entry to move from WIP to Inventory
					wip_entry = [[ wip_lot[0], wip_lot[1], world.now, wip_lot[4] + ' produced', wip_lot[4], wip_lot[5], wip_lot[6] or '', 'Inventory', wip_lot[7], wip_lot[9] ]]
					ledger.journal_entry(wip_entry)
			

	def capitalize(self, amount):
		capital_entry = [ ledger.get_event(), self.entity, self.world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', amount ]
		capital_event = [capital_entry]
		ledger.journal_entry(capital_event)

	def auth_shares(self, ticker, qty=None, counterparty=None):
		if counterparty is None:
			counterparty = self.entity
		if qty is None:
			qty = 1000000
		auth_shares_entry = [ ledger.get_event(), counterparty, self.world.now, 'Authorize shares', ticker, '', qty, 'Shares', 'Info', 0 ]
		auth_shares_event = [auth_shares_entry]
		ledger.journal_entry(auth_shares_event)

	def buy_shares(self, ticker, price, qty, counterparty):
		self.transact(ticker, price, qty, counterparty, 'Investments', 'Shares')

	# TODO Add logic triggers so individuals will incorporate companies on their own
	def incorporate(self, ticker, price, qty, counterparty):
		# TODO Add entity creation
		self.auth_shares(ticker, counterparty)
		self.buy_shares(ticker, price, qty, counterparty)
		return 4

	def claim_land(self, qty, price, item='Land'): # QTY in square meters
		ledger.set_entity(0)
		unused_land = ledger.get_qty(items=item)#, accounts=['Natural Wealth'])
		ledger.reset()
		#print('Unused Land: {}'.format(unused_land))
		if unused_land >= qty:
			claim_land_entry = [ ledger.get_event(), self.entity, self.world.now, 'Claim land', item, price, qty, 'Land', 'Natural Wealth', qty * price ]
			claim_land_event = [claim_land_entry]
			ledger.journal_entry(claim_land_event)
		else:
			print('Not enough {} available to claim.'.format(item))

	def pay_wages(self, job, counterparty):
		ledger.set_entity(self.entity)
		wages_payable = abs(ledger.balance_sheet(accounts=['Wages Payable'], item=job))
		labour_hours = abs(ledger.get_qty(items=job, accounts=['Wages Payable']))
		ledger.reset()
		print('Wages Payable: {}'.format(wages_payable))
		#print('Labour Hours: {}'.format(labour_hours))
		if wages_payable:
			# TODO Add check if enough cash, if not becomes salary payable
			wages_pay_entry = [ ledger.get_event(), self.entity, world.now, job + ' wages paid', job, wages_payable / labour_hours, labour_hours, 'Wages Payable', 'Cash', wages_payable ]
			wages_chg_entry = [ ledger.get_event(), counterparty, self.world.now, job + ' wages received', job, wages_payable / labour_hours, labour_hours, 'Cash', 'Wages Receivable', wages_payable ]
			pay_wages_event = [wages_pay_entry, wages_chg_entry]
			ledger.journal_entry(pay_wages_event)
			return 0# labour_hours
		#else:
			#print('No wages to pay for {} work.'.format(job))

	def accru_wages(self, job, counterparty, wage, labour_hours):
		check_wages = True # TODO Add check_wages() function to ensure wages have not gone unpaid too long
		if check_wages:
			# TODO Add check if enough cash, if not becomes salary payable
			wages_exp_entry = [ ledger.get_event(), self.entity, world.now, job + ' wages to be paid', job, wage, labour_hours, 'Wages Expense', 'Wages Payable', wage * labour_hours ]
			wages_rev_entry = [ ledger.get_event(), counterparty, self.world.now, job + ' wages to be received', job, wage, labour_hours, 'Wages Receivable', 'Wages Revenue', wage * labour_hours ]
			accru_wages_event = [wages_exp_entry, wages_rev_entry]
			ledger.journal_entry(accru_wages_event)
			return labour_hours
		else:
			print('Wages have no been paid for {} recently.'.format(job))

	def hire_worker(self, job, counterparty, price=0, qty=1):
		hire_worker_entry = [ ledger.get_event(), self.entity, self.world.now, 'Hired ' + job, job, price, qty, 'Worker Info', 'Hire Worker', 0 ]
		hire_worker_event = [hire_worker_entry]
		ledger.journal_entry(hire_worker_event)
		return 1

	def fire_worker(self, job, counterparty, price=0, qty=-1):
		fire_worker_entry = [ ledger.get_event(), self.entity, self.world.now, 'Fired ' + job, job, price, qty, 'Worker Info', 'Fire Worker', 0 ]
		fire_worker_event = [fire_worker_entry]
		ledger.journal_entry(fire_worker_event)
		return 1

	def check_salary(self, job, counterparty):
		# TODO Check all jobs
		 # TODO Get price and counterparty from hiring of worker
		ledger.set_entity(self.entity)
		worker_state = ledger.get_qty(items=job, accounts=['Worker Info'])
		ledger.reset()
		if worker_state:
			worker_state = int(worker_state)
		#print('Worker State: {}'.format(worker_state))
		if not worker_state:
			return 0
		for _ in range(worker_state):
			self.pay_salary(job, counterparty)

	def pay_salary(self, job, counterparty, salary=None, labour_hours=None): # TODO Fix defaults
		if salary is None:
			salary = 10
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
			print('Not enough cash to pay for {}: {}'.format(job, cash))

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
		# TODO Should check all active services and pay them with a check_service() function
		 # TODO Get price and counterparty from service order
		ledger.set_entity(self.entity)
		service_state = ledger.get_qty(items=item, accounts=['Service Info'])
		ledger.reset()
		if service_state:
			service_state = int(service_state)
		#print('Service State: {}'.format(service_state))
		if not service_state:
			return 0
		for _ in range(service_state):
			pay_service_entry = [ ledger.get_event(), self.entity, self.world.now, 'Payment for ' + item, item, price, qty, 'Service Expense', 'Cash', price ]
			charge_service_entry = [ ledger.get_event(), counterparty, self.world.now, 'Received payment for ' + item, item, price, qty, 'Cash', 'Service Revenue', price ]
			pay_service_event = [pay_service_entry, charge_service_entry]
			ledger.journal_entry(pay_service_event)
		return 0

	def collect_material(self, item, qty, price=1, account=None): # TODO Make cost based on time spent and salary
		if account is None:
			account = 'Inventory'
		collect_mat_entry = [ ledger.get_event(), self.entity, self.world.now, 'Forage ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		collect_mat_event = [collect_mat_entry]
		ledger.journal_entry(collect_mat_event)
		return qty * 1 # TODO Spend time collecting food, wood, ore

	def find_item(self, item, qty, price=1, account=None): # Assuming all materials found
		if account is None:
			account = 'Equipment'
		find_item_entry = [ ledger.get_event(), self.entity, self.world.now, 'Find ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		find_item_event = [find_item_entry]
		ledger.journal_entry(find_item_event)
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
			# TODO Lookup to items DataFrame
			cur = ledger.conn.cursor()
			lifespan = cur.execute('SELECT lifespan FROM items WHERE item_id = ?;', (item,)).fetchone()[0]
			metric = cur.execute('SELECT metric FROM items WHERE item_id = ?;', (item,)).fetchone()[0]
			cur.close()
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
			depreciation_entry = [ ledger.get_event(), self.entity, self.world.now, 'Depreciation of ' + item, item, '', '', 'Depreciation Expense', 'Accumulated Depreciation', dep_amount ]
			depreciation_event = [depreciation_entry]
			ledger.journal_entry(depreciation_event)

		if (metric == 'spoilage') or (metric == 'obsolescence'):
			#print('Spoilage: {} {} days {}'.format(item, lifespan, metric))
			rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			# Get list of Inventory txns
			inv_txns = ledger.gl[(ledger.gl['debit_acct'] == 'Inventory') & (ledger.gl['item_id'] == item) & (~ledger.gl['event_id'].isin(rvsl_txns))]
			if not inv_txns.empty:
				# Compare the gl dates to the lifetime from the items table
				items_spoil = world.items[world.items['metric'].str.contains('spoilage', na=False)]
				lifespan = items_spoil['lifespan'][item]
				for index, inv_lot in inv_txns.iterrows():
					date_done = (datetime.datetime.strptime(inv_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=lifespan)).date()
					# If the time elapsed has passed
					if date_done == world.now:
						# Book thes spoilage entry
						spoil_entry = [[ inv_lot[0], inv_lot[1], world.now, inv_lot[4] + ' spoilage', inv_lot[4], inv_lot[5], inv_lot[6] or '', 'Spoilage Expense', 'Inventory', inv_lot[9] ]]
						ledger.journal_entry(spoil_entry)

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
		entity_data = [ (name,0.0,1,100,0.5,'iex','Hunger,Thirst','100,100','1,2','40,60','50,100',None,'Labour') ] # Note: The 2nd to 5th values are for another program
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
		decay_rate = self.needs[need]['Decay Rate'] * -1
		#print('{} Decay Rate: {}'.format(need, decay_rate))
		self.set_need(need, decay_rate)
		return decay_rate

	def threshold_check(self, need):
		if self.needs[need]['Current Need'] <= self.needs[need]['Threshold']:
			print('{} Threshold met!'.format(need))
			self.address_need(need)

	def address_need(self, need): # TODO This needs a demand system
		items_info = accts.get_items()
		items_info = items_info[items_info['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
		items_info = items_info.sort_values(by='satisfy_rate', ascending=False)
		items_info.reset_index(inplace=True)
		item_choosen = items_info['item_id'].iloc[0]
		satisfy_rate = items_info['satisfy_rate'].iloc[0]

		item_type = self.get_base_item(item_choosen)
		#print('Item Type: {}'.format(item_type))

		if item_type == 'Service':
			ledger.set_entity(self.entity)
			service_state = ledger.get_qty(items=item_choosen, accounts=['Service Info'])
			ledger.reset()
			if service_state:
				self.needs[need]['Current Need'] = self.needs[need]['Max Need']
			else:
				self.order_service(item_choosen, counterparty=2, price=3)
		else:
			need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
			#print('Need Needed: {}'.format(need_needed))
			qty_needed = math.ceil(need_needed / satisfy_rate)
			#print('QTY Needed: {}'.format(qty_needed))
			ledger.set_entity(self.entity)
			qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
			ledger.reset()
			if qty_held < qty_needed:
				qty_purchase = qty_needed - qty_held
				#print('QTY Purchase: {}'.format(qty_purchase))
				#self.purchase(item_choosen, price=world.food_price, qty=100, counterparty=2) # TODO Change to transact() function
				self.transact(item_choosen, price=world.food_price, qty=qty_purchase, counterparty=2)#, buy_acct='Inventory', sell_acct='Inventory')
				ledger.set_entity(self.entity)
				qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
				ledger.reset()
				#print('QTY Held: {}'.format(qty_held))
			# TODO Maybe have consume() return how much was consumed and need adjustment calculated here
			if qty_held:
				self.consume(item_choosen, qty_held, need)

class Organization(Entity):
	def __init__(self, name, world):
		super().__init__(name, world)
		entity_data = [ (name,0.0,1,100,0.5,'iex',None,None,None,None,None,1000000,'Food') ] # Note: The 2nd to 5th values are for another program
		self.entity = accts.add_entity(entity_data)
		self.name = entity_data[0][0] # TODO Change this to pull from entities table
		print('Create Organization: {} | entity_id: {}'.format(self.name, self.entity))
		ledger.set_entity(self.entity)
		self.food = ledger.get_qty(items='Food', accounts=['Inventory'])
		ledger.reset()
		print('Starting Farm Food: {}'.format(self.food))

	# TODO Add subclasses to Organization() for company, non-profits, and government


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-p', '--player', action="store_true", help='Turn on player interaction.')
	# TODO Add an argparse for number of individuals to create
	args = parser.parse_args()
	if args.database is None:
		args.database = 'econ01.db'

	print(time_stamp() + 'Start Econ Sim')
	if (args.delay is not None) and (args.delay is not 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
	delete_db(args.database)
	accts = Accounts(conn=args.database) #TODO Fix init of accounts
	ledger = Ledger(accts) # TODO Move this into init for World()
	world = World(args.player)

	while True:
		world.update_econ()
		if world.end:
			break
		time.sleep(args.delay)

	print(time_stamp() + 'End of Econ Sim')


exit()


# Notes for factory functions
def g():
    return B()

def f(): # Singleton
    if f.obj is None:
        f.obj = A()
    return f.obj

f.obj = None


# import pygame, sys
# from pygame.locals import *

# pygame.init()
# pygame.display.set_mode((100,100))

# while True:
#    for event in pygame.event.get():
#       if event.type == QUIT: sys.exit()
#       if event.type == KEYDOWN and event.dict['key'] == 50:
#          print 'break'
#    pygame.event.pump()

   # http://forums.xkcd.com/viewtopic.php?t=99890
