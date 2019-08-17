# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 22:46:03 2019

@author: theoldestnoob
"""

import tcod
import tcod.event
from random import randint
from collections import deque

from render_functions import RenderOrder
from fov_functions import initialize_fov, init_fov_etheric, recompute_fov
from entity import Entity
from components.soul import Soul
from components.gnosis import Gnosis
from components.etheric import Etheric
from components.fighter import Fighter
from components.ai import IdleMonster
from components.inventory import Inventory
from game_messages import Message
from death_functions import kill_entity
from game_states import GameStates
from action import Action, Actions


# TODO: man I have to pass a lot of stuff in and out of these guys
#       there must be a better way?
def handle_entity_actions(actions, in_handle, entities, timeq, game_map,
                          console, message_log, controlled_entity, player,
                          game_state, prev_state, targeting_item, debug_f):
    action_cost = 0
    next_turn = True
    controlled_entity = controlled_entity
    render_update = False
    game_state = game_state
    prev_state = prev_state
    targeting_item = targeting_item

    while len(actions) > 0:
        action = actions.popleft()

        # (Actions.MESSAGE, source, args=msg)
        if action.ident == Actions.MESSAGE:
            message = action.args
            render_update = True
            message_log.add_message(message)

        # (Actions.MOVE, source, target, args=(dx, dy))
        elif action.ident == Actions.MOVE:
            action_cost = 100
            next_turn = True
            entity = action.source
            dx, dy = action.args
            # don't let entities move out of the map's boundaries
            if not (entity.x + dx < 0 or entity.y + dy < 0
                    or entity.x + dx >= game_map.width
                    or entity.y + dy >= game_map.height):
                entity.move(dx, dy)

        # (Actons.MOVE_ASTAR, source, target)
        elif action.ident == Actions.MOVE_ASTAR:
            action_cost = 100
            next_turn = True
            action.source.move_astar(action.target, entities, game_map)

        # (Actions.MELEE, source, target)
        elif action.ident == Actions.MELEE:
            action_cost = 100
            next_turn = True
            melee_results = action.source.fighter.attack(action.target)
            actions.extendleft(reversed(melee_results))

        # (Actions.WAIT, source, target, args=time)
        elif action.ident == Actions.WAIT:
            action_cost = action.args
            next_turn = True

        # (Actions.SPAWN_ETHERIC, source, args=(dest_x, dest_y))
        elif action.ident == Actions.SPAWN_ETHERIC:
            action_cost = 100
            next_turn = True
            render_update = True
            spawner = action.source
            dest_x, dest_y = action.args
            msg = Message("You manifest your etheric body!", tcod.light_gray)
            act_msg = Action(Actions.MESSAGE, source=spawner, args=msg)
            actions.appendleft(act_msg)
            etheric_soul = Soul(spawner.gnosis.char, spawner.gnosis.color)
            etheric_body = Etheric(move_range=spawner.gnosis.move_range,
                                   duration=spawner.gnosis.duration)
            etheric_fighter = Fighter(hp=1, defense=0, power=0)
            etheric_ai = IdleMonster()
            possessor = Entity(len(entities), dest_x, dest_y,
                               spawner.gnosis.char, spawner.gnosis.color,
                               "EBody", blocks=False,
                               etheric=etheric_body, soul=etheric_soul,
                               fighter=etheric_fighter, ai=etheric_ai,
                               render_order=RenderOrder.ACTOR,
                               speed=spawner.gnosis.speed)
            possessor.owner = spawner
            possessor.fov_map = init_fov_etheric(game_map)
            possessor.fov_recompute = True
            entities.append(possessor)
            for index, entity in enumerate(timeq):
                if entity.time_to_act > possessor.time_to_act:
                    timeq.insert(index, possessor)
                    break
            else:
                timeq.append(possessor)
            controlled_entity = possessor

        # (Actions.DESPAWN_ETHERIC, source, target)
        elif action.ident == Actions.DESPAWN_ETHERIC:
            action_cost = 50
            next_turn = True
            render_update = True
            entity = action.target
            owner = entity.owner
            controlled_entity = owner
            entities.remove(entity)
            entity.speed = 0

        # (Actions.POSSESS, source, target)
        elif action.ident == Actions.POSSESS:
            action_cost = 100
            next_turn = True
            render_update = True
            possessor = action.source
            target = action.target
            msg = (Message(f"You possess the {target.name}!", tcod.light_gray))
            act_msg = Action(Actions.MESSAGE, source=action.source, args=msg)
            actions.appendleft(act_msg)
            target.possessor = possessor
            controlled_entity = target

        # (Actions.UNPOSSESS, source, target, args=(dest_x, dest_y))
        elif action.ident == Actions.UNPOSSESS:
            action_cost = 100
            next_turn = True
            render_update = True
            entity = action.target
            dest_x, dest_y = action.args
            msg_str = f"You stop possessing the {controlled_entity.name}!"
            msg = Message(msg_str, tcod.light_gray)
            act_msg = Action(Actions.MESSAGE, source=action.target, args=msg)
            actions.appendleft(act_msg)
            controlled_entity = entity.possessor
            controlled_entity.x = dest_x
            controlled_entity.y = dest_y
            controlled_entity.fov_recompute = True
            entity.possessor = None

        # Action(Actions.PICKUP, source, target)
        elif action.ident == Actions.PICKUP and action.source.inventory:
            render_update = True
            actor = action.source
            for entity in entities:
                if (entity.item
                        and entity.x == actor.x
                        and entity.y == actor.y):
                    results = actor.inventory.add_item(entity)
                    actions.extendleft(reversed(results))
                    break
            else:
                msg = Message("There is nothing here to pick up.", tcod.yellow)
                act_msg = Action(Actions.MESSAGE, source=actor, args=msg)
                actions.appendleft(act_msg)

        # (Actions.ITEM_ADDED, source, args=item)
        elif action.ident == Actions.ITEM_ADDED:
            next_turn = True
            action_cost = 50
            entities.remove(action.args)

        # (Actions.USE_ITEM, source, target, args=item)
        elif action.ident == Actions.USE_ITEM:
            render_update = True
            user = action.source
            use_item = action.args
            use_results = user.inventory.use(use_item, entities=entities)
            # TODO: hack to clear targeting after item use, don't like it
            item_consumed = False
            for use_result in reversed(use_results):
                if use_result.ident == Actions.CONSUMED:
                    item_consumed = True
                actions.appendleft(use_result)
            if not item_consumed:
                use_item.item.target_x = None
                use_item.item.target_y = None
            elif use_item is targeting_item:
                targeting_item = None
                game_state = prev_state

        # (Actions.ITEM_USED, source=self.owner, target=item_entity)
        elif action.ident == Actions.ITEM_USED:
            next_turn = True
            action_cost = 100

        # (Actions.DROP_ITEM, source, target, args=item)
        elif action.ident == Actions.DROP_ITEM:
            render_update = True
            drop_item = action.args
            drop_results = controlled_entity.inventory.drop(drop_item)
            actions.extendleft(reversed(drop_results))

        # TODO: the way this works is gonna fuck up dropping items on death
        # (Actions.ITEM_DROPPED, source=self.owner, target=item)
        elif action.ident == Actions.ITEM_DROPPED:
            item_dropped = action.target
            action_cost = 50
            next_turn = True
            entities.append(item_dropped)

        # TODO: There has to be a better way to handle targeting than this
        # (Actions.TARGETING, source=self.owner, args=item_entity)
        elif action.ident == Actions.TARGETING:
            render_update = True
            next_turn = False
            prev_state = GameStates.NORMAL_TURN
            game_state = GameStates.TARGETING
            targeting_item = action.args
            msg = targeting_item.item.targeting_message
            act_msg = Action(Actions.MESSAGE, source=action.source, args=msg)
            actions.appendleft(act_msg)

        # (Actions.CANCEL_TARGET, source)
        elif action.ident == Actions.CANCEL_TARGET:
            game_state = prev_state
            render_update = True
            next_turn = False
            msg = (Message("Targeting cancelled", tcod.light_cyan))
            act_msg = Action(Actions.MESSAGE, source=action.source, args=msg)
            actions.appendleft(act_msg)

        # (Actions.DEAD, source=self.owner)
        elif action.ident == Actions.DEAD:
            render_update = True
            dead = action.source
            msg = kill_entity(dead)
            act_msg = Action(Actions.MESSAGE, source=dead, args=msg)
            actions.appendleft(act_msg)
            if dead == player:
                msg = Message("Oh no you lose!", tcod.red)
                act_msg = Action(Actions.MESSAGE, source=dead, args=msg)
                actions.appendleft(act_msg)
                game_state = GameStates.FAIL_STATE

        # Action(Actions.XP, source=xp_source, target=xp_target, args=xp_args)
        elif action.ident == Actions.XP:
            entity = action.target
            xp_gain = action.args
            if entity is not None and entity.level:
                level_from_xp = entity.level.add_xp(xp_gain)
                msg_str = f"{entity.name} gains {xp_gain} experience points."
                msg = Message(msg_str, tcod.white)
                act_msg = Action(Actions.MESSAGE, source=entity, args=msg)
                actions.appendleft(act_msg)
                if level_from_xp:
                    msg_str = (f"{entity.name} grows stronger!  They have "
                               f"reached level {entity.level.current_level}!")
                    msg = Message(msg_str, tcod.yellow)
                    act_msg = Action(Actions.MESSAGE, source=entity, args=msg)
                    actions.appendleft(act_msg)
                    if entity is controlled_entity:
                        prev_state = game_state
                        game_state = GameStates.LEVEL_UP

        # (Actions.LEVEL_UP, source, target, args=choice)
        elif action.ident == Actions.LEVEL_UP:
            entity = action.source
            choice = action.args
            if choice == "hp":
                entity.fighter.base_max_hp += 20
                entity.fighter.hp += 20
            elif choice == "str":
                entity.fighter.base_power += 1
            elif choice == "def":
                entity.fighter.base_defense += 1
            game_state = prev_state
            render_update = True
            next_turn = False

        # Action(Actions.EQUIP, source=self.owner, target=item_entity)
        elif action.ident == Actions.EQUIP:
            entity = action.source
            item = action.target
            equip_results = entity.equipment.toggle_equip(item)
            actions.extendleft(reversed(equip_results))

        # (Actions.DEQUIPPED, source=self.owner, target=equippable_entity)
        elif action.ident == Actions.DEQUIPPED:
            next_turn = True
            render_update = True
            action_cost = 50
            entity = action.source
            item = action.target
            msg_str = f"{entity.name} dequipped the {item.name}"
            msg = (Message(msg_str, tcod.white))
            act_msg = Action(Actions.MESSAGE, source=entity, args=msg)
            actions.appendleft(act_msg)

        # (Actions.EQUIPPED, source=self.owner, target=equippable_entity)
        elif action.ident == Actions.EQUIPPED:
            next_turn = True
            render_update = True
            action_cost = 50
            entity = action.source
            item = action.target
            msg_str = f"{entity.name} equipped the {item.name}"
            msg = (Message(msg_str, tcod.white))
            act_msg = Action(Actions.MESSAGE, source=entity, args=msg)
            actions.appendleft(act_msg)

    return (action_cost, next_turn, controlled_entity, render_update,
            game_state, prev_state, targeting_item)


def handle_player_actions(actions, in_handle, entities, game_map, console,
                          panel_ui, panel_map, curr_entity, controlled_entity,
                          player, omnivision, message_log,
                          timeq, game_state, prev_state,
                          constants, debug_f):
    """ Process out of turn and debug actions, things only the player can do"""
    # pull constants
    mapset = constants["mapset"]
    fov_radius = constants["fov_radius"]
    fov_light_walls = constants["fov_light_walls"]
    fov_algorithm = constants["fov_algorithm"]
    # setup stuff
    next_turn = False
    curr_entity = curr_entity
    controlled_entity = controlled_entity
    player = player
    actions_in = actions
    actions_out = deque()
    entities = entities
    omnivision = omnivision
    timeq = timeq
    want_exit = False
    render_update = False

    while len(actions_in) > 0:
        action = actions_in.popleft()

        # out of turn actions
        # (Actions.EXIT)
        if action.ident == Actions.EXIT:
            if game_state in (GameStates.SHOW_INVENTORY,
                              GameStates.DROP_INVENTORY,
                              GameStates.CHARACTER_SCREEN):
                game_state = prev_state
                want_exit = False
                render_update = True
            else:
                want_exit = True

        # (Actions.FULLSCREEN)
        elif action.ident == Actions.FULLSCREEN:
            next_turn = False
            render_update = True
            tcod.console_set_fullscreen(not tcod.console_is_fullscreen())

        # TODO: I'm not super happy about how this works
        #       but not sure how to elegantly tag render_update when the list
        #       of entities being moused over changes
        # (Actions.MOUSEMOTION, args=(x, y))
        elif action.ident == Actions.MOUSEMOTION:
            render_update = True

        # (Actions.MSG_UP, source)
        elif action.ident == Actions.MSG_UP:
            if message_log.bottom < message_log.length - message_log.height:
                message_log.scroll(1)
                render_update = True

        # (Actions.MSG_DOWN, source)
        elif action.ident == Actions.MSG_DOWN:
            if message_log.bottom > 0:
                message_log.scroll(-1)
                render_update = True

        # (Actions.SHOW_INVENTORY, source, target)
        elif action.ident == Actions.SHOW_INVENTORY:
            render_update = True
            next_turn = False
            prev_state = game_state
            game_state = GameStates.SHOW_INVENTORY

        # (Actions.DROP_INVENTORY, source, target)
        elif action.ident == Actions.DROP_INVENTORY:
            render_update = True
            next_turn = False
            prev_state = game_state
            game_state = GameStates.DROP_INVENTORY

        # (Actions.TAKE_STAIRS, source, target)
        elif action.ident == Actions.TAKE_STAIRS:
            for entity in entities:
                # TODO: this will be buggy a f, sort out the various player + entity things
                if (entity.stairs and entity.x == controlled_entity.x
                        and entity.y == controlled_entity.y):
                    game_map.dlevel += 1
                    game_map.tiles = game_map.initialize_tiles()
                    entities = [player, controlled_entity]
                    game_map.make_map(player, entities, **mapset)
                    # set up time system
                    actors = [e for e in entities if e.ai]
                    timeq = deque(sorted(actors, key=lambda e: e.time_to_act))
                    curr_entity = timeq.popleft()
                    next_turn = True
                    # FOV calculation setup
                    render_update = True
                    for entity in actors:
                        entity.fov_map = initialize_fov(game_map)
                        recompute_fov(game_map, entity, fov_radius,
                                      fov_light_walls, fov_algorithm)
                    break
            else:
                msg = Message("There are no stairs here.", tcod.yellow)
                act_msg = Action(Actions.MESSAGE, source=curr_entity, args=msg)
                actions_out.append(act_msg)

        # (Actions.SHOW_CHARACTER_SCREEN, source, target)
        elif action.ident == Actions.SHOW_CHARACTER_SCREEN:
            render_update = True
            next_turn = False
            prev_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        # debug actions
        # (Actions.OMNIVIS)
        elif action.ident == Actions.OMNIVIS:
            next_turn = False
            render_update = True
            omnivision = not omnivision

        # (Actions.SWITCH_CHAR, source)
        elif action.ident == Actions.SWITCH_CHAR:
            next_turn = False
            render_update = True
            index = controlled_entity.ident + 1
            if index >= len(entities):
                controlled_entity = entities[0]
            else:
                controlled_entity = entities[index]
            # only switch to controllable entities
            while not controlled_entity.soul:
                index = controlled_entity.ident + 1
                if index >= len(entities):
                    controlled_entity = entities[0]
                else:
                    controlled_entity = entities[index]

        # Action(Actions.MAP_GEN)
        elif action.ident == Actions.MAP_GEN:
            next_turn = True
            render_update = True
            game_map.seed = randint(0, 99999)
            game_map.tiles = game_map.initialize_tiles()
            player_soul = Soul("@", tcod.azure)
            player_gnosis = Gnosis()
            player_fighter = Fighter(hp=30, defense=2, power=5)
            player_ai = IdleMonster()
            player_inventory = Inventory(26)
            player = Entity(0, 0, 0, "&", tcod.yellow, "Player", blocks=True,
                            fighter=player_fighter, ai=player_ai,
                            soul=player_soul, gnosis=player_gnosis,
                            inventory=player_inventory,
                            render_order=RenderOrder.ACTOR)
            entities = [player]
            controlled_entity = player
            game_map.make_map(player, entities, **mapset)
            # set up time system
            actors = [e for e in entities if e.ai]
            timeq = deque(sorted(actors, key=lambda e: e.time_to_act))
            curr_entity = timeq.popleft()
            next_turn = True
            # FOV calculation setup
            render_update = True
            for entity in actors:
                if entity.ident == 0:
                    entity.fov_map = init_fov_etheric(game_map)
                else:
                    entity.fov_map = initialize_fov(game_map)
                recompute_fov(game_map, entity, fov_radius, fov_light_walls,
                              fov_algorithm)

        # (Actions.GRAPH_GEN)
        elif action.ident == Actions.GRAPH_GEN:
            game_map.make_graph()

        # (Actions.TEST)
        elif action.ident == Actions.TEST:
            pass

        # not an action we're handling in this function
        else:
            actions_out.append(action)

    return (next_turn, curr_entity, controlled_entity, entities, player,
            actions_out, timeq, omnivision, render_update, want_exit,
            game_state, prev_state)


''' Bunch of stuff pulled out of handle_player_actions to make it less awful:

            if show_vertices:  # {"show_vertices": True}
            for vertex in game_map.graph.vertices:
                display_space(console, vertex.space, tcod.green)
                tcod.console_flush()
                if debug_f:
                    print(f"***Vertex: {vertex}")
                while True:
                    for event in tcod.event.get():
                        in_handle.dispatch(event)
                    action = in_handle.get_user_input()
                    show_vertices = action.get("show_vertices")
                    want_exit = action.get("exit")
                    if show_vertices or want_exit:
                        break
                if want_exit:
                    break
                render_all(console, panel_ui, panel_map, entities, game_map,
                           controlled_entity, screen_width, screen_height,
                           bar_width, panel_ui_width, panel_ui_height,
                           panel_ui_y, panel_map_width, panel_map_height,
                           colors, message_log, mouse_x, mouse_y,
                           omnivision)
                tcod.console_flush()
            render_update = True

        if show_hyperedges:  # {"show_hyperedges": True}
            for edge in game_map.graph.hyperedges:
                display_space(console, edge.space, tcod.green)
                tcod.console_flush()
                if debug_f:
                    print(f"***Hyperedge: {edge}")
                while True:
                    for event in tcod.event.get():
                        in_handle.dispatch(event)
                    action = in_handle.get_user_input()
                    show_hyperedges = action.get("show_hyperedges")
                    want_exit = action.get("exit")
                    if show_hyperedges or want_exit:
                        break
                if want_exit:
                    break
                render_all(console, panel_ui, panel_map, entities, game_map,
                           controlled_entity, screen_width, screen_height,
                           bar_width, panel_ui_width, panel_ui_height,
                           panel_ui_y, panel_map_width, panel_map_height,
                           colors, message_log, mouse_x, mouse_y,
                           omnivision)
                tcod.console_flush()
            render_update = True

        if show_edges:  # {"show_edges": True}
            for edge in game_map.graph.edges:
                display_space(console, edge.space, tcod.green)
                tcod.console_flush()
                if debug_f:
                    print(f"***Edge: {edge}")
                while True:
                    for event in tcod.event.get():
                        in_handle.dispatch(event)
                    action = in_handle.get_user_input()
                    show_edges = action.get("show_edges")
                    want_exit = action.get("exit")
                    if show_edges or want_exit:
                        break
                if want_exit:
                    break
                render_all(console, panel_ui, panel_map, entities, game_map,
                           controlled_entity, screen_width, screen_height,
                           bar_width, panel_ui_width, panel_ui_height,
                           panel_ui_y, panel_map_width, panel_map_height,
                           colors, message_log, mouse_x, mouse_y,
                           omnivision)
                tcod.console_flush()
            render_update = True
'''
