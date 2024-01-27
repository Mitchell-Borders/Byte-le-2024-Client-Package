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
        self.not_in_middle = True

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

        if self.not_in_middle:
            if mobbot.position.x == 7 and mobbot.position.y == 7:
                self.not_in_middle = False
            else:
                return self.a_star_search(world.game_map, mobbot.position, Vector(7, 7))

        # set current tile to the tile that I'm standing on
        current_tile = world.game_map[mobbot.position.y][mobbot.position.x]

        # If I start the turn on my station, I should...
        if current_tile.occupied_by.object_type == self.my_station_type:
            # buy Improved Mining tech if I can...
            self.shop_for_tech(mobbot)
            # otherwise set my state to mining
            self.current_state = State.MINING

        # If I have at least 5 items in my inventory, set my state to selling
        if len([item for item in self.get_my_inventory(world) if item is not None]) >= 18:
            self.current_state = State.SELLING
            if mobbot.position == self.base_position:
                self.not_in_middle = True

        # Make action decision for this turn
        if self.current_state == State.SELLING:
            # actions = [ActionType.MOVE_LEFT if self.company == Company.TURING else ActionType.MOVE_RIGHT] # If I'm selling, move towards my base
            actions = self.a_star_search(
                world.game_map, mobbot.position, self.base_position)
        else:
            if current_tile.occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION:
                # If I'm mining and I'm standing on an ore, mine it
                actions = [ActionType.MINE]
            else:
                # If I'm mining and I'm not standing on an ore, move randomly
                actions = [random.choice(
                    [ActionType.MOVE_RIGHT, ActionType.MOVE_DOWN, ActionType.MOVE_LEFT, ActionType.MOVE_UP])]

        return actions
    
    def shop_for_tech(self, mobbot: Avatar):
        if mobbot.science_points >= mobbot.get_tech_info('Improved Drivetrain').cost and not mobbot.is_researched('Improved Drivetrain'):
            return [ActionType.BUY_IMPROVED_DRIVETRAIN]
        elif mobbot.science_points >= mobbot.get_tech_info('Improved Mining').cost and not mobbot.is_researched('Improved Mining'):
            return [ActionType.BUY_IMPROVED_MINING]
        elif mobbot.science_points >= mobbot.get_tech_info('Superior Drivetrain').cost and not mobbot.is_researched('Superior Drivetrain'):
            return [ActionType.BUY_SUPERIOR_DRIVETRAIN]
        elif mobbot.science_points >= mobbot.get_tech_info('Superior Mining').cost and not mobbot.is_researched('Superior Mining'):
            return [ActionType.BUY_SUPERIOR_MINING]
        elif mobbot.science_points >= mobbot.get_tech_info('Overdrive Drivetrain').cost and not mobbot.is_researched('Overdrive Drivetrain'):
            return [ActionType.BUY_OVERDRIVE_DRIVETRAIN]
        elif mobbot.science_points >= mobbot.get_tech_info('Overdrive Mining').cost and not mobbot.is_researched('Overdrive Mining'):
            return [ActionType.BUY_OVERDRIVE_MINING]
        else:
            return None
        

    def get_my_inventory(self, world: GameBoard):
        return world.inventory_manager.get_inventory(self.company)

    def a_star_search(self, map, start, end):
        def is_valid_tile(next):
            invalid_objects = {
                ObjectType.WALL, ObjectType.LANDMINE, ObjectType.TRAP, ObjectType.EMP}
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
                        pass  # Or some other value that indicates the start
                    else:
                        path.append(came_from[current][0])
                    current = came_from[current][1] if current != start else None

                path.reverse()
                return path  # Exclude the None at the end

            for direction, action in directions.items():
                next = (current[0] + direction[0], current[1] + direction[1])

                if not is_valid_tile(next):
                    continue

                new_cost = cost_so_far[current] + 1
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + \
                        abs(end[0] - next[0]) + abs(end[1] - next[1])
                    heapq.heappush(open_list, (priority, next))
                    came_from[next] = (action, current)

        return random.choice([ActionType.MOVE_RIGHT, ActionType.MOVE_DOWN, ActionType.MOVE_LEFT, ActionType.MOVE_UP])
