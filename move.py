#!/usr/bin/env python

import pandas as pd
import argparse
import random

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

        self.get_terrain()

        for row in self.world_map:
            for tile in row:
                terrain_select = random.choices(self.terrain_items['item_id'].tolist(), self.terrain_items['coverage'].tolist())[0]
                tile.update({'terrain': Tile(terrain_select, self.terrain_items)})
        # self.world_map = pd.DataFrame(self.world_map) # Replace pandas here
        # self.world_map.applymap(lambda d: d.update({'terrain': Tile()})) # Replace pandas here
        print('world_map created:\n', self)

    def get_terrain(self, infile='data/items.csv'):
        # Note: int_rate_var is the column name for units of land.
        with open(infile, 'r') as f:
            self.terrain_items = pd.read_csv(f, keep_default_na=False, comment='#')
        self.terrain_items = self.terrain_items[self.terrain_items['child_of'] == 'Land']
        self.terrain_items['int_rate_var'] = self.terrain_items['int_rate_var'].astype(int)
        self.terrain_items['coverage'] = self.terrain_items['int_rate_var'] / self.terrain_items['int_rate_var'].sum()
        print('terrain_items:')
        print(self.terrain_items)

    def calc_move():
        pass

    def __str__(self):
        self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        return self.map_display

    def __repr__(self):
        self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        return self.map_display

class Tile:
    def __init__(self, terrain='Land', terrain_items=None):
        self.terrain = terrain
        self.move_cost = terrain_items[terrain_items['item_id'] == self.terrain]['int_rate_fix'].values[0]

    def __str__(self):
        return self.terrain

    def __repr__(self):
        return self.terrain

class Player:
    def __init__(self, name, world_map):
        self.name = name
        self.pos = (0, 0)
        world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self.name
        # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name # Replace pandas here
        self.movement = 5
        self.remain_move = self.movement

    def move(self):
        self.old_pos = self.pos
        print('old_pos:', self.old_pos)
        if self.get_move() is None:
            return
        try:
            world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self.name
            del world_map.world_map[self.old_pos[0]][self.old_pos[1]]['Agent']
            # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name # Replace pandas here
            # del world_map.world_map.at[self.old_pos[0], self.old_pos[1]]['Agent'] # Replace pandas here
        except (IndexError, KeyError) as e:
            print('Out of bounds, try again.')
            self.pos = self.old_pos
            return
        print('end')

    def get_move(self):
        print('\nEnter "exit" to exit.')
        key = input('Use wasd to move: ')
        key = key.lower()
        if key == 'map':
            print('Display current world map:\n', world_map)
            self.pos = self.old_pos
            return
        if key == 'terrain':
            print('Display terrain item details:\n', world_map.terrain_items)
            self.pos = self.old_pos
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
                self.pos = self.old_pos
                return
        elif key == 'exit':
            quit()
        else:
            print('Not a valid input, please try again.')
            self.pos = self.old_pos
            return
        return self.pos

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size', type=str, help='The map size as either a list of two numbers or one for square.')
    parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
    parser.add_argument('-r', '--seed', type=str, default=11, help='Set the seed for the randomness.')
    args = parser.parse_args()

    if args.seed:
        print('Randomness seed {}.'.format(args.seed))
        random.seed(args.seed)
    if args.size is not None:
        if not isinstance(args.size, (list, tuple)):
            args.size = [int(x.strip()) for x in args.size.split(',')]
            MAP_SIZE = args.size
            print('MAP_SIZE:', MAP_SIZE)
    

    world_map = Map(MAP_SIZE)
    player = Player('Player 1', world_map)
    print('world_map:\n', world_map)

    while True:
        player.move()
        print('Current world map:\n', world_map)

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

# scp move.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct
