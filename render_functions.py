# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 19:35:17 2019

@author: theoldestnoob
"""

import tcod
from enum import Enum


class RenderOrder(Enum):
    CORPSE = 1
    ITEM = 2
    ACTOR = 3


def render_all(con, entities, game_map, curr_entity, render_update,
               screen_width, screen_height, colors, omnivision):
    # sort our entities so we render them in the right order
    entities_sorted = sorted(entities, key=lambda x: x.render_order.value)

    # if we're currently controlling entity 0, we see things differently
    if curr_entity.ident == 0:
        for entity in entities_sorted:
            if entity == curr_entity:
                draw_entity(con, entity, curr_entity.fov_map, omnivision)
            elif entity.soul > 0:
                draw_soul(con, entity, curr_entity.fov_map, omnivision)
        hp_str = f"HP: n/a  "
        tcod.console_set_default_foreground(con, tcod.white)
        tcod.console_print_ex(con, 1, screen_height - 2, tcod.BKGND_NONE,
                              tcod.LEFT, hp_str)

    # otherwise, we see things normally:
    else:
        # draw all the tiles in the game map
        if curr_entity.ident != 0:
            draw_map(con, game_map, curr_entity, render_update,
                     colors, omnivision)

        # draw all the entities in the list, except for entity 0
        for entity in entities_sorted:
            if entity.ident != 0:
                draw_entity(con, entity, curr_entity.fov_map, omnivision)

        hp_str = (f"HP: {curr_entity.fighter.hp:02}"
                  f"/{curr_entity.fighter.max_hp:02}")
        tcod.console_set_default_foreground(con, tcod.white)
        tcod.console_print_ex(con, 1, screen_height - 2, tcod.BKGND_NONE,
                              tcod.LEFT, hp_str)

    # tcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)


def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)


def draw_map(con, game_map, curr_entity, render_update, colors, omnivision):
    if render_update:
        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = curr_entity.fov_map.fov[y][x]
                wall = game_map.tiles[x][y].block_sight

                if visible:
                    if wall:
                        tcod.console_set_char_background(con, x, y,
                                                         colors["light_wall"],
                                                         tcod.BKGND_SET)
                    else:
                        tcod.console_set_char_background(con, x, y,
                                                         colors["light_ground"],
                                                         tcod.BKGND_SET)
                elif (curr_entity.ident in game_map.tiles[x][y].explored
                      or omnivision):
                    if wall:
                        tcod.console_set_char_background(con, x, y,
                                                         colors["dark_wall"],
                                                         tcod.BKGND_SET)
                    else:
                        tcod.console_set_char_background(con, x, y,
                                                         colors["dark_ground"],
                                                         tcod.BKGND_SET)


def blank_map(con, game_map):
    for y in range(game_map.height):
        for x in range(game_map.width):
            tcod.console_set_char_background(con, x, y, tcod.black,
                                             tcod.BKGND_SET)


def gray_map(con, game_map):
    for y in range(game_map.height):
        for x in range(game_map.width):
            tcod.console_set_char_background(con, x, y, tcod.grey,
                                             tcod.BKGND_SET)


def draw_entity(con, entity, fov_map, omnivision):
    if fov_map.fov[entity.y][entity.x] or omnivision:
        con.default_fg = entity.color
        con.put_char(entity.x, entity.y, ord(entity.char))


def draw_soul(con, entity, fov_map, omnivision):
    if fov_map.fov[entity.y][entity.x] or omnivision:
        soul_char = get_soul_char(entity.soul)
        soul_color = get_soul_color(entity.soul)
        con.default_fg = soul_color
        con.put_char(entity.x, entity.y, ord(soul_char))


def clear_entity(con, entity):
    # erase the character that represents this object
    con.put_char(entity.x, entity.y, ord(" "))


def display_space(con, space, color):
    for x, y in space:
        tcod.console_set_char_background(con, x, y, color, tcod.BKGND_SET)


def get_soul_char(soul):
    tens_digit = soul // 10
    if tens_digit % 2 == 0:
        char = '*'
    else:
        char = '+'
    return char


def get_soul_color(soul):
    if soul < 20:
        color = tcod.red
    elif soul < 40:
        color = tcod.orange
    elif soul < 60:
        color = tcod.yellow
    elif soul < 80:
        color = tcod.green
    elif soul < 100:
        color = tcod.blue
    else:
        color = tcod.violet
    return color
