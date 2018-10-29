from acct import Accounts
from acct import Ledger
import pandas as pd

DISPLAY_WIDTH = 97
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format

class World(object):
	def __init__(self):
		print('Create World')
		self.farm = self.create_org('Farm') # TODO Make this general
		self.farmer = self.create_indv('Farmer') # TODO Make this general

	def create_org(self, name):
		return Organization(name)

	def create_indv(self, name):
		return Individual(name)

	def update_econ(self):
		print('Econ Updated')
		self.farmer.need_decay(self.farmer.need)
		print('Farmer Need: {}'.format(self.farmer.need))

		self.farm.produce()
		print('Farm Food: {}'.format(self.farm.food))

		self.farmer.threshold()


class Entity(object):
	def __init__(self, name):
		print('Create Entity')

class Organization(Entity):
	def __init__(self, name):
		super().__init__(name)
		print('Create Org: {}'.format(name))
		self.food = 0

	def produce(self): # TODO Turn into journal entry
		self.food += 1

	def sell(self, qty): # TODO Turn into journal entry
		print('Sell: {}'.format(qty))
		self.food -= qty

class Individual(Entity):
	def __init__(self, name):
		super().__init__(name)
		print('Create Indv: {}'.format(name))
		self.max_need = 100
		self.need =  50
		print('Initial Need: {}'.format(self.need))

	def need_decay(self, need):
		self.need -= 1

	def consume(self, qty):
		print('Consume: {}'.format(qty))
		self.food += qty
		self.need += qty

	def purchase(self, qty): # TODO Turn into journal entry
		print('Purchase: {}'.format(qty))
		self.farm.sell(qty) # TODO Figure out how to get entities to interact

	def threshold(self):
		if self.need <= 40:
			print('Threhold met!')
			self.purchase(10)
			self.consume(5)


if __name__ == '__main__':
	print('Start Econ Sim')
	world = World()
	# TODO Init starting ledger and accounts

	#while True:
	for _ in range(20):
		world.update_econ()

	print('End Econ Sim')


exit()
#Note for factory functions
def g():
    return B()

def f(): # Singleton
    if f.obj is None:
        f.obj = A()
    return f.obj

f.obj = None
