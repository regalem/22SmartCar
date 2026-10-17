#!/usr/bin/env python3
"""M0-2：读取 YAML 配置，计算 CSV 两列数据的 Pearson 相关系数。

用法：
    python3 corr_tool.py --config config.yaml
    python3 corr_tool.py config.yaml

约定：
    - 配置文件包含 input_csv / columns.x / columns.y；
    - stdout 必有一行 "r = <数值>"；
    - 输入非法时打印可读错误到 stderr，并以退出码 2 结束。
"""

import argparse
import csv
import math
import sys
from pathlib import Path

import yaml


def pearson(xs, ys):
    """手写 Pearson 相关系数，返回 [-1, 1]。

    公式：
        r = Σ(x-x̄)(y-ȳ) / sqrt(Σ(x-x̄)² · Σ(y-ȳ)²)

    Raises:
        ValueError: 长度不一致、样本不足、或任一列方差为 0。
    """
    n = len(xs)
    # 相关系数至少需要两个点；长度不一致说明上游数据对齐出了问题。
    if n != len(ys) or n < 2:
        raise ValueError("数据点数量不足，或 x/y 长度不一致")

    # 两遍法：先求均值，再求偏差。
    # 这比 E[x²]-E[x]² 更稳，避免大数相减时的灾难性抵消。
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    # ss_x / ss_y 是离差平方和，sp 是协方差分子。
    ss_x = ss_y = sp = 0.0
    for x, y in zip(xs, ys):
        dx = x - mean_x
        dy = y - mean_y
        ss_x += dx * dx          # Σ(x - x̄)²
        ss_y += dy * dy          # Σ(y - ȳ)²
        sp += dx * dy            # Σ(x - x̄)(y - ȳ)

    # 任一列恒定 => 方差为 0 => 分母为 0 => 相关系数无定义。
    # 这里显式报错，避免输出 nan 或 ZeroDivisionError 栈。
    if ss_x == 0.0 or ss_y == 0.0:
        raise ValueError("某一列取值恒定，方差为 0，相关系数无定义")

    # 关键修复：分母必须开方。
    # 原脚本写成 sp / (ss_x * ss_y)，量纲不对，结果会趋近 0。
    r = sp / math.sqrt(ss_x * ss_y)

    # 浮点误差可能让理论上等于 1 的结果略超 1，钳位只做保护。
    return max(-1.0, min(1.0, r))


def read_config(path):
    """读取 YAML 配置，返回 (csv_path, x 列名, y 列名)。

    Raises:
        ValueError: 顶层不是映射、缺字段、字段类型不对。
    """
    # safe_load 不会构造任意 Python 对象，适合读取外部配置。
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("配置文件顶层必须是 YAML 映射")

    csv_name = cfg.get("input_csv")
    cols = cfg.get("columns")
    # 先校验结构，避免后面出现 KeyError / TypeError。
    if not isinstance(csv_name, str) or not isinstance(cols, dict):
        raise ValueError("配置缺少 input_csv 或 columns 字段")

    x_name, y_name = cols.get("x"), cols.get("y")
    if not isinstance(x_name, str) or not isinstance(y_name, str):
        raise ValueError("配置 columns 必须包含字符串 x 和 y")

    csv_path = Path(csv_name)
    if not csv_path.is_absolute():
        # 相对路径优先相对配置文件所在目录；不存在再相对当前工作目录。
        # 这样在 M0-2 目录内、仓库根目录下都能跑通。
        near_config = path.parent / csv_path
        near_cwd = Path.cwd() / csv_path
        if near_config.exists():
            csv_path = near_config
        elif near_cwd.exists():
            csv_path = near_cwd
        else:
            # 两处都不存在时保留 config 相对路径，错误信息更贴近配置。
            csv_path = near_config
    return csv_path, x_name, y_name


def read_xy(csv_path, x_name, y_name):
    """读取 CSV 指定两列，返回两个等长的 float 列表。

    Raises:
        ValueError: 文件不存在、空文件、缺列、非数值、有效点少于 2 个。
    """
    # is_file() 同时排除"不存在"和"是目录"。
    if not csv_path.is_file():
        raise ValueError(f"输入 CSV 不存在：{csv_path}")

    xs, ys = [], []
    # utf-8-sig 兼容 Windows/Excel 导出的 UTF-8 BOM；
    # newline="" 交给 csv 模块处理行尾。
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # fieldnames 为 None：空文件或没有表头。
        if reader.fieldnames is None:
            raise ValueError("CSV 为空或缺少表头")
        # 先统一校验列名，避免读到数据行才报 KeyError。
        for col in (x_name, y_name):
            if col not in reader.fieldnames:
                raise ValueError(f"CSV 缺少列：{col}")
        # 第 1 行是表头，数据从第 2 行开始，行号与编辑器一致。
        for line_no, row in enumerate(reader, start=2):
            try:
                xs.append(float(row[x_name]))
                ys.append(float(row[y_name]))
            except (TypeError, ValueError):
                # 缺列时 row[col] 是 None（TypeError）；字符串是 ValueError。
                raise ValueError(f"CSV 第 {line_no} 行不是有效数值")

    # 只有 1 个点无法定义相关系数。
    if len(xs) < 2:
        raise ValueError("有效数据点少于 2 个")
    return xs, ys


def main(argv=None):
    """命令行入口：解析参数、执行计算、统一处理错误。"""
    parser = argparse.ArgumentParser(description="计算两列数据的 Pearson 相关系数")
    # 同时支持 --config 和位置参数；--config 优先。
    parser.add_argument("config_pos", nargs="?", help="YAML 配置文件路径")
    parser.add_argument("--config", dest="config_opt", help="YAML 配置文件路径")
    args = parser.parse_args(argv)

    config_name = args.config_opt or args.config_pos
    if not config_name:
        # argparse 会打印用法并以 2 退出，不会产生 Traceback。
        parser.error("请通过 --config 或位置参数提供配置文件")

    try:
        cfg_path = Path(config_name).expanduser()
        if not cfg_path.is_file():
            raise ValueError(f"配置文件不存在：{cfg_path}")
        csv_path, x_name, y_name = read_config(cfg_path)
        xs, ys = read_xy(csv_path, x_name, y_name)
        n, mean_x = len(xs), sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        r = pearson(xs, ys)
    except Exception as exc:  # 统一收口：现场契约要求不抛 Traceback
        # 代价：会把自己的编程错误也吞掉；更严谨可自定义异常 + --debug。
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    # 验收契约：stdout 必须包含一行 "r = <数值>"。
    print(f"n = {n}")
    print(f"mean_x = {mean_x}")
    print(f"mean_y = {mean_y}")
    print(f"r = {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
