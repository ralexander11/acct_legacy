"""
Minimal foundation for a turn-based grid engine using pygame-ce.

Goals:
- Separate simulation from rendering
- pygame based ASCII renderer layer
- fallback CLI ASCII renderer layer
- Turn-based movement
- ECS-compatible direction
- Easy to expand later

Controls:
    WASD = move
    ESC  = quit

Requirements:
    pip install pygame-ce
"""

import argparse
from dataclasses import dataclass, asdict, is_dataclass
from collections import deque, defaultdict
from typing import Any, Callable
import random
import os, sys
import json
try:
    import pygame
    USE_PYGAME = True
except ImportError:
    print('pygame not installed, will run in CLI mode.')
    USE_PYGAME = False

from decimal import Decimal
from datetime import datetime

# =========================================================
# CVARS SYSTEM
# =========================================================

# Put this in a cvars.py file
@dataclass
class CVar:
    name: str
    value: Any
    default: Any
    description: str
    on_change_callback: Callable[[Any], None] = None

class CVarSystem:
    def __init__(self):
        self._vars: dict[str, CVar] = {}

    def register(self, name: str, default: Any, description: str, on_change: Callable = None) -> CVar:
        cvar = CVar(name=name, value=default, default=default, description=description, on_change_callback=on_change)
        self._vars[name] = cvar
        return cvar

    def get(self, name: str) -> Any:
        return self._vars[name].value

    def set_value(self, name: str, new_value: Any):
        if name not in self._vars:
            # raise KeyError(f'cvar {name} does not exist.')
            return  # Silently ignore unregistered parameters or log a warning
        cvar = self._vars[name]
        # Handle booleans safely (string 'False' or '0' from CLI should become boolean False)
        if isinstance(cvar.default, bool) and isinstance(new_value, str):
            cvar.value = new_value.lower() in ('true', '1', 'yes', 'y')
        else:
            cvar.value = type(cvar.default)(new_value)

        if cvar.on_change_callback:
            cvar.on_change_callback(cvar.value)

    # --- NEW: SEAMLESS INTEGRATION METHODS ---

    def load_from_dict(self, data: dict):
        '''Pours a raw dictionary key-value pair straight into matching cvars.'''
        for key, val in data.items():
            self.set_value(key, val)

    def load_json_config(self, filepath: str):
        '''Reads a JSON file and applies it to the registry.'''
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.load_from_dict(data)
                print(f'[cvar] Successfully loaded config from {filepath}')
        except FileNotFoundError:
            print(f'[cvar] Config file {filepath} not found. Using defaults.')
        except json.JSONDecodeError:
            print(f'[cvar] Warning: {filepath} contains malformed JSON. Skipping.')

    def load_yaml_config(self, filepath: str):
        '''Reads a YAML file (Requires 'pip install pyyaml').'''
        try:
            import yaml  # Lazy import so pyyaml isn't a hard requirement if unused
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    self.load_from_dict(data)
                    print(f'[cvar] Successfully loaded config from {filepath}')
        except FileNotFoundError:
            print(f'[cvar] Config file {filepath} not found. Using defaults.')
            
    def parse_cli_arguments(self):
        '''Dynamically builds CLI flags based on currently registered cvars.'''
        # argparse.SUPPRESS prevents omitted flags from populating the results with None
        parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
        for name, cvar in self._vars.items():
            # TODO Support single dash short names
            cli_flag = f'--{name}'
            # Use the type of the default value to enforce clean, automatic type casting
            # TODO Have this setup real bool args
            if isinstance(cvar.default, bool):
                parser.add_argument(cli_flag, type=str, help=f'{cvar.description} (True/False)')
            else:
                parser.add_argument(cli_flag, type=type(cvar.default), help=cvar.description)

        # parse_known_args allows your game to ignore irrelevant arguments without crashing
        args, unknown = parser.parse_known_args()
        
        # Convert parsed Namespace back into a normal dict and load it
        self.load_from_dict(vars(args))

# =========================================================
# CVARS
# =========================================================
# Default config values

cvars = CVarSystem()

cvars.register('MAP_MODE', 'random', 'Map gen type to select. [random, test]')
cvars.register('CLAMP_MAP', True, 'True for having the map stop at the edge, False for map to extend into the void. (for future infinite maps)')
cvars.register('SPRITES', True, 'True to use basic sprites in the tiles, False for ascii characters.')
cvars.register('HOLD_MOVE', True, 'True for continuous scrolling, False for single-press stepping.')
cvars.register('LOCAL_COOP', True, 'True for multiple users locally, False for single player.')
cvars.register('JOYSTICK', True, 'True to turn on pygame joystick support, False for keyboard only.')

cvars.register('SCREEN_WIDTH', 1280, 'Window width in pixels.')
cvars.register('SCREEN_HEIGHT', 720, 'Window height in pixels.')

cvars.register('TILE_SIZE', 32, 'Tile height and width in pixels.')

cvars.register('MAP_WIDTH', 768, 'Camera height in pixels.')
cvars.register('MAP_HEIGHT', 768, 'Camera height in pixels.')

