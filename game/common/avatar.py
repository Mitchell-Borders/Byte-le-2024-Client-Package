from typing import Self

from game.common.enums import ObjectType, Company, Tech
from game.common.game_object import GameObject
from game.quarry_rush.ability.emp_active_ability import EMPActiveAbility
from game.quarry_rush.ability.landmine_active_ability import LandmineActiveAbility
from game.quarry_rush.ability.trap_defusal_active_ability import TrapDefusalActiveAbility
from game.quarry_rush.tech.tech import TechInfo
from game.utils.vector import Vector
from game.quarry_rush.tech.tech_tree import TechTree
from game.quarry_rush.avatar.avatar_functions import AvatarFunctions
from game.quarry_rush.ability.dynamite_active_ability import DynamiteActiveAbility


class Avatar(GameObject):
    """
    `Avatar Inventory Notes:`

        The avatar's inventory is a list of items. Each item has a quantity and a stack_size (the max amount of an
        item that can be held in a stack. Think of the Minecraft inventory).

        This upcoming example is just to facilitate understanding the concept. The Dispensing Station concept that will
        be mentioned is completely optional to implement if you desire. The Dispensing Station is used to help with the
        explanation.

        ----

        **Items:**
            Every Item has a quantity and a stack_size. The quantity is how much of the Item the player *currently* has.
            The stack_size is the max of that Item that can be in a stack. For example, if the quantity is 5, and the
            stack_size is 5 (5/5), the item cannot be added to that stack

        -----

        **Picking up items:**

            Example 1:
                When you pick up an item (which will now be referred to as picked_up_item), picked_up_item has a given
                quantity. In this case, let's say the quantity of picked_up_item is 2.

                Imagine you already have this item in your inventory (which will now be referred to as inventory_item),
                and inventory_item has a quantity of 1 and a stack_size of 10 (think of this as a fraction: 1/10).

                When you pick up picked_up_item, inventory_item will be checked.
                If picked_up_item's quantity + inventory_item < stack_size, it'll be added without issue.
                Remember, for this example: picked_up_item quantity is 2, and inventory_item quantity is 1, and
                stack_size is 10.

                    Inventory_item quantity before picking up: 1/10
                    ::
                        2 + 1 < 10 --> True
                    Inventory_item quantity after picking up: 3/10

            ----

            Example 2:
                For the next two examples, the total inventory size will be considered.

                Let's say inventory_item has quantity 4 and a stack_size of 5. Now say that picked_up_item has
                quantity 3.

                Recall: if picked_up_item's quantity + inventory_item < stack_size, it will be added without issue

                    Inventory_item quantity before picking up: 4/5
                    ::
                        3 + 4 < 5 --> False

                What do we do in this situation? If you want to add picked_up_item to inventory_item and there is an
                overflow of quantity, that is handled for you.

                Let's say that your inventory size (which will now be referred to as max_inventory_size) is 5. You
                already have inventory_item in there that has a quantity of 4 and a stack_size of 5. An image of the
                inventory is below. 'None' is used to help show the max_inventory_size. Inventory_item quantity and
                stack_size will be listed in parentheses as a fraction.
                ::
                    Inventory:
                    [
                        inventory_item (4/5),
                        None,
                        None,
                        None,
                        None
                    ]

                Now we will add picked_up_item and its quantity of 3:
                ::
                    Inventory before:
                    [
                        inventory_item (4/5),
                        None,
                        None,
                        None,
                        None
                    ]

                    3 + 4 < 5 --> False

                inventory_item (4/5) will now be inventory_item (5/5)
                picked_up_item now has a quantity of 2 instead of 3
                Since we have a surplus, we will append the same item with a quantity of 2 in the inventory.
                ::
                    The result is:
                    [
                        inventory_item (5/5),
                        inventory_item (2/5),
                        None,
                        None,
                        None
                    ]

            ----

            Example 3:

                You can only fit one more inventory_item into the last stack before the inventory is full.
                Let's say that picked_up_item has quantity of 3 again.
                ::
                    Inventory before:
                    [
                        inventory_item (5/5),
                        inventory_item (5/5),
                        inventory_item (5/5),
                        inventory_item (5/5),
                        inventory_item (4/5)
                    ]

                        3 + 4 < 5 --> False

                inventory_item (4/5) will now be inventory_item (5/5)
                picked_up_item now has a quantity of 2
                However, despite the surplus, we cannot add it into our inventory, so the remaining quantity of
                picked_up_item is left where it was first found.
                ::
                    Inventory after:
                    [
                        inventory_item (5/5),
                        inventory_item (5/5),
                        inventory_item (5/5),
                        inventory_item (5/5),
                        inventory_item (5/5)
                    ]
    """

    def __init__(self, company: Company = Company.CHURCH, position: Vector | None = None):
        super().__init__()
        self.object_type: ObjectType = ObjectType.AVATAR
        self.score: int = 0
        self.science_points: int = 0
        self.position: Vector | None = position
        self.movement_speed: int = 1  # determines how many tiles the player moves
        self.drop_rate: int = 1  # determines how many items are dropped after mining
        self.abilities: dict = self.__create_abilities_dict()  # used to manage unlocking new abilities
        self.__tech_tree: TechTree = self.__create_tech_tree()  # the tech tree cannot be set; made private for security
        self.__company: Company = company
        self.dynamite_active_ability: DynamiteActiveAbility = DynamiteActiveAbility()
        self.landmine_active_ability: LandmineActiveAbility = LandmineActiveAbility()
        self.emp_active_ability: EMPActiveAbility = EMPActiveAbility()
        self.trap_defusal_active_ability: TrapDefusalActiveAbility = TrapDefusalActiveAbility()

    @property
    def company(self) -> Company:
        return self.__company

    @property
    def score(self) -> int:
        return self.__score

    @property
    def science_points(self) -> int:
        return self.__science_points

    @property
    def position(self) -> Vector | None:
        return self.__position

    @property
    def movement_speed(self) -> int:
        return self.__movement_speed

    @property
    def drop_rate(self) -> int:
        return self.__drop_rate

    @property
    def abilities(self):
        return self.__abilities

    @company.setter
    def company(self, company: Company) -> None:
        self.__company = company

    @score.setter
    def score(self, score: int) -> None:
        if score is None or not isinstance(score, int):
            raise ValueError(f'{self.__class__.__name__}.score must be an int.')

        if score < 0:
            raise ValueError(f'{self.__class__.__name__}.score must be a positive int.')

        self.__score: int = score

    @science_points.setter
    def science_points(self, points: int) -> None:
        if points is None or not isinstance(points, int):
            raise ValueError(f'{self.__class__.__name__}.science_points must be an int.')

        if points < 0:
            raise ValueError(f'{self.__class__.__name__}.science_points must be a positive int.')

        self.__science_points: int = points

    @position.setter
    def position(self, position: Vector | None) -> None:
        if position is not None and not isinstance(position, Vector):
            raise ValueError(f'{self.__class__.__name__}.position must be a Vector or None.')
        self.__position: Vector | None = position

    @movement_speed.setter
    def movement_speed(self, speed: int) -> None:
        if speed is None or not isinstance(speed, int):
            raise ValueError(f'{self.__class__.__name__}.movement_speed must be an int.')

        if speed < 0:
            raise ValueError(f'{self.__class__.__name__}.movement_speed must be a positive int.')

        self.__movement_speed: int = speed

    @drop_rate.setter
    def drop_rate(self, drop_rate: int) -> None:
        if drop_rate is None or not isinstance(drop_rate, int):
            raise ValueError(f'{self.__class__.__name__}.drop_rate must be an int.')

        if drop_rate < 0:
            raise ValueError(f'{self.__class__.__name__}.drop_rate must be a positive int.')

        self.__drop_rate = drop_rate

    @abilities.setter
    def abilities(self, abilities: dict[bool]) -> None:
        if abilities is None or not isinstance(abilities, dict):
            raise ValueError(f'{self.__class__.__name__}.abilities must be a dict.')

        for ability, value in abilities.items():
            if value is None or not isinstance(value, bool):
                raise ValueError(f'Every value in the {self.__class__.__name__}.abilities dict must be a bool.')

        self.__abilities = abilities

    def is_researched(self, tech_name: str | Tech) -> bool:
        ...

    def get_researched_techs(self) -> list[str]:
        ...

    def get_all_tech_names(self) -> list[str]:
        ...
    
    def get_tech_info(self, tech_name: str | Tech) -> TechInfo | None:
        ...

    # Dynamite placing functionality ----------------------------------------------------------------------------------
    # if avatar calls place dynamite, set to true, i.e. they want to place dynamite
    def can_place_dynamite(self) -> bool:
        ...

    def can_place_landmine(self) -> bool:
        ...

    def can_place_emp(self) -> bool:
        ...

    def can_defuse_trap(self) -> bool:
        ...

    # method to return the opposing team based on the avatar's company
    def get_opposing_team(self) -> Company:
        ...