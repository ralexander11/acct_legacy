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

DISPLAY_WIDTH = 98#130#
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

random.seed()

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

class World:
	def __init__(self, factory, population):
		self.clear_ledger()
		print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Create World ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))
		self.factory = factory
		self.items = accts.load_items('data/items.csv') # TODO Change config file to JSON
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

		for person in range(1, self.population + 1):
			print('Person: {}'.format(person))
			factory.create(Individual, 'Person ' + str(person))

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

	def check_end(self, v=False):
		population = len(factory.registry[Individual])
		if v: print('Population: {}'.format(population))
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
			price = 10
		else:
			price = 1
		#print('Price Function: {}'.format(price))
		return price

	def update_econ(self):
		t1_start = time.perf_counter()
		if str(self.now) == '1986-10-01':
			# TODO Pull shares authorized from entities table
			for individual in factory.get(Individual):
				individual.capitalize(amount=25000) # Hardcoded for now

		# TODO Maybe an update_world() method to adjust the needs and time
		print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Econ Updated ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))

		self.ticktock()
		self.check_end(v=True)
		if self.end:
			return
		t2_start = time.perf_counter()
		for individual in factory.get(Individual):
			print('Individual: {} | {}'.format(individual.name, individual.entity_id))
			individual.reset_hours()
			for need in individual.needs:
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
		print(ledger.get_qty(['Rock','Wood'], ['Inventory'], show_zeros=True, by_entity=True)) # Temp for testing
		print()

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
		for corporation in factory.get(Corporation):
			#print('Company Name: {} | {}'.format(corporation.name, corporation.entity_id))
			corporation.check_demand()
		t4_end = time.perf_counter()
		print(time_stamp() + '4: Demand list check took {:,.2f} min.'.format((t4_end - t4_start) / 60))
		print()
		t5_start = time.perf_counter()
		print('Check Optional Items:')
		for corporation in factory.get(Corporation):
			#print('Company Name: {} | {}'.format(corporation.name, corporation.entity_id))
			corporation.check_optional()
			corporation.dividend()
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
				ledger.set_entity(entity.entity_id)
				if 'Farm' in entity.name:
					entity.food = ledger.get_qty(items='Food', accounts=['Inventory'])
					#ledger.reset()
					print('{} Food: {}'.format(entity.name, entity.food))
				#ledger.set_entity(entity.entity_id)
				print('{} Cash: {}'.format(entity.name, ledger.balance_sheet(['Cash'])))
				ledger.reset()

			# Move first entity in list to the end, to switch things up
			lst = factory.get(typ)
			lst.append(lst.pop(0))

		t7_end = time.perf_counter()
		print(time_stamp() + '7: Cash check took {:,.2f} min.'.format((t7_end - t7_start) / 60))

		if args.random:
			if random.randint(1, 20) == 20:# or (str(self.now) == '1986-10-06'):
				print('Person randomly born!')
				self.entities = accts.get_entities()
				last_entity_id = self.entities.reset_index()['entity_id'].max()
				print('Last Entity ID: {}'.format(last_entity_id))
				factory.create(Individual, 'Person ' + str(last_entity_id + 1))
				individual = factory.get_by_id(last_entity_id + 1)
				individual.capitalize(amount=25000) # Hardcoded for now

		print()
		print('World Demand End: \n{}'.format(world.demand))
		print()
		print(ledger.get_qty(['Rock','Wood'], ['Inventory'], show_zeros=True, by_entity=True)) # Temp for testing

		if str(self.now) == '1986-10-08': # For debugging
			world.end = True

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
				print('Transaction for: {} {}'.format(qty, item))
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

		if global_qty >= qty or item_type == 'Service':
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
				if buffer:
					result = []
				while qty > 0:
					#print('QTY: {}'.format(qty))
					counterparty_id = global_inv.iloc[i].loc['entity_id']
					#print('Counterparty ID: {}'.format(counterparty_id))
					counterparty = factory.get_by_id(counterparty_id)
					#print('Purchase Counterparty: {}'.format(counterparty.name))
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
					qty -= purchase_qty
					i += 1
			if item_type == 'Service':
				print('{} trying to purchase Service: {}'.format(self.name, item))
				#if buffer:
					#outcome = counterparty.produce_entries(item=item, qty=qty, price=world.get_price(item))
				#else:
				outcome = counterparty.produce(item=item, qty=qty, price=world.get_price(item), buffer=buffer)
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
			self.adj_needs(item, qty)
		else:
			print('{} does not have enough {} available to use.'.format(self.name, item))

	def use_item(self, item, uses=1, buffer=False):
		incomplete, use_event, time_required = self.fulfill(item, qty=uses, reqs='usage_req', amts='use_amount')
		if incomplete:
			return
		orig_uses = uses
		lifespan = world.items['lifespan'][item]
		metric = world.items['metric'][item]
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

	def check_productivity(self, item):
		v = False
		# TODO Consider multiple modifiers simultaneously
		equip_list = ledger.get_qty(accounts=['Equipment'])
		if v: print('Equip List: \n{}'.format(equip_list))
		
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
		#print('Need Satisfy Rate: \n{}'.format(need_satisfy_rate))
		items_info = items_info.assign(efficiencies=efficiencies.values)
		items_info.reset_index(inplace=True)
		if v: print('Items Info: \n{}'.format(items_info))

		if not equip_list.empty and not items_info.empty:
			equip_info = equip_list.merge(items_info)
			equip_info.sort_values(by='efficiencies', ascending=False, inplace=True)
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
			print('{} used {} equipment to do {} task better by {}.'.format(self.name, items_info['item_id'].iloc[0], item, modifier))
			return modifier, items_info
		return None, None

	def get_item_type(self, item):
		if item in ['Land','Labour','Job','Equipment','Building','Subscription','Service','Commodity','Components','Technology','Education','Time','None']:
			return item
		else:
			return self.get_item_type(world.items.loc[item, 'child_of'])

	# TODO Proper costing, not to use price parameter
	# TODO Make each item take a certain amount of labour hours and have items able to reduce that
	# TODO Add WIP and COGS accounting
	def fulfill(self, item, qty, reqs='requirements', amts='amount'): # TODO Maybe add buffer=True
		v = False
		incomplete = False
		if qty == 0:
			return None, [], None
		event = []
		time_required = False
		item_info = world.items.loc[item]
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
			elif req_item_type == 'Building':
				building = ledger.get_qty(items=req_item, accounts=['Buildings'])
				if v: print('Building: {}'.format(land))
				if building < (req_qty * qty): # TODO FIx qty required
					if building == 0:
						print('{} does no have {} building to produce in. Will attempt to aquire some.'.format(self.name, req_item))
					print('{} does not have enough capacity in {} building to produce in. Will attempt to aquire some.'.format(self.name, req_item))
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(req_item, req_qty * qty, 'Building', buffer=True)
					# TODO Undecided if below produce() should be in final
					if not entries:
						entries = self.produce(req_item, qty=req_qty * qty, price=world.get_price(req_item))
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				if time_required: # TODO Handle land in use during one tick
					entries = self.in_use(req_item, req_qty * qty, world.get_price(req_item), 'Buildings', buffer=True)
					if not entries:
						entries = []
						incomplete = True
						#return
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
					if equip_qty == 0:
						print('{} does not have {} equipment to use. Will attempt to acquire some.'.format(self.name, req_item))
					else:
						print('{} not have enough capacity on {} equipment. Will attempt to aquire some.'.format(self.name, req_item))
					remaining_qty = (qty * req_qty) - (equip_qty * capacity)
					required_qty = math.ceil(remaining_qty / capacity)
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(req_item, required_qty, 'Equipment', buffer=True)
					# TODO Undecided if below produce() should be in final
					if not entries:
						entries = self.produce(req_item, required_qty, world.get_price(req_item))
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
					event += entries
				# else: # TODO Test that this works still
				# 	for _ in range(qty_to_use):
				# 		entries = self.use_item(req_item, buffer=True)
				# 		if not entries:
				# 			entries = []
				# 			incomplete = True
				# 			#return
				# 		event += entries

			elif req_item_type == 'Components':
				component_qty = ledger.get_qty(items=req_item, accounts=['Components'])
				if v: print('Land: {}'.format(component_qty))
				if component_qty < (req_qty * qty):
					print('{} does not have enough {} components. Will attempt to aquire some.'.format(self.name, req_item))
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(req_item, req_qty * qty, 'Components', buffer=True)
					if not entries:
						# TODO Uncomment below when item config is setup properly
						entries = self.produce(req_item, qty=req_qty * qty, price=world.get_price(req_item))
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
				entries += self.consume(req_item, qty=req_qty * qty)
				if not entries:
					entries = []
					incomplete = True
					#return
				event += entries

			elif req_item_type == 'Commodity':
				modifier, items_info = self.check_productivity(req_item)
				if modifier:
					event += self.use_item(items_info['item_id'].iloc[0], buffer=True)
				else:
					modifier = 1
				material_qty = ledger.get_qty(items=req_item, accounts=['Inventory'])
				if v: print('Land: {}'.format(material_qty))
				if material_qty < (req_qty * modifier * qty):
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
						entries = self.produce(req_item, qty=req_qty * qty, price=world.get_price(req_item))
					if not entries:
						entries = []
						incomplete = True
						#return
					event += entries
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
					entries = self.produce(req_item, qty=req_qty * qty, price=world.get_price(req_item))
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
				workers = ledger.get_qty(items=req_item, accounts=['Worker Info'])
				if v: print('Workers as {}: {}'.format(req_item, worker_state))
				# Get capacity amount
				capacity = world.items.loc[req_item, 'capacity']
				if capacity is None:
					capacity = 1
				capacity = float(capacity)
				print('Job: {} {} Capacity: {}'.format(workers, req_item, capacity))
				if ((workers * capacity) / (qty * req_qty)) < 1:
					remaining_qty = (qty * req_qty) - (workers * capacity)
					required_qty = math.ceil(remaining_qty / capacity)
					if workers <= 0:
						print('{} does not have a {} available to work. Will attempt to hire {}.'.format(self.name, req_item, required_qty))
					else:
						print('{} does not have enough capacity for {} jobs. Will attempt to hire {}.'.format(self.name, req_item, required_qty))
					for _ in range(required_qty):
						entries = self.hire_worker(job=req_item, counterparty=self.worker_counterparty(req_item), price=world.get_price(req_item), qty=1, buffer=True)
						if not entries:
							entries = []
							incomplete = True
							#return
						event += entries

			elif req_item_type == 'Labour':
				modifier, items_info = self.check_productivity(req_item)
				if modifier:
					event += self.use_item(items_info['item_id'].iloc[0], buffer=True)
				else:
					modifier = 1
				ledger.set_start_date(str(world.now))
				labour_done = ledger.get_qty(items=req_item, accounts=['Wages Expense'])
				ledger.reset()
				ledger.set_entity(self.entity_id)
				if v: print('Labour Done: {}'.format(labour_done))
				labour_required = (req_qty * modifier * qty)
				# Labourer does the amount they can, and get that value from the entries. Then add to the labour hours done and try again
				while labour_done < labour_required:
					required_hours = int(math.ceil((req_qty * modifier * qty) - labour_done))
					print('{} has not had enough {} labour done today for production. Will attempt to hire a worker for {} hours.'.format(self.name, req_item, required_hours))
					counterparty = self.worker_counterparty(req_item)
					if v: print('Wages Counterparty: {}'.format(counterparty.name))
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
			ledger.reset()
		if incomplete:
			print('{} cannot produce {} {} at this time.'.format(self.name, qty, item))
		return incomplete, event, time_required

	def produce(self, item, qty, price=None, debit_acct='Inventory', credit_acct='Goods Produced', buffer=False):
		if item not in self.produces: # TODO Should this be kept long term?
			return
		incomplete, produce_event, time_required = self.fulfill(item, qty)
		if incomplete:
			return
		produce_entry = []
		item_type = self.get_item_type(item)
		#print('Item Type: {}'.format(item_type))
		if price is None:
			price = world.get_price(item)
		if time_required and item_type != 'Service':
			produce_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' in process', item, price, qty, 'WIP Inventory', credit_acct, price * qty ]
		elif item_type != 'Service':
			produce_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' produced', item, price, qty, debit_acct, credit_acct, price * qty ]
		# Add all entries to same event and commit at the end once
		if produce_entry:
			produce_event += [produce_entry]
		if buffer:
			return produce_event
		# if not produce_event: # TODO Test if this is needed
		# 	return
		#print('Produce Event Final: \n{}'.format(produce_event))
		ledger.journal_entry(produce_event)
		return produce_event

	def wip_check(self):
		rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of WIP Inventory txns
		wip_txns = ledger.gl[(ledger.gl['debit_acct'] == 'WIP Inventory') & (ledger.gl['entity_id'] == self.entity_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		if not wip_txns.empty:
			# Compare the gl dates to the WIP time from the items table
			items_time = world.items[world.items['requirements'].str.contains('Time', na=False)]
			equip_continuous = world.items[world.items['freq'].str.contains('continuous', na=False)]
			for index, wip_lot in wip_txns.iterrows():
				item = wip_lot.loc['item_id']
				if item in equip_continuous.values:
					self.use_item(item)
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
					wip_entry = [[ wip_lot[0], wip_lot[1], world.now, wip_lot[4] + ' produced', wip_lot[4], wip_lot[5], wip_lot[6] or '', 'Inventory', wip_lot[7], wip_lot[9] ]]
					ledger.journal_entry(wip_entry)

	def capitalize(self, amount):
		capital_entry = [ ledger.get_event(), self.entity_id, world.now, 'Deposit capital', '', '', '', 'Cash', 'Wealth', amount ]
		capital_event = [capital_entry]
		ledger.journal_entry(capital_event)

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
		if qty == 0:
			for ticker in tickers:
				if ticker == 'Individual':
					#print('{} produced by individuals, no corporation needed.'.format(item))
					continue
				ledger.reset()
				corp_shares = ledger.get_qty(ticker, ['Investments'])
				#print('Corp Shares: \n{}'.format(corp_shares))
				if isinstance(corp_shares, pd.DataFrame): # TODO This is messy
					if corp_shares.empty:
						corp_shares = 0
					else:
						corp_shares = corp_shares.loc[0, 'qty']
					#print('Corp Shares After: \n{}'.format(corp_shares))
				if corp_shares == 0:
					corp = self.incorporate(item, name=ticker)
					item_type = self.get_item_type(item)
					if (item_type == 'Subscription' or item_type == 'Service') and demand_index is not None:
						world.demand = world.demand.drop([demand_index]).reset_index(drop=True)
					return corp

	def qty_demand(self, item, need=None):
		item_info = world.items.loc[item]
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
			item = items_info['item_id'].iloc[0]
			requirements = items_info[items_info['item_id'] == item]['requirements'].values[0]
			requirements = [x.strip() for x in requirements.split(',')]
			#print('Requirements: \n{}'.format(requirements))
			if 'Time' not in requirements:
				return
		item_type = self.get_item_type(item)
		# Check if entity already has item on demand list
		if not world.demand.empty:
			if item_type != 'Commodity':
				temp_df = world.demand[['entity_id','item_id']]
				#print('Temp DF: \n{}'.format(temp_df))
				temp_new_df = pd.DataFrame({'entity_id': self.entity_id, 'item_id': item}, index=[0])
				#print('Temp New DF: \n{}'.format(temp_new_df))
				#check = temp_df.intersection(temp_new_df)
				check = pd.merge(temp_df, temp_new_df, how='inner', on=['entity_id','item_id'])
				#print('Check: \n{}'.format(check))
				if not check.empty:
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
			qty = self.qty_demand(item, need)
		#print('Demand QTY: {}'.format(qty))
		if qty != 0:
			world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty}, ignore_index=True)
			print('{} added to demand list for {} units for {}.'.format(item, qty, self.name))
			#print('Demand after addition: \n{}'.format(world.demand))
			return item, qty

	def check_demand(self):
		for item in self.produces:
			#print('Check Demand Item: {}'.format(item))
			item_type = self.get_item_type(item)
			if item_type == 'Subscription':
				return
			#print('World Demand: \n{}'.format(world.demand))
			to_drop = []
			qty = 0
			# Filter for item and add up all qtys to support multiple entries
			for index, demand_row in world.demand.iterrows():
				#print('Index Loop: {}'.format(index))
				#print('Produces Item: {}'.format(item))
				#print('Demand Item: {}'.format(demand_row['item_id']))
				if demand_row['item_id'] == item:
					qty += demand_row['qty']
					to_drop.append(index)
			if qty == 0:
				continue
			print('{} attempting to produce {} {} from the demand table.'.format(self.name, qty, item))
			outcome = self.produce(item=item, qty=qty, price=world.get_price(item))
			if outcome:
				#print('Indexes To Drop: \n{}'.format(to_drop))
				#print('Demand Before Drop: \n{}'.format(world.demand))
				world.demand = world.demand.drop(to_drop).reset_index(drop=True)
				print('{} removed from demand list for {} units by {}.'.format(item, qty, self.name))
				#print('Demand After Drop: \n{}'.format(world.demand))

	def check_optional(self):
		# In corporation loop, check for for items that satisfy requirements for items from the produces items list.
		items_list = world.items[world.items['producer'] != None]
		#print('Items List: \n{}'.format(items_list))
		for item in self.produces:
			#print('Produces Item: {}'.format(item))
			# Get list of requirements and iterate through it
			requirements = world.items.loc[item, 'requirements']
			if isinstance(requirements, str):
				requirements = [x.strip() for x in requirements.split(',')]
			requirements = list(filter(None, requirements))
			#print('Requirements: \n{}'.format(requirements))
			# Filter items list for last column not equal None
			possible_items = items_list.loc[items_list['productivity'].isin(requirements)].reset_index()
			#print('Possible Items: \n{}'.format(possible_items))
			# If required item is on the filtered list, do below
			for index, item in possible_items.iterrows():
				item_type = self.get_item_type(item['item_id'])
				current_qty = ledger.get_qty(item['item_id'], [item_type])
				#print('Current QTY of {}: {}'.format(item['item_id'], current_qty))
				if current_qty == 0:
					self.purchase(item['item_id'], qty=1, acct_buy='Equipment')

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
				return claim_land_event
			# if not claim_land_event:
			# 	return
			ledger.journal_entry(claim_land_event)
			return True
		else:
			print('Not enough {} available to claim {} square meters for {}.'.format(item, qty, self.name))

	def get_counterparty(self, txns, rvsl_txns, item, account):
		#print('Item: {}'.format(item))
		txn = txns.loc[txns['item_id'] == item]
		#print('TXN: \n{}'.format(txn))
		if txn.empty:
			print('No counterparty exists for {}.'.format(item))
			return
		event_id = txn.iloc[0].loc['event_id']
		#print('Event ID: {}'.format(event_id))
		event_txns = ledger.gl[(ledger.gl['event_id'] == event_id) & (~ledger.gl['event_id'].isin(rvsl_txns))]
		#print('Event TXNs: \n{}'.format(event_txns))
		item_txn = event_txns.loc[event_txns['item_id'] == item] # If there are multiple items
		#print('Item TXN: \n{}'.format(item_txn))
		counterparty_txn = item_txn.loc[item_txn['debit_acct'] == account]
		#print('Counterparty TXN: \n{}'.format(counterparty_txn))
		counterparty_id = counterparty_txn.iloc[0].loc['entity_id']
		#print('Counterparty ID: {}'.format(counterparty_id))
		counterparty = factory.get_by_id(counterparty_id)
		while True:
			if counterparty is not None:
				break
			counterparty_id += 1
			counterparty = factory.get_by_id(counterparty_id)
		#print('Counterparty: {}'.format(counterparty))
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
				print('No wages payable to pay for {} work.'.format(job))
			elif cash >= wages_payable:
				# Get counterparty
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				wages_pay_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Wages Expense') & (ledger.gl['credit_acct'] == 'Wages Payable') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				#wages_pay_txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Wages Receivable') & (ledger.gl['credit_acct'] == 'Wages Revenue') ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				counterparty = self.get_counterparty(wages_pay_txns, rvsl_txns, job, 'Wages Receivable')
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

	def worker_counterparty(self, job):
		print('Job: {}'.format(job))
		item_type = self.get_item_type(job)
		workers = {}
		# Get list of all individuals
		world.entities = accts.get_entities()
		# Check total wages receivable for that job for each individual
		for individual in factory.get(Individual):
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
		workers_avail = {worker: v for worker, v in workers.items() if worker.hours > base_hours}
		if not workers_avail:
			return
		# Choose the worker with the most experience
		worker_choosen = max(workers_avail, key=lambda k: workers_avail[k])
		print('Worker Choosen: {}'.format(worker_choosen.name))
		return worker_choosen

	def accru_wages(self, job, counterparty, wage, labour_hours, buffer=False):
		if counterparty is None:
			print('No workers available to do {} job for {} hours.'.format(job, labour_hours))
			return
		recently_paid = self.check_wages(job)
		incomplete, accru_wages_event, time_required = self.fulfill(job, qty=labour_hours, reqs='usage_req', amts='use_amount')
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
				return accru_wages_event
			ledger.journal_entry(accru_wages_event)
			counterparty.set_hours(hours_worked)
		else:
			print('Wages have not been paid for {} recently by {}.'.format(job, self.name))
			return

	def hire_worker(self, job, counterparty, price=0, qty=1, buffer=False):
		incomplete, hire_worker_event, time_required = self.fulfill(job, qty)
		if incomplete:
			return
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
			return hire_worker_event
		ledger.journal_entry(hire_worker_event)

	def fire_worker(self, job, counterparty, price=0, qty=-1, buffer=False):
		fire_worker_entry = [ ledger.get_event(), self.entity_id, world.now, 'Fired ' + job, job, price, qty, 'Worker Info', 'Fire Worker', 0 ]
		quit_job_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Quit job as ' + job, job, price, qty, 'Quit Job', 'Worker Info', 0 ]
		fire_worker_event = [fire_worker_entry, quit_job_entry]
		if buffer:
			return fire_worker_event
		ledger.journal_entry(fire_worker_event)

	def check_salary(self, job=None, counterparty=None):
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
				self.pay_salary(job, counterparty)
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
				counterparty = self.get_counterparty(salary_txns, rvsl_txns, item, 'Start Job')
				for _ in range(worker_state):
					self.pay_salary(job['item_id'], counterparty)

	def pay_salary(self, job, counterparty, salary=None, labour_hours=None, buffer=False, first=False):
		# TODO Add accru_salary()
		if type(counterparty) != Individual: # TODO Cleanup, this is due to error from inheritance going to a Corporation
			print('Counterparty is not an Individual, it is {} | {}'.format(counterparty.name, counterparty.entity_id))
			return
		incomplete, pay_salary_event, time_required = self.fulfill(job, qty=1, reqs='usage_req', amts='use_amount')
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

	def check_subscriptions(self, counterparty=None):
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
				self.pay_subscription(subscription['item_id'], counterparty, world.get_price(subscription['item_id']), subscription['qty'])

	def pay_subscription(self, item, counterparty, price=None, qty='', buffer=False, first=False):
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
		for _ in range(subscription_state):
			incomplete, pay_subscription_event, time_required = self.fulfill(item, qty=1, reqs='usage_req', amts='use_amount')
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if cash >= price and not incomplete:
				pay_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Payment for ' + item, item, price, qty, 'Subscription Expense', 'Cash', price ]
				charge_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Received payment for ' + item, item, price, qty, 'Cash', 'Subscription Revenue', price ]
				pay_subscription_event += [pay_subscription_entry, charge_subscription_entry]
				if buffer:
					return pay_subscription_event
				ledger.journal_entry(pay_subscription_event)
				return True
			else:
				if not incomplete:
					print('{} does not have enough cash to pay for {} subscription. Cash: {}'.format(self.name, job, cash))
				else:
					print('{} cannot fulfill the requirements to keep {} subscription.'.format(self.name, item))
				if not first:
					self.cancel_subscription(item, counterparty)

	def collect_material(self, item, qty, price=None, account=None): # TODO Make cost based on time spent and salary
		if price is None:
			price = world.get_price(item)
		if account is None:
			account = 'Inventory'
		collect_mat_entry = [ ledger.get_event(), self.entity_id, world.now, 'Forage ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		collect_mat_event = [collect_mat_entry]
		ledger.journal_entry(collect_mat_event)
		return qty * 1 # TODO Spend time collecting food, wood, ore
		# TODO Check if enough land and return insufficient if not

	def find_item(self, item, qty, price=None, account=None): # Assuming all materials found
		if price is None:
			price = world.get_price(item)
		if account is None:
			account = 'Equipment'
		find_item_entry = [ ledger.get_event(), self.entity_id, world.now, 'Find ' + item, item, price, qty, account, 'Natural Wealth', qty * price ]
		find_item_event = [find_item_entry]
		ledger.journal_entry(find_item_event)
		return qty * 10 # TODO Spend time finding item

	def depreciation_check(self, items=None): # TODO Add support for explicitly provided items
		if items is None:
			ledger.set_entity(self.entity_id)
			items_list = ledger.get_qty(accounts=['Buildings','Equipment','Furniture','Inventory'])
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
			asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment'], item=item) # TODO Support other accounts like Tools
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

	def derecognize(self, item, qty):
		# TODO Check if item in use
		asset_bal = ledger.balance_sheet(accounts=['Equipment'], item=item)# TODO Support other accounts
		if asset_bal == 0:
				return
		accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
		if asset_bal == abs(accum_dep_bal):
			derecognition_entry = [ ledger.get_event(), self.entity_id, world.now, 'Derecognition of ' + item, item, asset_bal / qty, qty, 'Accumulated Depreciation', 'Equipment', asset_bal ]
			derecognition_event = [derecognition_entry]
			ledger.journal_entry(derecognition_event)


class Individual(Entity):
	def __init__(self, name):
		super().__init__(name)
		hunger_start = 50
		if args.random:
			hunger_start = random.randint(30, 100)
		# TODO Make starting need levels random
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Fun, Thirst','100,100,100','1,5,2','40,40,60','50,100,100',None,'Labour') ] # Note: The 2nd to 5th values are for another program
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Hygiene, Thirst, Fun','100,100,100,100','1,1,2,5','40,50,60,40', str(hunger_start) + ',80,100,100',None,'Labour') ]
		entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Hygiene, Thirst','100,100,100','1,1,2','40,50,60', str(hunger_start) + ',80,100',None,'Labour') ]
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Thirst','100,100','1,2','40,60','50,100',None,'Labour') ]
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger','100','1','40','50',None,'Labour') ]

		self.entity_id = accts.add_entity(entity_data)
		self.name = entity_data[0][0]
		self.dead = False
		#self.entity_id = 1 # TODO Have this read from the entities table
		print('Create Individual: {} | entity_id: {}'.format(self.name, self.entity_id))
		self.hours = entity_data[0][6]
		self.setup_needs(entity_data)
		for need in self.needs:
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))

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
		MAX_HOURS = 12
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

	def set_need(self, need, need_delta):
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
			print('{} died due to {}.'.format(self.name, need))
			#world.end = True
			self.dead = True
		return self.needs[need]['Current Need']

	def inheritance(self):
		individuals = itertools.cycle(factory.get(Individual))
		nextindv = next(individuals) # Prime the pump
		while True:
			individual, nextindv = nextindv, next(individuals)
			# print('Individual: {}'.format(individual.name))
			# print('Next Individual: {}'.format(nextindv.name))
			if individual.entity_id == self.entity_id:
				counterparty = nextindv
				break
		print('Inheritance counterparty: {}'.format(counterparty.entity_id))
		ledger.set_entity(self.entity_id)
		consolidated_gl = ledger.gl.groupby(['item_id','debit_acct','credit_acct']).sum()
		ledger.reset()
		inherit_event = []
		for index, entry in consolidated_gl.iterrows():
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
					#ledger.set_entity(world.farm.entity_id)
					# TODO Assumes only one entity has all available qty
					qty_avail = ledger.get_qty(items=item_choosen, accounts=['Inventory'])
					if qty_avail == 0:
						qty_avail = qty_wanted # So purchase for 0 qty is not attempted
					qty_purchase = min(qty_wanted, qty_avail)
					print('Satisfy need by purchasing: {} {}'.format(qty_purchase, item_choosen))
					outcome = self.purchase(item_choosen, qty_purchase)
					# TODO Generalize this for other entities
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
				if qty_held == 0:
					qty_purchase = 1
					metric = items_info['metric'].iloc[index]
					if metric == 'usage':
						lifespan = items_info['lifespan'].iloc[index]
						qty_purchase = math.ceil(uses_needed / lifespan)
					outcome = self.purchase(item_choosen, qty_purchase)
				if qty_held > 0 or outcome:
					self.use_item(item_choosen, uses_needed)
			# if not outcome and item_type != 'Subscription':
			# 	print('Add {} {} to demand list for {}.'.format(qty_purchase, item_choosen, self.name))
			# 	self.item_demanded(item_choosen, qty_purchase)

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
		self.name = entity_data[0][0] # TODO Change this to pull from entities table
		self.produces = entity_data[0][13]
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		self.produces = list(filter(None, self.produces))
		print('Create Organization: {} | Produces: {} | entity_id: {}'.format(self.name, self.produces, self.entity_id))

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

