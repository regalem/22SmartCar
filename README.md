# 22SmartCar ｜ 创意组一轮考核 · M0 阶段提交

本仓库是 **22SmartCar 创意组一轮考核（round1）M0 阶段** 的提交，按官方目录结构组织：

```text
round1/M0/
├── M0-1/   开发环境搭建 + 现场环境验收记录
├── M0-2/   首个代码工具：corr_tool.py（Pearson 相关系数）
├── M0-3/   代码排查：sensor_analyzer.py 问题报告
└── M0-4/   Mini 项目实战：TaskScheduler
```

提交方式：按模块分部分提交（M0-1 → M0-4），每个模块一次提交。

## 环境要求

- Ubuntu 22.04（VMware 虚拟机 / WSL2 / 物理机三选一），ROS2 Humble
- Python 3.10+；M0-2、M0-4 需要 `PyYAML`（见各自 `requirements.txt`）
- M0-2 / M0-3 / M0-4 是纯终端程序，不依赖 ROS 与 GUI

## 各模块说明与运行方式

### M0-1 ｜ 开发环境搭建

主环境为 VMware Workstation 中的 Ubuntu 22.04.5 LTS：ROS2 Humble、Python 虚拟环境（conda/venv）、
C/C++ 工具链（gcc/g++/make/cmake）、VS Code 及 Remote 插件、Git 与远程登录工具均已配置，
踩坑记录见 `round1/M0/M0-1/README.md`。

本模块自带官方现场验收脚本：

```bash
cd round1/M0/M0-1
bash check_env.sh          # 只做检查
bash check_env.sh --fix    # 检查并给出修复提示
```

2026-10-02 在 VMware + Ubuntu 22.04.5 实测：`PASS=30 FAIL=0 WARN=2`。

### M0-2 ｜ 首个代码工具

把官方原始脚本 `legacy_corr.py` 重构为可维护的命令行工具 `corr_tool.py`：
读取 YAML 配置与 CSV 数据，**手写**计算两列数据的 Pearson 相关系数。

```bash
cd round1/M0/M0-2
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 corr_tool.py --config config.yaml    # 位置参数写法：python3 corr_tool.py config.yaml
python3 -m unittest discover -s tests -v     # 单元测试
```

主要修复：Pearson 公式分母漏开方（`dx * dy` → `sqrt(ss_x * ss_y)`）、缺少异常处理与
`__main__` 入口保护、错误信息不可读等，详见 `round1/M0/M0-2/README.md`。

### M0-3 ｜ 代码排查：问题报告

保留官方原文件名 `sensor_analyzer.py`，按调试顺序定位 **8 处缺陷**，
逐条给出「现象 / 原因 / 修复」，并记录修复顺序之间的依赖关系。

```bash
cd round1/M0/M0-3
python3 sensor_analyzer.py --input sensor_data.csv --output cleaned_data.csv
python3 sensor_analyzer.py        # 默认输入 sensor_data.csv，输出 cleaned_data.csv
```

实测结果：`mean = 50.4315`、`std = 18.5033`、剔除 3 条、剩余 57 条。

### M0-4 ｜ Mini 项目实战：TaskScheduler

命令行任务调度模拟器：拓扑排序按依赖顺序执行、失败重试（≤3 次尝试）、
超时立即终止、控制台彩色实时日志，并输出 `report.json`。

```bash
cd round1/M0/M0-4
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 scheduler.py --config tasks_demo.yaml --timeout 15 --report report.json --seed 42
python3 scheduler.py --config tasks_demo.json --timeout 15 --report report.json --seed 0
python3 -m unittest discover -s tests -v
```

`report.json` 结构：`timeout` / `total_duration` / `tasks[]`。更多运行示例见 `round1/M0/M0-4/README.md`。

## 文档

每个模块目录下都有独立的 `README.md`，包含任务说明、实现思路、参数说明、
运行示例与踩坑/缺陷记录。