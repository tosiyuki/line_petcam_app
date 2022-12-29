#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import time
import requests
import threading

import cv2


class LineProvider:
    def __init__(self):
        self._interval = 300
        self.timer_thread = threading.Thread(target=self.interval_timer, daemon=True)

        self._load_config()

        self._api = "https://notify-api.line.me/api/notify"
        self._header = {"Authorization" : "Bearer "+ self.token}
        self._send_time = time.time()
        self._send_flag = True
        self._end_flag = False
        self.IMAGE_PATH = "tmp/send_image.png"

        self.timer_thread.start()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value * 60

    def _load_config(self):
        with open("config/setting.json") as f:
            setting_data = json.load(f)
            self.token = setting_data["token"]

    def send_message(self, image):
        if self._send_flag is False:
            return

        cv2.imwrite(self.IMAGE_PATH, image)

        message = '現在の様子です。'
        payload = {"message" :  message}
        files = {"imageFile": open(self.IMAGE_PATH, "rb")}

        post = requests.post(self._api, headers = self._header, params=payload, files=files)
        self._send_time = time.time()
        self._send_flag = False

    def interval_timer(self):
        while True:
            if (time.time() - self._send_time) > self._interval:
                self._send_flag = True

            time.sleep(1)