#!/usr/bin/env python

import pandas as pd
import numpy as np
import argparse
import random
from rich import print
import datetime as dt
import os, sys
import asyncio
# import builtins

from textual.app import App, ComposeResult
from textual.widgets import Static, TabbedContent, TabPane, RichLog, Input
from textual.containers import Container
from textual.reactive import reactive
from rich.console import Console
from rich.pretty import Pretty

MAP_SIZE = 4 #64

CORDS = {
        'Start': '338, 178',
        'Paws': 'HV, 439',
        'Trisic': 'JJ, 555',
        'Yew Woods': 'DQ, 163',
        'Yew': 'CL, 98',
        'Cove': 'OH, 323',
        'High Steppes': 'JW, 114',
        'Minoc': 'OA, 102',
        'Dry Lands': 'VH, 217',
        'Vesper': 'TJ, 285',
        'Castle of Fire': 'UC, 392',
        'Buccaneer\'s Den': 'OJ, 486',
        'New Magincia': 'TV, 550',
        'Moonglow': 'ZJ, 379',
        'Dagger Isle': 'YI, 290',
        'Ambrosia': 'AAN, 67',
        'Isle of the Avatar': 'ZJ, 653',
        'Skara Brae': 'DE, 406',
        'Jhelom': 'DR, 634',
        'Pirate House': 'IX, 684',
        'Pirate Cave': 'KT, 695',
        'Serpent\'s Hold': 'NB, 702',
        'Meditation Retreat': 'QD, 730',
        'Spektran': 'QW, 639',
        'Terfin': 'TK, 719',
        'Castle': 'HZ, 313',
        'Jungle': 'VE, 161',
        }

