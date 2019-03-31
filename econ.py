from acct import Accounts
from acct import Ledger
import pandas as pd
import collections
import itertools
import argparse
import datetime
import random
import time
import math
import os
import re

DISPLAY_WIDTH = 98#134#
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

MAX_HOURS = 12

def time_stamp():
	time_stamp = datetime.datetime.now().strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

def delete_db(db_name=None): # TODO Test and fix this for long term
	if db_name is None:
		db_name = 'econ01.db'
	db_path = 'db/'
	if os.path.exists(db_path + db_name):
		os.remove(db_path + db_name)
		print(time_stamp() + 'Database file reset: {}'
			.format(db_path + db_name))
	else:
		print(time_stamp() + 'The database file does not exist at {}.'
			.format(db_path + db_name))

econ_accts = [
	('Cash','Asset'),
	('Info','Admin'),
	('Natural Wealth','Wealth'),
	('Investments','Asset'),
	('Shares','Wealth'),
	('Land','Asset'),
	('Buildings','Asset'),
	('Building Produced','Revenue'),
	('Equipment','Asset'),
	('Machine','Equipment'),
	('Tools','Equipment'),
	('Furniture','Equipment'),
	('Inventory','Asset'),
	('WIP Inventory','Asset'),
	('WIP Equipment','Asset'),
	('Building Under Construction','Asset'),
	('In Use','Asset'),
	('Commodities','Inventory'),
	('Goods Produced','Revenue'),
	('Goods Consumed','Expense'),
	('Salary Expense','Expense'),
	('Salary Revenue','Revenue'),
	('Wages Payable','Liability'),
	('Wages Expense','Expense'),
	('Wages Receivable','Asset'),
	('Wages Revenue','Revenue'),
	('Depreciation Expense','Expense'),
	('Accumulated Depreciation','Asset'),
	('Loss on Impairment','Expense'),
	('Accumulated Impairment Losses','Asset'),
	('Spoilage Expense','Expense'),
	('Worker Info','Info'),
	('Hire Worker','Info'),
	('Fire Worker','Info'),
	('Start Job','Info'),
	('Quit Job','Info'),
	('Subscription Info','Info'),
	('Order Subscription','Info'),
	('Sell Subscription','Info'),
	('End Subscription','Info'),
	('Cancel Subscription','Info'),
	('Subscription Expense','Expense'),
	('Subscription Revenue','Revenue'),
	('Service Info','Info'),
	('Service Available','Info'),
	('Service Expense','Expense'),
	('Service Revenue','Revenue'),
	('Dividend Receivable','Asset'),
	('Dividend Income','Revenue'),
	('Dividend Payable','Liability'),
	('Dividend Expense','Expense'),
	('Education','Asset'),
	('Studying Education','Asset'),
	('Education Expense','Expense'),
	('Education Produced','Revenue'),
	('Technology','Asset'),
	('Researching Technology','Asset'),
	('Technology Expense','Expense'),
	('Technology Produced','Revenue')
] # TODO Remove div exp once retained earnings is implemented

class World:
	def __init__(self, factory, population):
		self.clear_ledger()
		print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Create World ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))
		self.factory = factory
		if args.items is None:
			items_file = 'data/items.csv'
		self.items = accts.load_items(items_file) # TODO Change config file to JSON
		self.now = datetime.datetime(1986,10,1).date()
		self.end = False
		print(self.now)
		self.demand = pd.DataFrame(columns=['date','entity_id','item_id','qty'])
		self.population = population
		self.create_land('Land', 100000)
		self.create_land('Arable Land', 150000)#32000)
		self.create_land('Forest', 100)
		self.create_land('Rocky Land', 100)
		self.create_land('Mountain', 100)

		self.indiv_items_produced = self.items[self.items['producer'].str.contains('Individual', na=False)].reset_index()
		self.indiv_items_produced = self.indiv_items_produced['item_id'].tolist()
		self.indiv_items_produced = ','.join(self.indiv_items_produced)

		for person in range(1, self.population + 1):
			print('Person: {}'.format(person))
			factory.create(Individual, 'Person-' + str(person), self.indiv_items_produced)

		print()
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
		land_entry = [ ledger.get_event(), 0, self.now, item + ' created', item, '', qty, 'Land', 'Natural Wealth', 0 ]
		land_event = [land_entry]
		ledger.journal_entry(land_event)

	def ticktock(self, ticks=1):
		self.now += datetime.timedelta(days=ticks)
		print(self.now)
		return self.now

	def get_hours(self):
		self.hours = {}
		for individual in factory.get(Individual):
			self.hours[individual.name] = individual.hours
		return self.hours

	def check_end(self, v=False):
		population = len(factory.registry[Individual])
		if v: print('Population: {}'.format(population))
		industry = len(factory.registry[Corporation])
		if v: print('Industry: {}'.format(industry))
		if population <= 0:
			print('Econ Sim ended due to human extinction.')
			self.end = True
		return self.end

	# def cycle_entities(self):
	# 	for typ in factory.registry.keys():
	# 		entities = factory.get(typ)
	# 		entities.append(entities.pop(0))

	def get_price(self, item):
		if item == 'Food':
			price = 10
		elif item == 'Water':
			price = 3
		elif item == 'Arable Land':
			price = 5
		elif item == 'Cultivator':
			price = 10
		elif item == 'Plow':
			price = 100
		elif item == 'Manager':
			price = 4
		elif item == 'Robot Plow':
			price = 1000
		else:
			price = 1
		#print('Price Function: {}'.format(price))
		return price

	def get_needs(self):
		global_needs = []
		for individual in factory.get(Individual):
			global_needs += list(individual.needs.keys())
		global_needs = list(set(global_needs))
		return global_needs

	def update_econ(self):
		t1_start = time.perf_counter()
		if str(self.now) == '1986-10-01':
			# TODO Pull shares authorized from entities table
			for individual in factory.get(Individual):
				individual.capitalize(amount=12000) # Hardcoded for now

		# TODO Maybe an update_world() method to adjust the needs and time
		print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Econ Updated ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))

		self.ticktock()
		self.check_end(v=True)
		if self.end:
			return
		t2_start = time.perf_counter()
		self.global_needs = self.get_needs() # TODO Iterate through global needs instead of the needs for each individual when checking if a corp is needed
		for individual in factory.get(Individual):
			print('Individual: {} | {}'.format(individual.name, individual.entity_id))
			individual.reset_hours()
			for need in individual.needs:
				#print('Need: {}'.format(need))
				individual.corp_needed(need=need)
				individual.item_demanded(need=need)
			for index, item in world.demand.iterrows():
				#print('Corp Check Demand Item: {}'.format(item['item_id']))
				individual.corp_needed(item=item['item_id'], demand_index=index)
		t2_end = time.perf_counter()
		print(time_stamp() + '2: Individual check took {:,.2f} min.'.format((t2_end - t2_start) / 60))
		print()
		print('World Demand Start: \n{}'.format(world.demand))
		print()
		# print(ledger.get_qty(['Rock','Wood','Paper','Food'], ['Inventory'], show_zeros=True, by_entity=True)) # Temp for testing
		# print()

		t3_start = time.perf_counter()
		for typ in factory.registry.keys():
			#print('Entity Type: {}'.format(typ))
			for entity in factory.get(typ):
				#print('Entity: {}'.format(entity))
				#print('Entity Name: {} | {}'.format(entity.name, entity.entity_id))
				t3_1_start = time.perf_counter()
				entity.depreciation_check()
				t3_1_end = time.perf_counter()
				print(time_stamp() + '3.1: Dep check took {:,.2f} sec for {}.'.format((t3_1_end - t3_1_start), entity.name))
				t3_2_start = time.perf_counter()
				entity.wip_check()
				t3_2_end = time.perf_counter()
				print(time_stamp() + '3.2: WIP check took {:,.2f} sec for {}.'.format((t3_2_end - t3_2_start), entity.name))
				t3_3_start = time.perf_counter()
				entity.check_subscriptions()
				t3_3_end = time.perf_counter()
				print(time_stamp() + '3.3: Sub check took {:,.2f} sec for {}.'.format((t3_3_end - t3_3_start), entity.name))
				t3_4_start = time.perf_counter()
				entity.check_salary()
				t3_4_end = time.perf_counter()
				print(time_stamp() + '3.4: Sal check took {:,.2f} sec for {}.'.format((t3_4_end - t3_4_start), entity.name))
				t3_5_start = time.perf_counter()
				entity.pay_wages()
				t3_5_end = time.perf_counter()
				print(time_stamp() + '3.5: Wag check took {:,.2f} sec for {}.'.format((t3_5_end - t3_5_start), entity.name))
		t3_end = time.perf_counter()
		print(time_stamp() + '3: Entity check took {:,.2f} min.'.format((t3_end - t3_start) / 60))
		print()

		t4_start = time.perf_counter()
		print('Check Demand List:')
		for entity in factory.get_all():#(Corporation):
			#print('Entity Name: {} | {}'.format(entity.name, entity.entity_id))
			entity.tech_motivation()
			entity.check_demand()
			entity.check_inv()
		t4_end = time.perf_counter()
		print(time_stamp() + '4: Demand list check took {:,.2f} min.'.format((t4_end - t4_start) / 60))
		print()
		t5_start = time.perf_counter()
		print('Check Optional Items:')
		for entity in factory.get_all():#(Corporation):
			#print('Entity Name: {} | {}'.format(entity.name, entity.entity_id))
			entity.check_optional()
			entity.check_inv()
			if type(entity) == Corporation:
				entity.dividend()
		t5_end = time.perf_counter()
		print(time_stamp() + '5: Optional check took {:,.2f} min.'.format((t5_end - t5_start) / 60))
		print()

		t6_start = time.perf_counter()
		 # TODO Fix assuming all individuals have the same needs
		for need in individual.needs:
			for individual in factory.get(Individual):
				#print('Individual Name: {} | {}'.format(individual.name, individual.entity_id))
				individual.threshold_check(need)
				individual.need_decay(need)
				print('{} {} Need: {}'.format(individual.name, need, individual.needs[need]['Current Need']))
				if individual.dead:
					break
		t6_end = time.perf_counter()
		print(time_stamp() + '6: Needs check took {:,.2f} min.'.format((t6_end - t6_start) / 60))
		print()

		if self.check_end():
			return

		t7_start = time.perf_counter()
		for typ in factory.registry.keys():
			for entity in factory.get(typ):
				if typ == Corporation: # TODO Temp fix for negative balances
					entity.negative_bal()
				ledger.set_entity(entity.entity_id)
				if 'Farm' in entity.name:
					entity.food = ledger.get_qty(items='Food', accounts=['Inventory'])
					print('{} Food: {}'.format(entity.name, entity.food))
				print('{} Cash: {}'.format(entity.name, ledger.balance_sheet(['Cash'])))
				ledger.reset()

			# Move first entity in list to the end, to switch things up
			if len(factory.registry[typ]) != 0:
				lst = factory.get(typ)
				lst.append(lst.pop(0))

		t7_end = time.perf_counter()
		print(time_stamp() + '7: Cash check took {:,.2f} min.'.format((t7_end - t7_start) / 60))

		# For testing to kill individuals
		# for individual in factory.get(Individual):
		# 	if str(self.now) == '1986-10-05' and individual.entity_id == 3:
		# 		individual.set_need('Hunger', -100, forced=True)

		# For testing to create individuals
		# if str(self.now) == '1986-10-03':
		# 	self.entities = accts.get_entities()
		# 	last_entity_id = self.entities.reset_index()['entity_id'].max()
		# 	print('Last Entity ID: {}'.format(last_entity_id))
		# 	factory.create(Individual, 'Person ' + str(last_entity_id + 1), self.indiv_items_produced)
		# 	individual = factory.get_by_id(last_entity_id + 1)
		# 	individual.capitalize(amount=25000) # Hardcoded for now

		if str(self.now) == '1986-10-10':
			individual.use_item('Rock', uses=1, counterparty=factory.get_by_name('Farm'), target='Plow')

		if args.random:
			if random.randint(1, 20) == 20:# or (str(self.now) == '1986-10-02'):
				individual.birth()

		if args.random:
			if random.randint(1, 40) == 40:# or (str(self.now) == '1986-10-03'):
				print('{} randomly dies!'.format(individual.name))
				individual.set_need('Hunger', -100, forced=True)

		print()
		print('World Demand End: \n{}'.format(world.demand))
		print()
		print(ledger.get_qty(['Wood Chips'], ['Inventory'], show_zeros=True, by_entity=True)) # Temp for testing #['Rock','Wood','Paper','Food']
		print()

		# if str(self.now) == '1986-10-12': # For debugging
		# 	world.end = True

		t1_end = time.perf_counter()
		print(time_stamp() + 'End of Econ Update. It took {:,.2f} min.'.format((t1_end - t1_start) / 60))

