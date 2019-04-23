#!/usr/bin/env python3
# coding: utf8


from __future__ import absolute_import

import sys

from client import YandexRadio
from player import Player


def main(gui):
    global terminate
    if len(sys.argv) > 1:
        tag = sys.argv[1]
    else:
        tag = gui.tag

    global ya_radio
    ya_radio = YandexRadio(tag)
    pl = Player(gui)

    last_track = None
    queue = []
    last_played = []

    while not pl.terminate:
        k = 0
        while len(queue) == 0:
            if k%2==0:
                queue = ya_radio.gettracks(last_track)
            else:
                queue = ya_radio.gettracks(None)


            list_to_delete = []
            for i in range(len(queue)):
                for j in range(len(last_played)):
                    if queue[i][2] == last_played[j][2]:
                        list_to_delete.append(i)
                        # print("I found the track which you hear before")

            list_to_delete = sorted(list(set(list_to_delete)),reverse=True)

            for i in range(len(list_to_delete)):
                queue.pop(list_to_delete[i])
            k+=1

        current_track = queue[0]
        gui.reset_flags()

        last_played.append(current_track)
        queue = queue[1:]
        info = current_track[2]
        dur = current_track[3]
        batch = current_track[4]
        current_track = current_track[:2]
        pl.play(ya_radio, current_track, info, batch, dur, len(last_played))
        last_track = current_track

        if gui.tag != tag:
            print("Refreshed queue and ya_radio")
            queue=[]
            last_played = []
            ya_radio.save_cookies()
            ya_radio = YandexRadio("epoch/fifties")


def close_app():
    global ya_radio
    ya_radio.save_cookies()