TILES = {
        'Grassland': '[green].[/green]',
        'Dirt': '[orange4]`[/orange4]',
        'Arable Land': '[yellow]#[/yellow]',
        'Forest': '[green]F[/green]',
        'Rocky Land': '[grey37]R[/grey37]',
        'Hills': '[green]H[/green]',
        'Mountain': '[red]M[/red]',
        'Wetlands': '[cyan]W[/cyan]',
        'Jungle': '[green1]J[/green1]',
        'Desert': '[yellow]D[/yellow]',
        'Sand': '[yellow]S[/yellow]',
        'Tundra': '[grey62]T[/grey62]',
        'Ocean': '[blue]O[/blue]',
        'Path': '[orange4]=[/orange4]',
        'Road': '[grey69]_[/grey69]',
        'Sidewalk': '[grey85]≡[/grey85]',
        'Wall': '[tan]▌[/tan]',
        'Door': '[chartreuse4]⌂[/chartreuse4]',
        'Window': '[sky_blue1]ш[/sky_blue1]',
        'Fence': '[dark_red]﬩[/dark_red]',
        'Fence Gate': '[tan];[/tan]',
        'Floor': '[dark_red]-[/dark_red]',
        'Rug': '[deep_pink4]®[/deep_pink4]',
        'Cave Floor': '[grey37],[/grey37]',
        'Dock': '[orange4]Ɗ[/orange4]',
        'Sign': '[bright_yellow]![/bright_yellow]',
        'Street Light': '[bright_yellow]ꝉ[/bright_yellow]',
        'Trees': '[green]Ҭ[/green]',
        'Potato': '[gold3]ꭅ[/gold3]',
        'Corn': '[bright_yellow]Ψ[/bright_yellow]',
        'Barred Window': '[red]₩[/red]',
        'Barred Door': '[grey42]ᴃ[/grey42]',
        'Bridge': '[orange4]≠[/orange4]',
        'Chicken Coup': '[bright_yellow]₠[/bright_yellow]',
        'City Gate': '[magenta]Ħ[/magenta]',
        'City Wall': '[grey37]█[/grey37]',
        'Fountain': '[blue]֎[/blue]',
        'Roped Guardrail': '[red]ꭆ[/red]',
        'Stain Glass Window': '[bright_cyan]₷[/bright_cyan]',
        'Stairs': '[purple4]𓊍[/purple4]',
        'Ladder': '[purple4]ǂ[/purple4]',
        'Well': '[blue]o[/blue]',
        'Roof': '[red]X[/red]',
        'Cave Roof': '[red]K[/red]',
        'Columns': '[white]ΐ[/white]',
        'Potted Plants': '[green]ꝕ[/green]',
        'Statue': '[magenta]ѯ[/magenta]',
        'Altar': '[bright_magenta]ꟸ[/bright_magenta]',
        'Anvil': '[grey37]ꭥ[/grey37]',
        'Bread Oven': '[bright_red]Ꝋ[/bright_red]',
        'Cauldron': '[cyan]ꭒ[/cyan]',
        'Forge': '[bright_red]₣[/bright_red]',
        'Keg': '[yellow]₭[/yellow]',
        'Lecturn': '[cyan]ꭋ[/cyan]',
        'Loom': '[yellow]Ɫ[/yellow]',
        'Mill': '[white]₥[/white]',
        'Spinning Wheel': '[orange4]₴[/orange4]',
        'Stove': '[bright_red]Θ[/bright_red]',
        'Sun Dial': '[bright_yellow]☼[/bright_yellow]',
        'Target': '[bright_red]ʘ[/bright_red]',
        'Target Dummy': '[bright_cyan]♀[/bright_cyan]',
        'Tub': '[blue]ṵ[/blue]',
        'Water Trough': '[blue]ⱳ[/blue]',
        'Water Wheel': '[orange4]Ꝯ[/orange4]',
        'Winch': '[grey62]ꞷ[/grey62]',
        'Carrot': '[orange3]Ɣ[/orange3]',
        'Lettuce': '[chartreuse1]Ϫ[/chartreuse1]',
        'Broccoli': '[chartreuse3]‽[/chartreuse3]',
        'Garlic': '[white]ɤ[/white]',
        'Onion': '[dark_goldenrod]ȸ[/dark_goldenrod]',
        'Tomato': '[red3]ɷ[/red3]',
        'Hay': '[wheat1]ⱨ[/wheat1]',
        'Bar': '[dark_orange3]Ꞵ[/dark_orange3]',
        'Bed': '[white]Ꞗ[/white]',
        'Bedside Table': '[orange3]Ɥ[/orange3]',
        'Bench': '[orange3]ꭑ[/orange3]',
        'Book Shelf': '[orange4]Ḇ[/orange4]',
        'Chair': '[dark_khaki]∟[/dark_khaki]',
        'Chest': '[gold3]∩[/gold3]',
        'Desk': '[orange3]∏[/orange3]',
        'Display Cabinet': '[light_cyan1]Ḓ[/light_cyan1]',
        'Display Case': '[light_cyan1]Ḑ[/light_cyan1]',
        'Display Table': '[light_cyan1]Ḏ[/light_cyan1]',
        'Dresser': '[orange4]Ð[/orange4]',
        'Pew': '[dark_khaki]Ꝓ[/dark_khaki]',
        'Round Table': '[orange4]ꝿ[/orange4]',
        'Shelf': '[orange4]ﬃ[/orange4]',
        'Side Table': '[orange4]Ꞁ[/orange4]',
        'Table': '[orange4]Ŧ[/orange4]',
        'Wardrobe': '[orange4]Ꝡ[/orange4]',
        'Harp': '[light_goldenrod1]ћ[/light_goldenrod1]',
        'Piano': '[grey82]♫[/grey82]',
        'Floor Candle': '[bright_yellow]ḉ[/bright_yellow]',
        'Cave': '[grey35]Ꞝ[/grey35]',
        'Plants': '[dark_sea_green4]♣[/dark_sea_green4]',
        'Flowers': '[medium_violet_red]ӂ[/medium_violet_red]',
        'Rocks': '[grey50]*[/grey50]',
        'Stalagmite': '[grey50]↑[/grey50]',
        'Stump': '[dark_goldenrod]ᶊ[/dark_goldenrod]',
        'Wheat': '[wheat1]ẅ[/wheat1]',
        'Barrel': '[dark_goldenrod]Ƀ[/dark_goldenrod]',
        'Crate': '[light_goldenrod3]₢[/light_goldenrod3]',
        'Sacks': '[khaki3]ṩ[/khaki3]',
        'Weapon Rack': '[grey84]♠[/grey84]',
        'Boat': '[magenta]ẞ[/magenta]',
        'Row Boat': '[magenta]Ṝ[/magenta]',
        'Ship': '[magenta]ᵿ[/magenta]',
        'Horse Wagon': '[magenta]◊[/magenta]',
        'Canon': '[grey84]ꬹ[/grey84]',
        'Flag Pole': '[red]Ƒ[/red]',
        'Banner': '[red]Ɓ[/red]',
        'Globe': '[green]₲[/green]',
        'Orrery': '[gold3]ⱺ[/gold3]',
        'Charcoal Mound': '[bright_red]Ꜿ[/bright_red]',
        'Kiln': '[bright_red]Ꝃ[/bright_red]',
        'Pottery Wheel': '[orange4]Ꝑ[/orange4]',
        'Floor Mirror': '[white]ᵯ[/white]',
        'Oven': '[bright_red]Ꝙ[/bright_red]',
        'Lockbox': '[gold3]Ⱡ[/gold3]',
        'Xylophone': '[grey85]♪[/grey85]',
        'Guitar': '[dark_goldenrod]♯[/dark_goldenrod]',
        'Menorah': '[gold3]₸[/gold3]',
        'Coins': '[gold1]₡[/gold1]',
        'Gems': '[magenta]ꞡ[/magenta]',
        'Gold Bar': '[gold1]₲[/gold1]',
        'Balance Scale': '[yellow]₮[/yellow]',
        'Easel': '[orange4]Д[/orange4]',
        'Child\'s Toys': '[white]Ɀ[/white]',
        'Tapestry': '[purple4]Ԏ[/purple4]',
        'Craddle': '[orange4]ᴗ[/orange4]',
        'Churn': '[orange4]ʆ[/orange4]',
        'River Crossing': '[orange4]⁞[/orange4]',
        'Mushrooms': '[tan]₼[/tan]',
        'Bones': '[white]↔[/white]',
        'Clock': '[gold3]§[/gold3]',
        'Portal': '[magenta]ᾮ[/magenta]',
        'Spider Web': '[white]ᾧ[/white]',
        'Wine Press': '[blue_violet]Ꝥ[/blue_violet]',
        'Grave Stone': '[grey78]ṉ[/grey78]',
        'Camp Fire': '[bright_red]ᵮ[/bright_red]',
        'Bellows': '[tan]ꞵ[/tan]',
        }

