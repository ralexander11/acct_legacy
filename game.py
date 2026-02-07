#!/usr/bin/env python

import econ
import move
from move import CivRPG
# import acct

class CombinedGame(CivRPG):
    def __init__(self, map_name, start_loc, view_size=None, num_players=1):
        super().__init__(map_name, start_loc)
        database = 'db/' + 'econ01.db'
        print('Game database:', database)
        econ.EntityFactory.init(database, econ.econ_accts)
        print('Creating econ world.')
        self.world = econ.create_world(database=database)
        print('Game world:\n', self.world)
        self.econ_interval = 1.0  # Seconds between econ updates
        print('econ_interval:', self.econ_interval)

    def on_mount(self):
        # Start a timer to update the economy every 'econ_interval' seconds
        print('Setting interval.')
        self.set_interval(self.econ_interval, self.update_economy)
        print('Interval set.')

    async def update_economy(self):
        print('Update econ tick.')
        self.world.update_econ()
        print('Done pdate econ tick.')
        if self.world.end:
            self.exit()

if __name__ == '__main__':
    print('Create app.')
    app = CombinedGame('map.csv', (446, 229), None, 1)#args.map, args.start, args.view_size, args.players)
    print('Run app.')
    app.run()
    print('Finish app.')

    # database = 'db/' + 'econ01.db'
    # econ.EntityFactory.init(database, econ.econ_accts)
    # world = econ.create_world(database=database)
    # print('world:', world)

    # while True:
    #     world.update_econ()
    #     if world.end:
    #         break
