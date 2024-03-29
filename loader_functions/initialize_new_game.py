# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 18:12:22 2019

@author: theoldestnoob
"""

import tcod
import tcod.event
from collections import deque

from entity import Entity
from render_functions import RenderOrder
from game_states import GameStates
from map_objects.game_map import GameMap
from map_objects.game_map_bsp import GameMapBSP
from map_objects.game_map_randomrooms import GameMapRandomRooms
from fov_functions import initialize_fov, init_fov_etheric, recompute_fov
from game_messages import MessageLog
from components.soul import Soul
from components.gnosis import Gnosis
from components.fighter import Fighter
from components.ai import IdleMonster
from components.inventory import Inventory
from components.level import Level
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots


def get_constants():
    # "global" variables
    debug_f = True
    seed = "testseed"

    # window settings
    window_title = "Roguelike Tutorial 2019 - theoldestnoob"
    screen_width = 80
    screen_height = 50

    # ui element settings
    bar_width = 20
    panel_ui_width = screen_width
    panel_ui_height = 7
    panel_ui_y = screen_height - panel_ui_height

    message_x = bar_width + 2
    message_width = screen_width - bar_width - 2
    message_height = panel_ui_height - 1

    panel_map_width = 80
    panel_map_height = 43

    # fov settings
    fov_algorithm = 0
    fov_light_walls = True
    fov_radius = 10
    omnivision = False

    # map settings
    map_width = 80
    map_height = 43

    # various map settings - TODO: move to other module
    mapset_bsprect = {
            "room_max_size": 15,
            "room_min_size": 8,
            "min_rooms": 8,
            "max_rooms": 30,
            "ratio_vh": 1,
            "ratio_hv": 1,
            "ratio_d": 0,
            "hall_rand": False,
            "circ_rooms": 0,
            "rect_rooms": 1,
            "unused": True,
            "bsp_range": 0.15,
            "bsp_depth": 4
    }

    mapset_bspcirc = {
            "room_max_size": 26,
            "room_min_size": 8,
            "min_rooms": 8,
            "max_rooms": 30,
            "ratio_vh": 0,
            "ratio_hv": 0,
            "ratio_d": 1,
            "hall_rand": True,
            "circ_rooms": 1,
            "rect_rooms": 0,
            "unused": True,
            "bsp_range": 0.25,
            "bsp_depth": 4
    }

    mapset_bsprand = {
            "room_max_size": 20,
            "room_min_size": 6,
            "min_rooms": 5,
            "max_rooms": 30,
            "ratio_vh": 1,
            "ratio_hv": 1,
            "ratio_d": 1,
            "hall_rand": True,
            "circ_rooms": 1,
            "rect_rooms": 1,
            "unused": True,
            "bsp_range": 0.4,
            "bsp_depth": 4
    }

    colors = {
            "dark_wall": tcod.Color(0, 0, 100),
            "dark_ground": tcod.Color(50, 50, 150),
            "light_wall": tcod.Color(130, 110, 50),
            "light_ground": tcod.Color(200, 180, 50)
    }

    # put it all into a dict to pass around
    constants = {
            "debug_f": debug_f,
            "seed": seed,
            "window_title": window_title,
            "screen_width": screen_width,
            "screen_height": screen_height,
            "bar_width": bar_width,
            "panel_ui_width": panel_ui_width,
            "panel_ui_height": panel_ui_height,
            "panel_ui_y": panel_ui_y,
            "message_x": message_x,
            "message_width": message_width,
            "message_height": message_height,
            "panel_map_width": panel_map_width,
            "panel_map_height": panel_map_height,
            "map_width": map_width,
            "map_height": map_height,
            "fov_algorithm": fov_algorithm,
            "fov_light_walls": fov_light_walls,
            "fov_radius": fov_radius,
            "omnivision": omnivision,
            "mapset": mapset_bsprand,
            "colors": colors
            }

    return constants


def get_game_variables(constants, root_console, panel_map, debug_f):

    # object setup
    player_soul = Soul("@", tcod.azure)
    player_fighter = Fighter(hp=100, defense=1, power=2)
    player_ai = IdleMonster()
    player_inventory = Inventory(26)
    player_level = Level()
    player_equipment = Equipment()
    player_gnosis = Gnosis()
    player = Entity(0, 0, 0, "@", tcod.yellow, "Player", blocks=True,
                    soul=player_soul, gnosis=player_gnosis,
                    fighter=player_fighter, ai=player_ai,
                    inventory=player_inventory,
                    render_order=RenderOrder.ACTOR, level=player_level,
                    equipment=player_equipment)
    entities = [player]
    controlled_entity = player
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2)
    dagger = Entity(len(entities), 0, 0, "-", tcod.sky, "Dagger",
                    equippable=equippable_component)
    player.inventory.add_item(dagger)
    player.equipment.toggle_equip(dagger)
    game_state = GameStates.NORMAL_TURN
    prev_state = GameStates.NORMAL_TURN

    message_log = MessageLog(constants["message_x"],
                             constants["message_width"],
                             constants["message_height"], 100)

    # create initial game map
    # game_map = GameMap(map_width, map_height, seed, con=con, debug=debug_f)
    # game_map = GameMapRandomRooms(map_width, map_height, seed, con=con, debug=debug_f)
    game_map = GameMapBSP(constants["map_width"], constants["map_height"],
                          constants["seed"], dlevel=1, con=root_console,
                          debug=debug_f)
    game_map.make_map(player, entities, **constants["mapset"])

    # set up time system
    actors = [e for e in entities if e.ai]
    timeq = deque(sorted(actors, key=lambda entity: entity.time_to_act))
    curr_entity = timeq.popleft()
    next_turn = True

    # FOV calculation setup
    render_update = True

    for entity in actors:
        if entity.etheric:
            entity.fov_map = init_fov_etheric(game_map)
        else:
            entity.fov_map = initialize_fov(game_map)
        recompute_fov(game_map, entity, constants["fov_radius"],
                      constants["fov_light_walls"],
                      constants["fov_algorithm"])

    # TODO: there has to be a better way to handle targeting than this
    targeting_item = None

    return (player, entities, controlled_entity, curr_entity,
            game_state, prev_state, message_log, game_map, timeq,
            next_turn, render_update, targeting_item)