cvars.register('FPS', 60, 'Game loop frames per second cap.')

cvars.register('seed', '11', 'Seed for randomness.')
cvars.register('save_path', 'data/save_game.json', 'Path file for save location.')
# cvars.register('save_path', 'data/save_game_make.json', 'Path file for save location.')

cvars.register('input_cooldown_ms', 180, 'Time player must wait between grid steps.')
# cvars.register('developer_cheats', False, 'Enables god-mode commands')


# =========================================================
# CONFIG
# =========================================================

# MAP_MODE = cvars.get('MAP_MODE')#'random'
# CLAMP_MAP = True
# SPRITES = True
# HOLD_MOVE = True
# LOCAL_COOP = False#True#
# JOYSTICK = True#False#

# SCREEN_WIDTH = 1280
# SCREEN_HEIGHT = 720

# 1280 / 32 = 40
# 720 / 32 = 22

# TILE_SIZE = 32

# MAP_WIDTH = 768
# MAP_HEIGHT = 768

# FPS = 60

random.seed(cvars.get('seed'))#'11'
save_path = cvars.get('save_path')#'data/save_game.json'
save_json = {}


# =========================================================
# SAVE SYSTEM
# =========================================================
# Put in the utils dir

def make_json_ready(obj):#make_json_ready
    '''Recursively converts Decimals, datetimes, and custom objects with a __dict__ into JSON primitives.'''
    # print('Running make_json_ready')
    if isinstance(obj, WorldMap):
        print('Skipping WorldMap object for saving.')
        return

    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, dict):
        # JSON keys must be strings. 
        # 1. Handle coordinate tuples like (0,1) -> '0,1'
        # 2. Handle class references like Position -> 'Position'
        # 3. Fallback to standard stringification
        return {
            (f'{k[0]},{k[1]}' if isinstance(k, tuple) and len(k) == 2 
             else k.__name__ if isinstance(k, type) 
             else str(k)): make_json_ready(v) 
            for k, v in obj.items()
        }

    if isinstance(obj, (list, tuple, set)):
        return [make_json_ready(item) for item in obj]

    if hasattr(obj, '__dict__'):
        # This catches Entity, SimState, or any other class instance automatically
        return make_json_ready(obj.__dict__)

    if type(obj).__module__ != 'builtins':
        # return obj.__class__.__name__
        return make_json_ready(obj.__name__) if isinstance(obj, type) else make_json_ready(obj.__class__.__name__)

    return obj

# =========================================================
# COMPONENTS
# =========================================================

@dataclass(slots=True)
class Position:
    x: int
    y: int

@dataclass(slots=True)
class Renderable:
    char: str
    color: tuple[int, int, int]

@dataclass(slots=True)
class Owner:
    entity_id: int

@dataclass(slots=True)
class ActionState:
    has_moved: bool = False
    # Add movement to track movement cost remaining

@dataclass(slots=True)
class Controller:
    user: bool

COMPONENT_REGISTRY = {
    name: obj for name, obj in globals().items()
    if isinstance(obj, type) and is_dataclass(obj)
}
print('COMPONENT_REGISTRY:', COMPONENT_REGISTRY)

# =========================================================
# TILE / MAP
# =========================================================
# Add option to have world wrap.
# One option for left right wrap teleport.
# Another additional option for top bottom, but mirror just the horizontal.

# tmp data until json file is made
TERRAIN_DATA = {
    'grassland':{'char': '.', 'color': (60, 180, 75), 'frames': 1, 'walkable': True},
    'ocean':    {'char': '~', 'color': (50, 100, 220), 'frames': 4, 'walkable': False},
    'mountain': {'char': '^', 'color': (160, 160, 160), 'frames': 1, 'walkable': False}
}

class Tile:
    def __init__(self, terrain='grassland', walkable=True):
        self.terrain = terrain
        self.walkable = walkable

        config = TERRAIN_DATA.get(terrain, {'char': '?', 'color': (255,0,255), 'walkable': False})
        
        self.char = config['char']
        self.color = config['color']
        self.walkable = config['walkable']

class WorldMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []

        self.get_map()

    def get_map(self):
        # if MAP_MODE == 'random':
        if cvars.get('MAP_MODE') == 'random':
            terrain_items = list(TERRAIN_DATA.keys())
            TERRAIN_WEIGHTS = [70, 20, 10]
            for y in range(self.get_height()):
                row = []
                for x in range(self.get_width()):
                    chosen_terrain = random.choices(terrain_items, weights=TERRAIN_WEIGHTS)[0]
                    row.append(Tile(chosen_terrain))
                self.tiles.append(row)

        # elif MAP_MODE == 'test':
        elif cvars.get('MAP_MODE') == 'test':
            for y in range(self.get_height()):
                row = []
                for x in range(self.get_width()):
                    # Simple test terrain generation
                    if x % 11 == 0:
                        row.append(Tile('ocean'))
                    elif y % 9 == 0:
                        row.append(Tile('mountain'))
                    else:
                        row.append(Tile('grassland'))
                self.tiles.append(row)
        

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def in_bounds(self, x, y):
        return (
            0 <= x < self.width and
            0 <= y < self.height
        )

    # Ensure this is always used to access tiles to allow easier transition to chunk streaming system later
    def get_tile(self, x, y):
        if not self.in_bounds(x, y):
            return None
        return self.tiles[y][x]

