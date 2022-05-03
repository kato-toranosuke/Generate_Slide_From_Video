#!/usr/bin/env python3
# coding: utf-8

import pyautogui
import datetime
from concurrent import futures
import os
import time
from PIL import Image
import imagehash
import queue

# Constants
OUTPUT_PATH = '/Users/toranosuke/Desktop/screen_shot_path'
VIDEO_DURATION_MIN = 1
INTERVAL_SEC = 3
THSH_DIFF_HASH_VAL = 10

# Queue
img_q = queue.Queue()

# スクリーンショットを撮る
def take_screenshot():
    video_start_time = datetime.datetime.now()
    index = -1

    # ビデオ時間以内でスクリーンショットを撮影し続ける
    while (datetime.datetime.now() - video_start_time).seconds <= VIDEO_DURATION_MIN * 60:
        # 撮影
        ss = pyautogui.screenshot()
        # 保存
        index = index + 1
        img_path = f'{OUTPUT_PATH}/{index}.png'
        ss.save(img_path)
        # キューへの登録
        img_q.put(img_path)

        print(f'SHOT! {index}')
        time.sleep(INTERVAL_SEC)

    # 番兵を挿入
    img_q.put('last')

# 画像の類似度により、画像を削除する
def exclude_similar_imgs():
    last_img_path = -1
    while True:
        if img_q.qsize() > 0:
            img_path = img_q.get()

            # 番兵に到達したら、関数を終了する
            if img_path == 'last':
                break

            # 1枚目の画像の時
            if last_img_path == -1:
                last_img_path = img_path
                continue

            # 直前の画像とハッシュ値を比較し、類似画像を削除する
            last_img_hash = imagehash.average_hash(Image.open(last_img_path))
            img_hash = imagehash.average_hash(Image.open(img_path))
            if abs(img_hash - last_img_hash) > THSH_DIFF_HASH_VAL:
                # 異なる画像の場合
                last_img_path = img_path

                print(
                    f'[diff img]{img_path}, {last_img_hash}, hash diff: {abs(img_hash - last_img_hash)}')
            else:
                # 類似画像の場合
                os.remove(img_path)
                print(
                    f'[similar img]{img_path}, {last_img_path}, hash diff: {abs(img_hash - last_img_hash)}')
        time.sleep(INTERVAL_SEC / 2)


def main():
    future_list = []
    # with futures.ThreadPoolExecutor(max_workers=4) as executor:
    with futures.ThreadPoolExecutor() as executor:
        future_take_ss = executor.submit(take_screenshot)
        future_list.append(future_take_ss)
        future_exclude_similar_imgs = executor.submit(exclude_similar_imgs)
        future_list.append(future_exclude_similar_imgs)

        _ = futures.as_completed(fs=future_list)

    print('Complete!')


if __name__ == '__main__':
    main()
