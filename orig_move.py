#!/usr/bin/env python

import pandas as pd
import numpy as np
import argparse
import random
from rich import print
import datetime as dt

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
            'Ship': '[magenta]ᵿ[/magenta]',
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
            'Garve Stone': '[grey78]ṉ[/grey78]',
            'Camp Fire': '[bright_red]ᵮ[/bright_red]',
            'Bellows': '[tan]ꞵ[/tan]',
        }

def time_stamp(offset=0):
	time_stamp = (dt.datetime.now() + dt.timedelta(hours=offset)).strftime('[%Y-%b-%d %I:%M:%S %p] ')
	return time_stamp

class Map:
    def __init__(self, map_size):
        if args.map is None:
            self.gen_map(map_size)
        else:
            self.map_gen_file()
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
        # print('world_map 1:', self.world_map)
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
        # print('new_view_size:', new_view_size)
        if args.view_size is not None:
            args.view_size = new_view_size
        self.view_port(pos, new_view_size)

    def view_port(self, pos, map_view=None):
        if map_view is None and args.view_size is not None:
            map_view = args.view_size
        self.map_view = map_view
        # print('self.map_view:', self.map_view)
        if isinstance(self.map_view, int):
            self.map_view = (self.map_view, self.map_view)
        elif len(self.map_view) == 1:
            self.map_view = (self.map_view[0], self.map_view[0])
        top_left = (pos[0] - int(self.map_view[0]/2), pos[1] - int(self.map_view[1]/2))
        self.view_port_map = [[' ' for _ in range(self.map_view[1])] for _ in range(self.map_view[0])]
        for i, row in enumerate(self.display_map):
            if i < top_left[0]:
                continue
            if i >= top_left[0] + self.map_view[0]:
                continue
            for j, tile in enumerate(row):
                if j < top_left[1]:
                    continue
                if j >= top_left[1] + self.map_view[1]:
                    continue
                self.view_port_map[i-top_left[0]][j-top_left[1]] = tile
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

    def get_terrain_data(self, infile='data/items.csv'):
        with open(infile, 'r') as f:
            self.terrain_items = pd.read_csv(f, keep_default_na=False, comment='#')
        self.terrain_items = self.terrain_items[self.terrain_items['child_of'] != 'Loan']
        self.terrain_items = self.terrain_items[self.terrain_items['freq'] != 'animal']
        # self.terrain_items['int_rate_var'] = self.terrain_items['int_rate_var'].astype(float)
        # self.terrain_items['coverage'] = self.terrain_items['int_rate_var'] / self.terrain_items['int_rate_var'].sum()
        print('terrain_items:')
        print(self.terrain_items)

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
            letters = input('Enter column letters: ')
        letters = letters.upper()
        if len(letters) == 1:
            col_pos = ord(letters[:1])-64
        elif len(letters) == 2:
            col_pos = ((ord(letters[:1])-64) * 26) + (ord(letters[1:2])-64)
        elif len(letters) == 3:
            col_pos = (676 + (ord(letters[1:2])-64) * 26) + (ord(letters[2:3])-64)        
        print(f'{letters} is column {col_pos}.')
        return col_pos

    def __str__(self):
        # self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        # self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
        self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.view_port_map])
        return self.map_display

    def __repr__(self):
        self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        # self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
        return self.map_display

class Tile:
    def __init__(self, terrain='Land', terrain_items=None):
        self.terrain = terrain
        if terrain in TILES:
            self.icon = TILES[terrain]
        else:
            self.icon = terrain
        try:
            # Note: The move cost data is contained in the int_rate_fix column.
            # TODO move from int_rate_fix column to int_rate_var column.
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

class Player: # ˂˃˄˅
    def __init__(self, name, world_map, icon='P', start=None, v=False):
        self.name = name
        self.world_map = world_map
        self.icon = '[blink]' + icon + '[/blink]'
        if v: print(f'{self} icon: {self.icon}')
        # self.pos = (0, int(icon)-1) # Start position at top left
        if start is None:
            self.pos = (int(round(self.world_map.map_size[0]/2, 0)), int(round(self.world_map.map_size[1]/2, 0)+int(icon)-1)) # Start position near middle
        else:
            start = (start[0], start[1] + (int(icon)-1))
            self.pos = start
        if v: print(f'{self} start pos: {self.pos}')
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
        self.current_terrain = world_map.world_map[self.old_pos[0]][self.old_pos[1]]['terrain']
        print(f'{self.name} position: {self.old_pos} on {self.current_tile} | Moves: {self.remain_move} | {self.current_terrain}')# | Test01\rTest02')
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
            world_map.display_map[self.old_pos[0]][self.old_pos[1]] = self.current_tile
            self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
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
        target_terrain = world_map.world_map[pos[0]][pos[1]]['terrain']
        if v: print('target_terrain:', target_terrain)
        if v: print('target_terrain.move_cost:', target_terrain.move_cost)
        if v: print('remaining_moves:', self.remain_move)
        # TODO Add ability for items to modify terrain_move_cost.
        if target_terrain.move_cost is None:
            print(f'Cannot cross {target_terrain}.')
            return
        if self.remain_move >= target_terrain.move_cost:
            self.remain_move -= target_terrain.move_cost
            return True

    def get_move(self):
        # print('\nEnter "exit" to exit.')#\033[F #\r
        key = input('Use wasd to move: ')
        # print('=' * ((world_map.map_view[1]*2)-1))
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
        if key == 'n' or key == 'next':
            self.remain_move = 0
            self.pos = self.old_pos
            return
        if key == 'v' or key == 'view':
            world_map.set_view_size(self.pos)
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
        if key == 'col':
            world_map.col()
            self.pos = self.old_pos
            return
        if key == 'cords':
            print(CORDS)
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
        elif key == 'tp' or key == 'move':
            x = input('Enter x coord: ')
            if x == '':
                return
            try:
                x = int(x)
            except ValueError:
                pass
            if isinstance(x, str):
                x = world_map.col(x)
            y = input('Enter y coord: ')
            if y == '':
                return
            try:
                self.pos = (int(y)-1, int(x)-1)
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
    parser.add_argument('-s', '--start', type=str, default='338, 178', help='The starting coords for the player.')
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
            else:
                args.start = (args.start, args.start)
    

    world_map = Map(MAP_SIZE)
    players = []
    for player_num in range(args.players):
        player_name = 'Player ' + str(player_num+1)
        player = Player(player_name, world_map, str(player_num+1), args.start)
        players.append(player)
    # print(f'Players:\n{players}')
    world_map.view_port(player.pos)
    # print(f'world_map:\n{world_map}')

    while True:
        for player in players:
            while player.remain_move:
                world_map.view_port(player.pos)
                print(f'Current world map:\n{world_map}')
                player.move()
            player.reset_moves()

## TODO
# Make togglable options for map wrapping
# Add support for mobs and combat
# Add roof reveal support

# scp data/items.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp data/map.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp move.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct