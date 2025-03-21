#!/usr/bin/env python

import pandas as pd
import numpy as np
import argparse
import random
from rich import print
import datetime as dt
import os, sys
import json
from io import StringIO
import asyncio
# import builtins

from textual.app import App, ComposeResult
from textual.widgets import Static, TabbedContent, TabPane, RichLog, Input
from textual.containers import Container
from textual.reactive import reactive
from textual.timer import Timer
from rich.console import Console
from rich.pretty import Pretty
from rich.text import Text

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
        'Buccaneer Den': 'OJ, 486',
        'New Magincia': 'TV, 550',
        'Moonglow': 'ZJ, 379',
        'Dagger Isle': 'YI, 290',
        'Ambrosia': 'AAN, 67',
        'Isle of the Avatar': 'ZJ, 653',
        'Skara Brae': 'DE, 406',
        'Jhelom': 'DR, 634',
        'Pirate House': 'IX, 684',
        'Pirate Cave': 'KT, 695',
        'Serpent Hold': 'NB, 702',
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
        'Sack': '[khaki3]ṩ[/khaki3]',
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
        'Child Toy': '[white]Ɀ[/white]',
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
    def __init__(self, game, map_name, start_loc, view_size, map_size=None):
        self.game = game
        self.map_name = map_name
        self.start_loc = start_loc
        self.view_size = view_size
        self.map_size = map_size
        if self.map_name is None:
            world_map = self.gen_map(self.map_size)
            # world_map = Reactive(self.gen_map(map_size))
        else:
            world_map = self.map_gen_file(self.map_name)
            # world_map = Reactive(self.map_gen_file())
        # if self.view_size[0] > self.map_size[0]:
        #     self.view_size = (self.map_size[0], self.view_size[1])
        #     print('view_size adj 1:', self.view_size)
        #     print('map_size adj 1:', self.map_size)
        # if self.view_size[1] > self.map_size[1]:
        #     self.view_size = (self.view_size[0], self.map_size[1])
        #     print('view_size adj 2:', self.view_size)
        #     print('map_size adj 2:', self.map_size)
        self.update_display_map()
        if self.start_loc is None:
            self.start_loc = (self.map_size[0]//2, self.map_size[1]//2)
            # self.start_loc = (int(round(self.map_size[0]/2, 0)), int(round(self.map_size[1]/2, 0)))
        self.view_port(self.start_loc)
        # print(f'world_map created:\n{self}')

    def gen_map(self, map_size, proc=False):
        if map_size is None:
            map_size = MAP_SIZE # TODO Is this needed still?
        self.map_size = map_size
        if isinstance(self.map_size, int):
            self.map_size = (self.map_size, self.map_size)
        elif len(self.map_size) == 1:
            self.map_size = (self.map_size[0], self.map_size[0])
        print('gen map_size:', self.map_size)
        self.world_map = [[dict() for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        # print('world_map gen:', self.world_map)
        self.get_terrain_data()
        self.load_players = []
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
        self.save_meta()
        # print('world_map gen final:', self.world_map)
        return self.world_map
    
    def map_gen_file(self, infile='data/map.csv', v=False):
        if self.map_name is not None:
            infile = self.map_name
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

        print('First cell type:')
        print(map_data[0][0])
        print(type(map_data[0][0]))
        try:
            cell_check = eval(map_data[0][0])
            print('cell_check:', type(cell_check))
        except (NameError, SyntaxError):
            cell_check = map_data[0][0]
        if isinstance(cell_check, dict):
            print('Is dict')
            self.world_map = self.load(map_data)
            return self.world_map

        self.get_terrain_data()
        tiles = {k: v.split('[')[1].split(']')[1] for k, v in TILES.items()}
        inv_tiles = {v: k for k, v in tiles.items()}
        print('Map Legend:', inv_tiles)
        meta_data = None
        self.load_players = []
        for i, row in map_data.iterrows():
            for j, tile in enumerate(row):
                if len(tile) == 1:
                    if tile in inv_tiles:
                        terrain_select = inv_tiles[tile]
                    elif tile is np.nan:
                        print(f'{i}, {j} | nan_tile: {tile} replaced with Grassland.')
                        terrain_select = 'Grassland' #tile
                    else:
                        print(time_stamp() + f'{i}, {j} | tile: {tile}')
                        terrain_select = tile
                    if v: print(f'{i}, {j} | terrain_select 1:', terrain_select)
                else:
                    if v: print('tile:', tile)
                    icon = tile[0]
                    if v: print('icon:', icon)
                    if icon in inv_tiles:
                        terrain_select = inv_tiles[icon]
                    if v: print(f'{i}, {j}terrain_select 2:', terrain_select)
                    other_data = tile[1:]
                    if v: print('other_data:', other_data)
                    if 'turn' in other_data:
                        meta_data = other_data
                        if v: print('meta_data loaded:', meta_data)
                    elif 'player_name' in other_data:
                        if v: print('player_data:', other_data)
                        player_data = json.loads(other_data, object_hook=None)
                        if v: print('player_data loaded:', player_data)
                        self.load_players.append(player_data)
                    else:
                        if v: print('other_data:', other_data)
                        other_data = json.loads(other_data, object_hook=None)
                        if v: print('other_data loaded:', other_data)
                        # TODO Finish this
                self.world_map[i][j].update({'terrain': Tile(terrain_select, self.terrain_items, loc=(i, j))})
        self.save_meta(meta_data)
        return self.world_map

    def export_map(self, filename=None, strip_rich=True, v=True):
        # Save a csv of just the icon char tiles of the map
        if filename is None:
            filename = input('Enter filename: ')
        if '.csv' not in filename:
            filename = filename + '.csv'
        if 'data/' not in filename:
            filename = 'data/' + filename
        print(time_stamp() + 'Export filename: ', filename)
        if v: print('world_map:\n', self.world_map)
        if v: print('display_map:\n', self.display_map)
        if strip_rich:
            plain_display_map = [[Text.from_markup(cell).plain for cell in row] for row in self.display_map]
        else:
            plain_display_map = self.display_map
        if v: print('plain_display_map:\n', plain_display_map)
        df = pd.DataFrame(plain_display_map)
        if v: print(df)
        df.to_csv(filename, index=False, header=False)
        print(time_stamp() + 'Map exported to:', filename)
    
    def save_map(self, filename='save_map01', use_json=True, strip_rich=True, v=False):
        if filename is None:
            filename = input('Enter filename: ')
        if '.csv' not in filename:
            filename = filename + '.csv'
        if 'data/' not in filename:
            filename = 'data/' + filename
        print(time_stamp() + 'Save filename: ', filename)
        if v: print('world_map:\n', self.world_map)
        if v: print('display_map:\n', self.display_map)
        if strip_rich:
            plain_display_map = [[Text.from_markup(cell).plain for cell in row] for row in self.display_map]
        else:
            plain_display_map = self.display_map
        if v: print('plain_display_map:\n', plain_display_map)
        df = pd.DataFrame(plain_display_map)
        if v: print(df)
        for i, row in enumerate(self.world_map):
            for j, cell in enumerate(row):
                if cell.get('meta'):
                    game_data = cell.get('meta')
                    game_data = {'meta': game_data}
                    contents = plain_display_map[i][j]
                    if v: print(f'{i}, {j} | meta contents: {contents}')
                    if v: print(f'{i}, {j} | meta contents type: {type(contents)}')
                    if use_json:
                        meta_data = contents + json.dumps(game_data)
                        if v: print('meta_data:', meta_data)
                        df[j][i] = meta_data
                if cell.get('Agent'):
                    player_data = cell.get('Agent')
                    contents = player_data.current_terrain.icon
                    contents = Text.from_markup(contents).plain
                    player_data = {'Agent': player_data}
                    if v: print(f'{i}, {j} | player contents: {contents}')
                    if v: print(f'{i}, {j} | player contents type: {type(contents)}')
                    if use_json:
                        agent_data = contents + json.dumps(player_data, default=self.custom_json)
                        if v: print('player agent_data:', agent_data)
                        df[j][i] = agent_data
                #     else:
                #         import pickle
                #         agent = pickle.dumps(agent, pickle.HIGHEST_PROTOCOL)
            if v: print(self.world_map)
            df.to_csv(filename, index=False, header=False)
        print(time_stamp() + 'Map saved to:', filename)

    def load_map(self, filename='save_map01', v=False): # TODO Is this used?
        print(time_stamp() + 'Loadmap with filename:', filename)
        if filename is None:
            filename = input('Enter filename: ')
        if '.csv' not in filename:
            filename = filename + '.csv'
        if 'data/' not in filename:
            filename = 'data/' + filename
        print(time_stamp() + 'Load filename: ', filename)
        with open(filename, 'r') as f:
            map_data = pd.read_csv(f)#, keep_default_na=False, comment='#')
        print(time_stamp() + 'Loading filename: ', filename)
        for i, row in map_data.iterrows():
            for j, tile in enumerate(row):
                # if v: print(f'{i} {row}: {j} {tile}')
                tile = eval(tile)
                # if v: print(f'{i} {row}: {j} {tile}')
                terrain_name = tile['terrain']
                self.world_map[i][j].update({'terrain': Tile(terrain_name, self.terrain_items)})
        print(time_stamp() + 'Loaded filename: ', filename)
        print(time_stamp() + 'Spawning players.')
        self.game.spawn_players()
        print(time_stamp() + 'Spawned players.')

    def save_meta(self, meta_data=None, v=False):
        if meta_data is None:
            meta_data = {'meta': {'players': 'single_player', 'game_mode': 'survival', 'turn': self.game.turn, 'cords': CORDS}}
        else:
            meta_data = eval(meta_data)
        contents = self.world_map[0][0]
        meta_data.update(contents)
        self.world_map[0][0] = meta_data
        if v: print(self.world_map[0][0])
        print('Meta data saved.')
        return meta_data

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

    def set_view_size(self, pos, x=None, y=None, man=False):
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
        # print('New Map view:', new_view_size)
        print(f'Changed view_size from: {self.view_size} to {new_view_size}.')
        self.view_size = new_view_size
        # if self.view_size is not None:# and not man:
        #     print(f'Changed view_size from: {self.view_size} to {new_view_size}.')
        #     self.view_size = new_view_size
        self.view_port(pos)#, new_view_size)

    def view_port(self, pos):#, map_view=None): # TODO Optimize this
        # if map_view is None and self.view_size is not None:
        #     # print('map view arg:', args.view_size)
        #     map_view = self.view_size
        #     # print('use map view arg:', map_view)
        # elif map_view is None:
        #     console = Console()
        #     # print(f'Console Size:', console.size)
        #     map_view = ((int(console.size[0]//2)-1), int(console.size[1]))
        #     # print('Console map view:', map_view)
        # self.map_view = map_view
        # print('self.map_view:', self.map_view)
        # if isinstance(self.map_view, int):
        #     self.map_view = (self.map_view, self.map_view)
        # elif len(self.map_view) == 1:
        #     self.map_view = (self.map_view[0], self.map_view[0])
        map_view_y = self.view_size[0]
        # print('map_view_y:', map_view_y)
        map_view_x = self.view_size[1]
        # print('map_view_x:', map_view_x)
        top_left = (max(pos[0] - int(self.view_size[0]/2), 0), max(pos[1] - int(self.view_size[1]/2), 0))
        top_left_y = top_left[0]
        # print('top_left_y:', top_left_y)
        top_left_x = top_left[1]
        # print('top_left_x:', top_left_x)
        bot_right_y = top_left_y + map_view_y
        # print('bot_right_y:', bot_right_y)
        bot_right_x = top_left_x + map_view_x
        # print('bot_right_x:', bot_right_x)
        # self.view_port_map = [[' ' for _ in range(self.map_view[1])] for _ in range(self.map_view[0])]
        # for i, row in enumerate(self.display_map):
        #     if i < top_left_y:
        #         continue
        #     if i >= bot_right_y:
        #         continue
        #     for j, tile in enumerate(row):
        #         if j < top_left_x:
        #             continue
        #         if j >= bot_right_x:
        #             continue
        #         self.view_port_map[i-top_left_y][j-top_left_x] = tile
        # return self.view_port_map

        self.view_port_map = [
            row[top_left_x:bot_right_x]
            for row in self.display_map[top_left_y:bot_right_y]
        ]
        return self.view_port_map

    def update_display_map(self):
        # TODO should self.display_map be a numpy or df?
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
                    print('Agent Tile:', agent_tile)
                    print('Agent Tile Type:', type(agent_tile))
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

    def edit_map_terrain(self, terrain=None, y=None, x=None):
        if terrain is None:
            terrain = input('Enter terrain: ')
        if y is None:
            # y = self.target_tile.loc[0] # TODO Need to make this a method of Player class
            y = input('Enter x coord: ')
        try:
            y = int(y)
        except ValueError:
            print('Enter whole numbers only, try again.')
            return
        if x is None:
            # y = self.target_tile.loc[1] # TODO Need to make this a method of Player class
            x = input('Enter x coord: ')
        try:
            x = int(x)
        except ValueError:
            print('Enter whole numbers only, try again.')
            return
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
    
    def add_cords(self, name, cords):
        name = name.title()
        cords = cords.upper()
        cords = cords.replace(',', ', ')
        CORDS[name] = cords
        self.save_meta()
        print(CORDS)

    def custom_json(self, obj):
        if isinstance(obj, Tile):
            return obj.json_dump()
        if isinstance(obj, Player):
            return obj.json_dump()
        if isinstance(obj, set):
            obj_desc = obj
        else:
            obj_desc = obj.__dict__
        return obj_desc

    def save(self, filename='save_game01', use_json=True, v=False):#async
        if '.csv' not in filename:
            filename = filename + '.csv'
        if 'data/' not in filename:
            filename = 'data/' + filename
        print(time_stamp() + f'Saving game state to {filename}.')
        save_map = pd.DataFrame(self.world_map)
        print('save_map size:', save_map.size)
        # await asyncio.sleep(0.1)
        for i, row in enumerate(self.world_map):
            if v: print(f'row i: {i}')
            for j, tile in enumerate(row):
                if v: print(f'{j} tile: {tile}')
                if v: print('tile type:', type(tile))
                # await asyncio.sleep(0.1)
                for icon, icon_tile in tile.items():
                    save_tile = {}
                    if v: print('icon:', icon)
                    if v: print('icon_tile:', icon_tile)
                    if v: print('icon_tile type:', type(icon_tile))
                    if icon == 'Agent':
                        print(f'Saving player at {i}, {j}.')
                        if not use_json:
                            save_tile[icon] = icon_tile
                            continue
                    if use_json:
                        json_default = self.custom_json
                        try:
                            icon_tile.__dict__
                        except AttributeError:
                            json_default = None
                        save_tile[icon] = json.dumps(icon_tile, default=json_default)
                    else:
                        import pickle
                        save_tile[icon] = pickle.dumps(icon_tile, pickle.HIGHEST_PROTOCOL)
                save_map[i][j] = save_tile
        save_map.to_csv(filename, index=False, header=False)
        print(time_stamp() + f'Game state saved to {filename}.')

    def load(self, map_data, use_json=True, v=True):
        print(time_stamp() + f'Loading game state.')
        if v: print(map_data)
        for i, row in map_data.iterrows():
            if v: print(f'row i: {i}')
            if v: print('row:\n', (row))
            if v: print('row type:', type(row))
            for j, tile in enumerate(row):
                tile = eval(tile)
                if v: print(f'{j} tile: {tile}')
                if v: print('tile type:', type(tile))
                for icon, icon_tile in tile.items():
                    load_tile = {}
                    if v: print('icon:', icon)
                    if v: print('icon_tile:', icon_tile)
                    if v: print('icon_tile type:', type(icon_tile))
                    # load_tile[icon]
                    if use_json:
                        icon_tile_data = json.loads(icon_tile, object_hook=None)
                        print(icon_tile_data)
                    else:
                        icon_tile_data = pickle.loads(env['obj'])
                    load_tile[icon] = icon_tile_data
                    print(load_tile[icon])
                    exit()
                self.world_map[i][j] = load_tile
        print(time_stamp() + f'Game state loaded.')
        return self.world_map

    def col(self, letters=None):
        # For max of 3 letters
        if letters is None:
            print('Need to enter letters with the command.')
            # letters = input('Enter column letters: ')
            # return
            # prompt = self.game.query_one('#prompt')
            # letters = prompt.value
        try:
            col_pos = int(letters)
            # print(f'{letters} is column {col_pos}.')
            return col_pos
        except ValueError:
            pass
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

    def __repr__(self):
        # self.map_display = '\n'.join(['\t'.join([str(tile) for tile in row]) for row in self.world_map])
        # # self.map_display = '\n'.join([' '.join([str(tile) for tile in row]) for row in self.display_map])
        # return self.map_display
        return self.world_map

class Tile:
    def __init__(self, terrain='Land', terrain_items=None, loc=None):
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
        if loc is not None:
            self.loc = loc
        else:
            self.loc = None
        self.hidden = False

    def json_dump(self):
        return {'tile_name': self.terrain, 'icon': self.icon, 'loc': self.loc, 'move_cost': self.move_cost, 'hidden': self.hidden}

    def __str__(self):
        return self.terrain

    def __repr__(self):
        return f"'{self.terrain}'"
        # return self.terrain

class Player:
    def __init__(self, player_name, world_map, icon='P', start=None, dictionary=None, v=False):
        if dictionary is not None:
            self.world_map = world_map
            # self.player_name = player_name
            self.__dict__.update(dictionary)
        else:
            self.player_name = player_name
            self.world_map = world_map
            self.icon = icon#'[blink]' + icon + '[/blink]'
            if v: print(f'{self} icon: {self.icon}')
            # self.pos = (0, int(icon)-1) # Start position at top left
            if start is None:
                self.pos = (int(round(self.world_map.map_size[0]/2, 0)), int(round(self.world_map.map_size[1]/2, 0)+int(icon)-1)) # Start position near middle
            else:
                start = (start[0], start[1] + (int(icon)-1))
                self.pos = start
            self.movement = 5
            self.remain_move = self.movement
            self.moves = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
            self.boat = False
        print(f'{self} start pos: {self.pos}')
        self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
        self.current_terrain = world_map.world_map[self.pos[0]][self.pos[1]]['terrain']
        self.world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self
        self.world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
        self.target_tile = world_map.display_map[self.pos[0]+1][self.pos[1]]
        self.target_terrain = world_map.world_map[self.pos[0]+1][self.pos[1]]['terrain']
        # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.player_name # Replace pandas here

    def reset_moves(self):
        # self.remain_move = 0
        self.remain_move = self.movement
        # world_map.game.turn += 1
        # print('Turn:', world_map.game.turn)
        print(f'Moves reset to {self.movement} for {self}.')

    def zero_moves(self):
        self.remain_move = 0
        print(f'Moves set to {self.remain_move} for {self}.')

    def change_dir(self, key):
        # print('key:', key)
        direction = {'w': 'Ʌ', 'a': '<', 's': 'V', 'd': '>'}
        self.icon = direction[key]
        world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
        target_offset = self.moves[key]
        # print('target_offset:', target_offset)
        # TODO This will give an error at the map edge
        try:
            if self.pos[0]+target_offset[1] < 0 or self.pos[1]+target_offset[0] < 0:
                self.target_tile = None#' '
                self.target_terrain = None
            else:
                self.target_tile = world_map.display_map[self.pos[0]+target_offset[1]][self.pos[1]+target_offset[0]]
                self.target_terrain = world_map.world_map[self.pos[0]+target_offset[1]][self.pos[1]+target_offset[0]]['terrain']
        except IndexError as e:
            self.target_tile = None#' '
            self.target_terrain = None
            # print('At map edge.')
        # print('pos:', self.pos)
        # print('target_tile:', self.target_tile)
        # print('target_tile type:', type(self.target_tile))

    def move(self, dy, dx, teleport=False):
        if not teleport:
            self.old_pos = self.pos
        else:
            print(f'{self} teleported.')
        # self.current_terrain = world_map.world_map[self.pos[0]][self.pos[1]]['terrain']
        print(f'{self.player_name} position: {self.pos} on {self.current_tile} | Moves: {self.remain_move} / {self.movement} | {self.current_terrain}')# | Test01\rTest02')
        # if self.get_command() is None: # TODO This isn't very clear
        #     return
        self.pos = (self.pos[0] + dy, self.pos[1] + dx)
        if self.pos[0] < 0 or self.pos[0] >= world_map.map_size[0] or self.pos[1] < 0 or self.pos[1] >= world_map.map_size[1]+1:
            print('Out of bounds, try again.')
            self.pos = self.old_pos
            return
        if self.is_occupied(self.pos):
            self.pos = self.old_pos
            return
        if not self.calc_move(self.pos) and not teleport:
            self.pos = self.old_pos
            return
        try:
            world_map.world_map[self.pos[0]][self.pos[1]]['Agent'] = self
            world_map.display_map[self.old_pos[0]][self.old_pos[1]] = self.current_tile
            self.current_tile = world_map.display_map[self.pos[0]][self.pos[1]]
            self.current_terrain = world_map.world_map[self.pos[0]][self.pos[1]]['terrain']
            world_map.display_map[self.pos[0]][self.pos[1]] = self.icon
            del world_map.world_map[self.old_pos[0]][self.old_pos[1]]['Agent']
            # world_map.world_map.at[self.pos[0], self.pos[1]]['Agent'] = self.player_name # Replace pandas here
            # del world_map.world_map.at[self.old_pos[0], self.old_pos[1]]['Agent'] # Replace pandas here
        except (IndexError, KeyError) as e: # TODO Is this check still needed?
            print('Out of map boundry, please try again.')
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
        if v: print('target_terrain type:', target_terrain)
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
            if self.remain_move == move_cost or self.remain_move < 1: # TODO Is this the best way to reset the moves?
                reset = True
            self.remain_move -= move_cost
            # if self.remain_move < 1:
                # reset = True
            if reset:
                # self.reset_moves()
                self.zero_moves()
            return True
        else:
            print(f'Costs {target_terrain.move_cost} movement to enter {target_terrain} ({target_terrain.icon}) tile. Movement remaining: {self.remain_move}/{self.movement}')

    def mount(self, v=False):
        print('Mount target tile:', self.target_terrain.terrain)
        print('Boat before:', self.boat)
        if self.current_terrain.terrain == 'Boat' or self.boat: #451, 279 #self.target_terrain.terrain == 'Boat' or 
            if self.boat:
                print('Set to Boat.', self.pos)
                # Change tile to Boat using edit function
                # world_map.display_map[self.pos[0]][self.pos[1]] = self.boat_tile#Tile('Boat', world_map.terrain_items)
                world_map.edit_map_terrain('Boat', self.pos[0], self.pos[1])
            self.boat = not self.boat
            # Change tile to Ocean using edit function
            if self.boat:
                # print('Target set to Ocean.', self.target_terrain.loc)
                # print('self.pos:', self.pos)
                print('Set to Ocean.', self.pos)
                self.boat_tile = self.current_tile
                if v: print('boat_tile:', self.boat_tile)
                # if self.target_terrain.terrain == 'Boat':
                #     self.pos = self.target_terrain.loc
                #     self.move(0, 0, teleport=True)
                world_map.edit_map_terrain('Ocean', self.pos[0], self.pos[1])
            if v: print('boat:', self.boat)
        if v: print('boat out:', self.boat)

    def get_command(self, command=None):
        # print('\nEnter "exit" to exit.')#\033[F #\r
        if command is None:
            command = input('Use wasd to move: ')
        # print('=' * ((world_map.map_view[1]*2)-1))
        command = command.lower().split(' ')
        # print('Command is:', command)
        if command[0] == 'exit':
            quit()
        elif command[0] == 'map':
            print(f'Display current world map raw:\n{world_map}')
        #     # self.pos = self.old_pos
            return
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
        elif command[0] == 'v' or command[0] == 'view' or command[0] == 'viewsize': # Update input
            world_map.set_view_size(self.pos, command[1], command[2], True)
            # self.pos = self.old_pos
            return
        elif command[0] == 'edit': # Update input
            world_map.edit_map_terrain(command[1], command[2], command[3])
            # self.pos = self.old_pos
            return
        elif command[0] == 'addcords':
            world_map.add_cords(command[1], command[2])
            return
        elif command[0] == 'export': # Update input
            world_map.export_map(command[1])
            # self.pos = self.old_pos
            return
        elif command[0] == 'exportmap':
            world_map.export_map(command[1])
            return
        elif command[0] == 'savemap':
            # TODO If command[1] does not exist, use a default name
            world_map.save_map()#command[1])
            return
        elif command[0] == 'loadmap':
            world_map.load_map()#command[1])
            return
        elif command[0] == 'spawn': # Old
            world_map.game.spawn_players()
            return
        elif command[0] == 'mapinitial':
            print(world_map.world_map[0][0])
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
            # try:
            #     y = int(y)
            # except ValueError:
            #     pass
            # if isinstance(y, str):
            #     y = world_map.col(y)
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
        elif command[0] == 'info':
            status = f'[green]{self.player_name} pos: [/green][cyan]{self.pos}[/cyan][green] moves: [/green][cyan]{self.remain_move:.2f}[/cyan][green] / [/green][cyan]{self.movement}[/cyan][green] faces: [/green]{self.target_tile}[green] {self.target_terrain} on: [/green]{self.current_tile}[green] {self.current_terrain}[/green]'
            print(status)
            print('Player:', self.player_name)
            print('Map Size:', world_map.map_size)
            print('Map View:', world_map.view_size)
            print('Player Pos:', self.pos)
            print('Player Terrain:', self.current_terrain)
            print('Player Target:', self.target_terrain)
            # print('Player Target Pos:', self.target_tile.loc)
        elif command[0] == 'save':
            try:
                world_map.save(command[1])
            except IndexError:
                world_map.save()
            return
        elif command[0] == 'help' or command[0] == 'movehelp':
            commands = {
                'exit': 'Exit the program.',
                'terrain': 'Display the different types of terrains and their stats.',
                'next': 'Next turn.',
                'size': 'Change the size of the map. [row, col]',
                'view': 'Change the display view of the map. [row, col]',
                'edit': 'Edit the terrain at a specific location. [terrain, row, col]',
                'export': 'Export just the tiles of the map. [name]',
                'exportmap': 'Export just the tiles of the map. [name]',
                'save': 'Old slow method of saving the map.',
                'loadmap': 'Old method to load the map from a saved file.',
                'spawn': 'Old method of spawning players on a loaded map.', # Old
                'mapinitial': 'Show the meta data of the game.',
                'col': 'Convert letter columns to numbers. [letters]',
                'cords': 'Display a list of location coordinates.',
                'addcords': 'Add cordinates to the cords list. [name, "row, col"]',
                'tp': 'Teleport the player to a location. [row, col]',
                'savemap': 'Save the map to file.',
            }
            cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
            with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
                print(cmd_table)
        else:
            print('Not a valid command, please try again.')
            # self.pos = self.old_pos
            return
        # return self.pos

    def json_dump(self):
        player_data = self.__dict__
        # print(player_data)
        if player_data.get('world_map'):
            player_data.pop('world_map')
        return player_data

    def __str__(self):
        return self.player_name

    def __repr__(self):
        return f"'{self.player_name}'"
        # return self.player_name


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
            self.log_widget.app.refresh()

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
    # def __init__(self, viewport):
    #     super().__init__()
    #     self.viewport = Static(viewport)
    def on_size(self):
        return self.size

class StatusBar(Container):#Static
    pass
    # def __init__(self, player):
    #     super().__init__()
    #     self.player = player
    
    # def on_mount(self):
    #     status = f'{self.player.player_name} position: {self.player.pos} on {self.player.current_tile} | Moves: {self.player.remain_move} / {self.player.movement} | {self.player.current_terrain}'
    #     self.update(status)

    # def on_key(self):
    #     status = f'{self.player.player_name} position: {self.player.pos} on {self.player.current_tile} | Moves: {self.player.remain_move} / {self.player.movement} | {self.player.current_terrain}'
    #     self.update(status)

class CivRPG(App):
    CSS = '''
    Screen {
        layout: vertical;
        align: center middle;
        background: black;
        # content-align: center middle;
    }

    # MapContainer {
    #     # height: 1fr;
    #     # align: center middle;
    #     # width: auto;
    #     text-align: center;
    #     content-align: center middle;
    #     border: white;
    # }

    #map_container {
        height: 1fr;
        # align: center middle;
        # width: auto;
        text-align: center;
        content-align: center middle;
        # border: white;
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
    # BINDINGS = [
    #             ('[', 'previous_tab', 'Previous tab'),
    #             (']', 'next_tab', 'Next tab'),
    #             # Binding('ctrl+left', 'previous_tab', 'Previous tab', show=False),
    #             # Binding('ctrl+right', 'next_tab', 'Next tab', show=False),
    #             ]

    def __init__(self, map_name, start_loc, view_size=None, num_players=1, filename=None):
        super().__init__()
        self.turn = 1
        self.stdout_redirector = None
        self.stdin_redirector = None
        if view_size is None:
            console = Console()
            print(f'Console Size:', console.size)
            view_size = (console.size[1], (console.size[0]//2)-1)
            print('init view size:', view_size)
        global world_map
        world_map = Map(self, map_name, start_loc, view_size)
        self.players = []
        if not world_map.load_players:
            for player_num in range(num_players):
                player_name = 'Player ' + str(player_num+1)
                self.player = Player(player_name, world_map, str(player_num+1), start_loc)
                self.players.append(self.player)
        else:
            for player_data in world_map.load_players:
                # print('player_data:', player_data)
                # print('player_data agent:', player_data['Agent'])
                player_name = player_data['Agent']['player_name']
                self.player = Player(player_name, world_map, dictionary=player_data['Agent'])
                self.players.append(self.player)
        print(f'Players:\n{self.players}')
        self.current_player_index = 0
        self.player = self.players[self.current_player_index]
        # self.viewport = reactive('')
        # self.viewport = Static(self.viewport)
        self.viewport = Static('')
        self.status_bar = Static('')
        # if view_size is None:
        #     console = Console()
        #     print(f'Console Size:', console.size)
        #     world_map.set_view_size(self.player.pos, (console.size[0]//2)-1, console.size[1]) # TODO This will center on the last player to load
        # world_map.view_port(self.player.pos)
        self.update_status()#False)
        # self.current_key = None
        # self.pressed_keys = set()
        self.timer = None
        print(f'World Map:\n{world_map}')

    def compose(self):
        with TabbedContent():
            with TabPane('Map', id='map_tab'):
                yield MapContainer(self.viewport, id='map_container')
                yield StatusBar(self.status_bar)#, id='status_bar')
            with TabPane('Log', id='log_tab'):
                yield RichLog(wrap=False, id='log_widget')#highlight=True, markup=True, wrap=True, id='log_widget')
                yield Input(placeholder='Enter command...', type='text', id='prompt')

    # def on_ready(self):
    #     self.text_log = self.query_one('#log_widget')

        # builtins.print = self.print_override
        # print('Test message to log.')
        # print(CORDS)

    # def on_tabbed_content_tab_activated(self, event):
    def on_tabs_tab_activated(self, event):
        print('tab_event:', event)
        # Focus the input widget corresponding to the active tab
        if event.tabpane.id == 'log_tab':
        # if event.tab.id == '--content-tab-log_tab':
            # self.query_one("#prompt", Input).focus()
            self.query_one("#prompt").focus()

    def update_viewport(self):#async
        # await asyncio.sleep(0)  # Yield control to ensure async behavior
        # self.stdout_redirector.set_widget_update(True) # Start widget update
        visible_map = world_map.view_port(self.player.pos)
        buffer = StringIO()
        # visible_map = buffer.write('\n'.join([' '.join([str(tile) for tile in row]) for row in visible_map]))
        visible_map = buffer.write('\n'.join([' '.join(row) for row in visible_map]))
        # visible_map = '\n'.join([' '.join([str(tile) for tile in row]) for row in visible_map])
        # visible_map = '\n'.join([' '.join([Pretty(str(tile)) for tile in row]) for row in visible_map])
        self.viewport.update(buffer.getvalue())
        # self.viewport.update(visible_map)#await
        # self.stdout_redirector.set_widget_update(False) # End widget update
    
    def update_status(self):#, check=True):#async
        # await asyncio.sleep(0)  # Yield control to ensure async behavior
        # if check: # TODO Find a better solution for the initial update
        #     print('Status update allowed 01.')
        #     self.stdout_redirector.set_widget_update(True) # Start widget update
        status = f'[green]{self.player.player_name} pos: [/green][cyan]{self.player.pos}[/cyan][green] moves: [/green][cyan]{self.player.remain_move:.2f}[/cyan][green] / [/green][cyan]{self.player.movement}[/cyan][green] faces: [/green]{self.player.target_tile}[green] {self.player.target_terrain} on: [/green]{self.player.current_tile}[green] {self.player.current_terrain}[/green]'
        # status = f'[green]{self.player.player_name} pos: [/green][cyan]{self.player.pos}[/cyan][green] faces [/green]{self.player.target_tile}[green] on: [/green]{self.player.current_tile}[green] | Moves: [/green][cyan]{self.player.remain_move:.2f}[/cyan][green] / [/green][cyan]{self.player.movement}[/cyan][green] | {self.player.target_terrain} | on: {self.player.current_terrain}[/green]'
        self.status_bar.update(status)#await
        self.refresh()
        # time.sleep(0.5)
        # self.status_bar.update(self.player)
        # if check:
        #     self.stdout_redirector.set_widget_update(False) # End widget update

    def on_mount(self):
        # self.timer = self.set_interval(0.5, self.check_movement)
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

    def check_movement(self):
        '''Check if current player's movement is 0, then switch turns.'''
        if all(unit.remain_move == 0 for unit in self.players):
            print('Next turn check')
            self.next_turn()
            return
        elif self.player.remain_move == 0:
            print('Next unit check')
            self.next_unit()
            return
        else:
            return True


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

    # async def on_key(self, event):
    #     # Prevent input queuing by only processing the latest key
    #     if self.current_key is None:
    #         self.current_key = event.key
    #         asyncio.create_task(self.move_character())

    def on_key(self, event):
        focused_widget = self.focused
        # print('focused_widget:', focused_widget)
        # self.text_log.write(print('focused_widget:', focused_widget))
        if isinstance(focused_widget, Input):
            # print('focused_widget:', focused_widget)
            # self.text_log.write(print('focused_widget:', focused_widget))
            return
        self.check_movement()
        if event.key in self.player.moves:
            # if event.key not in self.pressed_keys:
            #     self.pressed_keys.add(event.key)
            # Prevent input queuing by only processing the latest key
            # if self.current_key is None:
            dx, dy = self.player.moves[event.key]
            self.player.move(dy, dx)
            # asyncio.create_task(self.player.move(dy, dx))
            self.player.change_dir(event.key)
            if self.check_movement():
                self.update_viewport()
            else:
                self.update_viewport()
                # self.pressed_keys.remove(event.key)
        # elif event.key in ['up', 'lef', 'down', 'right']:
        elif event.key in ['i', 'j', 'k', 'l']:
            # turn = {'up': 'w', 'left': 'a', 'down': 's', 'right': 'd'}
            turn = {'i': 'w', 'j': 'a', 'k': 's', 'l': 'd'}
            self.player.change_dir(turn[event.key])
            self.update_viewport()
        elif event.key == 'r':
            self.player.zero_moves()
            self.player.reset_moves()
        elif event.key == 'e':
            print(f'{self.player} is mounting a boat at {self.player.pos}.')
            self.player.mount()
            self.update_viewport()
        self.update_status()
        # self.text_log.write(event.key)

    # def on_key_release(self, event):
    #     # Stop movement immediately when the key is released
    #     print(f'{event.key} release for {self.current_key}')
    #     if event.key == self.current_key:
    #         self.current_key = None

    def next_unit(self):
        '''Switch to the next player with movement remaining'''
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.player = self.players[self.current_player_index]
        self.update_viewport()
        print(f'Now unit {self.player}\'s turn.')
        # while self.players[self.current_player_index].remain_move <= 0:
        #     self.current_player_index = (self.current_player_index + 1) % len(self.players)
        # print('index after:', self.current_player_index)

    def next_turn(self):
        for unit in self.players:
            unit.reset_moves()
        self.player = self.players[0]
        self.update_viewport()
        world_map.game.turn += 1
        print('Turn:', world_map.game.turn)

    # self.player = Player(player_name, world_map, str(player_num+1), args.start)
    def spawn_players(self, v=True): # TODO Is this still needed?
        for i, row in enumerate(world_map.world_map):
            for j, cell in enumerate(row):
                if cell.get('Agent'):
                    agent = cell.get('Agent')
                    if v: print('Agent:', agent)
                    if v: print('Agent Type:', type(agent))
                    if v: print('Players:', self.players)
                    if v: print('Players first type:', type(self.players[0]))
                    if agent in self.players:
                        for i, player in enumerate(self.players):
                            if v: print('player type:', type(player))
                            if v: print('player name:', player.player_name)
                            print('agent:', agent)
                            print('agent type:', type(agent))
                            if agent is player:
                                agent = self.players[i]
                                print('agent type make:', type(agent))
                            print('agent type2:', type(agent))
                    world_map.world_map[i][j]['Agent'] = agent
                    print('world_map point:')
                    print('test:', world_map.world_map[i][j])
                    print('world_map point end.')
        self.update_viewport()
        self.update_status()
        print('End spawning players.')

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

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', type=str, default='446, 229', help='The starting coords for the player.')#338, 178
    parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
    parser.add_argument('-l', '--load', type=str, help='The name of the file to load.')
    parser.add_argument('-r', '--seed', type=str, default=11, help='Set the seed for the randomness.')
    parser.add_argument('-m', '--map', type=str, default='map.csv', help='The name of the map csv data file.')
    parser.add_argument('-p', '--players', type=int, default=1, help='The number of players in the world.')
    parser.add_argument('-vs', '--view_size', type=str, help='The size of the view of the world. E.g. "21, 33"')
    parser.add_argument('-z', '--size', type=str, help='The map size as either a list of two numbers or one for square.')
    args = parser.parse_args()

    if args.seed:
        print(time_stamp() + f'Randomness seed {args.seed}.')
        random.seed(args.seed)

    if args.size is not None:
        print('args.size init:', args.size)
        if not isinstance(args.size, (list, tuple)):
            args.size = [int(x.strip()) for x in args.size.split(',')]
            print('args.size not:', args.size)
            global MAP_SIZE
            MAP_SIZE = args.size
            print('MAP_SIZE:', MAP_SIZE)

    if args.view_size is not None: # '21, 33'
        if not isinstance(args.view_size, (list, tuple)):
            if isinstance(args.view_size, str):
                args.view_size = tuple([int(x.strip()) for x in args.view_size.split(',')])
        if len(args.view_size) == 1:
            args.view_size = (args.view_size[0], args.view_size[0])
        print('Starting view_size arg:', args.view_size)
    
    if args.map is not None:
        if args.map == '':
            args.map = None
        elif args.map == 'None':
            args.map = None

    if args.start is not None:
        if not isinstance(args.start, (list, tuple)):
            if isinstance(args.start, str):
                args.start = tuple(int(x.strip()) for x in args.start.split(','))
                if len(args.start) == 1:
                    print('single start str:', args.start)
                    args.start = (args.start[0], args.start[0])
                    print('single start str2:', args.start)
                # args.start = tuple(x.strip() for x in args.start.split(','))
                # try:
                #     args.start = tuple(int(x) for x in args.start)
                # except ValueError:
                #     pass
                # if isinstance(args.start[0], str):
                #     args.start[0] = world_map.col(args.start[0]) # TODO Maybe make world_map.col() global?
                #     args.start = tuple(int(x) for x in args.start)
            else:
                print('single start int:', args.start)
                args.start = (args.start, args.start)

    return args

if __name__ == '__main__':
    args = parse_args()

    app = CivRPG(args.map, args.start, args.view_size, args.players)
    app.run()
    # else:
    #     if 'data/' not in args.load:
    #         filename = 'data/' + filename
    #     app = CivRPG(args.players, filename)
    #     app.run()
        # with open(args.load) as f:
        #     app = pickle.load(f)
        #     app.run()


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

# [
#     [{'terrain': Tile('Grassland')},{'terrain': Tile('Ocean')}],
#     [{'terrain': Tile('Grassland')},{'terrain': Tile('Forest'), 'Agent': Player('Player 1')}]
# ]

## TODO
# Add support for multiple players/units
# Add player inventory
# Add lootable containers like chests
# Add harvestables
# Add lootable mobs
# Add combat

# scp data/items.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp data/map.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/data
# scp move.py robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct