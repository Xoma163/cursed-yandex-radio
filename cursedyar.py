#!/usr/bin/env python3
# coding: utf8

from __future__ import absolute_import

import random
import sys

from client import YandexRadio
from player import Player

MAX_LAST_PLAYED_LEN = 50
MAX_TRACKS_SHUFFLE = 2


def main(gui):
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

    track_index = 0
    prev_index = -2

    # ToDo: Можно придумать что-нибудь более логичное
    while not pl.terminate:
        # No memory overflow
        if len(last_played) > MAX_LAST_PLAYED_LEN:
            last_played.pop(0)

        k = 0
        # No repeat tracks
        while len(queue) == 0:
            if k % 2 == 0:
                queue = ya_radio.gettracks(last_track)
            else:
                queue = ya_radio.gettracks(None)

            list_to_delete = []
            for i in range(len(queue)):
                for j in range(len(last_played)):
                    if queue[i][2] == last_played[j][2]:
                        list_to_delete.append(i)

            if len(list_to_delete) > 0:
                print("#Tracks to delete: %s" % (len(list_to_delete)))

            list_to_delete = sorted(list(set(list_to_delete)), reverse=True)

            for i in range(len(list_to_delete)):
                queue.pop(list_to_delete[i])
            k += 1

        # prev track
        if gui.prev_clicked:
            current_track = last_played[prev_index]
            if -prev_index < len(last_played):  # Чтобы не заходил дальше того, чего нет
                prev_index -= 1
        else:
            track_index += 1
            prev_index = -2
            current_track = queue[0]
            last_played.append(current_track)

        gui.reset_flags()

        queue = queue[1:]
        info = current_track[2]
        dur = current_track[3]
        batch = current_track[4]
        current_track = current_track[:2]

        print("#Track №" + str(track_index))
        print("#queue.length = " + str(len(queue)))

        pl.play(ya_radio, current_track, info, batch, dur, len(last_played))
        last_track = current_track

        # Shuffle
        if gui.is_shuffle and track_index >= MAX_TRACKS_SHUFFLE:
            track_index = 0
            # ToDo: Это можно сделать умнее, узнай как
            rnd = random.randrange(0, gui.combo_tag.count(), 1)
            while rnd == gui.combo_tag.currentIndex():
                rnd = random.randrange(0, gui.combo_tag.count(), 1)
            gui.combo_tag.setCurrentIndex(rnd)

        # Tag changed
        if gui.tag != tag:
            prev_index = -2

            track_index = 0
            tag = gui.tag
            queue = []
            last_played = []
            ya_radio.save_cookies()
            ya_radio = YandexRadio(tag)


def close_app():
    global ya_radio
    ya_radio.save_cookies()
