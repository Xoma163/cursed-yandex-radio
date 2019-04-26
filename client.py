#!/usr/bin/env python3
# coding: utf8

import pickle
import requests
import json
import time
from Logger import Logger

import hashlib


class YandexRadio:
    def __init__(self, tag):
        self.log = Logger()
        self.api = 'https://radio.yandex.ru/api/v2.1/handlers/'
        self.cookies_file = 'cookies.dat'
        self.tag = tag
        self.gate = self.api + 'radio/' + tag
        self.session = None
        self.auth()
        self.radiostarted = False

    def make_headers(self, add_headers, get=False):
        headers = {
            'Accept': 'application/json; q=1.0, text/*; q=0.8, */*; q=0.1',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36',
            'Origin': 'https://radio.yandex.ru/'
        }
        headers.update(add_headers)
        return headers

    def make_params(self, add_params={}, get=False):
        tmark = str(int(time.time() * 1e3))
        params = {
            'external-domain': 'radio.yandex.ru',
            'overembed': 'no',
            '__t': tmark
        }
        if not get:
            params = {'__t': tmark}
        params.update(add_params)
        return params

    def make_data(self, add_data={}):
        tmark = str(int(time.time() * 1e3))
        data = {
            'external-domain': 'radio.yandex.ru',
            'overembed': 'no',
            'sign': self.sign,
            'timestamp': tmark
        }
        data.update(add_data)
        return data

    def auth(self):
        cookies = None
        try:
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
        except:
            pass
        self.log.debug("CLIENT: Cookies = " + str(cookies))

        self.session = requests.Session()
        if cookies:
            self.session.cookies = cookies

        url = self.api + 'auth'
        headers = {'X-Retpath-Y': 'https%3A%2F%2Fradio.yandex.ru%2F'}

        resp = self.session.get(url,
                                params=self.make_params(get=True),
                                headers=self.make_headers(headers, get=True)
                                )
        self.log.debug("CLIENT: Auth")

        self.log.debug('CLIENT: Auth ' + str(resp.status_code))
        if resp.status_code != 200:
            self.log.debug('CLIENT: Auth failed: ' + resp.text)
        else:
            authdata = json.loads(resp.text)
            self.sign = authdata['csrf']

    def gettracks(self, prev=None):
        url = self.gate + '/tracks'
        params = {}
        if prev is not None:
            params['queue'] = '%d:%d' % prev
        else:
            params['queue'] = ''

        headers = {'X-Retpath-Y': 'https%3A%2F%2Fradio.yandex.ru%2F' + self.tag.replace('/', '%2F')}

        resp = self.session.get(url,
                                params=self.make_params(params, get=True),
                                headers=self.make_headers(headers, get=True)
                                )
        self.log.debug("CLIENT: Get queue")
        if resp.status_code != 200:
            self.log.debug("CLIENT: " + str(resp.text))
            self.log.debug("CLIENT: tracks: " + str(resp.text))
        d = json.loads(resp.text)
        tracks = []
        for z in d['tracks']:
            if z['type'] != 'track':
                continue
            track = z['track']
            album = track['albums'][0]
            try:
                album_cover = "http://" + album['coverUri'][:-2] + "75x75"
            except:
                album_cover = "no-cover"

            artists = ', '.join([x['name'] for x in track['artists']])
            tid = int(track['id'])
            aid = int(album['id'])
            dur = track['durationMs']
            batch = track['batchId']
            info = (track['title'], album['title'], artists, album_cover)
            tracks.append((tid, aid, info, dur, batch))
        return tracks

    def radio_started(self, tid, aid):
        if self.radiostarted:
            return
        self.radiostarted = True

        url = self.gate + '/feedback/radioStarted/%d:%d' % (tid, aid)
        data = {'from': 'radio-web-%s-direct' % self.tag.replace('/', '-')}
        headers = {'X-Retpath-Y': 'https%3A%2F%2Fradio.yandex.ru%2F' + self.tag.replace('/', '%2F')}

        r = self.session.post(url,
                              data=self.make_data(data),
                              params=self.make_params(),
                              headers=self.make_headers(headers),
                              )

        self.log.debug("CLIENT: Post radioStarted")
        if r.status_code != 202:
            self.log.debug('CLIENT: radioStarted: ' + r.text)

    def hashify(self, s):
        message = 'XGRlBW9FXlekgbPrRHuSiA' + s.replace('\r\n', '\n')

        return hashlib.md5(message.encode('ascii')).hexdigest()

    def gettrack(self, tid, aid):
        url = self.api + 'track/%d:%d/radio-web-%s-direct/download/m' % (tid, aid, self.tag.replace('/', '-'))
        headers = {'X-Retpath-Y': 'https%3A%2F%2Fradio.yandex.ru%2F' + self.tag.replace('/', '%2F')}

        resp = self.session.get(url,
                                params=self.make_params({'hq': '0', 'strm': '0'}, get=True),
                                headers=self.make_headers(headers, get=True)
                                )

        self.log.debug('CLIENT: Ask for download')
        if resp.status_code != 200:
            self.log.debug('CLIENT: Ask for download failed ' + resp.text)
        meta = json.loads(resp.text)

        self.radio_started(tid, aid)

        src = meta['src']
        resp = self.session.get(src,
                                params=self.make_params({'format': 'json'}, get=True),
                                headers=self.make_headers(headers, get=True)
                                )
        self.log.debug('CLIENT: Get track url')
        d = json.loads(resp.text)
        n = self.hashify(d['path'][1:] + d['s'])
        path = 'http://' + d['host'] + '/get-' + meta['codec'] + '/' + \
               n + '/' + d['ts'] + \
               d['path'] + '?track-id=' + str(tid) + '&play=false&'
        return path

    def started(self, tid, aid, batch):
        url = self.gate + '/feedback/trackStarted/%d:%d' % (tid, aid)
        data = {
            'from': 'radio-web-%s-direct' % self.tag.replace('/', '-'),
            'batchId': batch,
            'trackId': tid,
            'albumId': aid,
            'totalPlayed': '0.1'
        }
        headers = {'X-Retpath-Y': 'https%3A%2F%2Fradio.yandex.ru%2F' + self.tag.replace('/', '%2F')}

        r = self.session.post(url,
                              data=self.make_data(data),
                              params=self.make_params(),
                              headers=self.make_headers(headers),
                              )

        self.log.debug('CLIENT: Post trackStarted')
        if r.status_code != 202:
            self.log.debug('CLIENT: trackStarted: ' + r.text)

    def feedback(self, reason, dur, tid, aid, batch):
        url = self.gate + '/feedback/' + reason + '/%d:%d' % (tid, aid)
        data = {
            'from': 'radio-web-%s-direct' % self.tag.replace('/', '-'),
            'batchId': batch,
            'trackId': tid,
            'albumId': aid,
            'totalPlayed': str(dur)
        }
        headers = {'X-Retpath-Y': 'https%3A%2F%2Fradio.yandex.ru%2F' + self.tag.replace('/', '%2F')}

        r = self.session.post(url,
                              data=self.make_data(data),
                              params=self.make_params(),
                              headers=self.make_headers(headers),
                              )

        self.log.debug("CLIENT: " + reason + ' totalPlayed = ' + str(dur) + 's')
        self.log.debug('CLIENT: Post feedback')
        if r.status_code != 202:
            self.log.debug("CLIENT: " + reason + ': ' + r.text)

    def save_cookies(self):
        cookies = self.session.cookies
        with open(self.cookies_file, 'wb') as f:
            pickle.dump(cookies, f)
