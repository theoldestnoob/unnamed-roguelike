# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 15:28:34 2019

@author: theoldestnoob
"""

import tcod

from game_messages import Message
from action import Action, Actions


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []

    def add_item(self, item):
        results = []

        if len(self.items) >= self.capacity:
            msg_str = "You cannot carry any more, your inventory is full."
            msg = Message(msg_str, tcod.yellow)
            act_msg = Action(Actions.MESSAGE, source=self.owner, args=msg)
            results.append(act_msg)
        else:
            msg = Message(f"You pick up the {item.name}!", tcod.blue)
            act_msg = Action(Actions.MESSAGE, source=self.owner, args=msg)
            results.append(act_msg)
            act_item_add = Action(Actions.ITEM_ADDED, source=self.owner,
                                  args=item)
            results.append(act_item_add)
            self.items.append(item)

        return results

    def remove_item(self, item):
        self.items.remove(item)

    def use(self, item_entity, **kwargs):
        results = []

        item_component = item_entity.item

        if item_component.use_function is None:
            equippable_component = item_entity.equippable
            if equippable_component:
                act_equip = Action(Actions.EQUIP, source=self.owner,
                                   target=item_entity)
                results.append(act_equip)
            else:
                msg_str = "The {item_entity.name} cannot be used"
                msg = Message(msg_str, tcod.yellow)
                act_msg = Action(Actions.MESSAGE, source=self.owner, args=msg)
                results.append(act_msg)
        else:
            if (item_component.targeting and
                    not (item_component.target_x or item_component.target_y)):
                act_tgt = Action(Actions.TARGETING, source=self.owner,
                                 args=item_entity)
                results.append(act_tgt)
            else:
                kwargs = {
                        "target_x": item_component.target_x,
                        "target_y": item_component.target_y,
                        **item_component.function_kwargs, **kwargs
                        }
                use_results = item_component.use_function(self.owner, **kwargs)

                for use_result in use_results:
                    if use_result.ident == Actions.CONSUMED:
                        self.remove_item(item_entity)
                        act_con = Action(Actions.CONSUMED, source=self.owner,
                                         target=item_entity)
                        results.append(act_con)
                    elif use_result.ident == Actions.ITEM_USED:
                        act_used = Action(Actions.ITEM_USED, source=self.owner,
                                          target=item_entity)
                        results.append(act_used)
                    else:
                        results.append(use_result)

        return results

    def drop(self, item):
        results = []

        # TODO: rewrite as part of equipment slot overhaul
        if (self.owner.equipment.main_hand == item
                or self.owner.equipment.off_hand == item):
            self.owner.equipment.toggle_equip(item)

        item.x = self.owner.x
        item.y = self.owner.y
        item.item.target_x = None
        item.item.target_y = None

        self.remove_item(item)

        msg = Message(f"You dropped the {item.name}", tcod.yellow)
        act_msg = Action(Actions.MESSAGE, source=self.owner, args=msg)
        results.append(act_msg)
        act_item_drop = Action(Actions.ITEM_DROPPED, source=self.owner,
                               target=item)
        results.append(act_item_drop)

        return results
