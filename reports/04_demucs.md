# 04 Demucs 前处理准备

## 2026-10-16 下一阶段实测更新

状态升级为 **LOCAL_SEPARATION_PASSED**。此前仅环境可用的记录保留在下方，当前已找到 UVR 官方 GitHub 模型发布入口，未使用被排除的默认 FBA 下载域。

- 上游 UVR commit：`a5f88453bfb2b38b05a965bcf67727243e0cbf19`。README 说明 UVR 自训模型和 MIT 署名要求；官方程序 `gui_data/constants.py` 指向 `TRvlvr/model_repo/releases/download/all_public_uvr_models/`。
- 本次模型：`UVR_Demucs_Model_1.yaml`，`ebf34a2db.th`（167,390,507 bytes），84M 左右参数，44.1kHz，vocals/non_vocals 两路。许可证按 UVR README 对模型的声明记录，文件 SHA256 见共享台账。
- `.envs/demucs` 仍为 torch/torchaudio 2.2.2；本机 MPS 成功加载并完成 5 秒冒烟，以及 target/source 两首完整分离。
- 冒烟 10.140 秒；完整两曲 34.429 秒，包括进程启动与文件读写；完整分离子树峰值 RSS 2,030,551,040 bytes。没有采样 MPS 内存峰值，不将 RSS 当独立显存。
- 结果：`work/stage2-full/separated/manifest.json`，包含完整人声与伴奏目录和逐曲命令。质量仍待抽听，不将分离成功当作去混响/和声已完成。

复现：

```bash
python3 scripts/download.py config/separation-models.json
python3 scripts/separate.py --model-repo models/demucs-uvr --model UVR_Demucs_Model_1 --run-id <新批次> --device mps
```

详见 [短片段阶段记录](08_short_poc.md) 和 [数据报告](03_data.md)。

## 初始化阶段记录（历史快照）

日期：2026-10-16。状态：`ENV_READY / BLOCKED_DOWNLOAD / BLOCKED_DATA`。

## 来源和安装结果

调研 GitHub SHA：`e976d93ecc3865e5757426930257e200846a520a`。实际安装 **官方 PyPI demucs==4.0.1 发布包**，不是声称构建此 HEAD。PyPI 发布包的 `requirements_minimal.txt` 仅约束 `torchaudio>=0.8`，GitHub HEAD 另有 `<2.1`；此差异已检查，最终采用发布包允许的 Torch/Torchaudio 2.2.2 配对。

- 独立环境 `.envs/demucs/`，Python 3.10.20；未改系统 Python/FFmpeg。
- `pip check` 通过，`python -m demucs --help` 通过。
- 核心版本：demucs 4.0.1、torch 2.2.2、torchaudio 2.2.2、numpy 1.26.4、soundfile 0.12.1；完整锁定 [demucs.lock.txt](../config/demucs.lock.txt)。
- demucs、dora-search、julius、antlr4 的官方 PyPI sdist 已记录 SHA256/许可证；读取 setup/requirements 后使用预装构建依赖 **离线**构建。未安装 dev extras、未执行 requirements 中 dev 的 git URL。

## 实际命令

```bash
/opt/homebrew/bin/python3.10 -m venv .envs/demucs
python3 scripts/download.py config/demucs-downloads.json
python3 scripts/download.py config/demucs-fix-downloads.json
python3 scripts/bootstrap.py demucs
```

bootstrap 校验本地分发文件哈希，再用 `pip install --no-index --no-build-isolation --find-links .cache/wheels` 安装锁定依赖，随后检查依赖和 CLI。安装命令、构建产物 SHA256 见 `logs/demucs-install-attempt1.log`、`logs/demucs-install-attempt2.log`。

## 问题与修复

初始 Torch 2.0.1 的 PyPI 文件名是 arm64，包内部 WHEEL 却标为 x86_64。CPU 张量和 Demucs CLI 可以导入，但新版 pip check 报“不支持本平台”。没有伪造/修改 WHEEL 标签，也没有关闭检查。

修复第 1 种：在 PyPI 4.0.1 发布包允许的依赖范围内换成成对的 Torch/Torchaudio 2.2.2；内部 WHEEL 为 arm64，pip check 与 CLI 均通过。未达到 3 种修复上限。

## 模型与后续运行

默认模型下载 URL 为 `https://dl.fbaipublicfiles.com/demucs/`（已核对 installed `demucs/pretrained.py`），没有擅自扩展用户列举的官方下载入口。没有下载模型、没有做实际人声分离。

`scripts/separate.py` 只接受 `models/` 内、已登记到下载台账且哈希匹配的本地模型文件，强制 Demucs `--repo`，避免首次自动拉取；缺模型/素材即退出。预设 CPU、two-stems=vocals、shifts=1、overlap=0.25、segment=7s、float32 WAV、jobs=1；后续需模型适配和真实分离验证，再考虑 MPS。

```bash
python3 scripts/separate.py --model-repo models/<已审计模型目录> --run-id <新批次> --device cpu
```

这是一条待模型与素材到位后使用的命令，**并非本轮跑通的人声分离结果**。

耗时：首轮依赖安装 8.40 秒（不含下载），修复安装+检查约 9.223 秒；下载与完整人工审查未单独计时。模型显存/统一内存峰值 N/A；没有听感评估。遗留：可接受来源的分离权重（或转 UVR5 官方 HF 路线）、真实歌曲、人声质量抽听。
