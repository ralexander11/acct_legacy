#!/usr/bin/env python

# import acct
import econ
import move

if __name__ == '__main__':
    database = 'db/' + 'econ01.db'

    econ.EntityFactory.init(database, econ.econ_accts)
    world = econ.create_world(database=database)
    print('world:', world)

    app = move.CivRPG('map.csv', (446, 229), None, 1)#args.map, args.start, args.view_size, args.players)
    app.run()

    # while True:
    #     world.update_econ()
    #     if world.end:
    #         break
