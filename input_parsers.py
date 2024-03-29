# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 22:14:46 2019

@author: theoldestnoob
"""

import tcod

from entity import get_blocking_entities_at_location
from entity import get_souled_entities_at_location
from game_messages import Message
from game_states import GameStates
from render_functions import get_map_offset, get_console_offset


def parse_input(console, in_handle, user_in, curr_entity, entities, game_map,
                mouse_x, mouse_y, game_state, prev_state, targeting_item):
    # set up stuff
    actions = []
    mouse_x = mouse_x
    mouse_y = mouse_y

    # get user input details
    move = user_in.get("move")
    wait = user_in.get("wait")
    possess = user_in.get("possess")
    want_exit = user_in.get("exit")
    fullscreen = user_in.get("fullscreen")
    map_gen = user_in.get("map_gen")
    graph_gen = user_in.get("graph_gen")
    show_vertices = user_in.get("show_vertices")
    show_hyperedges = user_in.get("show_hyperedges")
    show_edges = user_in.get("show_edges")
    test = user_in.get("test")
    omnivis = user_in.get("omnivis")
    switch_char = user_in.get("switch_char")
    mouse_motion = user_in.get("mousemotion")
    msg_up = user_in.get("msg_up")
    msg_down = user_in.get("msg_down")
    pickup = user_in.get("pickup")
    show_inventory = user_in.get("show_inventory")
    drop_inventory = user_in.get("drop_inventory")
    inventory_index = user_in.get("inventory_index")
    in_target = user_in.get("in_target")
    cancel_target = user_in.get("cancel_target")
    take_stairs = user_in.get("take_stairs")
    level_up = user_in.get("level_up")
    show_character_screen = user_in.get("show_character_screen")

    # put together actions based on user input
    if move:
        dx, dy = move
        dest_x = curr_entity.x + dx
        dest_y = curr_entity.y + dy
        # etheric entities can move through walls
        if curr_entity.etheric:
            target = get_blocking_entities_at_location(entities,
                                                       dest_x, dest_y)
            if target:
                act_msg = (f"A shudder runs through {target.name} "
                           f"as you press against its soul!")
                actions.append({"message": Message(act_msg, tcod.light_gray)})
            else:
                actions.append({"move": (curr_entity, dx, dy)})
        else:
            if not game_map.is_blocked(dest_x, dest_y):
                target = get_blocking_entities_at_location(entities,
                                                           dest_x,
                                                           dest_y)
                if target:
                    if curr_entity.fighter:
                        actions.append({"melee": (curr_entity, target)})
                else:
                    actions.append({"move": (curr_entity, dx, dy)})

    if wait:
        actions.append({"message":
                        Message(f"{curr_entity.name} waits.", tcod.white)})
        actions.append({"wait": 100})
        # TODO: potential future waits of variable length
        #       or normalized to entity speed

    if possess:
        # get a direction to try to possess/leave
        while not move:
            for event in tcod.event.get():
                in_handle.dispatch(event)
            user_in = in_handle.get_user_input()
            move = user_in.get("move")
        dx, dy = move
        dest_x = curr_entity.x + dx
        dest_y = curr_entity.y + dy
        target = get_souled_entities_at_location(entities, dest_x, dest_y)
        # if currently have gnosis, spawn our etheric body
        if curr_entity.gnosis:
            if target:
                msg_str = (f"Your etheric body cannot manifest "
                           f"in space occupied by another soul!")
                actions.append({"message": Message(msg_str, tcod.light_gray)})
            else:
                actions.append({"spawn_etheric": (curr_entity,
                                                  dest_x, dest_y)})
        # if currently etheric, we're not possessing anyone
        elif curr_entity.etheric:
            if target:
                if target is curr_entity.owner:
                    actions.append({"despawn_etheric": curr_entity})
                else:
                    actions.append({"possess": (curr_entity, target)})
            else:
                msg_str = "You cannot possess that with no soul!"
                actions.append({"message": Message(msg_str, tcod.light_gray)})
        # otherwise, we are possessing someone and want to leave
        else:
            if target:
                msg_str = (f"Your etheric body cannot manifest "
                           f"in space occupied by another soul!")
                actions.append({"message": Message(msg_str, tcod.light_gray)})
            else:
                actions.append({"unpossess": (curr_entity, dest_x, dest_y)})

    if (inventory_index is not None
            and game_state == GameStates.SHOW_INVENTORY
            and prev_state != GameStates.FAIL_STATE):
        if inventory_index < len(curr_entity.inventory.items):
            item = curr_entity.inventory.items[inventory_index]
            actions.append({"use_item": item})

    if (inventory_index is not None
            and game_state == GameStates.DROP_INVENTORY
            and prev_state != GameStates.FAIL_STATE):
        if inventory_index < len(curr_entity.inventory.items):
            item = curr_entity.inventory.items[inventory_index]
            actions.append({"drop_item": item})

    if curr_entity.inventory and show_inventory:
        actions.append(user_in)

    if curr_entity.inventory and drop_inventory:
        actions.append(user_in)

    if in_target and game_state == GameStates.TARGETING:
        x, y = in_target
        map_x, map_y = get_map_offset(console, game_map, curr_entity)
        con_x, con_y = get_console_offset(console, game_map)
        x_off = map_x - con_x
        y_off = map_y - con_y
        x += x_off
        y += y_off
        targeting_item.item.target_x = x
        targeting_item.item.target_y = y
        actions.append({"use_item": targeting_item})

    if level_up:
        print(level_up)
        choice = level_up
        actions.append({"level_up": (curr_entity, choice)})

    if show_character_screen:
        actions.append({"show_character_screen": True})

    # TODO: I don't like having to pass actions through like this
    if (want_exit or fullscreen or omnivis or switch_char or map_gen
            or graph_gen or test or msg_up or msg_down or pickup
            or inventory_index is not None or cancel_target or take_stairs):
        actions.append(user_in)

    if ((show_hyperedges or show_edges or show_vertices)
            and game_map.graph is not None):
        actions.append(user_in)

    if mouse_motion:
        x, y = mouse_motion
        if x != mouse_x or y != mouse_y:
            mouse_x = x
            mouse_y = y
        actions.append({"mousemotion": (x, y)})

    return actions, mouse_x, mouse_y
