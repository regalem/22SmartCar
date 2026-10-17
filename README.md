# 22SmartCar ｜ 创意组一轮考核 · M0 阶段提交

本仓库是 **22SmartCar 创意组一轮考核（round1）M0 阶段** 的提交，按官方目录结构组织：

```text
round1/M0/
├── M0-1/   开发环境搭建 + 现场环境验收记录
├── M0-2/   首个代码工具：corr_tool.py（Pearson 相关系数）
├── M0-3/   代码排查：sensor_analyzer.py 问题报告
└── M0-4/   Mini 项目实战：TaskScheduler
```

提交方式：按模块与调试步骤分批提交（M0-1 → M0-4；M0-2、M0-3 按“发现问题 → 修复 → 测试 → 文档”拆成多次提交，具体见各模块 README 的提交记录与 `git log`）。

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

## AI 使用与本人自主修改

本仓库的初稿由 AI（Codex）辅助生成。**本人独立定位了各模块的大部分问题，并在 AI 初稿基础上自主修改了约 1~2 处代码**；其余部分由本人逐行阅读、实际运行和测试验证，并非直接提交 AI 输出。

- **M0-1**：本人完成了 VMware / Ubuntu 22.04 / ROS2 Humble / conda / VS Code / Git 的实际安装配置，运行 `check_env.sh` 完成验收；踩坑记录来自本机真实报错与处理过程，AI 仅协助整理文字与命令。
- **M0-2**：本人独立定位了 Pearson 公式漏开方、零方差、缺列/非数值等问题，并对约 1~2 处代码做了自主修改；实际跑通 5 类异常输入，确认退出码为 2 且无 `Traceback`。
- **M0-3**：本人独立定位了大部分缺陷（共 8 处），并对其中约 1~2 处做了自主修改；其余修复逐条复现、核对，并用独立实现对拍 `mean/std` 与清洗结果。
- **M0-4**：本人独立定位了拓扑排序、失败传播、超时判定与报告结构等大部分问题，并对其中约 1~2 处做了自主修改；其余部分通过单元测试与示例运行验证。

更细的记录见各模块 README 的「AI 使用与本人自主修改说明」。

## 文档

每个模块目录下都有独立的 `README.md`，包含任务说明、实现思路、参数说明、
运行示例、踩坑/缺陷记录，以及「AI 使用与本人自主修改说明」。