def time_stamp(offset=0):
	time_stamp = (dt.datetime.now() + dt.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

class Map:
    def __init__(self, game, map_size=None):
        self.game = game
        if args.map is None:
            world_map = self.gen_map(map_size)
            # world_map = Reactive(self.gen_map(map_size))
        else:
            world_map = self.map_gen_file()
            # world_map = Reactive(self.map_gen_file())
        self.update_display_map()
        if args.start is not None:
            pos = args.start
        else:
            pos = (int(round(self.map_size[0]/2, 0)), int(round(self.map_size[1]/2, 0)))
        self.view_port(pos)
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
                    terrain_select = random.choices(self.terrain_items['item_id'].tolist(), self.terrain_items['coverage'].tolist())[0] # TODO This no longer works
                    # print(terrain_select)
                else:
                    terrain_select = 'Grassland'
                    tile.update({'terrain': Tile(terrain_select, self.terrain_items)})

        # self.world_map = pd.DataFrame(self.world_map) # Replace pandas here
        # self.world_map.applymap(lambda d: d.update({'terrain': Tile()})) # Replace pandas here
        return self.world_map
    
    def map_gen_file(self, infile='data/map.csv'):
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
        # print('world_map 1:', world_map)
        self.get_terrain_data()
        tiles = {k: v.split('[')[1].split(']')[1] for k, v in TILES.items()}
        inv_tiles = {v: k for k, v in tiles.items()}
        print('Map Legend:', inv_tiles)
        for i, row in map_data.iterrows():
            for j, tile in enumerate(row):
                if tile in inv_tiles:
                    terrain_select = inv_tiles[tile]
                elif tile is np.nan:
                    print(f'{i}, {j} | nan_tile: {tile} replaced with Grassland.')
                    terrain_select = 'Grassland' #tile
                else:
                    print(time_stamp() + f'{i}, {j} | tile: {tile}')
                    terrain_select = tile
                self.world_map[i][j].update({'terrain': Tile(terrain_select, self.terrain_items)})
        return self.world_map

    def export_map(self, filename=None):
        if filename is None:
            filename = input('Enter filename: ')
        if '.csv' not in filename:
            filename = filename + '.csv'
        if 'data/' not in filename:
            filename = 'data/' + filename
        print('Export filename: ', filename)
        df = pd.DataFrame(self.display_map)
        print(df)
        df.to_csv(filename, index=False, header=False)
    
    def save_map(self, filename=None, v=True):
        if filename is None:
            filename = input('Enter filename: ')
        if '.csv' not in filename:
            filename = filename + '.csv'
        if 'data/' not in filename:
            filename = 'data/' + filename
        print('Save filename: ', filename)
        if v: print(repr(self.world_map))
        with open(filename, 'r') as f:
            f.write(repr(self.world_map))
            f.close()

    def set_map_size(self, x=None, y=None):
        print('Current Map Size:', self.map_size)
        if x is None:
            x = input('Enter x new size: ')
        if x == '':
            return
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

    def set_view_size(self, pos, x=None, y=None):
        print('Current Map View:', self.map_view)
        if y is None:
            y = input('Enter y new size (75): ')
        if y == '':
            return
        if x is None:
            x = input('Enter x new size (81): ')
        if x == '':
            return
        if y == '':
            y = x
        new_view_size = (int(y), int(x))
        print('New Map view:', new_view_size)
        if args.view_size is not None:
            args.view_size = new_view_size
        self.view_port(pos, new_view_size)

    def view_port(self, pos, map_view=None): # TODO Optimize this
        if map_view is None and args.view_size is not None:
            map_view = args.view_size
        self.map_view = map_view
        # print('self.map_view:', self.map_view)
        if isinstance(self.map_view, int):
            self.map_view = (self.map_view, self.map_view)
        elif len(self.map_view) == 1:
            self.map_view = (self.map_view[0], self.map_view[0])
        map_view_y = self.map_view[0]
        map_view_x = self.map_view[1]
        top_left = (pos[0] - int(self.map_view[0]/2), pos[1] - int(self.map_view[1]/2))
        top_left_y = top_left[0]
        top_left_x = top_left[1]
        self.view_port_map = [[' ' for _ in range(self.map_view[1])] for _ in range(self.map_view[0])]
        for i, row in enumerate(self.display_map):
            if i < top_left_y:
                continue
            if i >= top_left_y + map_view_y:
                continue
            for j, tile in enumerate(row):
                if j < top_left_x:
                    continue
                if j >= top_left_x + map_view_x:
                    continue
                self.view_port_map[i-top_left_y][j-top_left_x] = tile
        return self.view_port_map

    def update_display_map(self):
        self.display_map = [[None for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        for i, row in enumerate(self.world_map):
            for j, tile in enumerate(row):
                terrain_tile = tile.get('terrain')
                if terrain_tile.hidden:
                    continue
                terrain = terrain_tile.terrain
                if terrain in TILES:
                    icon = TILES[terrain]
                elif tile is np.nan:
                    icon = '.'
                else:
                    icon = terrain
                self.display_map[i][j] = icon

                if tile.get('Agent'):
                    agent_tile = tile.get('Agent')
                    print('agent_tile:', agent_tile)
                    print('agent_tile type:', type(agent_tile))
                    icon = agent_tile.icon
                    self.display_map[i][j] = icon

    def get_terrain_data(self, infile='../acct_legacy/data/items.csv'):
        if not os.path.exists(infile):
            infile='data/items.csv'
        with open(infile, 'r') as f:
            self.terrain_items = pd.read_csv(f, keep_default_na=False, comment='#')
        self.terrain_items = self.terrain_items[self.terrain_items['child_of'] != 'Loan']
        self.terrain_items = self.terrain_items[self.terrain_items['freq'] != 'animal']
        # self.terrain_items['int_rate_var'] = self.terrain_items['int_rate_var'].astype(float)
        # self.terrain_items['coverage'] = self.terrain_items['int_rate_var'] / self.terrain_items['int_rate_var'].sum()
        print('terrain_items:')
        print(self.terrain_items)

    def edit_terrain(self, y=None, x=None, terrain=None):
        if y is None:
            y = input('Enter x coord: ')
        try:
            y = int(y)
        except ValueError:
            print('Enter whole numbers only, try again.')
            return
        if x is None:
            x = input('Enter x coord: ')
        try:
            x = int(x)
        except ValueError:
            print('Enter whole numbers only, try again.')
            return
        if terrain is None:
            terrain = input('Enter terrain: ')
        pos = (int(y), int(x))
        terrain = terrain.title()
        tile = self.world_map[pos[0]][pos[1]]
        tile.update({'terrain': Tile(terrain, self.terrain_items)})
        if terrain in TILES:
            icon = TILES[terrain]
        elif tile is np.nan:
            icon = '.'
        else:
            icon = terrain
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

    def col(self, letters=None):
        # For max of 3 letters
        if letters is None:
            print('Need to enter letters with the command.')
            # letters = input('Enter column letters: ')
            # return
            # prompt = self.game.query_one('#prompt')
            # letters = prompt.value
        letters = letters.upper()
        if len(letters) == 1:
            col_pos = ord(letters[:1])-64
        elif len(letters) == 2:
            col_pos = ((ord(letters[:1])-64) * 26) + (ord(letters[1:2])-64)
        elif len(letters) == 3:
            col_pos = (676 + (ord(letters[1:2])-64) * 26) + (ord(letters[2:3])-64)
        else:
            print('Columns of only 3 letters supported.')
        # text_log.write('Letters:', letters)
        # text_log.write('Column:', col_pos)
        print(f'{letters} is column {col_pos}.')
        return col_pos

    def __str__(self):
        # self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        # self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
        self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.view_port_map])
        return self.map_display

    # def __repr__(self):
    #     self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
    #     # self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
    #     return self.map_display

class Tile:
    def __init__(self, terrain='Land', terrain_items=None):
        self.terrain = terrain
        if terrain in TILES:
            self.icon = TILES[terrain]
        else:
            self.icon = terrain
        try:
            # Note: The move cost data is contained in the int_rate_fix column.
            # TODO move from int_rate_fix column to int_rate_var column?
            self.move_cost = terrain_items[terrain_items['item_id'] == self.terrain]['int_rate_fix'].values[0]
        except IndexError:
            # print('Move cost of 1 for:', terrain)
            self.move_cost = 1
        if self.move_cost == 'None':
            self.move_cost = None
        if self.move_cost is not None:
            self.move_cost = float(self.move_cost)
        self.hidden = False

    def __str__(self):
        return self.terrain

    def __repr__(self):
        return self.terrain

class Player:
    def __init__(self, name, world_map, icon='P', start=None, v=False):
        self.name = name
        self.world_map = world_map
        self.icon = icon#'[blink]' + icon + '[/blink]'
        if v: print(f'{self} icon: {self.icon}')
        # self.pos = (0, int(icon)-1) # Start position at top left
        if start is None:
            self.pos = (int(round(self.world_map.map_size[0]/2, 0)), int(round(self.world_map.map_size[1]/2, 0)+int(icon)-1)) # Start position near middle
        else:
            start = (start[0], start[1] + (int(icon)-1))
            self.pos = start
        if v: print(f'{self} start pos: {self.pos}')
        self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
        self.current_terrain = world_map.world_map[self.pos[0]][self.pos[1]]['terrain']
        self.world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self
        self.world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
        # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name # Replace pandas here
        self.movement = 5
        self.remain_move = self.movement
        self.boat = False

    def reset_moves(self):
        self.remain_move = self.movement
        print(f'Moves reset to {self.movement} for {self}.')

    def change_dir(self, key):
        direction = {'w': 'Ʌ', 'a': '<', 's': 'V', 'd': '>'}
        self.icon = direction[key]
        world_map.display_map[self.pos[0]][self.pos[1]] = self.icon

    def move(self, dy, dx, teleport=False):
        if not teleport:
            self.old_pos = self.pos
        else:
            print(f'{self} teleported.')
        # self.current_terrain = world_map.world_map[self.pos[0]][self.pos[1]]['terrain']
        print(f'{self.name} position: {self.pos} on {self.current_tile} | Moves: {self.remain_move} / {self.movement} | {self.current_terrain}')# | Test01\rTest02')
        # if self.get_command() is None: # TODO This isn't very clear
        #     return
        self.pos = (self.pos[0] + dy, self.pos[1] + dx)
        if self.is_occupied(self.pos):
            self.pos = self.old_pos
            return
        if not self.calc_move(self.pos):
            self.pos = self.old_pos
            return
        try:
            world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self
            world_map.display_map[self.old_pos[0]][self.old_pos[1]] = self.current_tile
            self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
            self.current_terrain = world_map.world_map[self.pos[0]][self.pos[1]]['terrain']
            world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
            del world_map.world_map[self.old_pos[0]][self.old_pos[1]]['Agent']
            # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.name # Replace pandas here
            # del world_map.world_map.at[self.old_pos[0], self.old_pos[1]]['Agent'] # Replace pandas here
        except (IndexError, KeyError) as e: # TODO Is this check still needed?
            print('Out of bounds, try again.')
            self.pos = self.old_pos
            return
        # print('End move.')

    def is_occupied(self, pos):
        try:
            if 'Agent' in world_map.world_map[pos[0]][pos[1]]:
                print('Cannot move to the same space as another Player or NPC.')
                return True
        except (IndexError, KeyError) as e:
            print('Out of bounds, try again.')
            return True

    def calc_move(self, pos, v=False):
        reset = False
        target_terrain = world_map.world_map[pos[0]][pos[1]]['terrain']
        if v: print('target_terrain:', target_terrain)
        if v: print('target_terrain.move_cost:', target_terrain.move_cost)
        if v: print('remaining_moves:', self.remain_move)
        # TODO Add ability for items to modify terrain_move_cost.
        move_cost = target_terrain.move_cost
        if self.boat:
            if target_terrain.terrain == 'Ocean':
                move_cost = 0.1
            else:
                move_cost = None
        if move_cost is None:                
            # if self.boat and target_terrain.terrain == 'Ocean':
            #     move_cost = 0.1
            # else:
                print(f'Cannot cross {target_terrain} ({target_terrain.icon}) tile at {pos}.')
                return
        if self.remain_move >= move_cost:
            if self.remain_move == move_cost or self.remain_move < 1: # TODO Is this the best way to rest the moves?
                reset = True
            self.remain_move -= move_cost
            if reset:
                self.reset_moves()
            return True
        else:
            print(f'Costs {target_terrain.move_cost} movement to enter {target_terrain} ({target_terrain.icon}) tile. Movement remaining: {self.remain_move}/{self.movement}')

    def mount(self):
        print('mount current_tile:', self.current_terrain.terrain)
        print('boat before:', self.boat)
        if self.current_terrain.terrain == 'Boat' or self.boat: #451, 279
            if self.boat:
                print('Set to Boat.', self.pos)
                # Change tile to Boat using edit function
                # world_map.display_map[self.pos[0]][self.pos[1]] = self.boat_tile#Tile('Boat', world_map.terrain_items)
                world_map.edit_terrain(self.pos[0], self.pos[1], 'Boat')
            self.boat = not self.boat
            # Change tile to Ocean using edit function
            if self.boat:
                print('Set to Ocean.', self.pos)
                self.boat_tile = self.current_tile
                print('boat_tile:', self.boat_tile)
                # world_map.display_map[self.pos[0]][self.pos[1]] = world_map.display_map[0][0]#Tile('Ocean', world_map.terrain_items)
                world_map.edit_terrain(self.pos[0], self.pos[1], 'Ocean')
            print('boat:', self.boat)
        print('boat out:', self.boat)

    def get_command(self, command=None):
        # print('\nEnter "exit" to exit.')#\033[F #\r
        if command is None:
            command = input('Use wasd to move: ')
        # print('=' * ((world_map.map_view[1]*2)-1))
        command = command.lower().split(' ')
        # print('Command is:', command)
        if command[0] == 'exit':
            quit()
        # elif command == 'map':
        #     print(f'Display current world map:\n{world_map}')
        #     self.pos = self.old_pos
        #     return
        elif command[0] == 'terrain' or command[0] == 'items':
            print('Display terrain item details:\n', world_map.terrain_items)
            # self.pos = self.old_pos
            return
        # elif command == 'r' or command == 'reset':
        #     self.reset_moves()
        #     self.pos = self.old_pos
        #     return
        elif command[0] == 'n' or command[0] == 'next':
            self.remain_move = 0
            # self.pos = self.old_pos
            return
        elif command[0] == 'size': # Update input
            world_map.set_map_size(command[1], command[2])
            # self.pos = self.old_pos
            return
        elif command[0] == 'v' or command[0] == 'view': # Update input
            world_map.set_view_size(self.pos, command[1], command[2])
            # self.pos = self.old_pos
            return
        elif command[0] == 'edit': # Update input
            world_map.edit_terrain(command[1], command[2], command[3])
            # self.pos = self.old_pos
            return
        elif command[0] == 'export': # Update input
            world_map.export_map(command[1])
            # self.pos = self.old_pos
            return
        elif command[0] == 'savemap':
            world_map.export_map(command[1])
            return
        elif command[0] == 'col':
            try:
                world_map.col(command[1])
            except IndexError:
                print('Enter the letters for the column with a space after "col".')
            # self.pos = self.old_pos
            return
        elif command[0] == 'c' or command[0] == 'cords':
            print(CORDS)
            # self.pos = self.old_pos
            return
        # elif command == 'w':
        #     self.pos = (self.pos[0] - 1, self.pos[1])
        # elif command == 's':
        #     self.pos = (self.pos[0] + 1, self.pos[1])
        # elif command == 'a':
        #     self.pos = (self.pos[0], self.pos[1] - 1)
        # elif command == 'd':
        #     self.pos = (self.pos[0], self.pos[1] + 1)
        elif command[0] == 'tp': # TODO Turn into teleport() function
            # y = input('Enter y coord: ')
            try:
                y = command[1]
            except IndexError:
                print('Enter the Y cord after a space after "tp".')
            if y == '':
                return
            # x = input('Enter x coord: ')
            try:
                x = command[2]
            except IndexError:
                print('Enter the X cord after a space after the Y cord.')
            if x == '':
                return
            try:
                x = int(x)
            except ValueError:
                pass
            if isinstance(x, str):
                x = world_map.col(x)
            try:
                self.old_pos = self.pos
                self.pos = (int(y)-1, int(x)-1)
                self.move(0, 0, teleport=True)
                world_map.game.update_viewport()
                world_map.game.update_status()
            except ValueError:
                print('Enter whole numbers only, try again.')
                self.pos = self.old_pos
                return
        else:
            print('Not a valid command, please try again.')
            # self.pos = self.old_pos
            return
        # return self.pos

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class StdoutRedirector:
    '''Redirects stdout to a RichLog widget.'''
    def __init__(self, log_widget: RichLog):
        self.log_widget = log_widget
        self.is_widget_update = False # Flag to differentiate rendering updates

    def write(self, text):
        if self.is_widget_update:
            return # Ignore rendering updates caused by Static widget updates
        if text.strip() and 'Player ' not in text:  # Discard 'Player' updates or empty lines
            # self.log_widget.write(text.strip())
            self.log_widget.write(text[:-1])

    def flush(self):
        pass # No-op to satisfy the file-like interface

    def set_widget_update(self, flag: bool):
        '''Set flag to indicate whether this is a widget update.'''
        self.is_widget_update = flag

class StdinRedirector:
    '''Redirects stdin to an Input widget.'''
    def __init__(self, input_widget: Input):
        self.input_widget = input_widget
        # self.input_buffer = ''
        self.input_buffer = []

    def readline(self):#async
        # Simulate blocking input from the Input widget
        while not self.input_buffer:
            self.input_widget.app.refresh() # Ensure the UI updates
            # await asyncio.sleep(0) # Yield control to the event loop
        # line = self.input_buffer
        # self.input_buffer = ''  # Clear buffer after reading
        line = self.input_buffer.pop(0)
        print('[DEBUG] readline:')
        print(line)
        return line

    def feed_input(self, text: str):
        '''Feeds input into the buffer (to be called when Input gets data).'''
        # self.input_buffer = text
        self.input_buffer.append(text)  # Add input to the buffer
        # print('input_buffer:')
        # print(self.input_buffer)
        line = self.input_buffer.pop(0)
        # print('[DEBUG] feed_input:', line)
        return line 

class MapContainer(Container):
    def on_size(self):
        return self.size

class StatusBar(Container):#Static
    pass
    # def __init__(self, player):
    #     super().__init__()
    #     self.player = player
    
    # def on_mount(self):
    #     status = f'{self.player.name} position: {self.player.pos} on {self.player.current_tile} | Moves: {self.player.remain_move} / {self.player.movement} | {self.player.current_terrain}'
    #     self.update(status)

    # def on_key(self):
    #     status = f'{self.player.name} position: {self.player.pos} on {self.player.current_tile} | Moves: {self.player.remain_move} / {self.player.movement} | {self.player.current_terrain}'
    #     self.update(status)

class CivRPG(App):
    CSS = '''
    Screen {
        layout: vertical;
        align: center middle;
        background: black;
    }

    MapContainer {
        height: 1fr;
    }

    StatusBar {
        height: 1;
        align: center bottom;
    }

    RichLog {
        height: 1fr;
        width: 1fr;
        background: black;
        color: green;
        text-style: bold;
    }

    Input {
        color: green;
        text-style: bold;
    }
    '''

    def __init__(self, num_players=1):
        super().__init__()
        self.stdout_redirector = None
        self.stdin_redirector = None
        global world_map 
        world_map = Map(self)
        players = []
        for player_num in range(num_players):
            player_name = 'Player ' + str(player_num+1)
            self.player = Player(player_name, world_map, str(player_num+1), args.start)
            players.append(self.player)
        # print(f'Players:\n{players}')
        self.viewport = Static('')
        self.status_bar = Static('')
        console = Console()
        print('console size:', console.size)
        world_map.set_view_size(self.player.pos, (console.size[0]//2)-1, console.size[1])
        # world_map.view_port(self.player.pos)
        self.update_status()#False)
        self.pressed_keys = set()
        print(f'world_map:\n{world_map}')

    def compose(self):
        with TabbedContent():
            with TabPane('Map', id='map_tab'):
                yield MapContainer(self.viewport)#, id='map')
                yield StatusBar(self.status_bar)#, id='status_bar')
            with TabPane('Log', id='log_tab'):
                yield RichLog(wrap=False, id='log_widget')#highlight=True, markup=True, wrap=True, id='log_widget')
                yield Input(placeholder='Enter command...', type='text', id='prompt')

    # def on_ready(self):
    #     self.text_log = self.query_one('#log_widget')

        # builtins.print = self.print_override
        # print('Test message to log.')
        # print(CORDS)

    def on_tabs_tab_activated(self, event):
        # Focus the input widget corresponding to the active tab
        if event.tab.id == 'log_tab':
            self.query_one("#prompt").focus()

    def update_viewport(self):#async
        # await asyncio.sleep(0)  # Yield control to ensure async behavior
        # self.stdout_redirector.set_widget_update(True) # Start widget update
        visible_map = world_map.view_port(self.player.pos)
        visible_map = '\n'.join([' '.join([str(tile) for tile in row]) for row in visible_map])
        # visible_map = '\n'.join([' '.join([Pretty(str(tile)) for tile in row]) for row in visible_map])
        self.viewport.update(visible_map)#await
        # self.stdout_redirector.set_widget_update(False) # End widget update
    
    def update_status(self):#, check=True):#async
        # await asyncio.sleep(0)  # Yield control to ensure async behavior
        # if check: # TODO Find a better solution for the initial update
        #     print('Status update allowed 01.')
        #     self.stdout_redirector.set_widget_update(True) # Start widget update
        status = f'[green]{self.player.name} position: [/green][cyan]{self.player.pos}[/cyan][green] on [/green]{self.player.current_tile}[green] | Moves: [/green][cyan]{self.player.remain_move:.2f}[/cyan][green] / [/green][cyan]{self.player.movement}[/cyan][green] | {self.player.current_terrain}[/green]'
        self.status_bar.update(status)#await
        # time.sleep(0.5)
        # self.status_bar.update(self.player)
        # if check:
        #     self.stdout_redirector.set_widget_update(False) # End widget update

    def on_mount(self):
        '''Redirect stdout and stdin'''
        log_widget = self.query_one('#log_widget')
        self.stdout_redirector = StdoutRedirector(log_widget)
        sys.stdout = self.stdout_redirector
        input_widget = self.query_one('#prompt')
        self.stdin_redirector = StdinRedirector(input_widget)
        sys.stdin = self.stdin_redirector
        # Set up input widget to capture input
        input_widget.action_submit = self.capture_input
        # Example print to test stdout
        print('Use WASD to move on the map view. Or type a command below and press Enter.')

        # TODO Need to support multiple units/players
        self.update_viewport()

    def capture_input(self):
        '''Capture input from the Input widget.'''
        input_widget = self.query_one('#prompt')
        user_input = input_widget.value
        input_widget.value = ''  # Clear the input field
        self.stdin_redirector.feed_input(user_input)# + '\n')
        # print(Pretty(user_input))
        print('>>>', user_input)
        self.player.get_command(user_input)

    # def on_key(self, event): #Orig
    #     focused_widget = self.focused
    #     if isinstance(focused_widget, Input):
    #         return
    #     moves = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
    #     if event.key in moves:
    #         dx, dy = moves[event.key]
    #         self.player.move(dy, dx)
    #         self.update_viewport()
    #     elif event.key == 'r':
    #         self.player.reset_moves()
    #     self.update_status()
    #     self.text_log.write(event.key)

##########################################################

    def on_key(self, event):
        focused_widget = self.focused
        # print('focused_widget:', focused_widget)
        # self.text_log.write(print('focused_widget:', focused_widget))
        if isinstance(focused_widget, Input):
            # print('focused_widget:', focused_widget)
            # self.text_log.write(print('focused_widget:', focused_widget))
            return
        moves = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
        if event.key in moves:
            if event.key not in self.pressed_keys:
                self.pressed_keys.add(event.key)
                self.player.change_dir(event.key)
                dx, dy = moves[event.key]
                self.player.move(dy, dx)
                self.update_viewport()
                self.pressed_keys.remove(event.key)
        elif event.key == 'r':
            self.player.reset_moves()
        elif event.key == 'e':
            print('Mounting boat.')
            self.player.mount()
            self.update_viewport()
        self.update_status()
        # self.text_log.write(event.key)

##########################

    # async def on_key(self, event):
    #     moves = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
    #     if event.key in moves:
    #          if event.key not in self.pressed_keys:
    #             self.pressed_keys.add(event.key)
    #             dx, dy = moves[event.key]
    #             # await self.player.move(dy, dx)
    #             self.player.move(dy, dx)
    #             # await self.update_viewport()
    #             self.update_viewport()
    #             await asyncio.sleep(0.1)
    #     elif event.key == 'r':
    #         self.player.reset_moves()
    #     self.update_status()
    
    # def on_key_release(self, event):
    #     if event.key in self.pressed_keys:
    #         self.pressed_keys.remove(event.key)

    # def process_key(self, key):
    #     moves = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
    #     if key in moves:
    #         dx, dy = moves[key]
    #         self.player.move(dy, dx)
    #         self.update_viewport()
    #     elif key == 'r':
    #         self.player.reset_moves()

    # def on_key(self, event):
    #     # if self.timer:
    #     #     self.timer.stop()
    #     self.timer = self.set_timer(1, self.process_key(event.key))
    #     self.update_status()

    # async def on_key(self, event):
    #     if self.timer:
    #         self.timer.stop()
    #     moves = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
    #     if event.key in moves:
    #         dx, dy = moves[event.key]
    #         await self.player.move(dy, dx)
    #         await self.update_viewport()
    #     elif event.key == 'r':
    #         self.player.reset_moves()
    #     self.update_status()
    #     await asyncio.sleep(0.1)

    # def on_input_submitted(self, event):
    #     self.text_log.write(event.value)
    #     self.query_one("#prompt").clear()
    #     print('test_get_command01:')
    #     self.player.get_command(event.value)
    #     return event.value

    # def print_override(*args, **kwargs):
    #     if len(args) == 1:
    #         self.text_log.write(str(args[0]))
    #     else:
    #         for i, arg in enumerate(args):
    #             if i:
    #                 self.text_log.write(kwargs[0])
    #             self.text_log.write(str(arg))
    #     builtins.print(*args, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', type=str, default='445, 229', help='The starting coords for the player.')#338, 178
    parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
    parser.add_argument('-r', '--seed', type=str, default=11, help='Set the seed for the randomness.')
    parser.add_argument('-m', '--map', type=str, default='map.csv', help='The name of the map csv data file.')
    parser.add_argument('-p', '--players', type=int, default=1, help='The number of players in the world.')
    parser.add_argument('-vs', '--view_size', type=str, default='21, 33', help='The size of the view of the world.')
    parser.add_argument('-z', '--size', type=str, help='The map size as either a list of two numbers or one for square.')
    args = parser.parse_args()

    if args.seed:
        print(time_stamp() + f'Randomness seed {args.seed}.')
        random.seed(args.seed)
    if args.size is not None:
        if not isinstance(args.size, (list, tuple)):
            args.size = [int(x.strip()) for x in args.size.split(',')]
            MAP_SIZE = args.size
            print('MAP_SIZE:', MAP_SIZE)

    if args.view_size is not None:
        if not isinstance(args.view_size, (list, tuple)):
            if isinstance(args.view_size, str):
                args.view_size = [int(x.strip()) for x in args.view_size.split(',')]
            # print('view_size arg:', args.view_size)

    if args.start is not None:
        if not isinstance(args.start, (list, tuple)):
            if isinstance(args.start, str):
                args.start = tuple(int(x.strip()) for x in args.start.split(','))
                # args.start = tuple(x.strip() for x in args.start.split(','))
                # try:
                #     args.start = tuple(int(x) for x in args.start)
                # except ValueError:
                #     pass
                # if isinstance(args.start[0], str):
                #     args.start[0] = world_map.col(args.start[0]) # TODO Maybe make world_map.col() global?
                #     args.start = tuple(int(x) for x in args.start)
            else:
                args.start = (args.start, args.start)

    app = CivRPG(args.players)
    app.run()

    # while True:
    #     for player in players:
    #         while player.remain_move:
    #             world_map.view_port(player.pos)
    #             print(f'Current world map:\n{world_map}')
    #             player.move()
    #         player.reset_moves()


## TODO
# Make togglable options for map wrapping?
# Add support for mobs and combat
# Add roof reveal support
# Change player icon to arrows to show direction (<>VɅ)
# Add multi levels by having other levels in the dict
# Add popup window for examining a tile with subtile items (such as a table)

# Add tabs at top with RichLog
# Add input box for tp coords

## TODO
# Fix map lag on held input
# Fix map update wave
# Fix map colors compared to Rich


# scp data/items.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp data/map.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp move.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct