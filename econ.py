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

DISPLAY_WIDTH = 98#130#
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
		self.create_land('Arable Land', 32000)
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
		else:
			price = 1
		#print('Price Function: {}'.format(price))
		return price

	def update_econ(self):
		if str(self.now) == '1986-10-01':
			# TODO Pull shares authorized from entities table
			for individual in factory.get(Individual):
				individual.capitalize(amount=25000) # Hardcoded for now

		# TODO Maybe an update_world() method to adjust the needs and time
		print(('=' * ((DISPLAY_WIDTH - 14) // 2)) + ' Econ Updated ' + ('=' * ((DISPLAY_WIDTH - 14) // 2)))

		self.ticktock()
		for individual in factory.get(Individual):
			print('Individual Name: {} | {}'.format(individual.name, individual.entity_id))
			individual.reset_hours()
			for need in individual.needs:
				individual.corp_needed(need=need)
				individual.need_decay(need)
				print('{} {} Need: {}'.format(individual.name, need, individual.needs[need]['Current Need']))
				individual.item_demanded(need=need)
			for index, item in world.demand.iterrows():
				#print('Corp Check Demand Item: {}'.format(item['item_id']))
				individual.corp_needed(item=item['item_id'], demand_index=index)
		print('World Demand Start: \n{}'.format(world.demand))

		for typ in factory.registry.keys():
			#print('Entity Type: {}'.format(typ))
			for entity in factory.get(typ):
				#print('Entity: {}'.format(entity))
				#print('Entity Name: {} | {}'.format(entity.name, entity.entity_id))
				entity.depreciation_check()
				entity.wip_check()
				entity.check_subscriptions()
				entity.check_salary()
				entity.pay_wages()

		print('Check Demand List:')
		for organization in factory.get(Organization):
			print('Company Name: {} | {}'.format(organization.name, organization.entity_id))
			organization.check_demand()
		print('Check Optional Items:')
		for organization in factory.get(Organization):
			print('Company Name: {} | {}'.format(organization.name, organization.entity_id))
			organization.check_optional()

		for individual in factory.get(Individual):
			#print('Individual Name: {} | {}'.format(individual.name, individual.entity_id))
			for need in individual.needs:
				individual.threshold_check(need)

		for individual in factory.get(Individual):
			individual.finish_hours()

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

		print('World Demand End: \n{}'.format(world.demand))

		if str(self.now) == '1986-10-08': # For debugging
			world.end = True


class Entity:
	def __init__(self, name):
		self.name = name
		#print('Entity created: {}'.format(name))

	def transact(self, item, price, qty, counterparty, acct_buy='Inventory', acct_sell='Inventory', item_type=None, buffer=False):
		if qty == 0:
			return
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
				print('Purchase: {} {}'.format(qty, item))
				purchase_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' purchased', item, price, qty, acct_buy, 'Cash', price * qty ]
				sell_entry = [ ledger.get_event(), counterparty.entity_id, world.now, item + ' sold', item, price, qty, 'Cash', acct_sell, price * qty ]
				purchase_event = [purchase_entry, sell_entry]
				if buffer:
					return purchase_event
				ledger.journal_entry(purchase_event)
				return True
			else:
				print('Not enough {} on hand to sell {} units of {}.'.format(item, qty, item))
		else:
			print('Not enough cash to purchase {} units of {}.'.format(qty, item))

	def purchase(self, item, qty, acct_buy='Inventory', acct_sell='Inventory', buffer=False):
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
				print('No {} to offer {} service. Will add it to the demand table'.format(producer, item))
				if producer is not None and producer != 'Individual':
					self.item_demanded(item, qty)
				return
			acct_buy = 'Service Expense'
			acct_sell = 'Service Revenue'
		ledger.reset()
		global_qty = ledger.get_qty(items=item, accounts=['Inventory'])
		print('Global QTY of {} for purchase: {}'.format(item, global_qty))
		if global_qty >= qty or item_type == 'Service':
			# Check which entity has the goods for the cheapest
			if item_type != 'Service':
				rvsl_txns = ledger.gl[ledger.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
				txns = ledger.gl[( (ledger.gl['debit_acct'] == 'Inventory') & (ledger.gl['item_id'] == item) ) & (~ledger.gl['event_id'].isin(rvsl_txns))]
				#print('Purchase TXNs: \n{}'.format(txns))
				counterparty = self.get_counterparty(txns, rvsl_txns, item, 'Inventory')
				if counterparty is None:
					producer = world.items.loc[item, 'producer']
					print('No {} to offer {} {}. Will add it to the demand table'.format(producer, item, item_type))
					if producer is not None and producer != 'Individual':
						self.item_demanded(item, qty)
					return
			if item_type == 'Service':
				print('Try to purchase Service: {}'.format(item))
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
			print('Purchase Counterparty: {}'.format(counterparty.name))
			result = self.transact(item, price=world.get_price(item), qty=qty, counterparty=counterparty, acct_buy=acct_buy, acct_sell=acct_sell, item_type=item_type, buffer=buffer)
			#print('Purchase Result: {} {} \n{}'.format(qty, item, result))
			if outcome and buffer:
				result = outcome + result
				#print('Buffer Result: \n{}'.format(result))
			return result
		else:
			print('Not enough quantity of {} to purchase {} units.'.format(item, qty))
			producer = world.items.loc[item, 'producer']
			#print('Producer: {}'.format(producer))
			if producer is not None and producer != 'Individual': # TODO Is this needed? Need to support multiple producers? Is this for items produced by Individuals?
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
			print('Not enough {} on hand to consume {} units of {}.'.format(item, qty, item))

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
			print('Not enough {} available to use.'.format(item))

	def use_item(self, item, uses=1, buffer=False):
		lifespan = world.items['lifespan'][item]
		metric = world.items['metric'][item]
		entries, uses = self.depreciation(item, lifespan, metric, uses, buffer)
		if entries:
			try:
				self.adj_needs(item, uses)
			except AttributeError as e:
				#print('Organizations do not have needs: {} | {}'.format(e, repr(e)))
				return entries
			return entries

	def get_item_type(self, item):
		if item in ['Land','Labour','Equipment','Building','Subscription','Service','Commodity','Components','Technology','Education','Time','None']:
			return item
		else:
			return self.get_item_type(world.items.loc[item, 'child_of'])

	# TODO Proper costing, not to use price parameter
	# TODO Make each item take a certain amount of labour hours and have items able to reduce that
	# TODO Add WIP accounting and COGS
	def produce_entries(self, item, qty, price=None, debit_acct='Inventory', credit_acct='Goods Produced'):
		v = False
		if qty == 0:
			return
		produce_event = []
		time_required = False
		item_type = self.get_item_type(item)
		cur = ledger.conn.cursor()
		requirements_info = cur.execute("SELECT requirements, amount FROM items WHERE item_id = '"+ item +"';").fetchone() # TODO Maybe get from items dataframe
		cur.close()
		if v: print('From Table: {}'.format(requirements_info))
		requirements = [x.strip() for x in requirements_info[0].split(',')]
		if v: print('Requirements Split: {}'.format(requirements))
		requirement_details = []
		for requirement in requirements:
			if v: print('Requirement: {}'.format(requirement))
			requirement_type = self.get_item_type(requirement)
			item_details = (requirement, requirement_type)
			requirement_details.append(item_details)
		if v: print('Requirements: {}'.format(requirement_details))
		amounts = [x.strip() for x in requirements_info[1].split(',')]
		amounts = list(map(float, amounts))
		if v: print('Amounts: {}'.format(amounts))
		requirement_details = list(zip(requirement_details, amounts))
		if v: print('Requirement Details: {}'.format(requirement_details))
		# TODO Sort so requirements with a capacity are first after time
		for requirement in requirement_details:
			ledger.set_entity(self.entity_id)
			if v: print('Requirement: {} {}'.format(requirement, requirement[0][1]))
			if requirement[0][1] == 'Time':
				time_required = True
				if v: print('Time Required: {}'.format(time_required))
			elif requirement[0][1] == 'Land':
				land = ledger.get_qty(items=requirement[0][0], accounts=['Land'])
				if v: print('Land: {}'.format(land))
				if land < (requirement[1] * qty):
					print('Not enough {} to produce on. Will attempt to claim {} square meters.'.format(requirement[0][0], (requirement[1] * qty) - land))
					needed_qty = (requirement[1] * qty) - land
					# Attempt to purchase land
					entries = self.purchase(requirement[0][0], requirement[1] * qty, 'Land', buffer=True)
					if not entries:
						entries = self.claim_land(needed_qty, price=world.get_price(requirement[0][0]), item=requirement[0][0], buffer=True)
						#print('Land Entries: \n{}'.format(entries))
						if entries is None:
							return
					produce_event += entries
				if time_required: # TODO Handle land in use during one tick
					entries = self.in_use(requirement[0][0], requirement[1] * qty, world.get_price(requirement[0][0]), 'Land', buffer=True)
					#print('Land In Use Entries: \n{}'.format(entries))
					if entries is None:
						return
					produce_event += entries
			elif requirement[0][1] == 'Building':
				building = ledger.get_qty(items=requirement[0][0], accounts=['Buildings'])
				if v: print('Building: {}'.format(land))
				if building < (requirement[1] * qty): # TODO FIx qty required
					if building == 0:
						print('No {} building to produce in. Will attempt to aquire some.'.format(requirement[0][0]))
					print('Not enough capacity in {} building to produce in. Will attempt to aquire some.'.format(requirement[0][0]))
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(requirement[0][0], requirement[1] * qty, 'Building', buffer=True)
					if not entries:
						entries = self.produce_entries(requirement[0][0], qty=requirement[1] * qty, price=world.get_price(requirement[0][0]))
						if entries is None:
							return
					produce_event += entries
					#return
				if time_required: # TODO Handle land in use during one tick
					entries = self.in_use(requirement[0][0], requirement[1] * qty, world.get_price(requirement[0][0]), 'Buildings', buffer=True)
					if entries is None:
						return
					produce_event += entries

			elif requirement[0][1] == 'Equipment': # TODO Make generic for process
				equip_qty = ledger.get_qty(items=requirement[0][0], accounts=['Equipment'])
				if v: print('Equipment: {} {}'.format(equip_qty, requirement[0][0]))
				if ((equip_qty * requirement[1]) / qty) < 1: # TODO Test turning requirement into capacity
					if equip_qty == 0:
						print('No {} equipment to use. Will attempt to aquire some.'.format(requirement[0][0]))
					else:
						print('Not enough capacity on {} equipment. Will attempt to aquire some.'.format(requirement[0][0]))
					remaining_qty = qty - (equip_qty * requirement[1])
					required_qty = math.ceil(remaining_qty / requirement[1])
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(requirement[0][0], requirement[1] * qty, 'Equipment', buffer=True)
					if not entries:
						entries = self.produce_entries(requirement[0][0], required_qty, world.get_price(requirement[0][0]))
						if entries is None:
							return
					produce_event += entries
					#return
				qty_in_use = math.ceil(qty / requirement[1])
				if time_required: # TODO Handle land in use during one tick
					entries = self.in_use(requirement[0][0], qty_in_use, world.get_price(requirement[0][0]), 'Equipment', buffer=True)
					if entries is None:
						return
					produce_event += entries
					for _ in range(qty_in_use):
						produce_event += self.use_item(requirement[0][0], buffer=True)
				else:
					for _ in range(qty_in_use):
						produce_event += self.use_item(requirement[0][0], buffer=True)

			elif requirement[0][1] == 'Components':
				component_qty = ledger.get_qty(items=requirement[0][0], accounts=['Components'])
				if v: print('Land: {}'.format(component_qty))
				if component_qty < (requirement[1] * qty):
					print('Not enough {} components. Will attempt to aquire some.'.format(requirement[0][0]))
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(requirement[0][0], requirement[1] * qty, 'Components', buffer=True)
					if not entries:
						# TODO Uncomment below when item config is setup properly
						# entries = self.produce_entries(requirement[0][0], qty=requirement[1] * qty, price=world.get_price(requirement[0][0]))
						# if entries is None:
						# 	return
						return
					produce_event += entries
					#return
				entries += self.consume(requirement[0][0], qty=requirement[1] * qty)
				if entries is None:
					return
				produce_event += entries

			elif requirement[0][1] == 'Commodity':
				material_qty = ledger.get_qty(items=requirement[0][0], accounts=['Inventory'])
				if v: print('Land: {}'.format(material_qty))
				if material_qty < (requirement[1] * qty):
					print('Not enough commodity: {}. Will attempt to aquire some.'.format(requirement[0][0]))
					# Attempt to purchase before producing self if makes sense
					entries = self.purchase(requirement[0][0], requirement[1] * qty, 'Inventory', buffer=True)
					if not entries:
						# TODO Uncomment below when item config is setup properly
						# entries = self.produce_entries(requirement[0][0], qty=requirement[1] * qty, price=world.get_price(requirement[0][0]))
						# if entries is None:
						# 	return
						return
					produce_event += entries
					#return
				entries = self.consume(requirement[0][0], qty=requirement[1] * qty, buffer=True)
				if entries is None:
					return
				produce_event += entries

			elif requirement[0][1] == 'Subscription': # TODO Add check to ensure payment has been made recently (maybe on day of)
				subscription_state = ledger.get_qty(items=requirement[0][0], accounts=['Subscription Info'])
				if v: print('Subscription State for {}: {}'.format(requirement[0][0], subscription_state))
				if not subscription_state:
					print('{} subscription is not active. Will attempt to activate it.'.format(requirement[0][0]))
					entries = self.order_subscription(item=requirement[0][0], counterparty=self.subscription_counterparty(requirement[0][0]), price=world.get_price(requirement[0][0]), qty=1, buffer=True)
					if entries is None:
						return
					produce_event += entries
					#return

			elif requirement[0][1] == 'Service':
				# Get entity that provides service and have them call the purchase func
				# producers = world.items.loc[requirement[0][0], 'producer']
				# if isinstance(producers, str):
				# 	producers = [x.strip() for x in producers.split(',')]
				# producers = list(set(filter(None, producers)))
				# if v: print('Producers: {}'.format(producers))
				# producer = producers[0] # TODO Better handle multiple producers
				# counterparty = factory.get_by_name(producer)
				# if counterparty is None:
				# 	print('No {} to offer {} service. Will create demand for service.'.format(producer, requirement[0][0]))
				# 	self.item_demanded(requirement[0][0], requirement[1] * qty)
				# 	return
					#entries = self.purchase(requirement[0][0], requirement[1] * qty, buffer=True)
				entries = self.purchase(requirement[0][0], requirement[1] * qty, buffer=True)
				if entries is None:
					return
				produce_event += entries
				#return

			elif requirement[0][1] == 'Labour': # TODO How to handle multiple workers
				modifier = 1
				# TODO Get list of all equipment that covers the requirement
				equip_list = ledger.get_qty(accounts=['Equipment'])#, v_qty=True)
				if v: print('Equip List: \n{}'.format(equip_list))
				
				items_data = world.items[world.items['satisfies'].str.contains(requirement[0][0], na=False)] # Supports if item satisfies multiple needs
				items_data.reset_index(inplace=True)
				if v: print('Items Data: \n{}'.format(items_data))

				if not equip_list.empty and not items_data.empty:
					equip_info = equip_list.merge(items_data)
					equip_info.sort_values(by='satisfy_rate', ascending=False, inplace=True)
					if v: print('Items Table Merged: \n{}'.format(equip_info))
					modifier = 1 / equip_info['satisfy_rate'].iloc[0]
					if v: print('Modifier: {}'.format(modifier))
					# Book deprecition on use of item
					print('Used {} equipment to do {} task better.'.format(items_data['item_id'].iloc[0], requirement[0][0]))
					produce_event += self.use_item(items_data['item_id'].iloc[0], buffer=True)

				# TODO Factor in equipment capacity and WIP time

				ledger.set_start_date(str(world.now))
				labour_done = ledger.get_qty(items=requirement[0][0], accounts=['Salary Expense'])
				ledger.reset()
				if v: print('Labour Done: {}'.format(labour_done))
				if labour_done < (requirement[1] * modifier * qty):
					required_hours = int(math.ceil((requirement[1] * modifier * qty) - labour_done))
					print('Not enough {} labour done today for production. Will attempt to hire a worker for {} hours.'.format(requirement[0][0], required_hours))
					counterparty = self.wages_counterparty(requirement[0][0])
					if v: print('Wages Counterparty: {}'.format(counterparty.name))
					entries = self.accru_wages(job=requirement[0][0], counterparty=counterparty, wage=world.get_price(requirement[0][0]), labour_hours=required_hours, buffer=True)
					if entries is None:
						return
					produce_event += entries
					counterparty.set_hours(required_hours)
					#return
			ledger.reset()
		#print('Item Type: {}'.format(item_type))
		produce_entry = []
		if time_required and item_type != 'Service':
			produce_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' in process', item, price, qty, 'WIP Inventory', credit_acct, price * qty ]
		elif item_type != 'Service':
			produce_entry = [ ledger.get_event(), self.entity_id, world.now, item + ' produced', item, price, qty, debit_acct, credit_acct, price * qty ]
		# Add all entries to same event during buffersion and commit at the end once
		if produce_entry:
			produce_event += [produce_entry]
		#print('Produce Event: \n{}'.format(produce_event))
		return produce_event

	def produce(self, item, qty, price=None, debit_acct='Inventory', credit_acct='Goods Produced', buffer=False):
		produce_event = self.produce_entries(item, qty, price, debit_acct, credit_acct)
		if not produce_event:
			return
		if buffer:
			return produce_event
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

	# Logic to make individuals incorporate companies without human input
	def incorporate(self, item=None, price=None, qty=None, ticker=None):
		if price is None: # TODO Fix temp defaults
			price = 5
		if qty is None:
			qty = 1000
		auth_qty = 100000 # TODO Get from entity details
		if ticker is None and item is not None:
			#items_info = accts.get_items()
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			tickers = list(set(filter(None, tickers)))
			ticker = tickers[0]
			#print('Ticker: {}'.format(ticker))
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		#print('Cash: {}'.format(cash))
		if price * qty > cash:
			print('Not enough cash to incorporate {}.'.format(ticker))
			return
		items_produced = world.items[world.items['producer'].str.contains(ticker, na=False)].reset_index()
		items_produced = items_produced['item_id'].tolist()
		items_produced = ','.join(items_produced)
		#print('Items Produced: {}'.format(items_produced))
		corp = factory.create(Organization, ticker, items_produced)
		counterparty = corp
		self.auth_shares(ticker, auth_qty, counterparty)
		self.buy_shares(ticker, price, qty, counterparty)
		return corp

	def corp_needed(self, item=None, need=None, ticker=None,demand_index=None):
		# Choose best item
		#print('Need Demand: {}'.format(need))
		if item is None and need is not None:
			#items_info = accts.get_items()
			#print('Items Info: \n{}'.format(items_info))
			items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
			items_info = items_info.sort_values(by='satisfy_rate', ascending=False)
			items_info.reset_index(inplace=True)
			item = items_info['item_id'].iloc[0]
			#print('Item Choosen: {}'.format(item))
		if ticker is None:
			#items_info = accts.get_items()
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			tickers = list(set(filter(None, tickers))) # Use set to ensure no dupes
			#print('Tickers: {}'.format(tickers))
			# TODO If ticker already exist, add number to this that increments so multiple of the same business can be made
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
				if isinstance(corp_shares, pd.DataFrame):
					if corp_shares.empty:
						corp_shares = 0
					else:
						corp_shares = corp_shares.loc[0, 'qty']
					#print('Corp Shares After: \n{}'.format(corp_shares))
				if corp_shares == 0:
					corp = self.incorporate(item, ticker=ticker)
					item_type = self.get_item_type(item)
					if item_type == 'Subscription' and demand_index is not None:
						world.demand = world.demand.drop([demand_index]).reset_index(drop=True)
					return corp

	def qty_demand(self, item): # TODO Determine qty for number of individuals
		#items_info = accts.get_items()
		#print('Items Info: \n{}'.format(items_info))
		item_info = world.items.loc[item]
		#print('Item Info: \n{}'.format(item_info))
		need = item_info['satisfies']
		decay_rate = self.needs[need]['Decay Rate']
		qty = math.ceil(decay_rate / item_info['satisfy_rate'])
		#qty = qty * world.population
		return qty

	def item_demanded(self, item=None, qty=None, need=None):
		if item is None and need is not None:
			items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
			items_info = items_info.sort_values(by='satisfy_rate', ascending=False)
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
			if item in world.demand['item_id'].values:
				print('{} service already on the demand table.'.format(item)) # TODO Finish this
				return
			tickers = world.items.loc[item, 'producer']
			if isinstance(tickers, str):
				tickers = [x.strip() for x in tickers.split(',')]
			tickers = list(set(filter(None, tickers)))
			#print('Tickers: {}'.format(tickers))
			for ticker in tickers:
				corp_shares = ledger.get_qty(ticker, ['Investments'])
				if corp_shares != 0:
					return
			qty = 1

		if qty is None:
			qty = self.qty_demand(item)
		#print('Demand QTY: {}'.format(qty))
		if qty != 0:
			world.demand = world.demand.append({'date': world.now, 'entity_id': self.entity_id, 'item_id': item, 'qty': qty}, ignore_index=True)
			print('{} added to demand list for {} units.'.format(item, qty))
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
				print('{} removed from demand list for {} units.'.format(item, qty))
				#print('Demand After Drop: \n{}'.format(world.demand))

	def check_optional(self):
		# In organization loop, check for for items that satisfy requirements for items from the produces items list.
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
			possible_items = items_list.loc[items_list['satisfies'].isin(requirements)].reset_index()
			#print('Possible Items: \n{}'.format(possible_items))
			# If required item is on the filtered list, do below
			for index, item in possible_items.iterrows():
				item_type = self.get_item_type(item['item_id'])
				current_qty = ledger.get_qty(item['item_id'], [item_type])
				#print('Current QTY of {}: {}'.format(item['item_id'], current_qty))
				if current_qty == 0:
					self.purchase(item['item_id'], qty=1, acct_buy='Equipment')

	def claim_land(self, qty, price, item='Land', buffer=False): # QTY in square meters
		ledger.set_entity(0)
		unused_land = ledger.get_qty(items=item, accounts=['Land'])
		ledger.reset()
		print('{} available to claim: {}'.format(item, unused_land))
		if unused_land >= qty:
			claim_land_entry = [ ledger.get_event(), self.entity_id, world.now, 'Claim land', item, price, qty, 'Land', 'Natural Wealth', qty * price ]
			yield_land_entry = [ ledger.get_event(), 0, world.now, 'Bestow land', item, price, qty, 'Natural Wealth', 'Land', qty * price ]
			claim_land_event = [yield_land_entry, claim_land_entry]
			if buffer:
				return claim_land_event
			ledger.journal_entry(claim_land_event)
		else:
			print('Not enough {} available to claim {} square meters.'.format(item, qty))

	def get_counterparty(self, txns, rvsl_txns, item, account):
		if txns.empty:
			return
		#print('Item: {}'.format(item))
		txn = txns.loc[txns['item_id'] == item]
		#print('TXN: \n{}'.format(txn))
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
				counterparty = self.get_counterparty(wages_pay_txns, rvsl_txns, job, 'Wages Receivable')
				wages_pay_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' wages paid', job, wages_payable / labour_hours, labour_hours, 'Wages Payable', 'Cash', wages_payable ]
				wages_chg_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' wages received', job, wages_payable / labour_hours, labour_hours, 'Cash', 'Wages Receivable', wages_payable ]
				pay_wages_event = [wages_pay_entry, wages_chg_entry]
				ledger.journal_entry(pay_wages_event)
			else:
				print('Not enough cash to pay wages for {} work. Cash: {}'.format(job, cash))

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

	def wages_counterparty(self, job):
		workers = {}
		# Get list of all individuals
		world.entities = accts.get_entities()
		# Check total wages receivable for that job for each individual
		for individual in factory.get(Individual):
			ledger.set_entity(individual.entity_id)
			experience = ledger.balance_sheet(accounts=['Wages Receivable'], item=job)
			ledger.reset()
			workers[individual] = experience
			#print('Workers: \n{}'.format(workers))
		# Choose the worker with the most experience
		worker_choosen = max(workers, key=lambda k: workers[k])
		#print('Worker Choosen: {}'.format(worker_choosen.name))
		return worker_choosen

	def accru_wages(self, job, counterparty, wage, labour_hours, buffer=False):
		if counterparty.hours < labour_hours:
			print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
			return
		recently_paid = self.check_wages(job)
		if recently_paid:
			wages_exp_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' wages to be paid', job, wage, labour_hours, 'Wages Expense', 'Wages Payable', wage * labour_hours ]
			wages_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' wages to be received', job, wage, labour_hours, 'Wages Receivable', 'Wages Revenue', wage * labour_hours ]
			accru_wages_event = [wages_exp_entry, wages_rev_entry]
			if buffer:
				return accru_wages_event
			ledger.journal_entry(accru_wages_event)
			counterparty.set_hours(labour_hours)
		else:
			print('Wages have not been paid for {} recently.'.format(job))
			return

	def hire_worker(self, job, counterparty, price=0, qty=1):
		hire_worker_entry = [ ledger.get_event(), self.entity_id, world.now, 'Hired ' + job, job, price, qty, 'Worker Info', 'Hire Worker', 0 ]
		start_job_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Started job as ' + job, job, price, qty, 'Start Job', 'Worker Info', 0 ]
		hire_worker_event = [hire_worker_entry, start_job_entry]
		ledger.journal_entry(hire_worker_event)

	def fire_worker(self, job, counterparty, price=0, qty=-1):
		fire_worker_entry = [ ledger.get_event(), self.entity_id, world.now, 'Fired ' + job, job, price, qty, 'Worker Info', 'Fire Worker', 0 ]
		quit_job_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Quit job as ' + job, job, price, qty, 'Quit Job', 'Worker Info', 0 ]
		fire_worker_event = [fire_worker_entry, quit_job_entry]
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
				print('Salary Job: \n{}'.format(job))
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

	def pay_salary(self, job, counterparty, salary=None, labour_hours=None):
		if salary is None:
			salary = world.get_price(job) # TODO Get price from hire entry
		if labour_hours is None:
			labour_hours = 8
		if counterparty.hours < labour_hours:
			print('{} does not have enough time left to do {} job for {} hours.'.format(counterparty.name, job, labour_hours))
			return
		ledger.set_entity(self.entity_id)
		cash = ledger.balance_sheet(['Cash'])
		ledger.reset()
		if cash >= (salary * labour_hours):
			# TODO Add check if enough cash, if not becomes salary payable
			salary_exp_entry = [ ledger.get_event(), self.entity_id, world.now, job + ' salary paid', job, salary, labour_hours, 'Salary Expense', 'Cash', salary * labour_hours ]
			salary_rev_entry = [ ledger.get_event(), counterparty.entity_id, world.now, job + ' salary received', job, salary, labour_hours, 'Cash', 'Salary Revenue', salary * labour_hours ]
			pay_salary_event = [salary_exp_entry, salary_rev_entry]
			ledger.journal_entry(pay_salary_event)
			counterparty.set_hours(labour_hours)
			return True
		else:
			print('Not enough cash to pay for {} salary. Cash: {}'.format(job, cash))
			# TODO Fire worker

	def subscription_counterparty(self, subscription):
		# Get entity that produces the subscription
		#print('Subscription Requested: {}'.format(subscription))
		for organization in factory.get(Organization):
			#print('Produces: {}'.format(organization.produces[0]))
			for item in organization.produces:
				if item == subscription:
					return organization
		print('No company exists that can provide the {} subscription.'.format(subscription))

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
			# TODO Add entry for counterparty
			if buffer:
				return order_subscription_event
			ledger.journal_entry(order_subscription_event)
			return True
		else:
			print('Not enough cash to pay for {} subscription. Cash: {}'.format(item, cash))

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

	def pay_subscription(self, item, counterparty, price, qty=''):
		# TODO Should check all active subscriptions and pay them with a check_subscriptions() function
		 # TODO Get price from subscription order
		ledger.set_entity(self.entity_id)
		subscription_state = ledger.get_qty(items=item, accounts=['Subscription Info'])
		ledger.reset()
		if subscription_state:
			subscription_state = int(subscription_state)
		#print('Subscription State: {}'.format(subscription_state))
		if not subscription_state:
			return
		for _ in range(subscription_state):
			ledger.set_entity(self.entity_id)
			cash = ledger.balance_sheet(['Cash'])
			ledger.reset()
			if cash >= price:
				pay_subscription_entry = [ ledger.get_event(), self.entity_id, world.now, 'Payment for ' + item, item, price, qty, 'Subscription Expense', 'Cash', price ]
				charge_subscription_entry = [ ledger.get_event(), counterparty.entity_id, world.now, 'Received payment for ' + item, item, price, qty, 'Cash', 'Subscription Revenue', price ]
				pay_subscription_event = [pay_subscription_entry, charge_subscription_entry]
				ledger.journal_entry(pay_subscription_event)
			else:
				self.cancel_subscription(item, counterparty, price)

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
			asset_bal = ledger.balance_sheet(accounts=['Buildings','Equipment','Furniture'], item=item) # TODO Support other accounts like Tools
			if asset_bal == 0:
				return
			#print('Asset Bal: {}'.format(asset_bal))
			dep_amount = (asset_bal / lifespan) * uses
			accum_dep_bal = ledger.balance_sheet(accounts=['Accumulated Depreciation'], item=item)
			remaining_amount = asset_bal - accum_dep_bal
			if dep_amount > remaining_amount:
				print('The {} breaks. Another is required to use.'.format(item))
				uses = remaining_amount / (asset_bal / lifespan)
				dep_amount = remaining_amount
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
		# TODO Make starting need levels random
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Thirst, Fun','100,100,100','1,2,5','40,60,40','50,100,100',None,'Labour') ] # Note: The 2nd to 5th values are for another program
		entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Thirst, Hygiene','100,100,100','1,2,1','40,60,50','60,100,80',None,'Labour') ]
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger, Thirst','100,100','1,2','40,60','50,100',None,'Labour') ]
		#entity_data = [ (name,0.0,1,100,0.5,'iex',12,'Hunger','100','1','40','50',None,'Labour') ]

		self.entity_id = accts.add_entity(entity_data)
		self.name = entity_data[0][0]
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
		self.hours = 12
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

	def address_need(self, need, item_given=None): # TODO This needs a demand system
		outcome = None
		items_info = world.items[world.items['satisfies'].str.contains(need, na=False)] # Supports if item satisfies multiple needs
		items_info = items_info.sort_values(by='satisfy_rate', ascending=False)
		items_info.reset_index(inplace=True)
		# If first item is not available, try the next one
		for index, item in items_info.iterrows():
			item_choosen = items_info['item_id'].iloc[index]
			satisfy_rate = items_info['satisfy_rate'].iloc[index]
			#print('Item Choosen: {}'.format(item_choosen))
			if item_given:
				item_choosen = item_given
				satisfy_rate = world.items.loc[item_choosen, 'satisfy_rate']
				print('Item Choosen: {} {}'.format(item_choosen, satisfy_rate))
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
				qty_purchase = 1

			if item_type == 'Service':
				need_needed = self.needs[need]['Max Need'] - self.needs[need]['Current Need']
				#print('Need Needed: {}'.format(need_needed))
				qty_purchase = math.ceil(need_needed / satisfy_rate)
				#print('QTY Needed: {}'.format(qty_needed))
				outcome = self.purchase(item_choosen, qty_purchase)
				if not outcome:
					outcome = self.produce(item_choosen, qty=qty_purchase, price=world.get_price(item_choosen))

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
					#ledger.reset()
					if qty_wanted > qty_avail:
						qty_purchase = qty_avail
					else:
						qty_purchase = qty_wanted
					#qty_purchase = min(qty_wanted, qty_avail)
					outcome = self.purchase(item_choosen, qty_purchase)
					if not outcome:
						outcome = self.produce(item_choosen, qty=qty_purchase, price=world.get_price(item_choosen))
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
			if not outcome and item_type != 'Subscription':
				print('Add {} to demand list.'.format(item_choosen))
				self.item_demanded(item_choosen, qty_purchase)

	def adj_needs(self, item, qty=1):
		indiv_needs = list(self.needs.keys())
		#print('Indiv Needs: \n{}'.format(indiv_needs))
		satisfies = world.items.loc[item, 'satisfies']
		satisfies = [x.strip() for x in satisfies.split(',')]
		#print('Satisfies: \n{}'.format(satisfies))
		needs = list(set(indiv_needs) & set(satisfies))
		#print('Adj. Needs: \n{}'.format(needs))
		if needs is None:
			return
		for need in needs:
			new_need = self.needs[need]['Current Need'] + (world.items.loc[item, 'satisfy_rate'] * qty)
			if new_need < self.needs[need]['Max Need']:
				self.needs[need]['Current Need'] = new_need
			else:
				self.needs[need]['Current Need'] = self.needs[need]['Max Need']
			print('{} {} Need: {}'.format(self.name, need, self.needs[need]['Current Need']))

	def finish_hours(self):
		if self.hours > 0: #while
			print('Hours Remaining for {}: {}'.format(self.name, self.hours))
			needs_ordered = {}
			for need in self.needs:
				#print(need, self.needs[need]['Current Need'])
				needs_ordered[need] = self.needs[need]['Current Need']
			needs_ordered = sorted(needs_ordered.items(), key=lambda x: x[1], reverse=True)
			#print('Needs Ordered: {}'.format(needs_ordered))
			for need in needs_ordered:
				#print('Need Value: {}'.format(need))
				items_info = world.items[world.items['satisfies'].str.contains(need[0], na=False)]
				items_info = items_info[items_info['producer'].str.contains('Individual', na=False)]
				items_info = items_info.sort_values(by='satisfy_rate', ascending=False)
				items_info.reset_index(inplace=True)
				#print(items_info)
				if not items_info.empty:
					#for index, item in items_info.iterrows():
					item_choosen = items_info['item_id'].iloc[0]#[index]
					print('Item Choosen: {}'.format(item_choosen))
					self.address_need(need[0], item_given=item_choosen)
			exit()