class Entity:
	def __init__(self, name):
		self.name = name
		#print('Entity created: {}'.format(name))

	def transact(self, item, price, qty, counterparty, acct_buy='Inventory', acct_sell='Inventory', item_type=None, buffer=False):
		if qty == 0:
			return
		purchase_event = []
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		#print('Cash: {}'.format(cash))
		ledger.set_entity(counterparty.entity_id)
		qty_avail = ledger.get_qty(items=item, accounts=[acct_sell])
		#print('QTY Available: {}'.format(qty_avail))
		ledger.reset()
		if cash >= (qty * price):
			#print('Transact Item Type: {}'.format(item_type))
			if qty <= qty_avail or item_type == 'Service':
				print('{} transacted with {} for {} {}'.format(self.name, counterparty.name, qty, item))
				purchase_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' purchased', item, price, qty, acct_buy, 'Cash', price * qty ]
				sell_entry = [ ledger.get_event(), counterparty.entity_id, world.now, item + ' sold', item, price, qty, 'Cash', acct_sell, price * qty ]
				purchase_event += [purchase_entry, sell_entry]
				if buffer:
					return purchase_event
				ledger.journal_entry(purchase_event)
				return True
			else:
				print('{} does not have enough {} on hand to sell {} units of {}.'.format(self.name, item, qty, item))
				if buffer:
					return purchase_event
				if not buffer:
					return False
		else:
			print('{} does not have enough cash to purchase {} units of {}.'.format(self.name, qty, item))
			if buffer:
				return purchase_event
			if not buffer:
				return False

	def purchase(self, item, qty, acct_buy='Inventory', acct_sell='Inventory', buffer=False):
		if qty == 0:
			return
		qty = math.ceil(qty)
		qty_wanted = qty
		# TODO Add support for purchasing from multiple entities
		outcome = None
		item_type = self.get_item_type(item)
		if item_type == 'Service':
			# Check if producer exists and get their ID
			# TODO Support multiple of the same producer
			producers = world.items.loc[item, 'producer']
			if isinstance(producers, str):
				producers = [x.strip() for x in producers.split(',')]
			producers = list(set(filter(None, producers)))
			producer = producers[0] # TODO Better handle multiple producers
			counterparty = factory.get_by_name(producer)
			if counterparty is None:
				print('No {} to offer {} service. Will add it to the demand table for {}.'.format(producer, item, self.name))
				self.item_demanded(item, qty)
				return
			acct_buy = 'Service Expense'
			acct_sell = 'Service Revenue'
		ledger.reset()
		global_qty = ledger.get_qty(items=item, accounts=['Inventory'])
		print('Global qty of {} available for purchase: {} Looking for: {}'.format(item, global_qty, qty))

		# Always buy some that is available
		if global_qty != 0:
			qty = min(global_qty, qty)

		if global_qty >= qty or item_type == 'Service': # TODO Is this needed?
			# Check which entity has the goods for the cheapest
			if item_type != 'Service':
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Inventory') & (ledger.gl['item_id'] == item) ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				#print('Purchase TXNs: \n{}'.format(txns))
				counterparty = self.get_counterparty(txns, rvsl_txns, item, 'Inventory')
				global_inv = ledger.get_qty(item, ['Inventory'], by_entity=True)
				if global_inv.empty:
					print('No counterparty exists for {}.'.format(item))
					return
				global_inv.sort_values(by=['qty'], ascending=False, inplace=True)
				#print('Global Inv: \n{}'.format(global_inv))
				i = 0
				result = False
				purchased_qty = 0
				if buffer:
					result = []
				while qty > 0:
					#print('QTY: {}'.format(qty))
					counterparty_id = global_inv.iloc[i].loc['entity_id']
					#print('Counterparty ID: {}'.format(counterparty_id))
					counterparty = factory.get_by_id(counterparty_id)
					#print('Purchase Counterparty: {}'.format(counterparty.name))
					if counterparty.entity_id == self.entity_id:
						print('{} unable to transact with themselves.'.format(self.name))
						return
					try:
						purchase_qty = global_inv.iloc[i].loc['qty']
					except IndexError as e:
						print('No other entities hold {} to purchase the remaining qty of {}.'.format(item, qty))
						break
					if purchase_qty > qty:
						purchase_qty = qty
					#print('Purchase QTY: {}'.format(purchase_qty))
					result += self.transact(item, price=world.get_price(item), qty=purchase_qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=buffer)
					if not result:
						break
					purchased_qty += purchase_qty
					qty -= purchase_qty
					i += 1
				if qty_wanted > purchased_qty:
					self.item_demanded(item, qty_wanted - purchased_qty)
			elif item_type == 'Service':
				print('{} trying to purchase Service: {}'.format(self.name, item))
				#if buffer:
					#outcome = counterparty.produce_entries(item=item, qty=qty, price=world.get_price(item))
				#else:
				outcome, req_time_required = counterparty.produce(item, qty, buffer=buffer)
				#print('Outcome: \n{}'.format(outcome))
				if not outcome:
					return
				try:
					self.adj_needs(item, qty)
				except AttributeError as e:
					#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
					pass
				result = self.transact(item, price=world.get_price(item), qty=qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=buffer)
				#print('Purchase Result: {} {} \n{}'.format(qty, item, result))
				if result is None:
					result = []
				if outcome and buffer:
					result = outcome + result
				#print('Buffer Result: \n{}'.format(result))
			return result
		else:
			print('Not enough quantity of {} to purchase {} units for {}.'.format(item, qty, self.name))
			producer = world.items.loc[item]['producer']
			#print('Producer: {}'.format(producer))
			if producer is not None: # For items like land
				directly_needed_items = world.items.loc[world.items['satisfies'].isin(world.global_needs)] # TODO Make able to support items that satisfy multiple needs
				if item not in directly_needed_items.index:
					self.item_demanded(item, qty)

	# TODO Use historical price
	# TODO Make qty wanting to be consumed smarter (this is to be done in the world)
	def consume(self, item, qty, need=None, buffer=False):
		if qty == 0:
			return
		ledger.set_entity(self.entity_id)
		qty_held = ledger.get_qty(items=item, accounts=['Inventory'])
		ledger.reset()
		#print('QTY Held: {} {}'.format(qty_held, item))
		if (qty_held >= qty) or buffer:
			#print('Consume: {} {}'.format(qty, item))
			price = world.get_price(item)
			consume_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' consumed', item, price, qty, 'Goods Consumed', 'Inventory', price * qty ]
			consume_event = [consume_entry]
			if buffer:
				return consume_event
			ledger.journal_entry(consume_event)
			self.adj_needs(item, qty) # TODO Add error checking
			return
		else:
			print('{} does not have enough {} on hand to consume {} units of {}.'.format(self.name, item, qty, item))

	def in_use(self, item, qty, price, account, buffer=False):
		ledger.set_entity(self.entity_id)
		qty_held = ledger.get_qty(items=item, accounts=[account])
		ledger.reset()
		if (qty_held >= qty) or buffer:
			in_use_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' in use', item, price, qty, 'In Use', account, price * qty ]
			in_use_event = [in_use_entry]
			if buffer:
				return in_use_event
			ledger.journal_entry(in_use_event)
			try:
				self.adj_needs(item, qty)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				return True
		else:
			print('{} does not have enough {} available to use.'.format(self.name, item))

	def use_item(self, item, uses=1, counterparty=None, target=None, buffer=False, check=False):
		if counterparty is not None and target is not None:
			dmg_type = world.items['dmg_type'][item] # Does not support more than one dmg_type on the attack
			dmg = world.items['dmg'][item]
			if dmg is None:
				dmg = 0
			dmg = float(dmg)
			if dmg_type is not None:
				res_types = [x.strip() for x in world.items['res_type'][item].split(',')]
				for i, res_type in enumerate(res_types):
					if res_type == dmg_type:
						break
				res = [x.strip() for x in world.items['res'][item].split(',')]
				res = list(map(float, res))
				resilience = res[i]
			else:
				resilience = world.items['res'][target]
			if resilience is None:
				resilience = 0
			resilience = float(resilience)
			print('Attack Dmg: {} | Target Resilience: {}'.format(dmg, resilience))
			reduction = dmg / resilience
			if reduction > 1:
				reduction = 1
			for n in range(uses):
				#target_type = self.get_item_type(target)
				ledger.set_entity(counterparty.entity_id)
				target_bal = ledger.balance_sheet(accounts=['Buildings','Equipment','Accumulated Depreciation','Accumulated Impairment Losses'], item=target)
				asset_cost = ledger.balance_sheet(accounts=['Buildings','Equipment'], item=target)
				# accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
				# accum_imp_bal = ledger.balance_sheet(accounts=['Accumulated Impairment Losses'], item=item)
				# accrum_reduction = abs(accum_dep_bal) + abs(accum_imp_bal)
				# target_bal = asset_cost - accrum_reduction
				print('Target Balance: {}'.format(target_bal))
				ledger.reset()
				impairment_amt = asset_cost * reduction
				if target_bal < impairment_amt:
					impairment_amt = target_bal
				counterparty.impairment(target, impairment_amt)

		# In both cases using the item still uses existing logic
		incomplete, use_event, time_required = self.fulfill(item, qty=uses, reqs='usage_req', amts='use_amount', check=check)
		# TODO Book journal entries within function and add buffer argument
		if incomplete or check:
			return
		orig_uses = uses
		lifespan = world.items['lifespan'][item]
		metric = world.items['metric'][item]
		if metric == 'usage':
			entries, uses = self.depreciation(item, lifespan, metric, uses, buffer)
			if entries:
				use_event += entries
				if orig_uses != uses:
					print('{} could not use {} {} as requested; was used {} times.'.format(self.name, item, orig_uses, uses))
				try:
					self.adj_needs(item, uses)
				except AttributeError as e:
					#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
					return use_event
				return use_event
		else:
			try:
				self.adj_needs(item, uses)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				pass
			if not use_event and not incomplete:
				#print('{} has no requirements in order to be used by {}.'.format(item, self.name))
				return True
			return use_event

	def check_productivity(self, item, v=False):
		equip_list = ledger.get_qty(accounts=['Equipment'])
		if v: print('Equip List: \n{}'.format(equip_list))
		if equip_list.empty:
			return None, None
		if v: print('Productivity Item Check: {}'.format(item))
		items_info = world.items[world.items['productivity'].str.contains(item, na=False)]
		efficiencies = []
		for index, item_row in items_info.iterrows():
			productivity = [x.strip() for x in item_row['productivity'].split(',')]
			for i, productivity_item in enumerate(productivity):
				if productivity_item == item:
					break
			efficiencies_list = [x.strip() for x in item_row['efficiency'].split(',')]
			efficiency = efficiencies_list[i]
			efficiencies.append(efficiency)
		efficiencies = pd.Series(efficiencies)
		if v: print('Productivity Efficiencies: \n{}'.format(efficiencies))
		items_info = items_info.assign(efficiencies=efficiencies.values)
		items_info.reset_index(inplace=True)
		if v: print('Items Info: \n{}'.format(items_info))
		if not equip_list.empty and not items_info.empty:
			equip_info = equip_list.merge(items_info)
			equip_info.sort_values(by='efficiencies', ascending=False, inplace=True)
			equip_info = equip_info.reset_index(drop=True)
			if v: print('Items Info Merged: \n{}'.format(equip_info))
			# equip_qty = float(equip_info['qty'].iloc[0])
			# equip_capacity = float(equip_info['capacity'].iloc[0])
			# if v: print('Equip Capacity: {}'.format(equip_capacity))
			# TODO Consider how to factor in equipment capacity and WIP time
			modifier = float(equip_info['efficiencies'].iloc[0])
			if v: print('Modifier: {}'.format(modifier))
			# coverage = (req_qty * modifier * qty) // equip_capacity
			# print('Charges: {}'.format(coverage))
			# Book deprecition on use of item
			print('{} used {} equipment to do {} task better by {}.'.format(self.name, equip_info['item_id'].iloc[0], item, modifier))
			return modifier, equip_info
		return None, None

	def get_item_type(self, item):
		if item in ['Land','Labour','Job','Equipment','Buildings','Subscription','Service','Commodity','Components','Technology','Education','Time','None']:
			return item
		else:
			return self.get_item_type(world.items.loc[item, 'child_of'])

	# TODO Proper costing, not to use price parameter
	# TODO Add COGS accounting and proper WIP
	def fulfill(self, item, qty, reqs='requirements', amts='amount', check=False): # TODO Maybe add buffer=True
		v = False
		incomplete = False
		if qty == 0:
			return None, [], None
		event = []
		time_required = False
		orig_hours = world.get_hours()
		if v: print('Orig Hours: \n{}'.format(orig_hours))
		item_info = world.items.loc[item]
		item_type = self.get_item_type(item)
		if v: print('Item Info: \n{}'.format(item_info))
		if item_info[reqs] is None or item_info[amts] is None:
			return None, [], None
		requirements = [x.strip() for x in item_info[reqs].split(',')]
		if v: print('Requirements: {}'.format(requirements))
		requirement_types = [self.get_item_type(requirement) for requirement in requirements]
		if v: print('Requirement Types: {}'.format(requirement_types))
		amounts = [x.strip() for x in item_info[amts].split(',')]
		amounts = list(map(float, amounts))
		if v: print('Requirement Amounts: {}'.format(amounts))
		requirements_details = list(itertools.zip_longest(requirements, requirement_types, amounts))
		if v: print('Requirements Details: {}'.format(requirements_details))
		# TODO Sort so requirements with a capacity are first after time
		for requirement in requirements_details:
			ledger.set_entity(self.entity_id)
			req_item = requirement[0]
			req_item_type = requirement[1]
			req_qty = requirement[2]
			if req_qty is None:
				req_qty = 1
			if v: print('Requirement: {} \n{} \n{} \n{}'.format(requirement, req_item, req_item_type, req_qty))

			if req_item_type == 'Time':
				# TODO Consider how Equipment could reduce time requirements
				time_required = True
				if v: print('Time Required: {}'.format(time_required))

			elif req_item_type == 'Land':
				land = ledger.get_qty(items=req_item, accounts=['Land'])
				if v: print('Land: {}'.format(land))
				if land < (req_qty * qty):
					print('{} does not have enough {} to produce on. Will attempt to claim {} square meters.'.format(self.name, req_item, (req_qty * qty) - land))
					needed_qty = (req_qty * qty) - land
					# Attempt to purchase land
					entries = self.purchase(req_item, req_qty * qty, 'Land', buffer=True)
					if not entries:
						ledger.set_entity(0) # Only try to claim land that is remaining
						land_avail = ledger.get_qty(items=req_item, accounts=['Land'])
						ledger.reset()
						ledger.set_entity(self.entity_id)
						qty_claim = min(needed_qty, land_avail)
						entries = self.claim_land(qty_claim, price=world.get_price(req_item), item=req_item, buffer=True)
						#print('Land Entries: \n{}'.format(entries))
						if not entries:
							entries = []
							incomplete = True
							#return
					event += entries
				if time_required: # TODO Handle land in use during one tick
					entries = self.in_use(req_item, req_qty * qty, world.get_price(req_item), 'Land', buffer=True)
					#print('Land In Use Entries: \n{}'.format(entries))
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries

			elif req_item_type == 'Buildings':
				building = ledger.get_qty(items=req_item, accounts=['Buildings'])
				if v: print('Building: {}'.format(building))
				# Get capacity amount
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None:
					capacity = 1
				capacity = float(capacity)
				print('Building: {} {} | Capacity: {}'.format(building, req_item, capacity))
				if ((building * capacity) / (qty * req_qty)) < 1:
					ledger.reset()
					building += ledger.get_qty(items=req_item, accounts=['Building Under Construction'])
					ledger.set_entity(self.entity_id)
					print('Building Construction: {} {}'.format(building, req_item))
					if building == 0:
						print('{} does not have a {} building to produce in. Will attempt to aquire one.'.format(self.name, req_item))
					else:
						print('{} does not have enough capacity in {} building to produce in. Will attempt to aquire some.'.format(self.name, req_item))
					remaining_qty = (qty * req_qty) - (building * capacity)
					required_qty = math.ceil(remaining_qty / capacity)
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(req_item, required_qty, 'Buildings', buffer=True)
					# TODO Undecided if below produce func should be in final
					if not entries:
						entries, req_time_required = self.produce(req_item, required_qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				building = ledger.get_qty(items=req_item, accounts=['Buildings'])
				qty_to_use = 0
				if building != 0:
					qty_to_use = int(min(building, math.ceil((qty * req_qty) / (building * capacity))))
					print('{} needs to use {} {} times to produce {}.'.format(self.name, req_item, qty_to_use, item))
				if time_required: # TODO Handle building in use during one tick
					entries = self.in_use(req_item, qty_to_use, world.get_price(req_item), 'Buildings', buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				for _ in range(qty_to_use):
					entries = self.use_item(req_item, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries

			elif req_item_type == 'Equipment': # TODO Make generic for process
				equip_qty = ledger.get_qty(items=req_item, accounts=['Equipment'])
				# Get capacity amount
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None:
					capacity = 1
				capacity = float(capacity)
				print('Equipment: {} {} Capacity: {}'.format(equip_qty, req_item, capacity))
				if ((equip_qty * capacity) / (qty * req_qty)) < 1: # TODO Test item with capacity
					ledger.reset()
					equip_qty += ledger.get_qty(items=req_item, accounts=['WIP Equipment'])
					ledger.set_entity(self.entity_id)
					if equip_qty == 0:
						print('{} does not have {} equipment to use. Will attempt to acquire some.'.format(self.name, req_item))
					else:
						print('{} not have enough capacity on {} equipment. Will attempt to aquire some.'.format(self.name, req_item))
					remaining_qty = (qty * req_qty) - (equip_qty * capacity)
					required_qty = math.ceil(remaining_qty / capacity)
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(req_item, required_qty, 'Equipment', buffer=True)
					# TODO Undecided if below produce func should be in final
					if not entries:
						entries, req_time_required = self.produce(req_item, required_qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				equip_qty = ledger.get_qty(items=req_item, accounts=['Equipment'])
				qty_to_use = 0
				if equip_qty != 0:
					qty_to_use = int(min(equip_qty, math.ceil((qty * req_qty) / (equip_qty * capacity))))
				if time_required: # TODO Handle equipment in use during only one tick
					entries = self.in_use(req_item, qty_to_use, world.get_price(req_item), 'Equipment', buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				for _ in range(qty_to_use):
					entries = self.use_item(req_item, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries

			elif req_item_type == 'Components':
				modifier, items_info = self.check_productivity(req_item)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
				else:
					modifier = 0
				component_qty = ledger.get_qty(items=req_item, accounts=['Components'])
				if v: print('Land: {}'.format(component_qty))
				if component_qty < (req_qty * (1-modifier) * qty):
					print('{} does not have enough {} components. Will attempt to aquire some.'.format(self.name, req_item))
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(req_item, req_qty * qty, 'Inventory', buffer=True)
					if not entries:
						# TODO Uncomment below when item config is setup properly
						entries, req_time_required = self.produce(req_item, req_qty * qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				if not check:
					entries += self.consume(req_item, qty=req_qty * qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries

			elif req_item_type == 'Commodity':
				modifier, items_info = self.check_productivity(req_item)
				if modifier:
					entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					if entries is True:
						entries = []
					event += entries
				else:
					modifier = 0
				material_qty = ledger.get_qty(items=req_item, accounts=['Inventory'])
				if v: print('Material Qty: {}'.format(material_qty))
				if material_qty < (req_qty * (1 - modifier) * qty):
					print('{} does not have enough commodity: {}. Will attempt to aquire some.'.format(self.name, req_item))
					# TODO Maybe add logic so that produces wont try and purchase items they can produce
					# Attempt to purchase before producing
					entries = self.purchase(req_item, req_qty * qty, 'Inventory', buffer=True)
					if entries:
						if entries[0][6] < (req_qty * qty):
							#print('Commodity Purchase not all required: \n{} | Required: {}'.format(entries[0][6], req_qty * qty))
							entries = []
							incomplete = True
							# TODO Decide how best to handle when not enough qty is available to be purchased
					if not entries:
						# TODO Uncomment below when item config is setup properly
						entries, req_time_required = self.produce(req_item, qty=req_qty * qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				if not check:
					entries = self.consume(req_item, qty=req_qty * qty, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries

			elif req_item_type == 'Service':
				print('{} will attempt to purchase the {} service.'.format(self.name, req_item))
				entries = self.purchase(req_item, req_qty * qty, buffer=True)
				if not entries:
					# TODO Uncomment below when item config is setup properly
					entries, req_time_required = self.produce(req_item, req_qty * qty, buffer=True)
				if not entries:
					entries = []
					incomplete = True
					#return
				event += entries

			elif req_item_type == 'Subscription': # TODO Add check to ensure payment has been made recently (maybe on day of)
				subscription_state = ledger.get_qty(items=req_item, accounts=['Subscription Info'])
				if v: print('Subscription State for {}: {}'.format(req_item, subscription_state))
				if not subscription_state:
					print('{} does not have {} subscription active. Will attempt to activate it.'.format(self.name, req_item))
					entries = self.order_subscription(item=req_item, counterparty=self.subscription_counterparty(req_item), price=world.get_price(req_item), qty=1, buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries

			elif req_item_type == 'Job':
				if item_type == 'Job' or item_type == 'Labour':
					if type(self) == Individual:
						experience = abs(ledger.get_qty(items=req_item, accounts=['Salary Revenue']))
						if experience < req_qty:
							incomplete = True
							# TODO Add to demand table
							return incomplete, event, time_required
				else:
					workers = ledger.get_qty(items=req_item, accounts=['Worker Info'])
					if v: print('Workers as {}: {}'.format(req_item, worker_state))
					# Get capacity amount
					capacity = world.items.loc[req_item, 'capacity']
					if capacity is None:
						capacity = 1
					capacity = float(capacity)
					print('{} has {} {} available with {} capacity each.'.format(self.name, workers, req_item, capacity))
					if ((workers * capacity) / (qty * req_qty)) < 1:
						remaining_qty = (qty * req_qty) - (workers * capacity)
						required_qty = math.ceil(remaining_qty / capacity)
						if workers <= 0:
							print('{} does not have a {} available to work. Will attempt to hire {}.'.format(self.name, req_item, required_qty))
						else:
							print('{} does not have enough capacity for {} jobs. Will attempt to hire {}.'.format(self.name, req_item, required_qty))
						for _ in range(required_qty):
							entries = self.hire_worker(job=req_item, price=world.get_price(req_item), qty=1, buffer=True)
							if not entries:
								entries = []
								incomplete = True
								#return
							event += entries

			elif req_item_type == 'Labour':
				if item_type == 'Job' or item_type == 'Labour':
					if type(self) == Individual:
						experience = abs(ledger.get_qty(items=req_item, accounts=['Wages Revenue']))
						if experience < req_qty:
							incomplete = True
							# TODO Add to demand table maybe
							return incomplete, event, time_required
				else:
					modifier, items_info = self.check_productivity(req_item)
					if modifier:
						entries = self.use_item(items_info['item_id'].iloc[0], buffer=True)
						if not entries:
							entries = []
							incomplete = True
							#return
						if entries is True:
							entries = []
						event += entries
					else:
						modifier = 0
					ledger.set_start_date(str(world.now))
					labour_done = ledger.get_qty(items=req_item, accounts=['Wages Expense'])
					ledger.reset()
					ledger.set_entity(self.entity_id)
					if v: print('Labour Done: {}'.format(labour_done))
					labour_required = (req_qty * (1-modifier) * qty)
					# Labourer does the amount they can, and get that value from the entries. Then add to the labour hours done and try again
					while labour_done < labour_required:
						required_hours = int(math.ceil((req_qty * (1-modifier) * qty) - labour_done))
						if item_type == 'Education':
							print('{} has not studied enough {} today. Will attempt to study for {} hours.'.format(self.name, req_item, required_hours))
							#MAX_HOURS = 12
							required_hours = min(required_hours, MAX_HOURS)
							counterparty = self
							entries = self.accru_wages(job=req_item, counterparty=counterparty, wage=0, labour_hours=required_hours, buffer=True)
						else:
							print('{} has not had enough {} labour done today for production. Will attempt to hire a worker for {} hours.'.format(self.name, req_item, required_hours))
							counterparty = self.worker_counterparty(req_item)
							if isinstance(counterparty, tuple):
								counterparty, entries = counterparty
								event += entries
							if v: print('Labour Counterparty: {}'.format(counterparty.name))
							entries = self.accru_wages(job=req_item, counterparty=counterparty, wage=world.get_price(req_item), labour_hours=required_hours, buffer=True)
						if not entries:
							entries = []
							incomplete = True
							break
							#return
						event += entries
						if entries:
							labour_done += entries[0][6] # Same as required_hours
							counterparty.set_hours(required_hours)
							if item_type == 'Education':
								break

			elif req_item_type == 'Education':
				if item_type == 'Job' or item_type == 'Labour':
					if type(self) == Individual:
						edu_status = ledger.get_qty(items=req_item, accounts=['Education'])
						print('{} has {} education hours for {} and requires {}'.format(self.name, edu_status, req_item, req_qty))
						if edu_status >= req_qty:
							print('{} has knowledge of {} to create {}.'.format(self.name, req_item, item))
						else:
							print('Studying Education: {}'.format(req_item))
							entries, req_time_required = self.produce(req_item, qty=req_qty, buffer=True)
							if req_time_required:
								edu_status = ledger.get_qty(items=req_item, accounts=['Studying Education'])
								if edu_status == 0:
									self.item_demanded(req_item, req_qty)
							if not entries:
								print('Studying Education not successfull for: {}'.format(req_item))
								entries = []
								incomplete = True
								edu_status = ledger.get_qty(items=req_item, accounts=['Studying Education'])
								if edu_status == 0 and not req_time_required:
									self.item_demanded(req_item, req_qty)
							else:
								edu_status = ledger.get_qty(items=req_item, accounts=['Education'])
								print('Education Status for {}: {}'.format(req_item, edu_status))
								if edu_status == 0:
									entries = []
									incomplete = True
							event += entries

			elif req_item_type == 'Technology':
				ledger.reset()
				tech_status = ledger.get_qty(items=req_item, accounts=['Technology'])
				if tech_status >= req_qty:
					print('{} has knowledge of {} to create {}.'.format(self.name, req_item, item))
				else:
					print('Researching Technology: {}'.format(req_item))
					entries, req_time_required = self.produce(req_item, qty=req_qty, buffer=True)
					if req_time_required:
						tech_status = ledger.get_qty(items=req_item, accounts=['Researching Technology'])
						if tech_status == 0:
							self.item_demanded(req_item, req_qty)
					if not entries:
						print('Tech Researching not successfull for: {}'.format(req_item))
						entries = []
						incomplete = True
						tech_status = ledger.get_qty(items=req_item, accounts=['Researching Technology'])
						if tech_status == 0 and not req_time_required:
							self.item_demanded(req_item, req_qty)
					else:
						tech_status = ledger.get_qty(items=req_item, accounts=['Technology'])
						print('Tech Status for {}: {}'.format(req_item, tech_status))
						if tech_status == 0:
							entries = []
							incomplete = True
					event += entries

			ledger.reset()
		if incomplete:
			for individual in factory.get(Individual):
				if v: print('Reset hours for {} from {} to {}.'.format(individual.name, individual.hours, orig_hours[individual.name]))
				individual.hours = orig_hours[individual.name]
			print('{} cannot produce {} {} at this time.\n'.format(self.name, qty, item))
		return incomplete, event, time_required

	def produce(self, item, qty, debit_acct=None, credit_acct=None, desc=None ,price=None, buffer=False):
		if item not in self.produces: # TODO Should this be kept long term?
			return [], False
		incomplete, produce_event, time_required = self.fulfill(item, qty)
		if incomplete:
			return [], time_required
		item_type = self.get_item_type(item)
		#print('Item Type: {}'.format(item_type))
		if debit_acct is None:
			if item_type == 'Technology':
				debit_acct = 'Technology'
			elif item_type == 'Education':
				debit_acct = 'Education'
			elif item_type == 'Equipment':
				debit_acct = 'Inventory'
			elif item_type == 'Buildings':
				debit_acct = 'Buildings'
			else:
				debit_acct = 'Inventory'
			if time_required:
				if item_type == 'Technology':
					debit_acct = 'Researching Technology'
				elif item_type == 'Education':
					debit_acct='Studying Education'
				elif item_type == 'Equipment':
					debit_acct = 'WIP Equipment'
				elif item_type == 'Buildings':
					debit_acct = 'Building Under Construction'
				else:
					debit_acct = 'WIP Inventory'
		if credit_acct is None:
			if item_type == 'Technology':
				credit_acct = 'Technology Produced'
			elif item_type == 'Education':
				credit_acct = 'Education Produced'
			elif item_type == 'Equipment':
				credit_acct = 'Goods Produced'
			elif item_type == 'Buildings':
				credit_acct = 'Building Produced'
			else:
				credit_acct = 'Goods Produced'
			# if time_required:
			# 	credit_acct = credit_acct
		if desc is None:
			if item_type == 'Technology':
				desc = item + ' researched'
				if time_required:
					desc = 'Researching ' + item
			elif item_type == 'Education':
				desc = item + ' studied'
				if time_required:
					desc = 'Studying ' + item
			elif item_type == 'Equipment':
				desc = item + ' manufactured'
				if time_required:
					desc = 'Manufacturing ' + item
			elif item_type == 'Buildings':
				desc = item + ' constructed'
				if time_required:
					desc = 'Constructing ' + item
			else:
				desc = item + ' produced'
				if time_required:
					desc = item + ' in process'
		# if args.random and item_type == 'Commodity':
		# 	rand = random.randint(1, 3)
		# 	qty = qty * rand
		produce_entry = []
		if price is None:
			price = world.get_price(item)
		if item_type != 'Service':
			produce_entry = [ ledger.get_event(), self.entity_id, world.now, desc, item, price, qty, debit_acct, credit_acct, price * qty ]
		if produce_entry:
			produce_event += [produce_entry]

		byproducts = world.items['byproduct'][item]
		byproduct_amts = world.items['byproduct_amt'][item]
		if byproducts is not None and byproduct_amts is not None:
			if isinstance(byproducts, str):
				byproducts = [x.strip() for x in byproducts.split(',')]
			byproducts = list(set(filter(None, byproducts)))
			if isinstance(byproduct_amts, str):
				byproduct_amts = [x.strip() for x in byproduct_amts.split(',')]
			byproduct_amts = list(set(filter(None, byproduct_amts)))
			for byproduct, byproduct_amt in zip(byproducts, byproduct_amts):
				item_type = self.get_item_type(byproduct)
				desc = item + ' byproduct produced'
				# TODO Support other account types, such as for pollution
				byproduct_price = world.get_price(byproduct)
				byproduct_amt = float(byproduct_amt)
				byproduct_entry = [ ledger.get_event(), self.entity_id, world.now, desc, byproduct, price, byproduct_amt * qty, debit_acct, credit_acct, price * byproduct_amt * qty ]
				if byproduct_entry:
					produce_event += [byproduct_entry]

		if buffer:
			return produce_event, time_required
		ledger.journal_entry(produce_event)
		return produce_event, time_required

	def wip_check(self, check=False):
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of WIP txns for different item types
		wip_txns = ledger.gl[(ledger.gl['debit_acct'].isin(['WIP Inventory','WIP Equipment','Researching Technology','Studying Education','Building Under Construction'])) & (ledger.gl['entity_id'] == self.entity_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		if not wip_txns.empty:
			#print('WIP Transactions: \n{}'.format(wip_txns))
			# Compare the gl dates to the WIP time from the items table
			items_time = world.items[world.items['requirements'].str.contains('Time', na=False)]
			items_continuous = world.items[world.items['freq'].str.contains('continuous', na=False)]
			for index, wip_lot in wip_txns.iterrows():
				wip_event = []
				item = wip_lot.loc['item_id']
				#print('WIP Item: {}'.format(item))
				requirements = world.items.loc[item, 'requirements']
				if isinstance(requirements, str):
					requirements = [x.strip() for x in requirements.split(',')]
				requirements = list(set(filter(None, requirements)))
				for requirement in requirements:
					if requirement in items_continuous.values:
						entries = self.use_item(requirement, check)
						if not entries:
							entries = []
						if entries is True:
							entries = []
						wip_event += entries
					if check:
						continue
				if check:
					break
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
					# Undo "in use" entries for related items
					release_txns = ledger.gl[(ledger.gl['credit_acct'] == 'In Use') & (ledger.gl['entity_id'] == self.entity_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
					#print('Release TXNs: \n{}'.format(release_txns))
					in_use_txns = ledger.gl[(ledger.gl['debit_acct'] == 'In Use') & (ledger.gl['entity_id'] == self.entity_id) & (ledger.gl['date'] <= wip_lot[2]) & (~ledger.gl['event_id'].isin(release_txns['event_id'])) & (~ledger.gl['event_id'].isin(rvsl_txns))] # Ensure only captures related items, perhaps using date as a filter
					#print('In Use TXNs: \n{}'.format(in_use_txns))
					for index, in_use_txn in in_use_txns.iterrows():
						release_entry = [ in_use_txn[0], in_use_txn[1], world.now, in_use_txn[4] + ' released', in_use_txn[4], in_use_txn[5], in_use_txn[6], in_use_txn[8], 'In Use', in_use_txn[9] ]
						release_event = [release_entry]
						ledger.journal_entry(release_event)
					# Book the entry to move from WIP to Inventory
					item_type = self.get_item_type(item)
					if item_type == 'Technology':
						debit_acct = 'Technology'
						desc = wip_lot[4] + ' researched'
					elif item_type == 'Education':
						debit_acct = 'Education'
						desc = wip_lot[4] + ' learned'
					elif item_type == 'Equipment':
						debit_acct = 'Inventory'#'Equipment'
						desc = wip_lot[4] + ' manufactured'
					elif item_type == 'Buildings':
						debit_acct = 'Inventory'#'Buildings' # TODO Update purchase() to handle non-inventory purchases
						desc = wip_lot[4] + ' constructed'
					else:
						debit_acct = 'Inventory'
						desc = wip_lot[4] + ' produced'
					wip_entry = [ wip_lot[0], wip_lot[1], world.now, desc, wip_lot[4], wip_lot[5], wip_lot[6] or '', debit_acct, wip_lot[7], wip_lot[9] ]
					wip_event += wip_entry
					ledger.journal_entry(wip_event)

	def check_inv(self, v=False):
		if type(self) == Corporation:
			v = False
		if v: print('{} running inventory check.'.format(self.name))
		self.check_salary(check=True)
		self.check_subscriptions(check=True)
		self.wip_check(check=True)
		if v: print('{} finished inventory check.\n'.format(self.name))

	def negative_bal(self):
		for item in self.produces:
			qty_inv = ledger.get_qty(item, ['Inventory'])
			if qty_inv < 0:
				print('{} has a negative item balance of {} {}. Will attempt to produce {} units'.format(self.name, qty_inv, item, abs(qty_inv)))
				outcome, time_required = self.produce(item, abs(qty_inv))


	def capitalize(self, amount, buffer=False):
		capital_entry = [ ledger.get_event(), self.entity_id, world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', amount ]
		capital_event = [capital_entry]
		if buffer:
			return capital_event
		ledger.journal_entry(capital_event)
		#return capital_event

	def auth_shares(self, ticker, qty=None, counterparty=None):
		if counterparty is None:
			counterparty = self
		if qty is None:
			qty = 100000
		auth_shares_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Authorize shares', ticker, '', qty, 'Shares', 'Info', 0 ]
		auth_shares_event = [auth_shares_entry]
		ledger.journal_entry(auth_shares_event)

	def buy_shares(self, ticker, price, qty, counterparty):
		self.transact(ticker, price, qty, counterparty, 'Investments', 'Shares')

	def org_type(self, name):
		if name == 'Government':
			return Government
		elif name == 'Non-Profit':
			return NonProfit
		else:
			try:
				return self.org_type(world.items.loc[name, 'child_of'])
			except KeyError:
				return Corporation

	# Allow individuals to incorporate organizations without human input
	def incorporate(self, item=None, price=None, qty=None, name=None):
		if price is None: # TODO Fix temp defaults
			price = 5
		if qty is None:
			qty = 1000
		auth_qty = 100000 # TODO Get from entity details
		if name is None and item is not None:
			#items_info = accts.get_items()
			names = world.items.loc[item, 'producer']
			if isinstance(names, str):
				names = [x.strip() for x in names.split(',')]
			names = list(set(filter(None, names)))
			name = names[0]
			#print('Ticker: {}'.format(name))
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		#print('Cash: {}'.format(cash))
		if price * qty > cash:
			print('{} does not have enough cash to incorporate {}.'.format(self.name, name))
			return
		items_produced = world.items[world.items['producer'].str.contains(name, na=False)].reset_index()
		items_produced = items_produced['item_id'].tolist()
		items_produced = ','.join(items_produced)
		#print('Items Produced: {}'.format(items_produced))
		legal_form = self.org_type(name)
		#print('Result: \n{}'.format(legal_form))
		corp = factory.create(legal_form, name, items_produced)
		counterparty = corp
		self.auth_shares(name, auth_qty, counterparty)
		self.buy_shares(name, price, qty, counterparty)
		return corp

	def corp_needed(self, item=None, need=None, ticker=None, demand_index=None):
		# Choose the best item
		#print('Need Demand: {}'.format(need))
		if item is None and need is not None:
			#items_info = accts.get_items()
			#print('Items Info: \n{}'.format(items_info))
			items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs

			need_satisfy_rate = []
			for index, item_row in items_info.iterrows():
				needs = [x.strip() for x in item_row['satisfies'].split(',')]
				for i, need_item in enumerate(needs):
					if need_item == need:
						break
				satisfy_rates = [x.strip() for x in item_row['satisfy_rate'].split(',')]
				satisfy_rate = satisfy_rates[i]
				need_satisfy_rate.append(satisfy_rate)
			need_satisfy_rate = pd.Series(need_satisfy_rate)
			#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
			items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)

			items_info = items_info.sort_values(by='satisfy_rate', ascending=False).reset_index()
			#items_info.reset_index(inplace=True)
			item = items_info['item_id'].iloc[0]
			#print('Item Choosen: {}'.format(item))
		if ticker is None:
			#items_info = accts.get_items()
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			tickers = list(set(filter(None, tickers))) # Use set to ensure no dupes
			#print('Tickers: {}'.format(tickers))
			# TODO Recursively check required items and add their producers to the ticker list
		# Check if item is produced or being produced
		# TODO How to handle service qty check
		qty_inv = ledger.get_qty(item, ['Inventory'])
		qty_wip = ledger.get_qty(item, ['WIP Inventory'])
		qty = qty_inv + qty_wip
		#print('QTY of {} existing: {}'.format(item, qty))
		# If not being produced incorporate and produce item
		if qty == 0: # TODO Fix this for when Food stops being produced
			for ticker in tickers:
				count = 0
				MAX_CORPS = 1
				#print('Ticker: {}'.format(ticker))
				if ticker == 'Individual':
					#print('{} produced by individuals, no corporation needed.'.format(item))
					continue
				for corp in factory.get(Corporation):
					#print('Corp: {}'.format(corp))
					if ticker == corp.name:
						count += 1
						if count >= MAX_CORPS:
							#print('{} {} corporation already exists.'.format(count, corp.name))
							return
				corp = self.incorporate(item, name=ticker)
				# TODO Have the demand table item cleared when entity gets the subscription
				item_type = self.get_item_type(item)
				if item_type == 'Subscription' and demand_index is not None:
					world.demand = world.demand.drop([demand_index]).reset_index(drop=True)
				return corp

	def tech_motivation(self):
		tech_info = world.items[world.items['child_of'] == 'Technology']
		tech_info.reset_index(inplace=True)
		#print('Tech Info: \n{}'.format(tech_info))
		# ledger.reset()
		for index, tech_row in tech_info.iterrows():
			tech = tech_row['item_id']
			#print('Tech Check: {}'.format(tech))
			tech_done_status = ledger.get_qty(items=tech, accounts=['Technology'])
			tech_research_status = ledger.get_qty(items=tech, accounts=['Researching Technology'])
			tech_status = tech_done_status + tech_research_status
			if tech_status == 0:
				#print('Tech Needed: {}'.format(tech))
				outcome = self.item_demanded(tech, qty=1)
				if outcome:
					return tech

	def check_eligible(self, item):
		#print('Check Eligible Item: {}'.format(item))
		item_info = world.items.loc[item]
		if item_info['requirements'] is None:
			return True
		requirements = [x.strip() for x in item_info['requirements'].split(',')]
		for requirement in requirements:
			item_type = self.get_item_type(requirement)
			#print('Check Eligible Requirement: {} | '.format(requirement, item_type))
			if item_type in ['Land','Labour','Job','Equipment','Buildings','Subscription','Service','Commodity','Components','Education','Time','None']:
				continue
			elif item_type == 'Technology':
				tech_status = ledger.get_qty(items=requirement, accounts=['Technology'])
				if tech_status == 0:
					#print('Do not have tech {} for item: {}'.format(requirement, item))
					return
				elif tech_status >= 0:
					#print('Have tech {} for item: {}'.format(requirement, item))
					return True
			else:
				return self.check_eligible(requirement)
		#print('No tech needed for item: {}'.format(item))
		return True

	def qty_demand(self, item, need=None, item_type=None):
		item_info = world.items.loc[item]
		if item_type is None:
			item_type = self.get_item_type(item)
		#print('Item Info: \n{}'.format(item_info))
		decay_rate = self.needs[need]['Decay Rate']
		if need is None: # This should never happen
			need = item_info['satisfies']
			qty = math.ceil(decay_rate / float(item_info['satisfy_rate']))
			return qty
		# Support items with multiple satisfies
		else:
			needs = [x.strip() for x in item_info['satisfies'].split(',')]
			for i, need_item in enumerate(needs):
				if need_item == need:
					break
			satisfy_rates = [x.strip() for x in item_info['satisfy_rate'].split(',')]
			qty = math.ceil(decay_rate / float(satisfy_rates[i]))
			if args.random and item_type != 'Commodity':
				rand = random.randint(1, 3)
				qty = qty * rand
			#qty = qty * world.population
			return qty

	def item_demanded(self, item=None, qty=None, need=None):
		if item is None and need is not None:
			items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
			#print('Items Info Before: \n{}'.format(items_info))
			need_satisfy_rate = []
			for index, item_row in items_info.iterrows():
				needs = [x.strip() for x in item_row['satisfies'].split(',')]
				for i, need_item in enumerate(needs):
					if need == need_item:
						break
				satisfy_rates = [x.strip() for x in item_row['satisfy_rate'].split(',')]
				satisfy_rate = satisfy_rates[i]
				need_satisfy_rate.append(satisfy_rate)
			need_satisfy_rate = pd.Series(need_satisfy_rate)
			#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
			items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)
			#print('Items Info After: \n{}'.format(items_info))
			items_info = items_info.sort_values(by='need_satisfy_rate', ascending=False)
			items_info.reset_index(inplace=True)
			for index, items_info_row in items_info.iterrows():
				#item = items_info['item_id'].iloc[0]
				item = items_info_row['item_id']
				requirements = items_info_row['requirements']
				requirements = [x.strip() for x in requirements.split(',')]
				#print('Requirements: \n{}'.format(requirements))
				if 'Time' not in requirements:
					return
				if self.check_eligible(item):
					break
		# Only allow one technology on demand list at a time
		item_type = self.get_item_type(item)
		tech_on_list = False
		if item_type == 'Technology':
			for index, demand_item in world.demand.iterrows():
				check_tech = demand_item['item_id']
				check_item_type = self.get_item_type(check_tech)
				if check_item_type == 'Technology':
					#print('Cannot add {} technology to demand list because {} technology is already on it.'.format(item, check_tech))
					tech_on_list = True
					return
		if tech_on_list:
			if not self.check_eligible(item):
				print('Technology required to create {} is not known; therefore it cannot be added to the demand list at this time.'.format(item))
				return
		# Check if entity already has item on demand list
		if not world.demand.empty: # TODO Commodity replaces existing commodity if qty is bigger
			#if item_type != 'Commodity': # TODO No longer needed
			temp_df = world.demand[['entity_id','item_id']]
			#print('Temp DF: \n{}'.format(temp_df))
			#temp_new_df = pd.DataFrame({'entity_id': self.entity_id, 'item_id': item}, index=[0]) # Old
			temp_new_df = pd.DataFrame(columns=['entity_id','item_id'])
			temp_new_df = temp_new_df.append({'entity_id': self.entity_id, 'item_id': item}, ignore_index=True)
			#print('Temp New DF: \n{}'.format(temp_new_df))
			#check = temp_df.intersection(temp_new_df)
			check = pd.merge(temp_df, temp_new_df, how='inner', on=['entity_id','item_id'])
			#print('Check: \n{}'.format(check))
			if not check.empty:
				if item_type != 'Commodity': # TODO Maybe add Components
					print('{} already on demand list for {}.'.format(item, self.name))
				return
		if item_type == 'Service':
			#print('Current Demand : \n{}'.format(world.demand['item_id']))
			qty = 1
			if item in world.demand['item_id'].values:
				print('{} service already on the demand table for {}.'.format(item, self.name)) # TODO Finish this
				return
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			tickers = list(set(filter(None, tickers)))
			#print('Tickers: {}'.format(tickers))
			for ticker in tickers: # TODO Check to entity register
				corp_shares = ledger.get_qty(ticker, ['Investments'])
				if corp_shares != 0:
					return
		if qty is None:
			qty = self.qty_demand(item, need, item_type)
		#print('Demand QTY: {}'.format(qty))
		if qty != 0:
			world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty}, ignore_index=True)
			if qty == 1:
				print('{} added to demand list for {} unit by {}.'.format(item, qty, self.name))
			else:
				print('{} added to demand list for {} units by {}.'.format(item, qty, self.name))
			#print('Demand after addition: \n{}'.format(world.demand))
			return item, qty

	def check_demand(self, v=False):
		if v: print('{} demand check for items: \n{}'.format(self.name, self.produces))
		for item in self.produces:
			if v: print('Check Demand Item for {}: {}'.format(self.name, item))
			item_type = self.get_item_type(item)
			if item_type == 'Subscription':
				continue
			#print('World Demand: \n{}'.format(world.demand))
			to_drop = []
			qty = 0
			# Filter for item and add up all qtys to support multiple entries
			for index, demand_row in world.demand.iterrows():
				if item_type == 'Education':
					if demand_row['entity_id'] == self.entity_id: # TODO Could filter df for entity_id first
						if demand_row['item_id'] == item:
							qty = demand_row['qty']
							break
				else:
					if demand_row['item_id'] == item:
						qty += demand_row['qty']
						to_drop.append(index)
			if qty == 0:
				continue
			print('{} attempting to produce {} {} from the demand table.'.format(self.name, qty, item))
			orig_qty = 0
			 # TODO Decide if chance of extra production of commodities should be used
			if args.random and item_type == 'Commodity': # TODO Maybe add Components
				orig_qty = qty
				rand = random.randint(0, 10) / 10
				qty = math.ceil(qty * (1 + rand))
			outcome, time_required = self.produce(item, qty)
			if v: print('Outcome: {} \n{}'.format(time_required, outcome))
			if outcome:
				if item_type == 'Education':
					edu_hours = qty - MAX_HOURS
					#print('Edu Hours: {} | {}'.format(edu_hours, index))
					if edu_hours <= 0:
						world.demand = world.demand.drop(index).reset_index(drop=True)
					else:
						world.demand.at[index, 'qty'] = edu_hours
					#print('Demand After: \n{}'.format(world.demand))
				else:
					world.demand = world.demand.drop(to_drop).reset_index(drop=True)
					if orig_qty:
						print('{} removed from demand list for {} units. Although, {} was randomly able to produce {} units instead.\n'.format(item, orig_qty, self.name, qty))
					else:
						print('{} removed from demand list for {} units by {}.\n'.format(item, qty, self.name))

	def check_optional(self):
		items_list = world.items[world.items['producer'] != None]
		#print('Items List: \n{}'.format(items_list))
		for item in self.produces:
			#print('Produces Item: {}'.format(item))
			requirements = world.items.loc[item, 'requirements']
			if isinstance(requirements, str):
				requirements = [x.strip() for x in requirements.split(',')]
			requirements = list(filter(None, requirements))
			#print('Requirements: \n{}'.format(requirements))
			for requirement in requirements:
				#print('Requirement: {}'.format(requirement))
				possible_items = items_list.loc[items_list['productivity'].str.contains(requirement, na=False)]#.reset_index()
				#print('Possible Items: \n{}'.format(possible_items))
				productivity_items = pd.DataFrame(columns=['item_id','efficiency'])
				for index, prod_item in possible_items.iterrows():
					productivities = [x.strip() for x in prod_item['productivity'].split(',')]
					for i, productivity in enumerate(productivities):
						if productivity == requirement:
							break
					efficiencies = [x.strip() for x in prod_item['efficiency'].split(',')]
					efficiencies = list(map(float, efficiencies))
					efficiency = efficiencies[i]
					productivity_items = productivity_items.append({'item_id': prod_item.name, 'efficiency': efficiency}, ignore_index=True)
				productivity_items = productivity_items.sort_values(by='efficiency', ascending=True)#.reset_index()
				#print('Productivity Items: \n{}'.format(productivity_items))
				if not productivity_items.empty:
					for index, prod_item in productivity_items.iterrows():
						item_type = self.get_item_type(prod_item['item_id'])
						current_qty = ledger.get_qty(prod_item['item_id'], [item_type])
						#print('Current Qty of {}: {}'.format(item['item_id'], current_qty))
						if current_qty == 0:
							self.purchase(prod_item['item_id'], qty=1, acct_buy='Equipment')
							break

	def claim_land(self, qty, price, item='Land', buffer=False): # QTY in square meters
		incomplete, claim_land_event, time_required = self.fulfill(item, qty)
		if incomplete:
			return
		claim_land_entry = []
		yield_land_entry = []
		# TODO Add WIP Time component
		ledger.set_entity(0)
		unused_land = ledger.get_qty(items=item, accounts=['Land'])
		ledger.reset()
		print('{} available to claim: {}'.format(item, unused_land))
		if unused_land >= qty:
			claim_land_entry = [ ledger.get_event(), self.entity_id, world.now, 'Claim land', item, price, qty, 'Land', 'Natural Wealth', qty * price ]
			yield_land_entry = [ ledger.get_event(), 0, world.now, 'Bestow land', item, price, qty, 'Natural Wealth', 'Land', qty * price ]
			# claim_land_event = [yield_land_entry, claim_land_entry]
			if claim_land_entry and yield_land_entry:
				claim_land_event += [yield_land_entry, claim_land_entry]
			if buffer:
				print('{} claims {} square meters of {}.'.format(self.name, qty, item))
				return claim_land_event
			# if not claim_land_event:
			# 	return
			ledger.journal_entry(claim_land_event)
			return True
		else:
			print('{} cannot claim {} square meters of {} because there is only {} square meters available.'.format(self.name, qty, item, unused_land))

	def get_counterparty(self, txns, rvsl_txns, item, account, allowed=None, v=False):
		if v: print('{} | Item: {}'.format(self.name, item))
		if allowed is None:
			allowed = factory.registry.keys()
		if v: print('Allowed: {}'.format(allowed))
		txn = txns.loc[txns['item_id'] == item]
		if v: print('TXN: \n{}'.format(txn))
		if txn.empty:
			print('No counterparty exists for {}.'.format(item))
			return
		event_id = txn.iloc[0].loc['event_id']
		if v: print('Event ID: {}'.format(event_id))
		event_txns = ledger.gl[(ledger.gl['event_id'] == event_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		if v: print('Event TXNs: \n{}'.format(event_txns))
		item_txn = event_txns.loc[event_txns['item_id'] == item] # If there are multiple items in same event
		if v: print('Item TXN: \n{}'.format(item_txn))
		counterparty_txn = item_txn.loc[item_txn['debit_acct'] == account]
		if v: print('Counterparty TXN: {} \n{}'.format(account, counterparty_txn))
		counterparty_id = counterparty_txn.iloc[0].loc['entity_id']
		counterparty = factory.get_by_id(counterparty_id)
		if v: print('Counterparty Type: {}'.format(type(counterparty)))
		while True:
			if counterparty is not None:
				break
			if type(counterparty) not in allowed:
				counterparty_id += 1
				counterparty = factory.get_by_id(counterparty_id)
		if v: print('Counterparty - {}'.format(counterparty))
		return counterparty

	def pay_wages(self, jobs=None, counterparty=None):
		if jobs is None:
			# Get list of jobs
			# TODO Get list of jobs that have accruals only
			ledger.set_entity(self.entity_id)
			wages_payable_list = ledger.get_qty(accounts=['Wages Expense'])
			ledger.reset()
			#print('Wages Payable List: \n{}'.format(wages_payable_list))
			jobs = wages_payable_list['item_id']
		# Ensure jobs is a list
		if isinstance(jobs, str):
			jobs = [x.strip() for x in jobs.split(',')]
		jobs = list(filter(None, jobs))
		for job in jobs:
			ledger.set_entity(self.entity_id)
			wages_payable = abs(ledger.balance_sheet(accounts=['Wages Payable'], item=job))
			labour_hours = abs(ledger.get_qty(items=job, accounts=['Wages Payable']))
			ledger.reset()
			#print('Wages Payable: {}'.format(wages_payable))
			#print('Labour Hours: {}'.format(labour_hours))
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if not wages_payable:
				#print('No wages payable to pay for {} work.'.format(job))
				return
			elif cash >= wages_payable:
				# Get counterparty
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				wages_pay_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Wages Expense') & (ledger.gl['credit_acct'] == 'Wages Payable') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				#wages_pay_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Wages Receivable') & (ledger.gl['credit_acct'] == 'Wages Revenue') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				counterparty = self.get_counterparty(wages_pay_txns, rvsl_txns, job, 'Wages Receivable', allowed=Individual)
				wages_pay_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' wages paid', job, wages_payable / labour_hours, labour_hours, 'Wages Payable', 'Cash', wages_payable ]
				wages_chg_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' wages received', job, wages_payable / labour_hours, labour_hours, 'Cash', 'Wages Receivable', wages_payable ]
				pay_wages_event = [wages_pay_entry, wages_chg_entry]
				ledger.journal_entry(pay_wages_event)
			else:
				print('{} does not have enough cash to pay wages for {} work. Cash: {}'.format(self.name, job, cash))

	def check_wages(self, job):
		TWO_PAY_PERIODS = 32 #datetime.timedelta(days=32)
		ledger.set_entity(self.entity_id)
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of Wages Payable txns
		payable = ledger.gl[(ledger.gl['credit_acct'] == 'Wages Payable') & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Payable: \n{}'.format(payable))
		paid = ledger.gl[(ledger.gl['debit_acct'] == 'Wages Payable') & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Paid: \n{}'.format(paid))
		ledger.reset()
		if not payable.empty:
			latest_payable = payable['date'].iloc[-1]
			latest_payable = datetime.datetime.strptime(latest_payable, '%Y-%m-%d').date()
			#print('Latest Payable: \n{}'.format(latest_payable))
		else:
			latest_payable = 0
		if not paid.empty:
			latest_paid = paid['date'].iloc[-1]
			latest_paid = datetime.datetime.strptime(latest_paid, '%Y-%m-%d').date()
			#print('Latest Paid: \n{}'.format(latest_paid))
		else:
			latest_paid = 0
			return True
		#print('Latest Payable: \n{}'.format(latest_payable))
		#print('Latest Paid: \n{}'.format(latest_paid))
		last_paid = latest_payable - latest_paid
		if isinstance(last_paid, datetime.timedelta):
			last_paid = last_paid.days
		#print('Last Paid: \n{}'.format(last_paid))
		if last_paid < TWO_PAY_PERIODS:
			return True

	def accru_wages(self, job, counterparty, wage, labour_hours, buffer=False, check=False):
		if counterparty is None:
			print('No workers available to do {} job for {} hours.'.format(job, labour_hours))
			return
		recently_paid = self.check_wages(job)
		incomplete, accru_wages_event, time_required = self.fulfill(job, qty=labour_hours, reqs='usage_req', amts='use_amount', check=check)
		if check:
			return
		if recently_paid and not incomplete:
			if counterparty.hours > 0:
				hours_worked = min(labour_hours, counterparty.hours)
				wages_exp_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' wages to be paid', job, wage, hours_worked, 'Wages Expense', 'Wages Payable', wage * hours_worked ]
				wages_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' wages to be received', job, wage, hours_worked, 'Wages Receivable', 'Wages Revenue', wage * hours_worked ]
				accru_wages_event += [wages_exp_entry, wages_rev_entry]
			else:
				if not incomplete:
					print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
				else:
					print('{} cannot fulfill the requirements to allow {} to work.'.format(self.name, job))
				return
			if buffer:
				print('{} hired {} as a {} for {} hours.'.format(self.name, counterparty.name, job, hours_worked))
				return accru_wages_event
			ledger.journal_entry(accru_wages_event)
			counterparty.set_hours(hours_worked)
		else:
			print('Wages have not been paid for {} recently by {}.'.format(job, self.name))
			return

	def worker_counterparty(self, job, only_avail=True):
		print('{} looking for worker for job: {}'.format(self.name, job))
		item_type = self.get_item_type(job)
		workers = {}
		# Get list of all individuals
		#world.entities = accts.get_entities()
		# Get list of eligible individuals
		worker_event = []
		individuals = []
		for individual in factory.get(Individual):
			incomplete, entries, time_required = individual.fulfill(job, qty=1)
			# TODO Capture entries
			if not incomplete:
				# This will cause all available workers to attempt to become qualified even if they don't get the job in the end
				individuals.append(individual)
				worker_event += entries
		#print('Eligible Individuals: \n{}'.format(individuals))
		# Check total wages receivable for that job for each individual
		for individual in individuals:
			experience_wages = 0
			experience_salary = 0
			ledger.set_entity(individual.entity_id)
			experience_wages = abs(ledger.get_qty(accounts=['Wages Revenue'], items=job))
			experience_salary = abs(ledger.get_qty(accounts=['Salary Revenue'], items=job))
			experience = experience_wages + experience_salary
			print('Experience for {}: {:g} | Hours Left: {}'.format(individual.name, experience, individual.hours))
			ledger.reset()
			workers[individual] = experience
		# Filter for workers with enough hours in the day left
		if item_type == 'Job':
			base_hours = 4
		else:
			base_hours = 0
		if only_avail:
			workers_avail = {worker: v for worker, v in workers.items() if worker.hours > base_hours}
		else:
			workers_avail = workers
		if not workers_avail:
				return None, []
		# Choose the worker with the most experience
		worker_choosen = max(workers_avail, key=lambda k: workers_avail[k])
		print('Worker Choosen: {}'.format(worker_choosen.name))
		if worker_event:
			return worker_choosen, worker_event
		return worker_choosen

	def hire_worker(self, job, counterparty=None, price=0, qty=1, buffer=False):
		if counterparty is None:
			entries = []
			counterparty = self.worker_counterparty(job, only_avail=False)
			if isinstance(counterparty, tuple):
				counterparty, entries = counterparty
		if counterparty is None:
			print('No workers available to do {} job for {}.'.format(job, self.name))
			return
		incomplete, hire_worker_event, time_required = self.fulfill(job, qty)
		if incomplete:
			return
		if entries:
			hire_worker_event += entries
		# hire_worker_entry = [] # TODO Test if not needed
		# start_job_entry = [] # TODO Test if not needed
		hire_worker_entry = [ ledger.get_event(), self.entity_id, world.now, 'Hired ' + job, job, price, qty, 'Worker Info', 'Hire Worker', 0 ]
		start_job_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Started job as ' + job, job, price, qty, 'Start Job', 'Worker Info', 0 ]
		# if hire_worker_entry and start_job_entry: # TODO Test if not needed
		hire_worker_event += [hire_worker_entry, start_job_entry]
		first_pay = self.pay_salary(job, counterparty, buffer=buffer, first=True)
		if not first_pay:
			hire_worker_event = []
			first_pay = []
		else:
			hire_worker_event += first_pay
		if buffer:
			print('{} hired {} as a {} fulltime.'.format(self.name, counterparty.name, job))
			return hire_worker_event
		ledger.journal_entry(hire_worker_event)

	def fire_worker(self, job, counterparty, price=0, qty=-1, quit=False, buffer=False):
		ent_id = self.entity_id
		cp_id = counterparty.entity_id
		if quit:
			ent_id, cp_id = cp_id, ent_id
		fire_worker_entry = [ ledger.get_event(), ent_id, world.now, 'Fired ' + job, job, price, qty, 'Worker Info', 'Fire Worker', 0 ]
		quit_job_entry = [ ledger.get_event(), cp_id, world.now, 'Quit job as ' + job, job, price, qty, 'Quit Job', 'Worker Info', 0 ]
		fire_worker_event = [fire_worker_entry, quit_job_entry]
		if buffer:
			return fire_worker_event
		ledger.journal_entry(fire_worker_event)

	def check_salary(self, job=None, counterparty=None, check=False):
		if job is not None:
			ledger.set_entity(self.entity_id)
			worker_state = ledger.get_qty(items=job, accounts=['Worker Info'])
			ledger.reset()
			if worker_state:
				worker_state = int(worker_state)
			#print('Worker State: {}'.format(worker_state))
			if not worker_state: # If worker_state is zero
				return
			for _ in range(worker_state):
				self.pay_salary(job, counterparty, check=check)
		elif job is None:
			ledger.set_entity(self.entity_id)
			worker_states = ledger.get_qty(accounts=['Worker Info'])
			ledger.reset()
			#print('Worker States: \n{}'.format(worker_states))
			rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			salary_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Worker Info') & (ledger.gl['credit_acct'] == 'Hire Worker') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
			#print('Worker TXNs: \n{}'.format(salary_txns))
			for index, job in worker_states.iterrows():
				#print('Salary Job: \n{}'.format(job))
				#print('Job: {}'.format(job['item_id']))
				item = job['item_id']
				worker_state = job['qty']
				#print('Worker State: {}'.format(worker_state))
				if worker_state:
					worker_state = int(worker_state)
				#print('Worker State: {}'.format(worker_state))
				if not worker_state: # If worker_state is zero
					return
				counterparty = self.get_counterparty(salary_txns, rvsl_txns, item, 'Start Job', allowed=Individual)
				for _ in range(worker_state):
					self.pay_salary(item, counterparty, check=check)

	def pay_salary(self, job, counterparty, salary=None, labour_hours=None, buffer=False, first=False, check=False):
		# TODO Add accru_salary()
		if type(counterparty) != Individual: # TODO Shouldn't be needed now, this was due to error from inheritance going to a Corporation
			print('Counterparty is not an Individual, it is {} | {}'.format(counterparty.name, counterparty.entity_id))
			return
		if first: # TODO Required due to not using db rollback in fulfill
			pay_salary_event = []
			incomplete = False
			time_required = False
		else:
			incomplete, pay_salary_event, time_required = self.fulfill(job, qty=1, reqs='usage_req', amts='use_amount', check=check)
		if check:
			if pay_salary_event and not incomplete:
				ledger.journal_entry(pay_salary_event)
				return True
			return
		WORK_DAY = 8
		if salary is None:
			salary = world.get_price(job) # TODO Get price from hire entry
		if labour_hours is None:
			labour_hours = WORK_DAY
		if counterparty.hours < labour_hours:
			print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= (salary * labour_hours) and not incomplete:
			# TODO Add check if enough cash, if not becomes salary payable
			salary_exp_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' salary paid', job, salary, labour_hours, 'Salary Expense', 'Cash', salary * labour_hours ]
			salary_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' salary received', job, salary, labour_hours, 'Cash', 'Salary Revenue', salary * labour_hours ]
			pay_salary_event += [salary_exp_entry, salary_rev_entry]
			# TODO Don't set hours if production is not possible
			counterparty.set_hours(labour_hours)
			if buffer:
				return pay_salary_event
			ledger.journal_entry(pay_salary_event)
			return True
		else:
			if not incomplete:
				print('{} does not have enough cash to pay for {} salary. Cash: {}'.format(self.name, job, cash))
			else:
				print('{} cannot fulfill the requirements to keep {} working.'.format(self.name, job))
			if not first:
				self.fire_worker(job, counterparty)

	def subscription_counterparty(self, subscription):
		# Get entity that produces the subscription
		#print('Subscription Requested: {}'.format(subscription))
		for corporation in factory.get(Corporation):
			#print('Produces: {}'.format(corporation.produces[0]))
			for item in corporation.produces:
				if item == subscription:
					return corporation
		print('No company exists that can provide the {} subscription for {}.'.format(subscription, self.name))

	def order_subscription(self, item, counterparty, price, qty=1, buffer=False):
		if counterparty is None:
			self.item_demanded(item, qty)
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= price:
			order_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Ordered ' + item, item, price, qty, 'Subscription Info', 'Order Subscription', 0 ]
			sell_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Sold ' + item, item, price, qty, 'Sell Subscription', 'Subscription Info', 0 ]
			order_subscription_event = [order_subscription_entry, sell_subscription_entry]
			first_payment = self.pay_subscription(item, counterparty, buffer=buffer, first=True)
			if not first_payment:
				order_subscription_event = []
				first_payment = []
			elif buffer:
				order_subscription_event += first_payment
				print('{} ordered {} subscription service from {}.'.format(self.name, item, counterparty.name))
				return order_subscription_event
			ledger.journal_entry(order_subscription_event)
			return True
		else:
			print('{} does not have enough cash to pay for {} subscription. Cash: {}'.format(self.name, item, cash))
			self.item_demanded(item, qty)

	def cancel_subscription(self, item, counterparty, price=0, qty=-1):
		cancel_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Cancelled ' + item, item, price, qty, 'Subscription Info', 'Cancel Subscription', 0 ]
		end_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'End ' + item, item, price, qty, 'End Subscription', 'Subscription Info', 0 ]
		cancel_subscription_event = [cancel_subscription_entry, end_subscription_entry]
		ledger.journal_entry(cancel_subscription_event)

	def check_subscriptions(self, counterparty=None, check=False):
		ledger.set_entity(self.entity_id)
		subscriptions_list = ledger.get_qty(accounts=['Subscription Info'])
		#print('Subscriptions List: \n{}'.format(subscriptions_list))
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		subscriptions_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Subscription Info') & (ledger.gl['credit_acct'] == 'Order Subscription') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Subscriptions TXNs: \n{}'.format(subscriptions_txns))
		ledger.reset()
		if not subscriptions_list.empty:
			for index, subscription in subscriptions_list.iterrows():
				item = subscription['item_id']
				counterparty = self.get_counterparty(subscriptions_txns, rvsl_txns, item, 'Sell Subscription')
				self.pay_subscription(subscription['item_id'], counterparty, world.get_price(subscription['item_id']), subscription['qty'], check=check)

	def pay_subscription(self, item, counterparty, price=None, qty='', buffer=False, first=False, check=False):
		if price is None:
			price = world.get_price(item) # TODO Get price from subscription order
		if first:
			subscription_state = 1
		else:
			ledger.set_entity(self.entity_id)
			subscription_state = ledger.get_qty(items=item, accounts=['Subscription Info'])
			ledger.reset()
			if subscription_state:
				subscription_state = int(subscription_state)
		#print('Subscription State: {}'.format(subscription_state))
		if not subscription_state:
			return
		pay_subscription_event = []
		for _ in range(subscription_state):
			incomplete, entries, time_required = self.fulfill(item, qty=1, reqs='usage_req', amts='use_amount', check=check)
			pay_subscription_event += entries
			if check:
				continue
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if cash >= price and not incomplete:
				pay_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Payment for ' + item, item, price, qty, 'Subscription Expense', 'Cash', price ]
				charge_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Received payment for ' + item, item, price, qty, 'Cash', 'Subscription Revenue', price ]
				pay_subscription_event += [pay_subscription_entry, charge_subscription_entry]
				if buffer:
					continue
				ledger.journal_entry(pay_subscription_event)
			else:
				if not incomplete:
					print('{} does not have enough cash to pay for {} subscription. Cash: {}'.format(self.name, item, cash))
				else:
					print('{} cannot fulfill the requirements to keep {} subscription.'.format(self.name, item))
				if not first:
					self.cancel_subscription(item, counterparty)
		if not incomplete:
			return pay_subscription_event

	def collect_material(self, item, qty, price=None, account='Inventory'): # TODO Make cost based on time spent and salary
		if price is None:
			price = world.get_price(item)
		collect_mat_entry = [ ledger.get_event(), self.entity_id, world.now, 'Forage ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		collect_mat_event = [collect_mat_entry]
		ledger.journal_entry(collect_mat_event)
		return True
		# TODO Check if enough land and return insufficient if not

	def find_item(self, item, qty, price=None, account=None): # Assuming all materials found for testing
		if price is None:
			price = world.get_price(item)
		if account is None:
			account = 'Equipment'
		find_item_entry = [ ledger.get_event(), self.entity_id, world.now, 'Find ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		find_item_event = [find_item_entry]
		ledger.journal_entry(find_item_event)
		return True

	def depreciation_check(self, items=None): # TODO Add support for explicitly provided items
		if items is None:
			ledger.set_entity(self.entity_id)
			items_list = ledger.get_qty(accounts=['Buildings','Equipment','Inventory','Furniture'])
			#print('Dep. Items List: \n{}'.format(items_list))
		for index, item in items_list.iterrows():
			#print('Depreciation Items: \n{}'.format(item))
			qty = item['qty']
			item = item['item_id']
			#print('Depreciation Item: {}'.format(item))
			lifespan = world.items['lifespan'][item]
			metric = world.items['metric'][item]
			#print('Item Lifespan: {}'.format(lifespan))
			#print('Item Metric: {}'.format(metric))
			self.derecognize(item, qty)
			if metric != 'usage':
				self.depreciation(item, lifespan, metric)
		ledger.reset()

	def depreciation(self, item, lifespan, metric, uses=1, buffer=False):
		if (metric == 'ticks') or (metric == 'usage'):
			#item_type = self.get_item_type(item)
			asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment'], item=item) # TODO Maybe support other accounts
			if asset_bal == 0:
				return
			depreciation_event = []
			#print('Asset Bal: {}'.format(asset_bal))
			dep_amount = (asset_bal / lifespan) * uses
			accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
			remaining_amount = asset_bal - accum_dep_bal
			if dep_amount > remaining_amount:
				uses = remaining_amount / (asset_bal / lifespan)
				dep_amount = remaining_amount
				new_qty = math.ceil(uses / lifespan)
				print('The {} breaks for the {}. Another {} are required to use.'.format(item, self.name, new_qty))
				# Try to purchase a new item if current one breaks
				outcome = self.purchase(item, new_qty)
				if outcome:
					entries, new_uses = self.depreciation(item, lifespan, metric, uses, buffer)
					if entries:
						depreciation_event += entries
						uses += new_uses
			#print('Depreciation: {} {} {}'.format(item, lifespan, metric))
			depreciation_entry = [ ledger.get_event(), self.entity_id, world.now, 'Depreciation of ' + item, item, '', '', 'Depreciation Expense', 'Accumulated Depreciation', dep_amount ]
			depreciation_event = [depreciation_entry]
			if buffer:
				return depreciation_event, uses
			ledger.journal_entry(depreciation_event)
			return depreciation_event, uses

		if (metric == 'spoilage') or (metric == 'obsolescence'):
			#print('Spoilage: {} {} days {}'.format(item, lifespan, metric))
			ledger.refresh_ledger()
			#print('GL: \n{}'.format(ledger.gl))
			rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			# Get list of Inventory txns
			inv_txns = ledger.gl[(ledger.gl['debit_acct'] == 'Inventory')
				& (ledger.gl['item_id'] == item)
				& (~ledger.gl['event_id'].isin(rvsl_txns))]
			#print('Inv TXNs: \n{}'.format(inv_txns))
			if not inv_txns.empty:
				# Compare the gl dates to the lifetime from the items table
				items_spoil = world.items[world.items['metric'].str.contains('spoilage', na=False)]
				lifespan = items_spoil['lifespan'][item]
				#print('Spoilage Lifespan: {}'.format(item))
				for txn_id, inv_lot in inv_txns.iterrows():
					#print('TXN ID: {}'.format(txn_id))
					#print('Inv Lot: \n{}'.format(inv_lot))
					date_done = (datetime.datetime.strptime(inv_lot['date'], '%Y-%m-%d') + datetime.timedelta(days=lifespan)).date()
					#print('Date Done: {}'.format(date_done))
					# If the time elapsed has passed
					if date_done == world.now:
						ledger.set_entity(self.entity_id)
						qty = ledger.get_qty(item, 'Inventory')
						txns = ledger.hist_cost(qty, item, 'Inventory', True)
						ledger.reset()
						#print('TXNs: \n{}'.format(txns))
						#print('Spoilage QTY: {}'.format(qty))
						if txn_id in txns.index:
							txn_qty = txns[txns.index == txn_id]['qty'].iloc[0]
							#print('Spoilage TXN QTY: {}'.format(txn_qty))
							# Book thes spoilage entry
							if qty < txn_qty:
								spoil_entry = [[ inv_lot[0], inv_lot[1], world.now, inv_lot[4] + ' spoilage', inv_lot[4], inv_lot[5], qty or '', 'Spoilage Expense', 'Inventory', inv_lot[5] * qty ]]
							else:
								spoil_entry = [[ inv_lot[0], inv_lot[1], world.now, inv_lot[4] + ' spoilage', inv_lot[4], inv_lot[5], inv_lot[6] or '', 'Spoilage Expense', 'Inventory', inv_lot[9] ]]
							ledger.journal_entry(spoil_entry)

	def impairment(self, item, amount):
		# TODO Maybe make amount default to None and have optional impact or reduction parameter
		# item_type = self.get_item_type(item)
		# asset_bal = ledger.balance_sheet(accounts=[item_type], item=item)

		impairment_entry = [ ledger.get_event(), self.entity_id, world.now, 'Impairment of ' + item, item, '', '', 'Loss on Impairment', 'Accumulated Impairment Losses', amount ]
		impairment_event = [impairment_entry]
		ledger.journal_entry(impairment_event)
		return impairment_event

	def derecognize(self, item, qty):
		# TODO Check if item in use
		#item_type = self.get_item_type(item)
		asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment'], item=item)# TODO Maybe support other accounts
		if asset_bal == 0:
				return
		accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
		accum_imp_bal = ledger.balance_sheet(accounts=['Accumulated Impairment Losses'], item=item)
		accrum_reduction = abs(accum_dep_bal) + abs(accum_imp_bal)
		if asset_bal == accrum_reduction:
			derecognition_entry = [ ledger.get_event(), self.entity_id, world.now, 'Derecognition of ' + item, item, asset_bal / qty, qty, 'Accumulated Depreciation', 'Equipment', asset_bal ]
			derecognition_event = [derecognition_entry]
			ledger.journal_entry(derecognition_event)


class Individual(Entity):
	def __init__(self, name, items, parents=(None, None)):
		super().__init__(name)
		hunger_start = 100
		if args.random:
			hunger_start = random.randint(30, 100)
			hunger_start = 100
		# TODO Make other starting need levels random

		# Note: The 2nd to 5th values are for another program
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Hygiene, Thirst, Fun','100,100,100,100','1,1,2,5','85,50,60,40', str(hunger_start)+',100,100,100',None,'Labour') ]
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Hygiene, Thirst','100,100,100','1,1,2','85,50,60', str(hunger_start)+',100,100',None,items) ]
		entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Thirst','100,100','1,2','85,60', str(hunger_start)+',100',None,items) ]
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger','100','1','85', str(hunger_start),None,items) ]

		self.entity_id = accts.add_entity(entity_data)
		self.name = entity_data[0][0]
		self.dead = False
		self.produces = entity_data[0][13]
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		self.produces = list(filter(None, self.produces))
		self.parents = parents
		print('Parents: {}'.format(self.parents))
		print('Create Individual: {} | entity_id: {}'.format(self.name, self.entity_id))
		self.hours = entity_data[0][6]
		self.setup_needs(entity_data)
		for need in self.needs:
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))

	def __str__(self):
		return 'Indv: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Indv: {} | {}'.format(self.name, self.entity_id)

	def set_hours(self, hours_delta=0):
		self.hours -= hours_delta
		if self.hours < 0:
			self.hours = 0
		cur = ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET hours = ?
			WHERE entity_id = ?;
		'''
		values = (self.hours, self.entity_id)
		cur.execute(set_need_query, values)
		ledger.conn.commit()
		cur.close()
		return self.hours

	def reset_hours(self):
		#MAX_HOURS = 12
		self.hours = MAX_HOURS
		return self.hours

	def setup_needs(self, entity_data):
		self.needs = collections.defaultdict(dict)
		needs_names = [x.strip() for x in entity_data[0][7].split(',')]
		needs_max = [x.strip() for x in str(entity_data[0][8]).split(',')]
		decay_rate = [x.strip() for x in str(entity_data[0][9]).split(',')]
		threshold = [x.strip() for x in str(entity_data[0][10]).split(',')]
		current_need = [x.strip() for x in str(entity_data[0][11]).split(',')]
		for i, name in enumerate(needs_names):
			self.needs[name]['Max Need'] = int(needs_max[i])
			self.needs[name]['Decay Rate'] = int(decay_rate[i])
			self.needs[name]['Threshold'] = int(threshold[i])
			self.needs[name]['Current Need'] = int(current_need[i])
		#print(self.needs)
		return self.needs

	def set_need(self, need, need_delta, forced=False):
		self.needs[need]['Current Need'] += need_delta
		cur = ledger.conn.cursor()
		set_need_query = '''
			UPDATE entities
			SET current_need = ?
			WHERE entity_id = ?;
		'''
		values = (self.needs[need]['Current Need'], self.entity_id)
		cur.execute(set_need_query, values)
		ledger.conn.commit()
		cur.close()
		if self.needs[need]['Current Need'] <= 0:
			self.inheritance()
			factory.destroy(self)
			if forced:
				print('{} died due to natural causes.'.format(self.name))
			else:
				print('{} died due to {}.'.format(self.name, need))
			#world.end = True
			self.dead = True
		return self.needs[need]['Current Need']

	def birth(self, counterparty=None):
		print('\nPerson to be born!')
		self.entities = accts.get_entities()
		if counterparty is None:
			individuals = factory.registry[Individual]
			#print('Individuals: {}'.format(individuals))
			self.entity_ids = [individual.entity_id for individual in individuals]
			self.entity_ids.remove(self.entity_id)
			print('Entity IDs Before: {}'.format(self.entity_ids))
			random.shuffle(self.entity_ids)
			print('Entity IDs: {}'.format(self.entity_ids))
			# Choose random partner is none is provided
			counterparty = factory.get_by_id(random.choice(self.entity_ids))
		gift_event = []
		ledger.set_entity(self.entity_id)
		cash1 = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash1 >= 1000:
			gift_entry1 = [ ledger.get_event(), self.entity_id, world.now, 'Gift cash to child', '', '', '', 'Wealth', 'Cash', 1000 ]
		else:
			print('{} does not have $1,000 in cash to give birth with {}.'.format(self.name, counterparty.name))
			return
		ledger.set_entity(counterparty.entity_id)
		cash2 = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash2 >= 1000:
			gift_entry2 = [ ledger.get_event(), counterparty.entity_id, world.now, 'Gift cash to child', '', '', '', 'Wealth', 'Cash', 1000 ]
		else:
			print('{} does not have $1,000 in cash to have child with {}.'.format(counterparty.name, self.name))
			return
			# TODO Support looping through counterparties if first does not have enough cash
			# self.entity_ids.remove(counterparty.entity_id)
			# for entity in self.entity_ids:
			# 	counterparty = factory.get_by_id(entity)

		gift_event += [gift_entry1, gift_entry2]

		self.indiv_items_produced = list(world.items[world.items['producer'].str.contains('Individual', na=False)].index.values)
		self.indiv_items_produced = ','.join(self.indiv_items_produced)
		#print('Individual Production: {}'.format(self.indiv_items_produced))
		last_entity_id = self.entities.reset_index()['entity_id'].max() # TODO Maybe a better way of doing this
		#print('Last Entity ID: {}'.format(last_entity_id))
		factory.create(Individual, 'Person-' + str(last_entity_id + 1), self.indiv_items_produced, (self, counterparty))
		individual = factory.get_by_id(last_entity_id + 1)

		gift_event += individual.capitalize(amount=2000, buffer=True) # Hardcoded amount for now

		ledger.journal_entry(gift_event)

	def inheritance(self, counterparty=None):
		# Remove any items that exist on the demand table for this entity
		demand_items = world.demand[world.demand['entity_id'] == self.entity_id]
		if not demand_items.empty:
			to_drop = demand_items.index.tolist()
			world.demand = world.demand.drop(to_drop).reset_index(drop=True)
			print('{} removed {} indexes for items from demand list.\n'.format(self.name, to_drop))

		# Quit any current jobs
		ledger.set_entity(self.entity_id)
		current_jobs = ledger.get_qty(accounts=['Start Job'])
		for index, job in current_jobs.iterrows():
			item = job['item_id']
			worker_state = job['qty']
			if worker_state >= 1: # Should never be greater than 1 for the same counterparty
				worker_state = int(worker_state)
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				hire_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Start Job') & (ledger.gl['credit_acct'] == 'Worker Info') ) & (ledger.gl['item_id'] == item) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				ledger.reset()
				counterparty = self.get_counterparty(hire_txns, rvsl_txns, item, 'Worker Info')
				for _ in range(worker_state): # TODO This for loop shouldn't be necessary
					self.fire_worker(item, counterparty, quit=True)

		# Cancel any current subscriptions
		ledger.set_entity(self.entity_id)
		current_subs = ledger.get_qty(accounts=['Subscription Info'])
		for index, sub in current_subs.iterrows():
			item = sub['item_id']
			sub_state = sub['qty']
			if sub_state >= 1:
				sub_state = int(sub_state)
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				sub_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Subscription Info') & (ledger.gl['credit_acct'] == 'Order Subscription') ) & (ledger.gl['item_id'] == item) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				ledger.reset()
				counterparty = self.get_counterparty(sub_txns, rvsl_txns, item, 'Sell Subscription')
				for _ in range(sub_state):
					self.cancel_subscription(item, counterparty)

		# Get the counterparty to inherit to
		if counterparty is None:
			counterparty = self.parents[0]
			#print('First Parent: {}'.format(counterparty))
			if counterparty is None:
				individuals = itertools.cycle(factory.get(Individual))
				nextindv = next(individuals) # Prime the pump
				while True:
					individual, nextindv = nextindv, next(individuals)
					# print('Individual: {}'.format(individual.name))
					# print('Next Individual: {}'.format(nextindv.name))
					if individual.entity_id == self.entity_id:
						counterparty = nextindv
						break
		print('Inheritance bequeathed from {} to {}'.format(self.name, counterparty.name))

		ledger.set_entity(self.entity_id)
		# Remove all job and subscription info entries
		ledger.gl = ledger.gl.loc[ledger.gl['credit_acct'] != 'Worker Info']
		ledger.gl = ledger.gl.loc[ledger.gl['debit_acct'] != 'Subscription Info']
		ledger.gl.fillna(0, inplace=True)
		consolidated_gl = ledger.gl.groupby(['item_id','debit_acct','credit_acct']).sum()
		ledger.reset()
		inherit_event = []
		for index, entry in consolidated_gl.iterrows():
			#print('Index: \n{}'.format(index))
			#print('Entry: \n{}'.format(entry))
			bequeath_entry = [ ledger.get_event(), self.entity_id, world.now, 'Bequeath to ' + counterparty.name, index[0], entry[2], entry[3], index[2], index[1], entry[4] ]
			inherit_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Inheritance from ' + self.name, index[0], entry[2], entry[3], index[1], index[2], entry[4] ]
			inherit_event += [bequeath_entry, inherit_entry]
		ledger.journal_entry(inherit_event)

	def need_decay(self, need):
		rand = 1
		if args.random:
			rand = random.randint(1, 3)
		decay_rate = self.needs[need]['Decay Rate'] * -1 * rand
		#print('{} Decay Rate: {}'.format(need, decay_rate))
		self.set_need(need, decay_rate)
		return decay_rate

	def threshold_check(self, need):
		if self.needs[need]['Current Need'] <= self.needs[need]['Threshold']:
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))
			print('{} threshold met for {}!'.format(need, self.name))
			self.address_need(need)

	def address_need(self, need):
		outcome = None
		items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs

		need_satisfy_rate = []
		for index, item_row in items_info.iterrows():
			needs = [x.strip() for x in item_row['satisfies'].split(',')]
			for i, need_item in enumerate(needs):
				if need_item == need:
					break
			satisfy_rates = [x.strip() for x in item_row['satisfy_rate'].split(',')]
			satisfy_rate = satisfy_rates[i]
			need_satisfy_rate.append(satisfy_rate)
		need_satisfy_rate = pd.Series(need_satisfy_rate)
		#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
		items_info = items_info.assign(need_satisfy_rate=need_satisfy_rate.values)

		items_info = items_info.sort_values(by='need_satisfy_rate', ascending=False)
		items_info.reset_index(inplace=True)
		# If first item is not available, try the next one
		for index, item in items_info.iterrows():
			item_choosen = items_info['item_id'].iloc[index]
			# TODO Support multiple satisfies
			satisfy_rate = float(items_info['need_satisfy_rate'].iloc[index])
			#print('Item Choosen: {}'.format(item_choosen))
			item_type = self.get_item_type(item_choosen)
			#print('Item Type: {}'.format(item_type))
			if item_type == 'Subscription':
				ledger.set_entity(self.entity_id)
				subscription_state = ledger.get_qty(items=item_choosen, accounts=['Subscription Info'])
				ledger.reset()
				if subscription_state:
					self.needs[need]['Current Need'] = self.needs[need]['Max Need']
				else:
					outcome = self.order_subscription(item_choosen, counterparty=self.subscription_counterparty(item_choosen), price=world.get_price(item_choosen))
				# qty_purchase = 1 # TODO Remove as was needed for demand call below

			if item_type == 'Service':
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_purchase = math.ceil(need_needed / satisfy_rate)
				#print('QTY Needed: {}'.format(qty_needed))
				outcome = self.purchase(item_choosen, qty_purchase)

			elif (item_type == 'Commodity') or (item_type == 'Component'):
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_needed = math.ceil(need_needed / satisfy_rate)
				#print('QTY Needed: {}'.format(qty_needed))
				ledger.set_entity(self.entity_id)
				qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
				ledger.reset()
				# TODO Attempt to use item before aquiring some
				if qty_held < qty_needed:
					qty_wanted = qty_needed - qty_held
					qty_avail = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					if qty_avail == 0:
						qty_avail = qty_wanted # Prevent purchase for 0 qty
					qty_purchase = min(qty_wanted, qty_avail)
					print('Satisfy need by purchasing: {} {}'.format(qty_purchase, item_choosen))
					outcome = self.purchase(item_choosen, qty_purchase)
					ledger.set_entity(self.entity_id)
					qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					ledger.reset()
					#print('QTY Held: {}'.format(qty_held))
					if qty_held < qty_wanted:
						outcome, time_required = self.produce(item_choosen, qty_wanted - qty_held)
						ledger.set_entity(self.entity_id)
						qty_held = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
						ledger.reset()
						#print('QTY Held: {}'.format(qty_held))
				if qty_held:
					self.consume(item_choosen, qty_held, need)

			elif item_type == 'Equipment':
				# TODO Decide how qty will work with time spent using item
				ledger.set_entity(self.entity_id)
				qty_held = ledger.get_qty(items=item_choosen, accounts=['Equipment'])
				ledger.reset()
				#print('QTY Held: {}'.format(qty_held))
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				uses_needed = math.ceil(need_needed / satisfy_rate)
				print('Uses Needed: {}'.format(uses_needed))
				event = []
				if qty_held == 0:
					qty_purchase = 1
					metric = items_info['metric'].iloc[index]
					if metric == 'usage':
						lifespan = items_info['lifespan'].iloc[index]
						qty_purchase = math.ceil(uses_needed / lifespan)
					outcome = self.purchase(item_choosen, qty_purchase)
				if qty_held > 0 or outcome:
					entries = self.use_item(item_choosen, uses_needed)
					if not entries:
						entries = []
					if entries is True:
						entries = []
					event += entries
					ledger.journal_entry(event)
					return event

	def adj_needs(self, item, qty=1):
		indiv_needs = list(self.needs.keys())
		#print('Indiv Needs: \n{}'.format(indiv_needs))
		satisfies = world.items.loc[item, 'satisfies']
		satisfies = [x.strip() for x in satisfies.split(',')]
		#print('Satisfies: \n{}'.format(satisfies))
		satisfy_rates = world.items.loc[item, 'satisfy_rate']
		satisfy_rates = [x.strip() for x in satisfy_rates.split(',')]
		#print('Satisfy Rates: \n{}'.format(satisfy_rates))
		needs = list(set(indiv_needs) & set(satisfies))
		if needs is None:
			return
		for need in needs:
			for i, satisfy_need in enumerate(satisfies):
				if satisfy_need == need:
					break
			new_need = self.needs[need]['Current Need'] + (float(satisfy_rates[i]) * qty)
			if new_need < self.needs[need]['Max Need']:
				self.needs[need]['Current Need'] = new_need
			else:
				self.needs[need]['Current Need'] = self.needs[need]['Max Need']
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))


class Organization(Entity):
	def __init__(self, name):
		super().__init__(name)


class Corporation(Organization):
	def __init__(self, name, items):
		super().__init__(name)
		entity_data = [ (name,0.0,1,100,0.5,'iex',None,None,None,None,None,None,1000000,items) ] # Note: The 2nd to 5th values are for another program
		self.entity_id = accts.add_entity(entity_data)
		self.name = entity_data[0][0]
		self.produces = entity_data[0][13]
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		self.produces = list(filter(None, self.produces))
		print('Create Organization: {} | Produces: {} | entity_id: {}'.format(self.name, self.produces, self.entity_id))

	def __str__(self):
		return 'Corp: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Corp: {} | {}'.format(self.name, self.entity_id)

	def declare_div(self, div_rate): # TODO Move this to corporation subclass
		item = self.name
		shareholders = ledger.get_qty(items=item, accounts='Investments', by_entity=True)
		if shareholders.empty:
			return
		total_shares = shareholders['qty'].sum()
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		#print('{} cash: {}'.format(self.name, cash))
		if cash < total_shares * div_rate:
			print('{} does not have enough cash to pay dividend at a rate of {}.'.format(self.name, div_rate))
			return
		div_event = []
		for index, shareholder in shareholders.iterrows():
			shares = shareholder[2]
			counterparty_id = shareholder[0]
			# TODO Add div accrual entries and payments
			div_rev_entry = [ ledger.get_event(), counterparty_id, world.now, 'Dividend received for ' + item, item, div_rate, shares, 'Cash', 'Dividend Income', shares * div_rate ]
			div_event += [div_rev_entry]
		# TODO This should book against Retained Earnings
		div_exp_entry = [ ledger.get_event(), self.entity_id, world.now, 'Dividend payment for ' + item, item, div_rate, total_shares, 'Dividend Expense', 'Cash', total_shares * div_rate ]
		div_event += [div_exp_entry]
		ledger.journal_entry(div_event)

	def dividend(self):
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		#print('{} cash: {}'.format(self.name, cash))
		funding = ledger.balance_sheet(accounts=['Shares'], item=self.name)
		#print('{} funding: {}'.format(self.name, funding))
		ledger.reset()
		if cash >= funding * 2:
			self.declare_div(div_rate=1)

class Government(Organization):
	def __init__(self, name, items):
		super().__init__(name)

	def __str__(self):
		return 'Gov: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Gov: {} | {}'.format(self.name, self.entity_id)

class NonProfit(Organization):
	def __init__(self, name, items):
		super().__init__(name)

	def __str__(self):
		return 'Non-Profit: {} | {}'.format(self.name, self.entity_id)

	def __repr__(self):
		return 'Non-Profit: {} | {}'.format(self.name, self.entity_id)


class EntityFactory:
	def __init__(self):
		self.registry = {}
		self.registry[Individual] = []
		self.registry[Organization] = []
		self.registry[Corporation] = []
		self.registry[Government] = []
		self.registry[NonProfit] = []

	def create(self, cls, *args, **kwargs):
		entity = cls(*args, **kwargs)  # create the instance
		self.register_instance(entity) # add to registry
		return entity

	def register_instance(self, entity):
		typ = type(entity)
		if typ not in self.registry:
			self.registry[typ] = []
		self.registry[typ].append(entity)

	def destroy(self, entity):
		typ = type(entity)
		index = self.get_pos(entity)
		return self.registry[typ].pop(index)

	def get(self, typ):
		if not isinstance(typ, (list, tuple)):
			typ = [typ]
		orgs = []
		for el in typ:
			orgs += self.registry[el]
		return orgs

	def get_all(self):
		org_types = [*self.registry.keys()]
		return self.get(org_types)

	def get_pos(self, entity):
		typ = type(entity)
		for index, el in enumerate(self.get(typ)):
			if el.entity_id == entity.entity_id:
				return index

	def get_by_name(self, name):
		for typ in self.registry.keys():
			for entity in self.get(typ):
				if entity.name == name:
					#print('Entity by Name: {}'.format(entity))
					#print('Entity Name by Name: {}'.format(entity.name))
					return entity

	def get_by_id(self, entity_id):
		for typ in self.registry.keys():
			for entity in self.get(typ):
				if entity.entity_id == entity_id:
					#print('Entity by ID: {} | {}'.format(entity, entity.entity_id))
					#print('Entity Name by ID: {}'.format(entity.name))
					return entity

	def __str__(self):
		counts = {typ.__name__: len(reg) for typ, reg in self.registry.items()}
		return 'EntityFactory: ' + str(counts)

#def main():
	# TODO Ledger gives a not defined error
	#pass

if __name__ == '__main__':
	t0_start = time.perf_counter()
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-p', '--population', type=int, default=1, help='The number of people in the econ sim.')
	parser.add_argument('-r', '--random', action="store_false", help='Add some randomness to the sim!')
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
	args = parser.parse_args()
	if args.database is None:
		args.database = 'econ01.db'

	print(time_stamp() + 'Start Econ Sim')
	if (args.delay is not None) and (args.delay is not 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
	if args.random:
		if args.seed:
			print(time_stamp() + 'Randomness turned on with a seed of {}.'.format(args.seed))
			random.seed(args.seed)
		else:
			print(time_stamp() + 'Randomness turned on with no seed provided.')
			random.seed()
	delete_db(args.database)
	accts = Accounts(args.database, econ_accts)
	ledger = Ledger(accts)
	factory = EntityFactory()
	world = World(factory, args.population)

	while True:
		world.update_econ()
		if world.end:
			break
		time.sleep(args.delay)

	t0_end = time.perf_counter()
	print(time_stamp() + 'End of Econ Sim! It took {:,.2f} min.'.format((t0_end - t0_start) / 60))