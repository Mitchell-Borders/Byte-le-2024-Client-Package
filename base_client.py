import random

from game.client.user_client import UserClient
from game.common.enums import *
from game.common.map.tile import Tile
from game.utils.vector import Vector
from game.common.map.game_board import GameBoard
from game.common.avatar import Avatar
import heapq


class State(Enum):
    START = auto()
    MINING = auto()
    SELLING = auto()
    UPGRADING = auto()


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
        self.prev_position = None

    def team_name(self):
        """
        Allows the team to set a team name.
        :return: Your team name
        """
        return 'Epic'

    def first_turn_init(self, world: GameBoard, mobbot: Avatar):
        """
        This is where you can put setup for things that should happen at the beginning of the first turn
        """
        self.company = mobbot.company
        self.my_station_type = ObjectType.TURING_STATION if self.company == Company.TURING else ObjectType.CHURCH_STATION
        self.current_state = State.MINING
        self.base_position = world.get_objects(self.my_station_type)[0][0]
        self.mine_back = [10, 16, 48]
        self.cur_mine_index = 0
        self.max = 14
        self.min = -1


    # This is where your AI will decide what to do
    def take_turn(self, turn, actions, world: GameBoard, mobbot: Avatar):
        """
        This is where your AI will decide what to do.
        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        actions = []
        current_tile = world.game_map[mobbot.position.y][mobbot.position.x] # set current tile to the tile that I'm standing on
        if turn == 1:
            self.first_turn_init(world, mobbot)
        if len([item for item in self.get_my_inventory(world) if item is not None]) > self.mine_back[self.cur_mine_index]:
            self.current_state = State.SELLING
        elif mobbot.position == self.base_position and State.SELLING == self.current_state:
            self.current_state = State.UPGRADING
            self.max = 12
            self.min = 1
        elif self.current_state == State.UPGRADING:
            self.current_state = State.MINING

        if State.MINING == self.current_state:
            # If I'm mining and I'm standing on an ore, mine it
            if len([item for item in self.get_my_inventory(world) if item is not None]) < 50:
                if current_tile.occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION and current_tile.get_occupied_by(ObjectType.ORE_OCCUPIABLE_STATION).held_item:
                    actions = [ActionType.MINE]
                else:
                    near = self.find_around(mobbot.position, world)
                    actions = self.a_star_search(world.game_map, mobbot.position, near)
        elif State.SELLING == self.current_state:
                actions = self.a_star_search(world.game_map, mobbot.position, self.base_position)
        elif State.UPGRADING == self.current_state:
            actions = self.shop_for_tech(mobbot)
            self.current_state = State.MINING
            self.cur_mine_index = min(len(self.mine_back) - 1, self.cur_mine_index + 1)
        if len([item for item in self.get_my_inventory(world) if item is not None]) < 50:
            if current_tile.occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION and current_tile.get_occupied_by(ObjectType.ORE_OCCUPIABLE_STATION).held_item:
                actions = [ActionType.MINE]
            
        if turn >= 190:
            self.current_state = State.SELLING
            actions = self.a_star_search(world.game_map, mobbot.position, self.base_position)

        self.prev_position = mobbot.position
        if actions == None or isinstance(actions, ActionType) or len(actions) == 0:
            actions = [ActionType.MINE]
        # print(f"actions: {actions}")
        # print(f"turn: {turn} state: {self.current_state}")
        return actions
    
    def can_purchase(self, mobbot: Avatar, world: GameBoard):
        total_potential_sp = mobbot.science_points
        if total_potential_sp >= mobbot.get_tech_info('Improved Drivetrain').cost and not mobbot.is_researched('Improved Drivetrain')\
        or total_potential_sp >= mobbot.get_tech_info('Improved Mining').cost and not mobbot.is_researched('Improved Mining')\
        or total_potential_sp >= mobbot.get_tech_info('Superior Drivetrain').cost and not mobbot.is_researched('Superior Drivetrain')\
        or total_potential_sp >= mobbot.get_tech_info('Superior Mining').cost and not mobbot.is_researched('Superior Mining')\
        or total_potential_sp >= mobbot.get_tech_info('Overdrive Drivetrain').cost and not mobbot.is_researched('Overdrive Drivetrain')\
        or total_potential_sp >= mobbot.get_tech_info('Overdrive Mining').cost and not mobbot.is_researched('Overdrive Mining')\
            :
            return True
        return False
        

    def shop_for_tech(self, mobbot: Avatar):
        if not mobbot.is_researched('Improved Mining'):
            return [ActionType.BUY_IMPROVED_MINING]
        elif not mobbot.is_researched('Improved Drivetrain'):
            return [ActionType.BUY_IMPROVED_DRIVETRAIN]
        elif not mobbot.is_researched('Superior Drivetrain'):
            return [ActionType.BUY_SUPERIOR_DRIVETRAIN]
        elif not mobbot.is_researched('Superior Mining'):
            return [ActionType.BUY_SUPERIOR_MINING]
        elif not mobbot.is_researched('Overdrive Drivetrain'):
            return [ActionType.BUY_OVERDRIVE_DRIVETRAIN]
        elif not mobbot.is_researched('Overdrive Mining'):
            return [ActionType.BUY_OVERDRIVE_MINING]
        else:
            return None
        
    def find_around(self, start_position, world):
            gm = world.game_map
            for mult in range(1, 15):
                for x in range(-1, 2):
                    for y in range(-1, 2):
                            new_x = start_position.x - (x * mult)
                            new_y = start_position.y - (y * mult)
                            if self.min <= new_y < self.max and self.min <= new_x < self.max:
                                if world.game_map[new_y][new_x].occupied_by != None and world.game_map[new_y][new_x].occupied_by.object_type == ObjectType.ORE_OCCUPIABLE_STATION and world.game_map[new_y][new_x].get_occupied_by(ObjectType.ORE_OCCUPIABLE_STATION).held_item:
                                    return Vector(new_x, new_y)

    def get_my_inventory(self, world: GameBoard):
        return world.inventory_manager.get_inventory(self.company)

    def a_star_search(self, map, start, end):
        def is_valid_tile(next):
            invalid_objects = {
                ObjectType.WALL, ObjectType.TRAP, ObjectType.AVATAR}
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
