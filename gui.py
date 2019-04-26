#!/usr/bin/env python3
# coding: utf8

import os
import pickle
import sys
import threading

import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QSlider

from Logger import Logger
from cursedyar import main, close_app

BUTTON_SIZE = [50, 40]
BUTTON_SMALL_SIZE = [20, 20]
BUTTON_SMALL_MARGIN = [5, 10]  # from [top,left/right]
BUTTON_MARGIN = 55
WINDOW_SIZE = [400, 250]

_N_BUTTONS = 3
_TOTAL = BUTTON_SIZE[0] * _N_BUTTONS + BUTTON_MARGIN * (_N_BUTTONS - 1)


class Gui(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.log = Logger()
        self.is_playing = False
        self.is_repeated = False
        self.is_saved = False
        self.is_liked = False
        self.is_shuffle = False

        self.album_cover = QLabel(self)
        self.label_artist = QLabel(self)
        self.label_title = QtWidgets.QLabel(self)
        self.label_start_time = QtWidgets.QLabel(self)
        self.label_finish_time = QtWidgets.QLabel(self)
        self.slider_timeline = QSlider(Qt.Horizontal, self)
        self.button_prev = QtWidgets.QPushButton(self)
        self.button_pause = QtWidgets.QPushButton(self)
        self.button_next = QtWidgets.QPushButton(self)
        self.button_dislike = QtWidgets.QPushButton(self)
        self.button_save = QtWidgets.QPushButton(self)
        self.button_share = QtWidgets.QPushButton(self)
        self.button_like = QtWidgets.QPushButton(self)
        self.combo_tag = QtWidgets.QComboBox(self)
        self.button_repeat = QtWidgets.QPushButton(self)
        self.button_shuffle = QtWidgets.QPushButton(self)
        self.slider_volume = QtWidgets.QSlider(self)
        self.button_settings = QtWidgets.QPushButton(self)

        self.tag = ""
        self.save_directory = "%s/saved/" % (os.getcwd())
        self.timeline = 0
        self.volume = 0.5

        self.prev_clicked = False
        self.pause_clicked = False
        self.next_clicked = False
        self.like_clicked = False
        self.save_clicked = False
        self.share_clicked = False
        self.dislike_clicked = False
        self.repeat_clicked = False
        self.timeline_released = False
        self.timeline_pressed = False

        self.init_gui()
        self.init_gui_geometry()
        self.load_settings()
        self.show()
        self.log.debug("GUI: Init complete")

    # inits
    def init_gui(self):
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

        self.label_title.setText("")
        # self.label_title.setWordWrap(True)
        self.label_title.setFont(font_medium)

        self.label_artist.setText("")
        self.label_artist.setFont(font_small)

        # --- Time --- #
        self.label_start_time.setText("00:00")
        self.label_start_time.setFont(font_small)

        self.label_finish_time.setText("00:00")
        self.label_finish_time.setFont(font_small)

        # --- Slider --- #
        self.slider_timeline.sliderPressed.connect(self.slider_timeline_pressed)
        self.slider_timeline.sliderReleased.connect(self.slider_timeline_released)

        # --- Music control buttons --- #
        self.button_prev.setIcon(QIcon('media/prev.svg'))
        self.button_prev.setIconSize(QSize(BUTTON_SIZE[0], BUTTON_SIZE[1]))
        self.button_prev.clicked.connect(self.button_prev_clicked)

        self.button_pause.setIcon(QIcon('media/pause.svg'))
        self.button_pause.setIconSize(QSize(BUTTON_SIZE[0] - 10, BUTTON_SIZE[1] - 10))
        self.button_pause.clicked.connect(self.button_pause_clicked)

        self.button_next.setIcon(QIcon('media/next.svg'))
        self.button_next.setIconSize(QSize(BUTTON_SIZE[0], BUTTON_SIZE[1]))
        self.button_next.clicked.connect(self.button_next_clicked)

        # --- Extra buttons --- #
        self.button_dislike.setIcon(QIcon('media/dislike.svg'))
        self.button_dislike.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_dislike.clicked.connect(self.button_dislike_clicked)

        self.button_save.setIcon(QIcon('media/save.svg'))
        self.button_save.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_save.clicked.connect(self.button_save_clicked)

        self.button_share.setIcon(QIcon('media/share.svg'))
        self.button_share.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_share.clicked.connect(self.button_share_clicked)

        self.button_like.setIcon(QIcon('media/heart.svg'))
        self.button_like.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_like.clicked.connect(self.button_like_clicked)

        # --- Extra buttons 2 --- #
        self.button_repeat.setIcon(QIcon('media/repeat.svg'))
        self.button_repeat.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_repeat.clicked.connect(self.button_repeat_clicked)

        self.button_shuffle.setIcon(QIcon('media/shuffle.svg'))
        self.button_shuffle.setIconSize(QSize(BUTTON_SMALL_SIZE[0], BUTTON_SMALL_SIZE[1]))
        self.button_shuffle.clicked.connect(self.button_shuffle_clicked)

        # --- Stations --- #
        f = open('stations.txt', 'r')

        for line in f:
            line = line.replace('\n', '').replace('\r', '').replace(' ', '')
            self.combo_tag.addItem(line)

        self.combo_tag.activated[str].connect(self.combo_tag_changed)
        self.combo_tag.setCurrentIndex(0)
        self.tag = self.combo_tag.currentText()

        # --- Volume --- #
        self.slider_volume.setMaximum(100)
        self.slider_volume.setValue(50)
        self.slider_volume.valueChanged.connect(self.slider_volume_changed)
        self.log.debug("GUI: Init GUI complete")

        # --- Settings --- #
        self.button_settings.setText("...")

    def init_gui_geometry(self):
        self.album_cover.setGeometry(15, 15, 75, 75)
        self.label_title.setGeometry(100, 25, WINDOW_SIZE[0] - 100, 27)
        self.label_artist.setGeometry(100, 60, WINDOW_SIZE[0] - 100, 20)
        self.label_start_time.setGeometry(10, WINDOW_SIZE[1] / 2 - 40, WINDOW_SIZE[0] - 40, 30)
        self.label_finish_time.setGeometry(WINDOW_SIZE[0] - 50, WINDOW_SIZE[1] / 2 - 40, WINDOW_SIZE[0] - 40, 30)

        self.slider_timeline.setGeometry(20, WINDOW_SIZE[1] / 2 - 15, WINDOW_SIZE[0] - 40, 30)

        self.button_prev.setGeometry((WINDOW_SIZE[0] - _TOTAL) / 2 + (BUTTON_MARGIN + BUTTON_SIZE[0]) * 0,
                                     WINDOW_SIZE[1] / 2 + 30,
                                     BUTTON_SIZE[0],
                                     BUTTON_SIZE[1])
        self.button_pause.setGeometry((WINDOW_SIZE[0] - _TOTAL) / 2 + (BUTTON_MARGIN + BUTTON_SIZE[0]) * 1,
                                      WINDOW_SIZE[1] / 2 + 30,
                                      BUTTON_SIZE[0],
                                      BUTTON_SIZE[1])
        self.button_next.setGeometry((WINDOW_SIZE[0] - _TOTAL) / 2 + (BUTTON_MARGIN + BUTTON_SIZE[0]) * 2,
                                     WINDOW_SIZE[1] / 2 + 30,
                                     BUTTON_SIZE[0],
                                     BUTTON_SIZE[1])
        self.button_dislike.setGeometry(
            BUTTON_SMALL_MARGIN[0] * 2 + (BUTTON_SMALL_SIZE[0] + BUTTON_SMALL_MARGIN[0]) * 0,
            WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - BUTTON_SMALL_MARGIN[1],
            BUTTON_SMALL_SIZE[0],
            BUTTON_SMALL_SIZE[1])
        self.button_save.setGeometry(BUTTON_SMALL_MARGIN[0] * 2 + (BUTTON_SMALL_SIZE[0] + BUTTON_SMALL_MARGIN[0]) * 1,
                                     WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - BUTTON_SMALL_MARGIN[1],
                                     BUTTON_SMALL_SIZE[0],
                                     BUTTON_SMALL_SIZE[1])
        self.button_share.setGeometry(BUTTON_SMALL_MARGIN[0] * 2 + (BUTTON_SMALL_SIZE[0] + BUTTON_SMALL_MARGIN[0]) * 2,
                                      WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - BUTTON_SMALL_MARGIN[1],
                                      BUTTON_SMALL_SIZE[0],
                                      BUTTON_SMALL_SIZE[1])
        self.button_like.setGeometry(BUTTON_SMALL_MARGIN[0] * 2 + (BUTTON_SMALL_SIZE[0] + BUTTON_SMALL_MARGIN[0]) * 3,
                                     WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - BUTTON_SMALL_MARGIN[1],
                                     BUTTON_SMALL_SIZE[0],
                                     BUTTON_SMALL_SIZE[1])
        self.button_repeat.setGeometry(WINDOW_SIZE[0] * 2 / 3 + (BUTTON_SMALL_MARGIN[0] + BUTTON_SMALL_SIZE[0]) * 2,
                                       WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - BUTTON_SMALL_MARGIN[1],
                                       BUTTON_SMALL_SIZE[0],
                                       BUTTON_SMALL_SIZE[1])
        self.button_shuffle.setGeometry(WINDOW_SIZE[0] * 2 / 3 + (BUTTON_SMALL_MARGIN[0] + BUTTON_SMALL_SIZE[0]) * 3,
                                        WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - BUTTON_SMALL_MARGIN[1],
                                        BUTTON_SMALL_SIZE[0],
                                        BUTTON_SMALL_SIZE[1])

        self.combo_tag.setGeometry(WINDOW_SIZE[0] - 2 * WINDOW_SIZE[0] / 3, WINDOW_SIZE[1] - BUTTON_SMALL_SIZE[1] - 10,
                                   WINDOW_SIZE[0] / 3, 20)

        self.slider_volume.setGeometry(WINDOW_SIZE[0] - 20, WINDOW_SIZE[1] - 110, 20, 80)

        self.button_settings.setGeometry(WINDOW_SIZE[0] - 15, WINDOW_SIZE[1] - 15, 15, 15)

        self.log.debug("GUI: Init GUI_geometry complete")

    # setters
    def set_song_info(self, artist, title, album_title, duration, image_link):
        self.is_playing = True
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
        self.label_finish_time.setText("%s:%s" % (m, s))

        if image_link != "no-cover":
            data = requests.get(image_link).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.album_cover.setPixmap(pixmap)
        else:
            pixmap = QPixmap()
            self.album_cover.setPixmap(pixmap)

        self.log.debug("GUI: Set song info complete: %s-%s (%s). %s sec" % (artist, title, album_title, duration))

    def set_time(self, seconds):
        self.slider_timeline.setValue(seconds)
        m, s = self._get_time_from_seconds(seconds)
        self.label_start_time.setText("%s:%s" % (m, s))

    def set_is_saved(self, status):
        self.is_saved = status

        if self.is_saved:
            self.button_save.setIcon(QIcon('media/save_active.png'))
        else:
            self.button_save.setIcon(QIcon('media/save.svg'))
        self.log.debug("GUI: set is_saved = %s" % self.is_saved)

    def set_is_liked(self, status):
        self.is_liked = status

        if self.is_liked:
            self.button_like.setIcon(QIcon('media/heart_active.png'))
        else:
            self.button_like.setIcon(QIcon('media/heart.svg'))
        self.log.debug("GUI: set is_liked = %s" % self.is_liked)

    # togglers
    def toggle_icon_paused(self):
        if self.is_playing:
            self.button_pause.setIcon(QIcon('media/play.svg'))
        else:
            self.button_pause.setIcon(QIcon('media/pause.svg'))

    def toggle_icon_shuffle(self):
        if self.is_shuffle:
            self.button_shuffle.setIcon(QIcon('media/shuffle_active.png'))
        else:
            self.button_shuffle.setIcon(QIcon('media/shuffle.svg'))

    def toggle_icon_repeated(self):
        if self.is_repeated:
            self.button_repeat.setIcon(QIcon('media/repeat_active.png'))
        else:
            self.button_repeat.setIcon(QIcon('media/repeat.svg'))

    # events
    def slider_timeline_pressed(self):
        self.timeline_pressed = True
        self.log.debug("GUI: slider_timeline_pressed")

    def slider_timeline_released(self):
        self.timeline_released = True
        self.timeline = self.slider_timeline.value()
        self.log.debug("GUI: slider_timeline_released")

    def button_prev_clicked(self):
        self.prev_clicked = True
        self.log.debug("GUI: button_prev_clicked")

    def button_pause_clicked(self):
        self.pause_clicked = True
        self.toggle_icon_paused()
        self.is_playing = not self.is_playing
        self.log.debug("GUI: button_pause_clicked")

    def button_next_clicked(self):
        self.next_clicked = True
        self.log.debug("GUI: button_next_clicked")

    def button_dislike_clicked(self):
        self.dislike_clicked = True
        self.log.debug("GUI: button_dislike_clicked")

    def button_share_clicked(self):
        self.share_clicked = True
        self.log.debug("GUI: button_share_clicked")

    def button_save_clicked(self):
        self.save_clicked = True
        self.log.debug("GUI: button_save_clicked")

    def button_like_clicked(self):
        self.like_clicked = True
        self.log.debug("GUI: button_like_clicked")

    def combo_tag_changed(self, text):
        self.tag = text
        self.log.debug("GUI: combo_tag_changed. Tag = %s" % self.tag)

    def button_repeat_clicked(self):
        self.is_repeated = not self.is_repeated
        self.toggle_icon_repeated()
        self.log.debug("GUI: button_repeat_clicked")

    def button_shuffle_clicked(self):
        self.is_shuffle = not self.is_shuffle
        self.toggle_icon_shuffle()
        self.log.debug("GUI: button_shuffle_clicked")

    def slider_volume_changed(self):
        self.volume = self.slider_volume.value() / 100
        self.log.debug("GUI: slider_volume_changed. Volume = %s" % self.volume)

    def closeEvent(self, args):
        self.save_settings()
        self.log.debug("GUI: closeEvent")

        close_app()

    # reset all flags
    def reset_flags(self):
        self.prev_clicked = False
        self.pause_clicked = False
        self.next_clicked = False
        self.like_clicked = False
        self.save_clicked = False
        self.dislike_clicked = False
        self.repeat_clicked = False
        self.share_clicked = False

        self.timeline_released = False
        self.timeline_pressed = False

        self.log.debug("GUI: reset_flags")

    # settings
    def load_settings(self):
        try:
            with open("settings.txt", 'rb') as f:
                settings = pickle.load(f)
                self.combo_tag.setCurrentText(settings['last-station'])
                self.is_shuffle = settings['shuffle']
                self.is_repeated = settings['repeat']
                self.save_directory = settings['save-directory']
                self.toggle_icon_shuffle()
                self.toggle_icon_repeated()
                self.volume = settings['volume']
                print(self.volume)
                self.slider_volume.setValue(self.volume*100)
                self.log.debug("GUI: Settings opened")
        except:
            self.log.debug("GUI: Settings not opened")

    def save_settings(self):
        # save settings
        settings = {'last-station': self.combo_tag.currentText(),
                    'shuffle': self.is_shuffle,
                    'repeat': self.is_repeated,
                    'save-directory': self.save_directory,
                    'volume': self.volume
                    }
        print(self.volume)

        with open('settings.txt', 'wb') as f:
            pickle.dump(settings, f)
        self.log.debug("GUI: Settings saved")

    @staticmethod
    def _get_time_from_seconds(seconds):
        m, s = divmod(seconds, 60)
        if m < 10:
            m = "0" + str(m)
        if s < 10:
            s = "0" + str(s)
        return m, s


if __name__ == '__main__':

    app = QApplication(sys.argv)
    g = Gui()

    # create path if doesn't exist
    saved_path = os.getcwd() + r'/saved'
    if not os.path.exists(saved_path):
        os.makedirs(saved_path)

    thread_worker = threading.Thread(target=main, args=(g,), daemon=True).start()

    sys.exit(app.exec_())
