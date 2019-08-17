# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 21:05:32 2019

@author: theoldestnoob
"""

from equipment_slots import EquipmentSlots
from action import Action, Actions


# TODO: rewrite to use list of equipment slots, properties iterate over list
class Equipment:
    def __init__(self, main_hand=None, off_hand=None):
        self.main_hand = main_hand
        self.off_hand = off_hand

    @property
    def max_hp_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.max_hp_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.max_hp_bonus

        return bonus

    @property
    def power_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.power_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.power_bonus

        return bonus

    @property
    def defense_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.defense_bonus
        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.defense_bonus

        return bonus

    # TODO: one if/else to do all of this instead of separate for each slot
    def toggle_equip(self, equippable_entity):
        results = []

        slot = equippable_entity.equippable.slot

        # per slot
        if slot == EquipmentSlots.MAIN_HAND:
            # if you have the item equipped, dequip it
            if self.main_hand == equippable_entity:
                self.main_hand = None
                act_deqp = Action(Actions.DEQUIPPED, source=self.owner,
                                  target=equippable_entity)
                results.append(act_deqp)
            # otherwise, dequip what you have and equip the item
            else:
                if self.main_hand:
                    act_deqp = Action(Actions.DEQUIPPED, source=self.owner,
                                      target=self.main_hand)
                    results.append(act_deqp)
                self.main_hand = equippable_entity
                act_eqp = Action(Actions.EQUIPPED, source=self.owner,
                                 target=equippable_entity)
                results.append(act_eqp)

        elif slot == EquipmentSlots.OFF_HAND:
            # if you have the item equipped, dequip it
            if self.off_hand == equippable_entity:
                self.off_hand = None
                act_deqp = Action(Actions.DEQUIPPED, source=self.owner,
                                  target=equippable_entity)
                results.append(act_deqp)
            # otherwise, dequip what you have and equip the item
            else:
                if self.off_hand:
                    act_deqp = Action(Actions.DEQUIPPED, source=self.owner,
                                      target=self.off_hand)
                    results.append(act_deqp)
                self.off_hand = equippable_entity
                act_eqp = Action(Actions.EQUIPPED, source=self.owner,
                                 target=equippable_entity)
                results.append(act_eqp)

        return results
