import random

from game.client.user_client import UserClient
from game.common.enums import *
from game.common.map.tile import Tile
from game.utils.vector import Vector
from game.common.map.game_board import GameBoard
from game.common.avatar import Avatar
import heapq


class State(Enum):
    MINING = auto()
    SELLING = auto()

class Node:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

class Client(UserClient):
    # Variables and info you want to save between turns go here
    def __init__(self):
        super().__init__()

    def team_name(self):
        """
        Allows the team to set a team name.
        :return: Your team name
        """
        return 'AlumniNotLegacy'
    
    def first_turn_init(self, world: GameBoard, mobbot: Avatar):
        """
        This is where you can put setup for things that should happen at the beginning of the first turn
        """
        self.company = mobbot.company
        self.my_station_type = ObjectType.TURING_STATION if self.company == Company.TURING else ObjectType.CHURCH_STATION
        self.current_state = State.MINING
        self.base_position = world.get_objects(self.my_station_type)[0][0]

    # This is where your AI will decide what to do
    def take_turn(self, turn, actions, world: GameBoard, mobbot: Avatar):
        """
        This is where your AI will decide what to do.
        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        if turn == 1:
            self.first_turn_init(world, mobbot)

        if turn == 2:
            return [ActionType.MOVE_RIGHT]
        
        if turn == 3:
            return [ActionType.MOVE_RIGHT]
        
        if turn == 4:
            return [ActionType.MOVE_UP]
        a_star_path = []
        if mobbot.position != self.base_position:
            print(f"mobbot.position: {mobbot.position}")
            print(f"self.base_position: {self.base_position}")
            a_star_path = self.a_star_search(world.game_map, mobbot.position, self.base_position)

        a_star_path = self.a_star_search(world.game_map, mobbot.position, Vector(12, 12))
        
        # if turn == 7:
        #     a_star_path = self.a_star_search(world.game_map, mobbot.position, self.base_position)
        print(f"a_star_path: {a_star_path}")
        return a_star_path
            
        current_tile = world.game_map[mobbot.position.y][mobbot.position.x] # set current tile to the tile that I'm standing on
        
        # If I start the turn on my station, I should...
        if current_tile.occupied_by.object_type == self.my_station_type:
            # buy Improved Mining tech if I can...
            if mobbot.science_points >= mobbot.get_tech_info('Improved Drivetrain').cost and not mobbot.is_researched('Improved Drivetrain'):
                return [ActionType.BUY_IMPROVED_DRIVETRAIN]
            # otherwise set my state to mining
            self.current_state = State.MINING
            
        # If I have at least 5 items in my inventory, set my state to selling
        if len([item for item in self.get_my_inventory(world) if item is not None]) >= 5:
            self.current_state = State.SELLING
            
        # Make action decision for this turn
        if self.current_state == State.SELLING:
            # actions = [ActionType.MOVE_LEFT if self.company == Company.TURING else ActionType.MOVE_RIGHT] # If I'm selling, move towards my base
            actions = self.a_star_search(world.game_map, mobbot.position, self.base_position)
        else:
            if current_tile.occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION:
                # If I'm mining and I'm standing on an ore, mine it
                actions = [ActionType.MINE]
            else:
                # If I'm mining and I'm not standing on an ore, move randomly
                actions = [random.choice([ActionType.MOVE_RIGHT, ActionType.MOVE_DOWN, ActionType.MOVE_LEFT, ActionType.MOVE_UP])]
                
        return actions

    def generate_moves(self, start_position, end_position, vertical_first):
        """
        This function will generate a path between the start and end position. It does not consider walls and will
        try to walk directly to the end position.
        :param start_position:      Position to start at
        :param end_position:        Position to get to
        :param vertical_first:      True if the path should be vertical first, False if the path should be horizontal first
        :return:                    Path represented as a list of ActionType
        """
        dx = end_position.x - start_position.x
        dy = end_position.y - start_position.y
        
        horizontal = [ActionType.MOVE_LEFT] * -dx if dx < 0 else [ActionType.MOVE_RIGHT] * dx
        vertical = [ActionType.MOVE_UP] * -dy if dy < 0 else [ActionType.MOVE_DOWN] * dy
        
        return vertical + horizontal if vertical_first else horizontal + vertical
    
    def get_my_inventory(self, world: GameBoard):
        return world.inventory_manager.get_inventory(self.company)


    def a_star_search(self, map, start, end):
        def is_valid_tile(next):
            invalid_objects = {ObjectType.WALL, ObjectType.LANDMINE, ObjectType.TRAP, ObjectType.EMP}
            next = (next[1], next[0])
            for invalid_object in invalid_objects:
                if map[next[1]][next[0]].get_occupied_by(invalid_object):
                    return False
            return True

        start = start.as_tuple()
        start = (start[1], start[0])
        end = end.as_tuple()
        end = (end[1], end[0])

        open_list = []
        heapq.heappush(open_list, (0, start))

        came_from = {start: None}
        cost_so_far = {start: 0}

        directions = {
            (1, 0): ActionType.MOVE_DOWN,
            (0, 1): ActionType.MOVE_RIGHT,
            (0, -1): ActionType.MOVE_LEFT,
            (-1, 0): ActionType.MOVE_UP,
        }

        while open_list:
            current = heapq.heappop(open_list)[1]

            if current == end:
                path = []
                while current is not None:
                    if current == start:
                        pass # Or some other value that indicates the start
                    else:
                        path.append(came_from[current][0])
                    current = came_from[current][1] if current != start else None
                    
                path.reverse()
                return path # Exclude the None at the end

            for direction, action in directions.items():
                next = (current[0] + direction[0], current[1] + direction[1])

                if not is_valid_tile(next):
                    continue

                new_cost = cost_so_far[current] + 1
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + abs(end[0] - next[0]) + abs(end[1] - next[1])
                    heapq.heappush(open_list, (priority, next))
                    came_from[next] = (action, current)


        return random.choice([ActionType.MOVE_RIGHT, ActionType.MOVE_DOWN, ActionType.MOVE_LEFT, ActionType.MOVE_UP])

