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
import glob

# Constants
OUTPUT_PATH = '/Users/toranosuke/Desktop/screen_shot_path'
TARGET_IMGS_PATH = './target_imgs_ds'
VIDEO_DURATION_MIN = 60
# スクショ撮るのに約0.4s, 保存に0.8~0.9s,　全体で約1.5sかかると思った方が良い
INTERVAL_SEC = 5  # INTERVAL_SEC should be largeer than 1.5s.
THSH_DIFF_HASH_VAL = 5
THSH_TARGET_HASH_VAL = 3

# Queue
img_q = queue.Queue()

# スクリーンショットを撮る
def take_screenshot():
    video_start_time = datetime.datetime.now()
    index = -1

    # ビデオ時間以内でスクリーンショットを撮影し続ける
    while (datetime.datetime.now() - video_start_time).seconds <= VIDEO_DURATION_MIN * 60:
        start_t = time.perf_counter()
        # 撮影
        ss = pyautogui.screenshot()
        # 保存
        index = index + 1
        img_path = f'{OUTPUT_PATH}/{index}.png'
        ss.save(img_path)
        # キューへの登録
        img_q.put(img_path)

        end_t = time.perf_counter()
        print(f'SHOT! {index}')
        wait_time = INTERVAL_SEC - (end_t - start_t)
        time.sleep(wait_time if wait_time > 0 else 0.01)

    # 番兵を挿入
    img_q.put('last')

# 画像の類似度により、画像を削除する
def exclude_similar_imgs():
    # 保存対象画像のハッシュ値を取得
    target_img_hash = calc_target_imgs_hash(TARGET_IMGS_PATH)

    last_img_path = -1
    last_img_hash = -1
    while True:
        if img_q.qsize() > 0:
            img_path = img_q.get()

            # 番兵に到達したら、関数を終了する
            if img_path == 'last':
                break

            # 1枚目の画像の時
            if last_img_path == -1:
                last_img_path = img_path
                last_img_hash = imagehash.dhash_vertical(
                    Image.open(last_img_path))
                continue

            # 保存対象の画像でない時
            if abs(imagehash.colorhash(Image.open(img_path)) - target_img_hash) > THSH_TARGET_HASH_VAL:
                print(f'[not target img]{img_path}')
                os.remove(img_path)
                continue

            # 直前の画像とハッシュ値を比較し、類似画像を削除する
            img_hash = imagehash.dhash_vertical(Image.open(img_path))
            if abs(img_hash - last_img_hash) > THSH_DIFF_HASH_VAL:
                # 異なる画像の場合
                print(
                    f'[diff img]{img_path}, {last_img_hash}, hash diff: {abs(img_hash - last_img_hash)}')
                last_img_path = img_path
                last_img_hash = img_hash
            else:
                # 類似画像の場合
                print(
                    f'[similar img]{img_path}, {last_img_path}, hash diff: {abs(img_hash - last_img_hash)}')
                os.remove(img_path)

        time.sleep(INTERVAL_SEC / 2)

def calc_target_imgs_hash(path):
    file_list = glob.glob(f'{path}/*.*')
    dec_hashes = []

    img_hash = imagehash.colorhash(Image.open(file_list[0]))

    # for file_path in file_list:
    #     file_hash = imagehash.colorhash(Image.open(file_path))
    #     # ハッシュ値を文字列に変換し、10進数にさらに変換する
    #     dec_hash = int(str(file_hash), 16)
    #     dec_hashes.append(dec_hash)

    # # 10進数ハッシュ値の平均を求める
    # dec_hash_mean = int(sum(dec_hashes) / len(dec_hashes))
    # # 16進数文字列に変換
    # hex_hash_str = hex(dec_hash_mean)
    # print(type(hex_hash_str))
    # # ImageHashに変換
    # img_hash = imagehash.hex_to_hash(hex_hash_str)

    return img_hash

def main():
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    future_list = []
    with futures.ThreadPoolExecutor() as executor:
        future_take_ss = executor.submit(take_screenshot)
        future_list.append(future_take_ss)
        future_exclude_similar_imgs = executor.submit(exclude_similar_imgs)
        future_list.append(future_exclude_similar_imgs)

        _ = futures.as_completed(fs=future_list)

    print('Complete!')


if __name__ == '__main__':
    main()
