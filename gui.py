#!/usr/bin/env python3
# coding: utf8

import os
import sys
import threading

import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QSlider

from cursedyar import main, close_app

BUTTON_SIZE = [50, 40]
BUTTON_SMALL_SIZE = [20, 20]
BUTTON_MARGIN = 55
WINDOW_SIZE = [400, 250]

_N_BUTTONS = 3
_TOTAL = BUTTON_SIZE[0] * _N_BUTTONS + BUTTON_MARGIN * (_N_BUTTONS - 1)
START_POS = (WINDOW_SIZE[0] - _TOTAL) / 2

thread_worker = None


class Gui(QMainWindow):
    def __init__(self):

        super(QMainWindow, self).__init__()

        self.label_artist = QLabel(self)
        self.label_title = QtWidgets.QLabel(self)
        self.slider_timeline = QSlider(Qt.Horizontal, self)
        self.button_prev = QtWidgets.QPushButton(self)
        self.button_pause = QtWidgets.QPushButton(self)
        self.button_next = QtWidgets.QPushButton(self)
        self.button_dislike = QtWidgets.QPushButton(self)
        self.button_save = QtWidgets.QPushButton(self)
        self.button_share = QtWidgets.QPushButton(self)
        self.button_like = QtWidgets.QPushButton(self)
        self.label_duration_0 = QtWidgets.QLabel(self)
        self.label_duration_1 = QtWidgets.QLabel(self)
        self.slider_volume = QtWidgets.QSlider(self)
        self.album_cover = QLabel(self)
        self.button_repeat = QtWidgets.QPushButton(self)
        self.button_shuffle = QtWidgets.QPushButton(self)
        self.combo_tag = QtWidgets.QComboBox(self)

        self.is_playing = False
        self.is_repeated = False
        self.is_saved = False
        self.is_liked = False
        self.is_shuffle = False
        self.tag = ""

        self.prev_clicked = False
        self.pause_clicked = False
        self.next_clicked = False
        self.like_clicked = False
        self.save_clicked = False
        self.share_clicked = False
        self.dislike_clicked = False
        self.timeline_changed = False

        self.last_timeline_value = 0
        self.timeline = 0
        self.volume = 0.5

        self.init_GUI()
        self.show()

    def set_song_info(self, artist, title, album_title, duration, image_link):
        self.label_artist.setText("%s (%s)" % (artist, album_title))
        self.label_title.setText(title)
        self.slider_timeline.setMaximum(duration)

        filename = "%s/saved/%s - %s.mp3" % (os.getcwd(), artist, title)
        if os.path.isfile(filename):
            self.set_is_saved(True)
        else:
            self.set_is_saved(False)

        # ToDo: Возможно ли сделать проверку на лайкнуто?
        self.set_is_liked(False)

        m, s = self._get_time_from_seconds(duration)
        self.label_duration_1.setText("%s:%s" % (m, s))

        data = requests.get(image_link).content
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.album_cover.setPixmap(pixmap)

    def set_time(self, seconds):
        self.last_timeline_value = seconds
        self.slider_timeline.setValue(seconds)
        m, s = self._get_time_from_seconds(seconds)
        self.label_duration_0.setText("%s:%s" % (m, s))

    @staticmethod
    def _get_time_from_seconds(seconds):
        m, s = divmod(seconds, 60)
        if m < 10:
            m = "0" + str(m)
        if s < 10:
            s = "0" + str(s)
        return m, s

    def set_is_saved(self, status):
        self.is_saved = status

        if self.is_saved:
            self.button_save.setIcon(QIcon('media/save_active.png'))
        else:
            self.button_save.setIcon(QIcon('media/save.svg'))

    def set_is_liked(self, status):
        self.is_liked = status

        if self.is_liked:
            self.button_like.setIcon(QIcon('media/heart_active.png'))
        else:
            self.button_like.setIcon(QIcon('media/heart.svg'))

    def button_prev_clicked(self):
        self.prev_clicked = True

    def button_pause_clicked(self):
        self.pause_clicked = True

        self.is_playing = not self.is_playing
        if self.is_playing:
            self.button_pause.setIcon(QIcon('media/play.svg'))
        else:
            self.button_pause.setIcon(QIcon('media/pause.svg'))

    def button_next_clicked(self):
        self.next_clicked = True

    def button_like_clicked(self):
        self.like_clicked = True

    def button_save_clicked(self):
        self.save_clicked = True

    def button_share_clicked(self):
        self.share_clicked = True

    def button_dislike_clicked(self):
        self.dislike_clicked = True

    def button_repeat_clicked(self):
        self.is_repeated = not self.is_repeated

        if self.is_repeated:
            self.button_repeat.setIcon(QIcon('media/repeat_active.png'))
        else:
            self.button_repeat.setIcon(QIcon('media/repeat.svg'))

    def button_shuffle_clicked(self):
        self.is_shuffle = not self.is_shuffle
        if self.is_shuffle:
            self.button_shuffle.setIcon(QIcon('media/shuffle_active.png'))
        else:
            self.button_shuffle.setIcon(QIcon('media/shuffle.svg'))

    def reset_flags(self):
        self.prev_clicked = False
        self.pause_clicked = False
        self.next_clicked = False
        self.like_clicked = False
        self.save_clicked = False
        self.dislike_clicked = False
        self.timeline_changed = False
        self.repeat_clicked = False
        self.share_clicked = False

    def slider_timeline_changed(self):
        # TODO: Сделай что-нибудь поадекватнее.
        #  Проблема в том, что при обновлении текущей продолжительности трека эта фигофина срабатывает.
        #  Этот костыль фиксит проблему, типа, если на секундочку дельта, то не срабатываем.
        #  Хотя, не такой уж и костыль, видали похуже
        delta_time = 1  # sec
        if self.slider_timeline.value() > self.last_timeline_value + delta_time or self.slider_timeline.value() < self.last_timeline_value - delta_time:
            self.timeline_changed = True
            self.timeline = self.slider_timeline.value()

    def slider_volume_changed(self):
        self.volume = self.slider_volume.value() / 100

    def combo_tag_changed(self, text):
        self.tag = text

    def closeEvent(self, args):
        close_app()

    def init_GUI(self):
        self.setWindowTitle("radio.yandex")
        self.setFixedSize(WINDOW_SIZE[0], WINDOW_SIZE[1])

        # --- Fonts --- #
        font_big = QFont()
        font_big.setFamily("Arial")
        font_big.setPointSize(26)

        font_medium = QFont()
        font_medium.setFamily("Arial")
        font_medium.setPointSize(18)

        font_small = QFont()
        font_small.setFamily("Arial")
        font_small.setPointSize(13)

        # --- Song info labels ---#
        self.album_cover.setGeometry(15, 15, 75, 75)

        self.label_title.setText("")
        # self.label_title.setWordWrap(True)
        self.label_title.setFont(font_medium)
        self.label_title.setGeometry(100, 25, WINDOW_SIZE[0] - 100, 27)

        self.label_artist.setText("")
        self.label_artist.setFont(font_small)
        self.label_artist.setGeometry(100, 60, WINDOW_SIZE[0] - 100, 20)

        # --- Time --- #
        self.label_duration_0.setText("00:00")
        self.label_duration_0.setFont(font_small)
        self.label_duration_0.setGeometry(10, 95, WINDOW_SIZE[0] - 40, 30)

        self.label_duration_1.setText("00:00")
        self.label_duration_1.setFont(font_small)
        self.label_duration_1.setGeometry(WINDOW_SIZE[0] - 50, 95, WINDOW_SIZE[0] - 40, 30)

        # --- Slider --- #
        self.slider_timeline.setGeometry(20, 115, WINDOW_SIZE[0] - 40, 30)
        self.slider_timeline.valueChanged.connect(self.slider_timeline_changed)

        # --- Music control buttons --- #
        self.button_prev.setIcon(QIcon('media/prev.svg'))
        self.button_prev.setIconSize(QSize(BUTTON_SIZE[0], BUTTON_SIZE[1]))
        self.button_prev.setGeometry(START_POS + (BUTTON_MARGIN + BUTTON_SIZE[0]) * 0, 150, BUTTON_SIZE[0],
                                     BUTTON_SIZE[1])
        self.button_prev.clicked.connect(self.button_prev_clicked)

        self.button_pause.setIcon(QIcon('media/pause.svg'))
        self.button_pause.setIconSize(QSize(BUTTON_SIZE[0] - 10, BUTTON_SIZE[1] - 10))
        self.button_pause.setGeometry(START_POS + (BUTTON_MARGIN + BUTTON_SIZE[0]) * 1, 150, BUTTON_SIZE[0],
                                      BUTTON_SIZE[1])
        self.button_pause.clicked.connect(self.button_pause_clicked)

        self.button_next.setIcon(QIcon('media/next.svg'))
        self.button_next.setIconSize(QSize(BUTTON_SIZE[0], BUTTON_SIZE[1]))
        self.button_next.setGeometry(START_POS + (BUTTON_MARGIN + BUTTON_SIZE[0]) * 2, 150, BUTTON_SIZE[0],
                                     BUTTON_SIZE[1])
        self.button_next.clicked.connect(self.button_next_clicked)

        # --- Extra buttons --- #
        self.button_dislike.setIcon(QIcon('media/dislike.svg'))
        self.button_dislike.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_dislike.setGeometry(30 + (10 + 20) * 0, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                        BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1])
        self.button_dislike.clicked.connect(self.button_dislike_clicked)

        self.button_save.setIcon(QIcon('media/save.svg'))
        self.button_save.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_save.setGeometry(30 + (10 + 20) * 1, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                     BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1])
        self.button_save.clicked.connect(self.button_save_clicked)

        self.button_share.setIcon(QIcon('media/share.svg'))
        self.button_share.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_share.setGeometry(30 + (10 + 20) * 2, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                      BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1])
        self.button_share.clicked.connect(self.button_share_clicked)


        self.button_like.setIcon(QIcon('media/heart.svg'))
        self.button_like.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_like.setGeometry(30 + (10 + 20) * 3, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                     BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1])
        self.button_like.clicked.connect(self.button_like_clicked)

        # --- Extra buttons 2 --- #
        self.button_repeat.setIcon(QIcon('media/repeat.svg'))
        self.button_repeat.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_repeat.setGeometry(WINDOW_SIZE[0] - 70, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                       BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1])
        self.button_repeat.clicked.connect(self.button_repeat_clicked)

        self.button_shuffle.setIcon(QIcon('media/shuffle.svg'))
        self.button_shuffle.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_shuffle.setGeometry(WINDOW_SIZE[0] - 40, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                        BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1])
        self.button_shuffle.clicked.connect(self.button_shuffle_clicked)

        self.combo_tag.setGeometry(WINDOW_SIZE[0] - 2 * WINDOW_SIZE[0] / 3 + 20, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                   WINDOW_SIZE[0] / 3, 20)

        f = open('stations.txt', 'r')

        for line in f:
            line = line.replace('\n', '').replace('\r', '').replace(' ', '')
            self.combo_tag.addItem(line)

        self.combo_tag.activated[str].connect(self.combo_tag_changed)
        self.combo_tag.setCurrentIndex(0)
        self.tag = self.combo_tag.currentText()

        # --- Volume --- #
        self.slider_volume.setGeometry(WINDOW_SIZE[0] - 20, WINDOW_SIZE[1] - 100, 20, 80)
        self.slider_volume.setMaximum(100)
        self.slider_volume.setValue(50)
        self.slider_volume.valueChanged.connect(self.slider_volume_changed)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    g = Gui()

    # create path if doesn't exist
    saved_path = os.getcwd() + r'/saved'
    if not os.path.exists(saved_path):
        os.makedirs(saved_path)

    thread_worker = threading.Thread(target=main, args=(g,), daemon=True).start()

    sys.exit(app.exec_())
