# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 22:06:21 2019

@author: theoldestnoob
"""

from collections import namedtuple
from enum import Enum, auto


Action = namedtuple("Action", "ident, source, target, args",
                    defaults=(None, None, None, None))


class Actions(Enum):
    MESSAGE = auto()
    MOVE = auto()
    MOVE_ASTAR = auto()
    MELEE = auto()
    WAIT = auto()
    SPAWN_ETHERIC = auto()
    DESPAWN_ETHERIC = auto()
    POSSESS = auto()
    UNPOSSESS = auto()
    PICKUP = auto()
    ITEM_ADDED = auto()
    USE_ITEM = auto()
    CONSUMED = auto()
    DROP_ITEM = auto()
    ITEM_DROPPED = auto()
    TARGETING = auto()
    CANCEL_TARGET = auto()
    DEAD = auto()
    XP = auto()
    LEVEL_UP = auto()
    EQUIP = auto()
    EQUIPPED = auto()
    DEQUIPPED = auto()
    EXIT = auto()
    FULLSCREEN = auto()
    MOUSEMOTION = auto()
    MSG_UP = auto()
    MSG_DOWN = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    TAKE_STAIRS = auto()
    SHOW_CHARACTER_SCREEN = auto()
    OMNIVIS = auto()
    SWITCH_CHAR = auto()
    MAP_GEN = auto()
    GRAPH_GEN = auto()
    TEST = auto()