# =========================================================
# ENTITY
# =========================================================
# Shouldn't entities just be an id?

class Entity:
    _next_id = 1

    def __init__(self, data_dict=None):
        self.id = Entity._next_id
        Entity._next_id += 1
        if data_dict:
            # Bulk apply all primitive fields (id, name, etc.)
            self.__dict__.update(data_dict)
            # Re-cast the specific fields that need to be Decimals
            # self.balance = Decimal(self.balance) # Not used yet
        else:
            self.components = {}

    # This cannot have more than one component of the same type. Not sure if I will need that yet though. If I do, assign a list to the component
    def add_component(self, component):
        self.components[type(component)] = component

    def get(self, component_type):
        return self.components.get(component_type)

    # entity_data: {'id': 1, 'components': {<class '__main__.Position'>: Position(x=5, y=5), <class '__main__.Renderable'>: Renderable(char='@', color=(255, 255, 255))}}
    def json_dump(self):
        entity_data = self.__dict__.copy()
        json_entity_data = {
            'id': entity_data['id'],
            'components': {
                cls_key.__name__: asdict(comp_val) 
                for cls_key, comp_val in entity_data['components'].items()
            }
        }
        # print('json_entity_data:', json_entity_data)
        return json_entity_data

# =========================================================
# Entity Factory
# =========================================================

class EntityFactory:
    @staticmethod
    def spawn_player(state, x, y):
        if os.path.exists(save_path):
            print(f'Loading saved player data from {save_path}.')
            with open(save_path, 'r') as f:
                save_json = json.load(f)
            loaded_components = {}
            for class_name, item_data in save_json['components'].items():
                dataclass_type = COMPONENT_REGISTRY.get(class_name)
                if dataclass_type:
                    instance = dataclass_type(**item_data)
                    loaded_components[dataclass_type] = instance
                else:
                    print(f'Warning: Component class {class_name} is not registered.')
            # print('loaded_components:', loaded_components)
            save_json['components'] = loaded_components
            # print('save_json:', save_json)
            player = Entity(data_dict=save_json)
            print(f'Loaded Player: {player}\n', player.__dict__)
        else:
            player = Entity()
            player.add_component(Position(x, y))
            state.add_entity_loc(player.id, x, y)
            player.add_component(Owner(player.id)) # TODO Temp hardcoded for now
            player.add_component(Controller(True))
            player.add_component(ActionState())
            player.add_component(Renderable('@', (255, 255, 255)))
            # print('Spawn Player:', player)
            # print(player.__dict__)
        
        # Put it in the state database
        state.entities[player.id] = player
        state.player = player # Keep the reference
        return player

# =========================================================
# COMMANDS
# =========================================================
# Could be a dict also

@dataclass(slots=True)
class MoveCommand:
    entity_id: int
    dx: int
    dy: int

@dataclass(slots=True)
class EndTurnCommand:
    entity_id: int

# =========================================================
# ACTIONS
# =========================================================
# Could be a dict also

@dataclass(slots=True)
class MoveAction:
    entity_id: int
    to_x: int
    to_y: int

@dataclass(slots=True)
class EndTurnAction:
    player_id: int

# =========================================================
# ACTION QUEUE
# =========================================================

class ActionQueue:
    def __init__(self):
        self.queue = deque()

    def push(self, action):
        self.queue.append(action)

    def pop(self):
        if self.queue:
            return self.queue.popleft()

    def empty(self):
        return len(self.queue) == 0

# ==========================================
# EVENTS
# ==========================================
# Keep as pure data
# Is frozen needed? Should I add it to other dataclasses?

@dataclass(slots=True)#, frozen=True)
class EntityMovedEvent:
    entity_id: int
    from_x: int
    from_y: int
    to_x: int
    to_y: int

@dataclass(slots=True)#, frozen=True)
class DamageEvent:
    target_id: int
    attacker_id: int
    damage_amount: int
    # damage_type: str

@dataclass(slots=True)
class TurnChangedEvent:
    ended_player_id: int
    new_player_id: int
    global_turn: int

# =========================================================
# EVENTS
# =========================================================
# The ECS Way: The CombatSystem simply pushes a DamageEvent to the Event Bus. It doesn't care who is listening. Later in the frame, the AudioSystem sees the event and plays a sound. The Renderer sees the event and draws a red flash.

class EventQueue:
    def __init__(self):
        # self.events = defaultdict(list)
        self.events = deque() # Should this be self._queue?

    # def push(self, event_type, data):
    #     self.events[event_type].append(data)

    def push(self, data):
        self.events.append(data)

    # def clear(self):
    #     self.events.clear()

    def pop_next(self):
        return self.events.popleft() if self.events else None

    def is_empty(self):
        return len(self.events) == 0

# EVENT BUS

