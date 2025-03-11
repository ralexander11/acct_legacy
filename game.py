#!/usr/bin/env python

# import acct
import econ
import move
from move import CivRPG

class CombinedGame(CivRPG):
    def __init__(self, map_name, start_loc, view_size=None, num_players=1):
        super().__init__(map_name, start_loc)
        database = 'db/' + 'econ01.db'
        econ.EntityFactory.init(database, econ.econ_accts)
        self.world = econ.create_world(database=database)
        print('world:', self.world)
        self.econ_interval = 1.0  # Seconds between econ updates

    def on_mount(self):
        # Start a timer to update the economy every 'econ_interval' seconds
        self.set_interval(self.econ_interval, self.update_economy)
        print('Interval set.')

    async def update_economy(self):
        print('Update econ.')
        self.world.update_econ()
        if self.world.end:
            self.exit()

if __name__ == '__main__':
    # database = 'db/' + 'econ01.db'

    # econ.EntityFactory.init(database, econ.econ_accts)
    # world = econ.create_world(database=database)
    # print('world:', world)

    app = CombinedGame('map.csv', (446, 229), None, 1)#args.map, args.start, args.view_size, args.players)
    app.run()

    # while True:
    #     world.update_econ()
    #     if world.end:
    #         break
