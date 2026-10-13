#!/usr/bin/env python3
"""M0-2：读取 YAML 配置，计算两列数据的 Pearson 相关系数。"""

import csv
from pathlib import Path

import yaml


def read_config(path):
    """读取 YAML，返回 (csv 文件名, x 列名, y 列名)。"""
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    return cfg["input_csv"], cfg["columns"]["x"], cfg["columns"]["y"]


def read_xy(csv_path, x_name, y_name):
    """读取 CSV 的两列，转成 float 列表。"""
    xs, ys = [], []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            xs.append(float(row[x_name]))
            ys.append(float(row[y_name]))
    return xs, ys


def pearson(xs, ys):
    """手写 Pearson 相关系数。"""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    ss_x = ss_y = sp = 0.0
    for x, y in zip(xs, ys):
        dx = x - mean_x
        dy = y - mean_y
        ss_x += dx * dx
        ss_y += dy * dy
        sp += dx * dy

    return sp / (ss_x * ss_y)


if __name__ == "__main__":
    cfg_path = Path("config.yaml")
    csv_name, x_name, y_name = read_config(cfg_path)
    xs, ys = read_xy(cfg_path.parent / csv_name, x_name, y_name)

    print("n =", len(xs))
    print("mean_x =", sum(xs) / len(xs))
    print("mean_y =", sum(ys) / len(ys))
    print("r =", pearson(xs, ys))