class EventBus:
    def __init__(self):
        # Maps event types to a list of callback functions
        self._listeners = defaultdict(list) # or self._subscribers

    def subscribe(self, event_type, callback):
        if event_type not in self._listeners:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)

    def publish(self, event):
        event_type = type(event)
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                callback(event)

    # TODO Need to use this still
    # Learn better what this decorator does
    def on(self, event_type):
        def decorator(func):
            self.subscribe(event_type, func)
            return func
        return decorator

    # Maybe test with a PlayerHitMountain event that prints a msg

# =========================================================
# TURN MANAGER
# =========================================================
# Need to support more than one player or NPC. Or a player controlling multiple avatars/units

# The (old) Fix: You will eventually need a concept of "Energy" or an "Initiative Tracker" system. Instead of checking if the queue is empty to advance the turn, the Turn Manager should poll entities to see whose turn it is. If it's an NPC's turn, an AI system pushes actions. If it's the player's turn, the simulation waits for a MoveCommand.

# To support multiple players and multiple units per player, you need to add two concepts to your data: Ownership and Action Points (or HasMoved).
# New Components:
# Owner(player_id: int): Attach this to every unit so the game knows who controls it.

# ActionState(has_moved: bool = False): Attach this to track if a unit has acted this turn.

# TurnManager Upgrade:
# Instead of just a turn number, your TurnManager needs a current_player_index and a list of active_players.

# The Flow:
# When Player 1 presses an "End Turn" button (e.g., the Spacebar), push an EndTurnCommand to the queue. The TurnSystem processes this by resetting the has_moved flag for all of Player 1's units, and then increments the current_player_index to Player 2.

class TurnManager:
    def __init__(self, player_ids):
        self.global_turn_number = 1
        self.active_players = player_ids#.keys() # Can use state.entities?
        self.current_player_index = 0

    @property
    def current_player_id(self):
        return self.active_players[self.current_player_index]

    def advance_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.active_players) # Make sure self.active_players is never zero
        print(f'It is now Player {self.current_player_id}\'s turn.')

    def advance_turn(self):
        self.global_turn_number += 1
        print(f'Turn {self.global_turn_number}')

# TODO Not sure I like this TurnSystem strategy. Need to clean this up.
class TurnSystem:
    # TODO Should I init with state and the action_queue and event_queue?
    def process_command(self, command, state, action_queue):
        if not isinstance(command, EndTurnCommand):
            return

        # Validation: A player can only end the turn if it's actually their turn
        if command.entity_id != state.turn_manager.current_player_id:
            print(f'Rejected: Player {command.entity_id} tried to end Player {state.turn_manager.current_player_id}\'s turn!')
            return

        action_queue.push(EndTurnAction(command.entity_id))

    def update(self, state, action, event_queue):
        if not isinstance(action, EndTurnAction):
            return

        old_player = state.turn_manager.current_player_id

        # 1. Find all entities belonging to the player who just ended their turn, and reset them
        for _, entity in state.entities.items():
            owner = entity.get(Owner)
            action_state = entity.get(ActionState)

            # print(f'Owner: {owner}, action_state: {action_state}, {owner.entity_id}, old_player: {old_player}')#, entity: {entity}')
            if owner and action_state and owner.entity_id == old_player:
                print(f'Reset Player {entity.id}\'s moves.')
                action_state.has_moved = False  # Refreshed for their next turn!

        # 2. Advance the TurnManager state
        state.turn_manager.advance_player()
        new_player = state.turn_manager.current_player_id

        # 3. Broadcast the historical fact that the turn changed
        event_queue.push(TurnChangedEvent(
            ended_player_id=old_player,
            new_player_id=new_player,
            global_turn=state.turn_manager.global_turn_number
        ))

# =========================================================
# SIM STATE
# =========================================================
# This should be pure data only

# Never put pygame objects, open files, or network sockets inside a Component or the SimState

class SimState:
    def __init__(self):
        self.world = WorldMap(cvars.get('MAP_WIDTH'), cvars.get('MAP_HEIGHT'))
        self.entities = {}
        # Spatial Hash: {(x, y): [entity_id_1, ...]}
        self.entity_locations = defaultdict(list)
        self.player = EntityFactory.spawn_player(self, 5, 5) # TODO Better choose start location
        # self.turn_manager = TurnManager(self.entities)
        self.turn_manager = TurnManager(player_ids=[1])#, 2]) # TODO Should this be here or in SimState?

    # Should this be here? If not, where? Move to own SpatialIndex class
    def add_entity_loc(self, entity_id, x, y):
        if entity_id not in self.entity_locations[(x, y)]:
            self.entity_locations[(x, y)].append(entity_id)

    # Should this be here? If not, where? Move to own SpatialIndex class
    def remove_entity_loc(self, entity_id, x, y):
        if entity_id in self.entity_locations[(x, y)]:
            self.entity_locations[(x, y)].remove(entity_id)
            # Remove the key entirely if the list is empty
            if not self.entity_locations[(x, y)]:
                del self.entity_locations[(x, y)]

    # Should this be here? If not, where? Move to own SpatialIndex class
    def get_entities_at(self, x, y):
        return self.entity_locations.get((x, y), [])

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

