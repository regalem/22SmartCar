#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sensor_analyzer.py —— 传感器数据清洗与统计工具

流程：
    1. 读取 CSV（列：time, value）；
    2. 计算 value 的均值与总体标准差；
    3. 按 |value - mean| > 2 * std 双向剔除离群值；
    4. 写出 time,value 两列到 cleaned_data.csv；
    5. 打印统计摘要。

用法：
    python3 sensor_analyzer.py --input sensor_data.csv --output cleaned_data.csv
    python3 sensor_analyzer.py   # 默认读写当前目录

约定：
    - 输入非法时打印可读错误到 stderr，退出码 2；
    - 输出文件默认写在当前工作目录，不写死绝对路径。
"""

import argparse
import csv
import math
import os
import sys

TIME_COL = "time"
VALUE_COL = "value"


def load_data(path, time_col=TIME_COL, value_col=VALUE_COL):
    """读取 CSV，返回 (times, values) 两个等长列表。

    Raises:
        ValueError: 文件不存在、为空、缺列、行内有非数值、没有数据行。
    """
    # exists() 先给出更友好的错误；目录会在 open() 时由 OSError 兜住。
    if not os.path.exists(path):
        raise ValueError("输入文件不存在: %s" % path)

    times = []
    values = []
    # 注意：这里用 utf-8；如果现场 CSV 带 BOM，应改为 utf-8-sig，
    # 否则首列名会变成 "\\ufefftime"，被误判为缺列。
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # fieldnames 为 None：空文件或没有表头。
        if reader.fieldnames is None:
            raise ValueError("输入文件为空: %s" % path)
        # 一次性报出所有缺失列，并打印实际表头，方便定位。
        missing = [c for c in (time_col, value_col) if c not in reader.fieldnames]
        if missing:
            raise ValueError(
                "输入文件缺少列 %s（实际表头: %s）"
                % (", ".join(missing), ",".join(reader.fieldnames))
            )
        # 第 1 行是表头，数据从第 2 行开始，行号与编辑器一致。
        for lineno, row in enumerate(reader, start=2):
            try:
                t = float(row[time_col])
                v = float(row[value_col])
            except (TypeError, ValueError):
                # 缺列 -> None（TypeError）；字符串 -> ValueError。
                raise ValueError("第 %d 行存在非数值内容: %r" % (lineno, row))
            times.append(t)
            values.append(v)

    # 只有表头没有数据行时，后面的 mean/std 没有意义。
    if not values:
        raise ValueError("输入文件没有数据行: %s" % path)
    return times, values


def mean_and_std(values):
    """返回 (mean, std)，std 为总体标准差（除以 n）。"""
    n = len(values)
    mean = sum(values) / n
    # 总体方差：Σ(v-mean)² / n；再开方得到标准差。
    # 题面把给定数据当作全部数据，所以用 n 而不是 n-1。
    variance = sum((v - mean) ** 2 for v in values) / n
    return mean, math.sqrt(variance)


def remove_outliers(times, values, mean, std, k=2.0):
    """按 |value - mean| > k*std 剔除离群值，返回 (times, values, n_removed)。"""
    kept_times = []
    kept_values = []
    # abs 同时覆盖上界（v > mean+k*std）和下界（v < mean-k*std）。
    # 构造新列表而不是原地 remove，避免边遍历边改列表导致跳过元素。
    for t, v in zip(times, values):
        if abs(v - mean) <= k * std:
            kept_times.append(t)
            kept_values.append(v)
    # 同时保留 time，保证写出的两列仍然对齐。
    return kept_times, kept_values, len(values) - len(kept_values)


def write_cleaned(path, times, values):
    """把清洗后的 (time, value) 写出为 CSV。"""
    # newline="" 让 csv 模块自己写 \\r\\n，避免 Windows 下多出空行。
    # with 保证异常时文件也能关闭。
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([TIME_COL, VALUE_COL])
        for t, v in zip(times, values):
            writer.writerow([t, v])


def parse_args(argv=None):
    """解析命令行参数：默认读写当前目录，也支持显式 --input/--output。"""
    parser = argparse.ArgumentParser(description="传感器数据清洗与统计（M0-3）")
    parser.add_argument(
        "--input",
        default="sensor_data.csv",
        help="输入 CSV 路径（默认：当前目录 sensor_data.csv）",
    )
    parser.add_argument(
        "--output",
        default="cleaned_data.csv",
        help="输出 CSV 路径（默认：当前目录 cleaned_data.csv）",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """命令行入口：读取 → 统计 → 清洗 → 写文件，异常统一收口。"""
    args = parse_args(argv)
    print("=== 传感器数据分析 ===")
    try:
        times, values = load_data(args.input)
        mean, std = mean_and_std(values)
        kept_times, kept_values, n_removed = remove_outliers(times, values, mean, std)
        write_cleaned(args.output, kept_times, kept_values)
    except (ValueError, OSError) as exc:
        # 只捕获可预期的输入/文件错误，不吞 KeyboardInterrupt 等。
        print("错误: %s" % exc, file=sys.stderr)
        return 2

    print("共读取 %d 条数据" % len(values))
    print("均值 mean = %.4f" % mean)
    print("标准差 std = %.4f" % std)
    print("剔除离群值 %d 条" % n_removed)
    print("清洗后剩余 %d 条" % len(kept_values))
    print("已保存到 %s" % os.path.abspath(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
