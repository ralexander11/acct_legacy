#!/usr/bin/env python

import econ
import move
try:
    from move import CivRPG
except ImportError as e:
    print('Not using textual:', e)
import asyncio
# import acct


# class CombinedGame(CivRPG):!
class CombinedGame(move.Map):
    def __init__(self, map_name, start_loc, view_size=None, num_players=1):
        self.econ_running = False
        econ_entities = None
        config = {'population': 1, 'users': 1, 'reset': True}
        print('Config:', config)
        database = 'db/' + 'econ01.db'
        print('Game database:', database)
        econ.EntityFactory.init(database, econ.econ_accts)
        print('Creating econ world.')
        self.world = econ.create_world(database=database, config=config)
        print('Game world:', self.world)
        econ_entities = self.world.factory.get(econ.Individual, computers=False)
        print('econ_entities:', econ_entities)
        super().__init__(map_name, start_loc, view_size, num_players, entities=econ_entities)
        self.econ_interval = 1.0  # Seconds between econ updates
        print('econ_interval:', self.econ_interval)

    def on_mount(self):
        # Start a timer to update the economy every 'econ_interval' seconds
        print('Setting interval.')
        self.set_interval(self.econ_interval, self.update_economy)
        print('Interval set.')

    # async def update_economy(self):
    #     print('Update econ tick.')
    #     # self.world.update_econ()
    #     await asyncio.to_thread(self.world.update_econ)
    #     print('Done update econ tick.')
    #     if self.world.end:
    #         self.exit()
    
    def update_economy(self):
        if self.econ_running:
            return
        self.econ_running = True
        async def run():
            print('Update econ tick.')
            await asyncio.to_thread(self.world.update_econ)
            print('Done update econ tick.')
            self.econ_running = False
            if self.world.end:
                self.exit()
        asyncio.create_task(run())

if __name__ == '__main__':
    print('Create app.')
    try:
        app = CombinedGame('map.csv', (446, 229), None, 1)#args.map, args.start, args.view_size, args.players)
        print('Run CivRPG app.')
        app.run()
    except TypeError as e:
        move.main()
        # world_map = move.Map(None, 'map.csv', (446, 229), None, 1)#(None, args.map, args.start, args.view_size, args.players)
    print('Finish CivRPG app.')