# =========================================================
# Simulation Logic
# =========================================================
# This would be in a sim.py type file

class Simulation:
    def __init__(self):
        self.state = SimState()
        # self.state.turn_manager = TurnManager(player_ids=[1])#, 2]) # TODO Should this be here or in SimState?
        self.action_queue = ActionQueue()
        self.event_bus = EventBus()
        self.event_queue = EventQueue()
        self.systems = [
            MovementSystem(),
            # EconomySystem(),
            # CombatSystem(),
            # SocialSystem(),
            AISystem(self.state, self.event_bus, self.action_queue),
            TurnSystem(),
        ]

    def process_command(self, command):
        ''' Process_command is the Input Gate (Intent): This handles untrusted requests coming from the outside world (like a human smashing the W key). Systems look at the command, check if it's legal, and if it is, they translate it into a guaranteed Action and drop it into the action_queue.'''
        for system in self.systems:
            # if isinstance(command, MoveCommand): # Not needed since check in func
            system.process_command(command, self.state, self.action_queue)
            # Save here?
            save_json = self.state.player.json_dump()
            # save_json = make_json_ready(self.state.player)
            with open(save_path, 'w') as f:
                json.dump(save_json, f, indent=4)


    def update(self):
        ''' Update is the Engine Heartbeat (Execution): This executes trusted consequences. It pops a confirmed action from the queue, mutates the SimState, and generates events.'''
        # If there are actions in the queue, process ONE action per update
        if not self.action_queue.empty():
            action = self.action_queue.pop()
            for system in self.systems:
                system.update(self.state, action, self.event_queue)

        while not self.event_queue.is_empty():
            next_event = self.event_queue.pop_next()
            self.event_bus.publish(next_event)

        # If the action queue is now empty, advance the game turn
        # Removed for the TurnSystem now
        # if self.action_queue.empty():
        #     self.state.turn_manager.advance_turn()

# This would be in the move.py file
# This should contain no state of it's own
class MovementSystem:
    def process_command(self, command, state, action_queue):
        '''Turns commands into actions if they are legal.'''
        if not isinstance(command, MoveCommand):
            return

        entity = state.get_entity(command.entity_id)
        if not entity: return

        # if LOCAL_COOP:
        if cvars.get('LOCAL_COOP'):
            owner = entity.get(Owner)
            if owner.entity_id != state.turn_manager.current_player_id:
                print(f'Rejected: It is not Player {owner.entity_id}\'s turn!')
                return

            action_state = entity.get(ActionState)
            if action_state.has_moved:
                print(f'Rejected: Unit {entity.id} has already moved this turn!')
                return

        pos = entity.get(Position)
        new_x = pos.x + command.dx
        new_y = pos.y + command.dy

        # Check collision bounds
        if not state.world.in_bounds(new_x, new_y): return
        if not state.world.get_tile(new_x, new_y).walkable: return

        # Valid move! Push action to action_queue
        action_queue.push(MoveAction(entity.id, new_x, new_y))

    def update(self, state, action, event_queue):
        '''Executes the move action on the SimState data.'''
        if not isinstance(action, MoveAction):
            return

        entity = state.get_entity(action.entity_id)
        pos = entity.get(Position)
        action_state = entity.get(ActionState)

        old_x, old_y = pos.x, pos.y
        state.remove_entity_loc(entity.id, pos.x, pos.y)
        pos.x = action.to_x
        pos.y = action.to_y
        state.add_entity_loc(entity.id, pos.x, pos.y)
        action_state.has_moved = True

        # Broadcast event
        event_queue.push(EntityMovedEvent(entity.id, old_x, old_y, pos.x, pos.y))

# TODO This is not implemented yet
class AISystem:#EnemyAiSystem:
    def __init__(self, state, event_bus, action_queue):
        self.action_queue = action_queue
        self.state = state
        
        # Subscribe to the event bus to know WHEN to think
        event_bus.subscribe(TurnChangedEvent, self.on_turn_changed)

    def on_turn_changed(self, event):
        # Data-driven check using your Entity or Player data
        entity = self.state.get_entity(event.new_player_id)
        control = entity.get(Controller)
        if control.user:
            print(f'Player {entity.id} is not AI controlled.')
            return
        
        # Bypass the command and drop the action directly into your existing queue!
        self.action_queue.push(EndTurnAction(player_id=event.new_player_id))
        # print('action_queue after:', self.action_queue.queue)

    def process_command(self, command, state, action_queue):
        # AI doesn't accept external commands, so this can stay empty
        pass

    def update(self, state, action, event_queue):
        # Run standard AI thinking updates per frame if needed
        pass

# =========================================================
# PYGAME ASCII RENDERER
# =========================================================
# In file render.py?

class PgAsciiRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(
            'consolas',
            24,
            bold=True
        )
        self._text_cache = {}

        # if SPRITES:
        # if cvars.get('SPRITES'):
        # self.tile_sprites = {}
        self.tile_sprites = defaultdict(list)
        self.load_sprites()

        # Pre-calculate screen capacities in tiles
        # self.tiles_wide = SCREEN_WIDTH // TILE_SIZE
        # self.tiles_high = SCREEN_HEIGHT // TILE_SIZE
        self.tiles_wide = cvars.get('SCREEN_WIDTH') // cvars.get('TILE_SIZE')
        self.tiles_high = cvars.get('SCREEN_HEIGHT') // cvars.get('TILE_SIZE')

    def load_sprites(self):
        animated_config = {
            'ocean': 4,     # Expects water_01.png, water_1.png, etc.
            'grassland': 1, # Expects grassland.png
            'mountain': 1,
        }
        terrain_items = list(TERRAIN_DATA.keys())
        TILE_SIZE = cvars.get('TILE_SIZE')
        for terrain in terrain_items:
            frames = TERRAIN_DATA[terrain]['frames']
            for i in range(frames):
                if i == 0:
                    filename = f'assets/{terrain}.png'
                else:
                    filename = f'assets/{terrain}_{i:02d}.png'
                if os.path.exists(filename):
                    img = pygame.image.load(filename).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.tile_sprites[terrain].append(scaled)
                else:
                    print(f'Warning: Sprite {filename} not found. Falling back to ASCII text.')

    def _get_surface(self, char, color):
        if char not in self._text_cache:
            self._text_cache[char] = self.font.render(char, True, color)
        return self._text_cache[char]

    def render(self, sim_state):#, camera_x, camera_y):
        self.screen.fill((0, 0, 0))
        player_pos = sim_state.player.get(Position)
        camera_x = player_pos.x - (self.tiles_wide // 2)
        camera_y = player_pos.y - (self.tiles_high // 2)
        # if CLAMP_MAP:
        if cvars.get('CLAMP_MAP'):
            world = sim_state.world
            camera_x = max(0, min(camera_x, world.get_width() - self.tiles_wide))
            camera_y = max(0, min(camera_y, world.get_height() - self.tiles_high))
        self.draw_world(sim_state.world, camera_x, camera_y)
        self.draw_entities(sim_state.entities, camera_x, camera_y)

    # With camera culling
    def draw_entities(self, entities, camera_x, camera_y):
        TILE_SIZE = cvars.get('TILE_SIZE')
        for entity in entities.values():
            pos = entity.get(Position)
            render = entity.get(Renderable)

            if pos is None or render is None:
                continue

            if not (camera_x <= pos.x < camera_x + self.tiles_wide + 1 and
                    camera_y <= pos.y < camera_y + self.tiles_high + 1):
                continue

            px = (pos.x - camera_x) * TILE_SIZE
            py = (pos.y - camera_y) * TILE_SIZE

            text_surface = self._get_surface(render.char, render.color)
            # Center character in tile
            text_rect = text_surface.get_rect()
            text_rect.center = (px + TILE_SIZE // 2, py + TILE_SIZE // 2)
            self.screen.blit(text_surface, text_rect)

    # With camera culling
    def draw_world(self, world, camera_x, camera_y):
        TILE_SIZE = cvars.get('TILE_SIZE')
        current_time_ms = pygame.time.get_ticks()
        # if CLAMP_MAP:
        if cvars.get('CLAMP_MAP'):
            start_x = max(0, camera_x)
            end_x = min(world.get_width(), camera_x + self.tiles_wide + 2)
            
            start_y = max(0, camera_y)
            end_y = min(world.get_height(), camera_y + self.tiles_high + 2)
        else:
            start_x = camera_x
            end_x = camera_x + self.tiles_wide + 1
            
            start_y = camera_y
            end_y = camera_y + self.tiles_high + 1

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = world.get_tile(x, y)
                if tile is None:
                    continue
                px = (x - camera_x) * TILE_SIZE
                py = (y - camera_y) * TILE_SIZE
                # if SPRITES and tile.terrain in self.tile_sprites:
                if cvars.get('SPRITES') and tile.terrain in self.tile_sprites:
                    frames = self.tile_sprites[tile.terrain]
                    # Determine which frame to show
                    # Change 250 to control animation speed (250ms per frame)
                    frame_duration = 250 
                    current_frame = (current_time_ms // frame_duration) % len(frames)
                    self.screen.blit(frames[current_frame], (px, py))
                else:
                    text_surface = self._get_surface(tile.char, tile.color)
                    text_rect = text_surface.get_rect()
                    text_rect.center = (px + TILE_SIZE // 2, py + TILE_SIZE // 2)
                    self.screen.blit(text_surface, text_rect)

# CLI ASCII RENDERER

class CliRenderer:
    def __init__(self):
        size = os.get_terminal_size()
        print('terminal size:', size)
        self.view_width = size.columns
        self.view_height = size.lines - 3

    def render(self, sim_state):
        player_pos = sim_state.player.get(Position)
        camera_x = player_pos.x - (self.view_width // 2)
        camera_y = player_pos.y - (self.view_height // 2)

        start_x = camera_x
        end_x = camera_x + self.view_width
        start_y = camera_y
        end_y = camera_y + self.view_height
        for y in range(start_y, end_y):
            row = ''
            for x in range(start_x, end_x):
                entity_ids = sim_state.get_entities_at(x, y)
                if entity_ids:
                    entity = sim_state.get_entity(entity_ids[0])
                    render_entity = entity.get(Renderable)
                    row += render_entity.char if render_entity else '?'
                else:
                    tile = sim_state.world.get_tile(x, y)
                    row += tile.char if tile else ' ' 
            print(row)
        print()
        print(f'Global Turn: {sim_state.turn_manager.global_turn_number}')

# =========================================================
# INPUT
# =========================================================
# Maybe have a parse_command() function

class PgInputHandler:
    def __init__(self):
        self.last_move_time = 0
        self.action_stack = []

        self.active_gamepads = {}
        self.THRESHOLD = 0.5

        # --- KEYBOARD BINDINGS CONFIG ---
        self.keyboard_map = {
            pygame.K_d:     'move_right', pygame.K_RIGHT: 'move_right',
            pygame.K_a:     'move_left',  pygame.K_LEFT:  'move_left',
            pygame.K_s:     'move_down',  pygame.K_DOWN:  'move_down',
            pygame.K_w:     'move_up',    pygame.K_UP:    'move_up',
            pygame.K_SPACE: 'end_turn',
        }

        # --- GAMEPAD BUTTON CONFIG ---
        self.gamepad_button_map = {
            7: 'end_turn',  # Start button
            0: 'confirm',   # 'A' or 'Cross' button
        }

    def handle_event(self, event, current_player_id):
        # --- GAMEPAD CONNECTION HANDLING ---
        if event.type == pygame.JOYDEVICEADDED:
            new_joy = pygame.joystick.Joystick(event.device_index)
            new_joy.init()
            self.active_gamepads[new_joy.get_instance_id()] = new_joy
            print(f'Gamepad Connected: {new_joy.get_name()} (ID: {new_joy.get_instance_id()})')
            return None

        elif event.type == pygame.JOYDEVICEREMOVED:
            if event.instance_id in self.active_gamepads:
                print(f'Gamepad Disconnected (ID: {event.instance_id})')
                del self.active_gamepads[event.instance_id]
            return None

        # B. Handle Keyboard Inputs using our Clean Action Map
        elif event.type == pygame.KEYDOWN:
            action = self.keyboard_map.get(event.key)
            if action:
                if action == 'end_turn':
                    return EndTurnCommand(entity_id=current_player_id)
                elif action not in self.action_stack and action.startswith('move_'):
                    self.action_stack.append(action)

        elif event.type == pygame.KEYUP:
            action = self.keyboard_map.get(event.key)
            if action and action in self.action_stack and action.startswith('move_'):
                self.action_stack.remove(action)

        # --- GAMEPAD DISCRETE ACTIONS ---
        elif event.type == pygame.JOYBUTTONDOWN:
            action = self.gamepad_button_map.get(event.button)
            if action == 'end_turn':
                return EndTurnCommand(entity_id=current_player_id)
        return None

    def get_command(self, event, player_id):
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_w:
            return MoveCommand(player_id, 0, -1)
        elif event.key == pygame.K_s:
            return MoveCommand(player_id, 0, 1)
        elif event.key == pygame.K_a:
            return MoveCommand(player_id, -1, 0)
        elif event.key == pygame.K_d:
            return MoveCommand(player_id, 1, 0)
        return None

    def gather_movement_input(self, player_id: int) -> MoveCommand or None:
        '''Polls current Keyboard + active Gamepads state and maps to a unique MoveCommand.'''
        current_time = pygame.time.get_ticks()
        # Enforce cooldown to prevent lightning-fast multi-movements
        if current_time - self.last_move_time < cvars.get('input_cooldown_ms'):
            return None

        dx, dy = 0, 0
        # 1. Read Keyboard Input via the prioritized Action Stack
        if self.action_stack:
            active_action = self.action_stack[-1]
            if active_action ==   'move_right': dx = 1
            elif active_action == 'move_left':  dx = -1
            elif active_action == 'move_down':  dy = 1
            elif active_action == 'move_up':    dy = -1

        # B. Read all active gamepads safely (From your snippet)
        if dx == 0 and dy == 0:
            for gamepad_id, joy in self.active_gamepads.items():
                try:
                    # Left analog stick conversion
                    axis_x = joy.get_axis(0)
                    axis_y = joy.get_axis(1)

                    if axis_x > self.THRESHOLD:    dx = 1
                    elif axis_x < -self.THRESHOLD: dx = -1
                        
                    if axis_y > self.THRESHOLD:    dy = 1
                    elif axis_y < -self.THRESHOLD: dy = -1

                    # D-pad (Hats) check
                    if joy.get_numhats() > 0:
                        hat_x, hat_y = joy.get_hat(0)
                        if hat_x != 0: dx = hat_x
                        if hat_y != 0: dy = -hat_y  # Invert pygame's vertical hat layout
                except pygame.error:
                    pass  # Handles rare mid-frame disconnect read-failures

        if dx != 0 or dy != 0:
            self.last_move_time = current_time
            return MoveCommand(player_id, dx, dy)
        return None

class CliInputHandler:
    def get_command(self, player_id):
        text = input('> ').lower()#.strip()
        text = text if text == ' ' else text.strip()
        if text == 'w':
            return MoveCommand(player_id, 0, -1)
        elif text == 's':
            return MoveCommand(player_id, 0, 1)
        elif text == 'a':
            return MoveCommand(player_id, -1, 0)
        elif text == 'd':
            return MoveCommand(player_id, 1, 0)
        elif text == ' ':
            return EndTurnCommand(player_id)
        elif text == 'exit' or text == 'quit':
            return text
        return None

# =========================================================
# MAIN APP
# =========================================================

class PgSimApp:
    def __init__(self):
        pygame.init()
        cvars.load_json_config('config.json')
        # cvars.load_yaml_config('config.yaml')
        cvars.parse_cli_arguments()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode((cvars.get('SCREEN_WIDTH'), cvars.get('SCREEN_HEIGHT')))
        pygame.display.set_caption('Turn-Based Econ Sim Prototype')
        self.clock = pygame.time.Clock()

        self.sim = Simulation()
        self.renderer = PgAsciiRenderer(self.screen)
        self.input_handler = PgInputHandler()
        self.running = True

    def run(self):
        while self.running:
            macro_cmd = self.handle_events()
            if macro_cmd:
                # self.action_queue.append(macro_cmd)
                self.sim.process_command(macro_cmd)

            # Hold continuous movement
            # if HOLD_MOVE:
            if cvars.get('HOLD_MOVE'):
                # if JOYSTICK:
                if cvars.get('JOYSTICK'):
                    move_cmd = self.input_handler.gather_movement_input(player_id=self.sim.state.player.id)
                # elif not JOYSTICK:
                elif not cvars.get('JOYSTICK'):
                    move_cmd = self.input_handler.get_movement_command(player_id=self.sim.state.player.id)
                if move_cmd:
                    self.sim.process_command(move_cmd)

            self.sim.update()

            self.renderer.render(self.sim.state)
            pygame.display.flip()
            self.clock.tick(cvars.get('FPS'))
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            else:
                player_id = self.sim.state.turn_manager.current_player_id
                # if HOLD_MOVE:
                if cvars.get('HOLD_MOVE'):
                    # print('event:', event)
                    command = self.input_handler.handle_event(event, player_id)
                # elif not HOLD_MOVE:
                elif not cvars.get('HOLD_MOVE'):
                    command = self.input_handler.get_command(event, player_id)
                if command:
                    # self.sim.process_command(command)
                    return command

class CliSimApp:
    def __init__(self):
        self.sim = Simulation()
        self.renderer = CliRenderer()
        self.input_handler = CliInputHandler()
        self.running = True

    def run(self):
        while self.running:
            self.renderer.render(self.sim.state)
            command = self.input_handler.get_command(self.sim.state.player.id)
            if command == 'exit' or command == 'quit':
                self.running = False
                continue
            if command:
                self.sim.process_command(command)
            self.sim.update()

def main():
    if USE_PYGAME and 'pygame' in sys.modules:
        app = PgSimApp()
        # print(pygame.version.vernum)
        app.run()
    else:
        # Run CLI interface and renderer
        app = CliSimApp()
        app.run()

# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == '__main__':
    main()


# The Full Turn Lifecycle (How your code executes it)
# Let's watch how your code naturally handles a full round step-by-step:

# Step A: The Human Player Moves
# In your run loop, a human presses a key. Your input handler creates a MoveCommand.

# The run loop calls self.sim.process_command(move_cmd).

# Your MovementSystem.process_command() verifies the move is legal, wraps it in a MoveAction, and appends it to self.action_queue.

# Step B: The Simulation Executes and Switches Turns
# The run loop calls self.sim.update().

# sim.update() pops the MoveAction from the queue and feeds it to system.update().

# The state changes. The player shifts tiles. The TurnSystem determines the human's turn is done, updates state.turn_manager, and appends a TurnChangedEvent(active_player_id=2) to the event_queue.

# At the bottom of sim.update(), the event_queue is drained, publishing the event to the event_bus.

# Step C: The AI Automatically Intercepts
# The EventBus fires the event. AISystem.on_turn_changed() catches it instantly.

# The AI sees it's player 2's turn, creates an EndTurnAction, and shoves it into self.action_queue.

# The frame ends.

# Step D: The Next Frame Handles the AI Automatically
# The game loops around to the next frame. No human buttons are pressed.

# The run loop calls self.sim.update().

# sim.update() checks if action_queue is empty. It's not! It contains the AI's EndTurnAction.

# It pops it, passes it to TurnSystem.update(), which flips the turn manager back to Player 1.


# TODO
# [Done] Implement InputMapper
# [Done] Ask AI about scalable cvar system and implement it
# [Done] Ask AI about best save system, can I use json
# [Done] Animated tiles, like ocean waves
# Smoother transition movement
# Put in long term folder structure
# Ask AI to review whole code