class Organization(Entity):
	def __init__(self, name, item):
		super().__init__(name)
		entity_data = [ (name,0.0,1,100,0.5,'iex',None,None,None,None,None,None,1000000,item) ] # Note: The 2nd to 5th values are for another program
		self.entity_id = accts.add_entity(entity_data)
		self.name = entity_data[0][0] # TODO Change this to pull from entities table
		self.produces = entity_data[0][13]
		if isinstance(self.produces, str):
			self.produces = [x.strip() for x in self.produces.split(',')]
		self.produces = list(filter(None, self.produces))
		print('Create Organization: {} | Produces: {} | entity_id: {}'.format(self.name, self.produces, self.entity_id))

		# ledger.set_entity(self.entity_id) # TODO Remove this
		# self.food = ledger.get_qty(items='Food', accounts=['Inventory'])
		# ledger.reset()
		# print('Starting {} Food: {}'.format(self.name, self.food))

	# TODO Add subclasses to Organization() for companies, non-profits, and government


class EntityFactory:
	def __init__(self):
		self.registry = {}

	def create(self, cls, *args, **kwargs):
		obj = cls(*args, **kwargs)  # create the instance
		self.register_instance(obj) # add to registry
		return obj

	def register_instance(self, obj):
		typ = type(obj)
		if typ not in self.registry:
			self.registry[typ] = []
		self.registry[typ].append(obj)

	def get(self, typ):
		return self.registry[typ]

	def get_by_name(self, name):
		for typ in factory.registry.keys():
			for entity in factory.get(typ):
				if entity.name == name:
					#print('Entity by Name: {}'.format(entity))
					#print('Entity Name by Name: {}'.format(entity.name))
					return entity

	def get_by_id(self, entity_id):
		world.entities = accts.get_entities()
		#print('All Entities: \n{}'.format(world.entities))
		entity_row = world.entities.loc[[entity_id]]
		#print('Entity Row: \n{}'.format(entity_row))
		entity_name = entity_row.iloc[0].loc['name']
		#print('Entity Name: {}'.format(entity_name))
		entity = self.get_by_name(entity_name)
		#print('Entity: {}'.format(entity))
		return entity

	def __str__(self):
		counts = {typ.__name__: len(reg) for typ, reg in self.registry.items()}
		return 'RegistryFactory: ' + str(counts)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-p', '--population', type=int, default=1, help='The number of people in the econ sim.')
	args = parser.parse_args()
	if args.database is None:
		args.database = 'econ01.db'

	print(time_stamp() + 'Start Econ Sim')
	if (args.delay is not None) and (args.delay is not 0):
		print(time_stamp() + 'With update delay of {:,.2f} minutes.'.format(args.delay / 60))	
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

	print(time_stamp() + 'End of Econ Sim')



exit()


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