class NonProfit(Organization):
	def __init__(self, name, items):
		super().__init__(name)


class EntityFactory:
	def __init__(self):
		self.registry = {}

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

	def get(self, *typ):
		orgs = []
		for el in typ:
			orgs += self.registry[el]
		return orgs

	def get_pos(self, entity):
		typ = type(entity)
		for index, el in enumerate(factory.get(typ)):
			if el.entity_id == entity.entity_id:
				return index

	def get_by_name(self, name):
		for typ in factory.registry.keys():
			for entity in factory.get(typ):
				if entity.name == name:
					#print('Entity by Name: {}'.format(entity))
					#print('Entity Name by Name: {}'.format(entity.name))
					return entity

	def get_by_id(self, entity_id):
		for typ in factory.registry.keys():
			for entity in factory.get(typ):
				if entity.entity_id == entity_id:
					#print('Entity by ID: {} | {}'.format(entity, entity.entity_id))
					#print('Entity Name by ID: {}'.format(entity.name))
					return entity

	def __str__(self):
		counts = {typ.__name__: len(reg) for typ, reg in self.registry.items()}
		return 'RegistryFactory: ' + str(counts)


if __name__ == '__main__':
	t0_start = time.perf_counter()
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-p', '--population', type=int, default=1, help='The number of people in the econ sim.')
	parser.add_argument('-r', '--random', action="store_true", help='Add some randomness to the sim!')
	args = parser.parse_args()
	if args.database is None:
		args.database = 'econ01.db'

	print(time_stamp() + 'Start Econ Sim')
	if (args.delay is not None) and (args.delay is not 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
	if args.random:
		print(time_stamp() + 'Randomness turned on.')
	delete_db(args.database)
	accts = Accounts(args.database)
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