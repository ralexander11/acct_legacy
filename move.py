#!/usr/bin/env python

import pandas as pd
import argparse
import random
from rich import print

MAP_SIZE = 4 #64
MAP_VIEW = 10 #(26, 37)

class Map:
    def __init__(self, map_size):
        if args.map is None:
            self.gen_map(map_size)
        else:
            self.map_gen_file()
        self.update_display_map()
        # print(f'world_map created:\n{self}')

    def gen_map(self, map_size, proc=False):
        self.map_size = map_size
        if isinstance(self.map_size, int):
            self.map_size = (self.map_size, self.map_size)
        elif len(self.map_size) == 1:
            self.map_size = (self.map_size[0], self.map_size[0])
        print('map_size:', self.map_size)
        self.world_map = [[dict() for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        # print('world_map 1:', self.world_map)
        self.get_terrain_data()
        for row in self.world_map:
            for tile in row:
                if proc:
                    terrain_select = random.choices(self.terrain_items['item_id'].tolist(), self.terrain_items['coverage'].tolist())[0]
                    print(terrain_select)
                    exit()
                else:
                    terrain_select = 'Grassland'
                    tile.update({'terrain': Tile(terrain_select, self.terrain_items)})

        # self.world_map = pd.DataFrame(self.world_map) # Replace pandas here
        # self.world_map.applymap(lambda d: d.update({'terrain': Tile()})) # Replace pandas here
        return self.world_map
    
    def map_gen_file(self, infile='data/map01.csv'):
        if args.map is not None:
            infile = args.map
            if '.csv' not in infile:
                infile = infile + '.csv'
            if 'data/' not in infile:
                infile = 'data/' + infile
            print('infile:', infile)
        with open(infile, 'r') as f:
            map_data = pd.read_csv(f, header=None)
        self.map_size = map_data.shape
        print('map_size:', self.map_size)
        self.world_map = [[dict() for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        # print('world_map 1:', self.world_map)
        self.get_terrain_data()
        for i, row in map_data.iterrows():
            for j, tile in enumerate(row):
                if tile == '.':
                    terrain_select = 'Grassland'
                elif tile == '#':
                    terrain_select = 'Arable Land'
                elif tile == 'F':
                    terrain_select = 'Forest'
                elif tile == 'R':
                    terrain_select = 'Rocky Land'
                elif tile == 'H':
                    terrain_select = 'Hills'
                elif tile == 'M':
                    terrain_select = 'Mountain'
                elif tile == 'W':
                    terrain_select = 'Wetlands'
                elif tile == 'J':
                    terrain_select = 'Jungle'
                elif tile == 'D':
                    terrain_select = 'Desert'
                elif tile == 'T':
                    terrain_select = 'Tundra'
                elif tile == 'O':
                    terrain_select = 'Ocean'
                else:
                    terrain_select = 'Grassland'
                self.world_map[i][j].update({'terrain': Tile(terrain_select, self.terrain_items)})
        return self.world_map

    def save_map(self, filename=None):
        if filename is None:
            filename = input('Enter filename: ')
            if '.csv' not in filename:
                filename = filename + '.csv'
            if 'data/' not in filename:
                filename = 'data/' + filename
        print('Save filename: ', filename)
        df = pd.DataFrame(self.display_map)
        print(df)
        df.to_csv(filename, index=False, header=False)

    def set_map_size(self, x=None, y=None):
        print('Current Map Size:', self.map_size)
        if x is None:
            x = input('Enter x new size: ')
        if y is None:
            y = input('Enter y new size: ')
        if y == '':
            y = x
        new_map_size = (int(x), int(y))
        print('new_map_size:', new_map_size)
        map_size_diff = (int(x) - self.map_size[0], int(y) - self.map_size[1])
        print('map_size_diff:', map_size_diff)
        # print(repr(self.world_map))
        for _ in range(map_size_diff[0]):
            self.world_map.append([{'terrain': Tile('Grassland', self.terrain_items)} for _ in range(self.map_size[1])])
        for row in self.world_map:
            for _ in range(map_size_diff[1]):
                row.append({'terrain': Tile('Grassland', self.terrain_items)})
        # print(repr(self.world_map))
        self.map_size = new_map_size
        self.update_display_map()

    def view_port(self, map_view=MAP_VIEW):
        self.map_view = map_view
        if isinstance(self.map_view, int):
            self.map_view = (self.map_view, self.map_view)
        elif len(self.map_view) == 1:
            self.map_view = (self.map_view[0], self.map_view[0])
        print('map_view:', self.map_view)
        return self.map_view

    def edit_terrain(self, pos=None, terrain=None):
        if pos is None:
            x = input('Enter x coord: ')
            y = input('Enter y coord: ')
            try:
                pos = (int(y), int(x))
            except ValueError:
                print('Enter whole numbers only, try again.')
                return
        if terrain is None:
            terrain = input('Enter terrain: ')
            terrain = terrain.title()
        tile = self.world_map[pos[0]][pos[1]]
        tile.update({'terrain': Tile(terrain, self.terrain_items)})
        if terrain == 'Grassland': # TODO Could likely do this more efficiently
            icon = '[bright_green].[/bright_green]'
        elif terrain == 'Arable Land':
            icon = '[yellow]#[/yellow]'
        elif terrain == 'Forest':
            icon = '[green]F[/green]'
        elif terrain == 'Rocky Land':
            icon = '[grey62]R[/grey62]'
        elif terrain == 'Hills':
            icon = '[green]H[/green]'
        elif terrain == 'Mountain':
            icon = '[red]M[/red]'
        elif terrain == 'Wetlands':
            icon = '[cyan]W[/cyan]'
        elif terrain == 'Jungle':
            icon = '[green]J[/green]'
        elif terrain == 'Desert':
            icon = '[yellow]D[/yellow]'
        elif terrain == 'Tundra':
            icon = '[grey62]T[/grey62]'
        elif terrain == 'Ocean':
            icon = '[blue]O[/blue]'
        else:
            icon = ','
        if tile.get('Agent'):
            agent_tile = tile.get('Agent')
            print('agent_tile:', agent_tile)
            print('agent_tile type:', type(agent_tile))
            current_terrain = tile['terrain']
            agent_tile.current_terrain = current_terrain
            print(f'Edited Terrain: {current_terrain}')
            agent_tile.current_tile = icon
            return
        self.display_map[pos[0]][pos[1]] = icon

    def get_terrain_data(self, infile='data/items.csv'):
        # Note: int_rate_var is the column name for units of land.
        with open(infile, 'r') as f:
            self.terrain_items = pd.read_csv(f, keep_default_na=False, comment='#')
        self.terrain_items = self.terrain_items[self.terrain_items['child_of'] == 'Land']
        self.terrain_items['int_rate_var'] = self.terrain_items['int_rate_var'].astype(int)
        self.terrain_items['coverage'] = self.terrain_items['int_rate_var'] / self.terrain_items['int_rate_var'].sum()
        print('terrain_items:')
        print(self.terrain_items)

    def update_display_map(self):
        self.display_map = [[None for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        for i, row in enumerate(self.world_map):
            for j, tile in enumerate(row):
                terrain_tile = tile.get('terrain')
                if terrain_tile.hidden:
                    continue
                terrain = terrain_tile.terrain
                if terrain == 'Grassland': # TODO Could likely do this more efficiently
                    icon = '[bright_green].[/bright_green]'
                elif terrain == 'Arable Land':
                    icon = '[yellow]#[/yellow]'
                elif terrain == 'Forest':
                    icon = '[green]F[/green]'
                elif terrain == 'Rocky Land':
                    icon = '[grey62]R[/grey62]'
                elif terrain == 'Hills':
                    icon = '[green]H[/green]'
                elif terrain == 'Mountain':
                    icon = '[red]M[/red]'
                elif terrain == 'Wetlands':
                    icon = '[cyan]W[/cyan]'
                elif terrain == 'Jungle':
                    icon = '[green]J[/green]'
                elif terrain == 'Desert':
                    icon = '[yellow]D[/yellow]'
                elif terrain == 'Tundra':
                    icon = '[grey62]T[/grey62]'
                elif terrain == 'Ocean':
                    icon = '[blue]O[/blue]'
                else:
                    icon = ','
                self.display_map[i][j] = icon

                if tile.get('Agent'):
                    agent_tile = tile.get('Agent')
                    print('agent_tile:', agent_tile)
                    print('agent_tile type:', type(agent_tile))
                    icon = agent_tile.icon
                    self.display_map[i][j] = icon

    def __str__(self):
        # self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
        return self.map_display

    def __repr__(self):
        self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        # self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
        return self.map_display

class Tile:
    def __init__(self, terrain='Land', terrain_items=None):
        self.terrain = terrain
        self.move_cost = terrain_items[terrain_items['item_id'] == self.terrain]['int_rate_fix'].values[0]
        if self.move_cost == 'None':
            self.move_cost = None
        if self.move_cost is not None:
            self.move_cost = int(self.move_cost)
        self.hidden = False

    def __str__(self):
        return self.terrain

    def __repr__(self):
        return self.terrain

class Player:
    def __init__(self, name, world_map, icon='P'):
        self.name = name
        self.world_map = world_map
        self.icon = '[blink]' + icon + '[/blink]'
        print(f'{self} icon: {self.icon}')
        # self.pos = (0, int(icon)-1) # Start position at top left
        self.pos = (int(round(self.world_map.map_size[0]/2, 0)), int(round(self.world_map.map_size[1]/2, 0)+int(icon)-1)) # Start position near middle
        print(f'{self} start pos: {self.pos}')
        self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
        self.world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self
        self.world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
        # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name # Replace pandas here
        self.movement = 5
        self.remain_move = self.movement

    def reset_moves(self):
        self.remain_move = self.movement
        print(f'Moves reset for {self}.')

    def move(self):
        self.old_pos = self.pos
        print(f'Current position: {self.old_pos}')
        self.current_terrain = world_map.world_map[self.old_pos[0]][self.old_pos[1]]['terrain']
        print(f'Current Terrain: {self.current_terrain}')
        if self.get_move() is None: # TODO This isn't very clear
            return
        if self.is_occupied(self.pos):
            self.pos = self.old_pos
            return
        if not self.calc_move(self.pos):
            print(f'Not enough movement to enter tile. Movement Remaining: {self.remain_move}/{self.movement}')
            self.pos = self.old_pos
            return
        try:
            world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self

            world_map.display_map[self.old_pos[0]][self.old_pos[1]] = self.current_tile #self.get_terrain(self.old_pos)
            self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
            print(f'Current Tile: {self.current_tile}')
            world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
            del world_map.world_map[self.old_pos[0]][self.old_pos[1]]['Agent']
            # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name # Replace pandas here
            # del world_map.world_map.at[self.old_pos[0], self.old_pos[1]]['Agent'] # Replace pandas here
        except (IndexError, KeyError) as e: # TODO Is this check still needed?
            print('Out of bounds, try again.')
            self.pos = self.old_pos
            return
        print('End move.')

    def is_occupied(self, pos):
        try:
            if 'Agent' in world_map.world_map[pos[0]][pos[1]]:
                print('Cannot move to the same space as another Player or NPC.')
                return True
        except (IndexError, KeyError) as e:
            print('Out of bounds, try again.')
            return True

    def calc_move(self, pos):
        target_terrain = world_map.world_map[pos[0]][pos[1]]['terrain']
        if target_terrain.move_cost is None:
            print(f'Cannot cross {target_terrain}.')
            return
        print('remaining_moves:', self.remain_move)
        print('target_terrain.move_cost:', target_terrain.move_cost)
        if self.remain_move >= target_terrain.move_cost:
            self.remain_move -= target_terrain.move_cost
            return True

    def get_terrain(self, pos=None, terrain=None):
        if terrain is None and pos is not None:
            terrain = world_map.world_map[pos[0]][pos[1]]['terrain'].terrain
        if terrain == 'Grassland': # TODO Could likely do this more efficiently
            icon = '[bright_green].[/bright_green]'
        elif terrain == 'Arable Land':
            icon = '[yellow]#[/yellow]'
        elif terrain == 'Forest':
            icon = '[green]F[/green]'
        elif terrain == 'Rocky Land':
            icon = '[grey62]R[/grey62]'
        elif terrain == 'Hills':
            icon = '[green]H[/green]'
        elif terrain == 'Mountain':
            icon = '[red]M[/red]'
        elif terrain == 'Wetlands':
            icon = '[cyan]W[/cyan]'
        elif terrain == 'Jungle':
            icon = '[green]J[/green]'
        elif terrain == 'Desert':
            icon = '[yellow]D[/yellow]'
        elif terrain == 'Tundra':
            icon = '[grey62]T[/grey62]'
        elif terrain == 'Ocean':
            icon = '[blue]O[/blue]'
        else:
            icon = ','
        return icon

    def get_move(self):
        print('\nEnter "exit" to exit.')
        key = input('Use wasd to move: ')
        print('===================')
        key = key.lower()
        if key == 'map':
            print(f'Display current world map:\n{world_map}')
            self.pos = self.old_pos
            return
        if key == 'terrain' or key == 'items':
            print('Display terrain item details:\n', world_map.terrain_items)
            self.pos = self.old_pos
            return
        if key == 'r' or key == 'reset':
            self.reset_moves()
            self.pos = self.old_pos
            return
        if key == 'size':
            world_map.set_map_size()
            self.pos = self.old_pos
            return
        if key == 'edit':
            world_map.edit_terrain()
            self.pos = self.old_pos
            return
        if key == 'save':
            world_map.save_map()
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

def setup():
    # TODO Move class instantiation here?
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size', type=str, help='The map size as either a list of two numbers or one for square.')
    parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
    parser.add_argument('-r', '--seed', type=str, default=11, help='Set the seed for the randomness.')
    parser.add_argument('-m', '--map', type=str, help='The name of the map csv data file.')
    parser.add_argument('-p', '--players', type=int, default=1, help='The number of players in the world.')
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
    players = []
    for player_num in range(args.players):
        player_name = 'Player ' + str(player_num+1)
        player = Player(player_name, world_map, str(player_num+1))
        players.append(player)
    print(f'Players:\n{players}')
    print(f'world_map:\n{world_map}')

    while True:
        for player in players:
            print(f'Current Player: {player}')
            print(f'Start Tile: {player.current_tile}')
            while player.remain_move:
                player.move()
                print(f'Current world map:\n{world_map}')
                # TODO Display player map attribute
                print(f'{player.name} moves left: {player.remain_move}')
            player.reset_moves()

## TODO
# Display map

# Factor is terrain cost
# Movement turns

# Edit terrain
# Load map
# Save map

# Multiple Players/Units
# Don't allove move into unit tile
# Create tile for player spawn, that isn't visible on the map
#    Can make a reusable property for items that don't show on map
# Allow player spawns to be randomly placed and randomly used
# Make similar to above for mob spawns

# Make togglable options for map wrapping

# scp data/map03.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp data/items.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp move.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct
