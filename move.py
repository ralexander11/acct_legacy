#!/usr/bin/env python

import pandas as pd

MAP_SIZE = 4 #64

class Map:
    def __init__(self, map_size):
        self.map_size = map_size
        if isinstance(self.map_size, int):
            self.map_size = (self.map_size, self.map_size)

        print('map_size:', self.map_size)
        self.world_map = [[dict() for _ in range(self.map_size[0])] for _ in range(self.map_size[1])]
        # print('world_map 1:', self.world_map)

        self.world_map = pd.DataFrame(self.world_map)
        self.world_map.applymap(lambda d: d.update({'terrain': Tile()}))# or d)
        print('world_map created:\n', self.world_map)

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

    def move(player):
        #TODO Get input from user
        print('\nEnter "exit" to exit.')
        key = input('Use wasd to move: ')
        key = key.lower()
        old_pos = player.pos
        print('old_pos:', old_pos)
        if key == 'w':
            player.pos = (player.pos[0] - 1, player.pos[1])
        elif key == 's':
            player.pos = (player.pos[0] + 1, player.pos[1])
        elif key == 'a':
            player.pos = (player.pos[0], player.pos[1] - 1)
        elif key == 'd':
            player.pos = (player.pos[0], player.pos[1] + 1)
        elif key == 'move':
            # key = input('Enter coords to try and move to: ')
            x = input('Enter x coord: ')
            y = input('Enter y coord: ')
            player.pos = (int(y), int(x))
        elif key == 'exit':
            quit()
        else:
            print('Not a valid input, please try again.')
            self.move()
        del world_map.world_map.at[old_pos[0], old_pos[1]]['Agent']
        world_map.world_map.at[player.pos[0], player.pos[1]]['Agent'] = player.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

if __name__ == '__main__':
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

# scp <file to upload> <username>@<hostname>:<destination path>
# scp foobar.txt your_username@remotehost.edu:/some/remote/directory
# scp move.py robale5@becauseinterfaces.com:/acct