#!/usr/bin/env python

import pandas as pd
import argparse

MAP_SIZE = 4 #64

class Map:
    def __init__(self, map_size):
        self.map_size = map_size
        if isinstance(self.map_size, int):
            self.map_size = (self.map_size, self.map_size)
        elif len(self.map_size) == 1:
            self.map_size = (self.map_size[0], self.map_size[0])

        print('map_size:', self.map_size)
        self.world_map = [[dict() for _ in range(self.map_size[0])] for _ in range(self.map_size[1])]
        print('world_map 1:', self.world_map)

        self.build_terrain()

        self.world_map = pd.DataFrame(self.world_map)
        self.world_map.applymap(lambda d: d.update({'terrain': Tile()}))# or d)
        print('world_map created:\n', self.world_map)

    def build_terrain(self, infile='data/items.csv'):
        # Note: int_rate_var is the column name for units of land.
        with open(infile, 'r') as f:
            self.items = pd.read_csv(f, keep_default_na=False, comment='#')
        self.items = self.items[self.items['child_of'] == 'Land']
        self.items['int_rate_var'] = self.items['int_rate_var'].astype(int)
        self.items['coverage'] = self.items['int_rate_var'] / self.items['int_rate_var'].sum()
        print('items:')
        print(self.items)

class Tile:
    def __init__(self, terrain='Land'):
        self.terrain = terrain
        self.move_cost = 1

    def __str__(self):
        return self.terrain

    def __repr__(self):
        return self.terrain

class Player:
    def __init__(self, name, world_map):
        self.name = name
        self.pos = (0, 0)
        world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name
        self.movement = 3

    def move(self):
        old_pos = self.pos
        print('old_pos:', old_pos)
        self.get_move()
        try:
            world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name
            del world_map.world_map.at[old_pos[0], old_pos[1]]['Agent']
        except KeyError:
            print('Out of bounds, try again.')
            self.pos = old_pos
            return
        print('end')

    def get_move(self):
        print('\nEnter "exit" to exit.')
        key = input('Use wasd to move: ')
        key = key.lower()
        if key == 'map':
            print('Current world map:\n', world_map.world_map)
            self.pos = old_pos
            return
        elif key == 'w':
            self.pos = (self.pos[0] - 1, self.pos[1])
        elif key == 's':
            self.pos = (self.pos[0] + 1, self.pos[1])
        elif key == 'a':
            self.pos = (self.pos[0], self.pos[1] - 1)
        elif key == 'd':
            self.pos = (self.pos[0], self.pos[1] + 1)
        elif key == 'move':
            x = input('Enter x coord: ')
            y = input('Enter y coord: ')
            try:
                self.pos = (int(y), int(x))
            except ValueError:
                print('Enter whole numbers only, try again.')
                self.pos = old_pos
                return
        elif key == 'exit':
            quit()
        else:
            print('Not a valid input, please try again.')
            self.pos = old_pos
            return
        # return self.pos

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size', type=str, help='The map size as either a list of two numbers or one for square.')
    parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
    args = parser.parse_args()

    if args.size is not None:
        if not isinstance(args.size, (list, tuple)):
            args.size = [int(x.strip()) for x in args.size.split(',')]
            MAP_SIZE = args.size
            print('MAP_SIZE:', MAP_SIZE)
    

    world_map = Map(MAP_SIZE)
    player = Player('Player 1', world_map)
    print('world_map:\n', world_map.world_map)

    while True:
        player.move()
        print('Current world map:\n', world_map.world_map)

## TODO
# Make a map class
#   Give size attr
#   Give default tile attr
#   Each cell to contain a dict

# Make a tile class
#   Give tile a movement cost attr
#   With default tile type?

# Make player class
#   Have a default, but import as well
#   Give location attr
#   Give movement dist attr
#   Add movement func to player class

# scp foobar.txt your_username@remotehost.edu:/some/remote/directory
# scp move.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct
