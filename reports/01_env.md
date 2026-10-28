# 01 本机环境

日期：2026-10-16；原始探测 [environment.json](evidence/environment.json)，本机 MPS 实测 [mps-probe.json](evidence/mps-probe.json)，沙箱对照 [mps-probe-sandbox.json](evidence/mps-probe-sandbox.json)。

状态：`ENV_CHECKED`。本机有可用 MPS；没有 NVIDIA/CUDA。不能把张量测试通过当成任一歌声模型可用。

| 项目 | 实测结果 |
|---|---|
| OS | macOS 15.6 / 24G84，arm64 |
| CPU | Apple M4 Pro，14 核（10 性能 + 4 能效）；sysctl 物理/逻辑各 14 |
| 内存 | 51,539,607,552 bytes = 48 GiB 统一内存 |
| GPU | Apple M4 Pro，20 核；Metal Supported |
| 独立显存/驱动/CUDA | 独立显存不适用；驱动随 macOS，未读取独立版本；CUDA 不适用 |
| 可用磁盘（初始） | 120,371,425,280 bytes，约 112.1 GiB；下载后见总报告 |
| 默认 Python | 3.14.5，不用于旧音频项目 |
| 已有 Python | 3.10.20、3.12.13；当前独立实验环境使用 3.10.20 |
| uv / conda | uv 0.12.5；conda 未找到 |
| git | 2.35.1；本仓库已初始化 main，无提交/远端 |
| ffmpeg / ffprobe | 8.1.1，已有 `/opt/homebrew/bin/` 安装；本次未全局安装 |

## MPS 验证

核心环境 `.envs/seed-vc/`：PyTorch 2.14.1 + NumPy 1.26.4 + SciPy 1.13.1 + SoundFile 0.12.1 及锁定依赖。这里只安装 Seed-VC 准备所需核心，不含完整 Seed-VC 包/源码/模型；新 PyTorch 与旧 Seed 代码的 API 兼容性尚未验证。

沙箱内 `is_built=True`、`is_available=False`；切换到已授权的本机执行上下文后 `is_available=True`，512×512 FP32 矩阵乘通过，结果全部 finite。测试执行约 0.326 秒（不含 Python 导入）；末端 MPS allocated=2,097,152 bytes，driver allocated=8,880,128 bytes。**这是微型张量测试结束时内存，不是模型峰值显存。**

## 关键命令

```bash
sw_vers
sysctl -n hw.memsize hw.physicalcpu hw.logicalcpu
system_profiler SPDisplaysDataType
python3 scripts/env_check.py
/opt/homebrew/bin/python3.10 -m venv .envs/seed-vc
/opt/homebrew/bin/python3.10 -m venv .envs/demucs
.envs/seed-vc/bin/python scripts/mps_probe.py
python3 scripts/bootstrap.py seed-vc-core
python3 scripts/bootstrap.py demucs
```

`env_check.py` 不采集序列号/硬件 UUID。需要本机 MPS 权限时使用相同小型只读/张量探测，不改系统设置。conda 缺失不阻塞，已有 Python + venv 足够；没有下载新解释器。

## 判断与遗留

- 最适合先做 Seed-VC 官方 Mac 分支的零样本短片段 SVC。训练型次选 Applio，其他老模型单独适配。
- Demucs CPU 前处理环境可用；模型权重尚未下载，真实分离/MPS 推理未验证。
- NVIDIA-only 或依赖 CUDA kernel 的步骤不能照搬；需要上游 CPU/MPS 路线或标记跳过，不能远程上传替代。
- 环境探测命令耗时见原始 JSON 各项 `elapsed_seconds`；安装各阶段日志见 04 报告。没有模型训练/推理峰值资源数据。
