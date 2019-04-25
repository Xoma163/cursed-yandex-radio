# cursed-yandex-radio
A simple Yandex Radio client with gui interface

### REQUIREMENTS
1. pip install -r requirements.txt


### USAGE
1. `$ python gui.py <tag>`
where `tag` is like `genre/rock`, `mood/calm`, `activity/party`, `user/username` etc.
### OR
1. Add your stations into `stations.txt`

2.`$ python gui.py`

Work only on unix-based systems.
Python3 required

Requires `pygst` v1.0 with mp3 decoder and http source plugins (for Debian/Ubuntu `python-gst1.0` (or `python3-gst1.0`), `gstreamer1.0-plugins-good`).