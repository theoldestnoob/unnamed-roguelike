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
from action import Action, Actions


def parse_input(console, in_handle, user_in, actions, curr_entity, entities,
                game_map, mouse_x, mouse_y, game_state, prev_state,
                targeting_item):
    # set up stuff
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
                msg = Message(act_msg, tcod.light_gray)
                act_msg = Action(Actions.MESSAGE, source=curr_entity, args=msg)
                actions.append(act_msg)
            else:
                act_move = Action(Actions.MOVE, source=curr_entity,
                                  target=curr_entity, args=(dx, dy))
                actions.append(act_move)
        else:
            if not game_map.is_blocked(dest_x, dest_y):
                target = get_blocking_entities_at_location(entities,
                                                           dest_x,
                                                           dest_y)
                if target:
                    if curr_entity.fighter:
                        act_melee = Action(Actions.MELEE, source=curr_entity,
                                           target=target)
                        actions.append(act_melee)
                else:
                    act_move = Action(Actions.MOVE, source=curr_entity,
                                      target=curr_entity, args=(dx, dy))
                    actions.append(act_move)

    if wait:
        msg = Message(f"{curr_entity.name} waits.", tcod.white)
        act_msg = Action(Actions.MESSAGE, source=curr_entity, args=msg)
        actions.append(act_msg)
        act_wait = Action(Actions.WAIT, source=curr_entity, target=curr_entity,
                          args=100)
        actions.append(act_wait)
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
                msg = (msg_str, tcod.light_gray)
                act_msg = Action(Actions.MESSAGE, source=curr_entity, args=msg)
                actions.append(act_msg)
            else:
                act_spawn = Action(Actions.SPAWN_ETHERIC, source=curr_entity,
                                   args=(dest_x, dest_y))
                actions.append(act_spawn)
        # if currently etheric, we're not possessing anyone
        elif curr_entity.etheric:
            if target:
                if target is curr_entity.owner:
                    act_despawn = Action(Actions.DESPAWN_ETHERIC,
                                         source=curr_entity,
                                         target=curr_entity)
                    actions.append(act_despawn)
                else:
                    act_possess = Action(Actions.POSSESS, source=curr_entity,
                                         target=target)
                    actions.append(act_possess)
            else:
                msg_str = "You cannot possess that with no soul!"
                msg = Message(msg_str, tcod.light_gray)
                act_msg = Action(Actions.MESSAGE, source=curr_entity, args=msg)
                actions.append(act_msg)
        # otherwise, we are possessing someone and want to leave
        else:
            if target:
                msg_str = (f"Your etheric body cannot manifest "
                           f"in space occupied by another soul!")
                msg = Message(msg_str, tcod.light_gray)
                act_msg = Action(Actions.MESSAGE, source=curr_entity, args=msg)
                actions.append(act_msg)
            else:
                act_unpossess = Action(Actions.UNPOSSESS, source=curr_entity,
                                       target=curr_entity,
                                       args=(dest_x, dest_y))
                actions.append(act_unpossess)

    if (inventory_index is not None
            and game_state == GameStates.SHOW_INVENTORY
            and prev_state != GameStates.FAIL_STATE):
        if inventory_index < len(curr_entity.inventory.items):
            item = curr_entity.inventory.items[inventory_index]
            act_use = Action(Actions.USE_ITEM, source=curr_entity,
                             target=curr_entity, args=item)
            actions.append(act_use)

    if (inventory_index is not None
            and game_state == GameStates.DROP_INVENTORY
            and prev_state != GameStates.FAIL_STATE):
        if inventory_index < len(curr_entity.inventory.items):
            item = curr_entity.inventory.items[inventory_index]
            act_drop = Action(Actions.DROP_ITEM, source=curr_entity,
                              target=curr_entity, args=item)
            actions.append(act_drop)

    if curr_entity.inventory and show_inventory:
        act_show_inv = Action(Actions.SHOW_INVENTORY, source=curr_entity,
                              target=curr_entity)
        actions.append(act_show_inv)

    if curr_entity.inventory and drop_inventory:
        act_drop_inv = Action(Actions.DROP_INVENTORY, source=curr_entity,
                              target=curr_entity)
        actions.append(act_drop_inv)

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
        act_use = Action(Actions.USE_ITEM, source=curr_entity,
                         target=curr_entity, args=targeting_item)
        actions.append(act_use)

    if level_up:
        print(level_up)
        choice = level_up
        act_levelup = Action(Actions.LEVEL_UP, source=curr_entity,
                             target=curr_entity, args=choice)
        actions.append(act_levelup)

    if show_character_screen:
        act_show_char = Action(Actions.SHOW_CHARACTER_SCREEN,
                               source=curr_entity, target=curr_entity)
        actions.append(act_show_char)

    if want_exit:
        actions.append(Action(Actions.EXIT))

    if fullscreen:
        actions.append(Action(Actions.FULLSCREEN))

    if omnivis:
        actions.append(Action(Actions.OMNIVIS))

    if switch_char:
        actions.append(Action(Actions.SWITCH_CHAR, source=curr_entity))

    if map_gen:
        actions.append(Action(Actions.MAP_GEN))

    if graph_gen:
        actions.append(Action(Actions.GRAPH_GEN))

    if test:
        actions.append(Action(Actions.TEST))

    if msg_up:
        actions.append(Action(Actions.MSG_UP, source=curr_entity))

    if msg_down:
        actions.append(Action(Actions.MSG_DOWN, source=curr_entity))

    if pickup:
        actions.append(Action(Actions.PICKUP, source=curr_entity,
                              target=curr_entity))

    if cancel_target:
        actions.append(Action(Actions.CANCEL_TARGET, source=curr_entity))

    if take_stairs:
        actions.append(Action(Actions.TAKE_STAIRS, source=curr_entity,
                              target=curr_entity))

    if mouse_motion:
        x, y = mouse_motion
        if x != mouse_x or y != mouse_y:
            mouse_x = x
            mouse_y = y
        actions.append(Action(Actions.MOUSEMOTION, args=(x, y)))

    return mouse_x, mouse_y
