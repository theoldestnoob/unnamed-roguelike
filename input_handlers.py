# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 21:35:02 2019

@author: theoldestnoob
"""

import tcod.event


class InputHandler(tcod.event.EventDispatch):

    def __init__(self):
        self._actionq = []

    def ev_quit(self, event):
        self._actionq.append({"exit": True})

    def ev_keydown(self, event):
        # first check for mapped modified keys
        if (event.mod & tcod.event.KMOD_LALT
                and event.sym in in_keymap_lalt.keys()):
            self._actionq.append(in_keymap_lalt[event.sym])
        # if no meaningful modified keys, push the mapped action to our queue
        elif event.sym in in_keymap_nomod.keys():
            self._actionq.append(in_keymap_nomod[event.sym])

    def get_action(self):
        if self._actionq:
            return self._actionq.pop(0)
        else:
            return {}

    def clear_actionq(self):
        self._actionq.clear()


in_keymap_nomod = {
        tcod.event.K_UP: {"move": (0, -1)},
        tcod.event.K_DOWN: {"move": (0, 1)},
        tcod.event.K_LEFT: {"move": (-1, 0)},
        tcod.event.K_RIGHT: {"move": (1, 0)},
        tcod.event.K_ESCAPE: {"exit": True}
        }

in_keymap_lalt = {
        tcod.event.K_RETURN: {"fullscreen": True}
        }
