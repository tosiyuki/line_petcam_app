#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import copy

import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import cv2

from coco_classes import COCO_CLASSES
from yolox_onnx import YoloxONNX
from line_provider import LineProvider


class PetCam:
    def __init__(self):
        self.yolox = YoloxONNX(
            model_path='models/yolox_nano.onnx',
            input_shape=(416,416),
            class_score_th=0.3,
            nms_th=0.45,
            nms_score_th=0.1,
        )
        self.line_provider = LineProvider()

        self._interval_dict = {"1min": 1, "5min": 5, "10min": 10, "30min": 30, "1hour": 60, "2hour": 120}

        self.init_gui()

    def init_gui(self):
        st.title("PetCam")
        webrtc_streamer(key="example", video_frame_callback=self.image_callback)

        col1, col2 = st.columns(2)
        with col1:
            self.interval_box = st.selectbox(
                "Select send interval",
                self._interval_dict.keys(),
                index=1,
                on_change=self.change_interval
            )
        with col2:
            self.animal_box = st.radio(
                "Select animal type",
                ("bird", "cat", "dog"),
                index=1
            )

        # 各モジュールに設定を送信する
        self.change_interval()

    def image_callback(self, frame):
        image = frame.to_ndarray(format="bgr24")

        # YOLOXで物体検出してみる
        bboxes, scores, class_ids = self.yolox.inference(image)
        yolox_image = self._view_yolo_image(image, bboxes, scores, class_ids)

        # ラベルを見て画像を送信するかを判断する
        for class_id in class_ids:
            if self.animal_box != COCO_CLASSES[int(class_id)]:
                continue
            else:
                self.line_provider.send_message(image)
                break

        return av.VideoFrame.from_ndarray(yolox_image, format="bgr24")

    def _view_yolo_image(self, image, bboxes, scores, class_ids):
        # 推論結果の可視化
        yolox_image = copy.deepcopy(image)

        for bbox, score, class_id in zip(bboxes, scores, class_ids):
            if self.animal_box != COCO_CLASSES[int(class_id)]:
                continue

            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

            # バウンディングボックス
            yolox_image = cv2.rectangle(
                yolox_image,
                (x1, y1),
                (x2, y2),
                (255, 255, 255),
                thickness=1,
            )

            # クラスID、スコア
            score = '%.2f' % score
            text = '%s:%s' % (COCO_CLASSES[int(class_id)], score)
            yolox_image = cv2.putText(
                yolox_image,
                text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                thickness=1,
            )

        return yolox_image

    def change_interval(self):
        self.line_provider.interval = self._interval_dict[self.interval_box]

def main():
    petcam = PetCam()


if __name__ == "__main__":
    main()
    