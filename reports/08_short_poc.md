# 20 秒歌声转换阶段记录

日期：2026-10-16。用户已授权依据上一阶段结论执行。目标：Seed-VC V1 歌声/F0 路线，约 20 秒源人声，两组参数输出及伴奏混音。本轮已完成，状态 `POC_PASSED_20S`；完整歌曲和多项目比较尚未执行。

## 已完成

- 官方 Seed-VC 源码固定到 `51383efd921027683c89e5348211d93ff12ac2a8`。GitHub API 限流后改用官方 Git blobless/sparse 检出；仅选源码与配置，排除所有示例音频和仓库内模型二进制。67 个文件、528,355 展开字节，逐文件 SHA256 已登记。Git 传输压缩量/索引元数据未单独计量，台账明确采用展开源码量。
- UVR 上游为 `a5f88453bfb2b38b05a965bcf67727243e0cbf19`。README 指向官方程序；其 `gui_data/constants.py` 明确配置 `TRvlvr/model_repo` GitHub Releases 为普通公开模型下载源。选择 UVR 自训的 `UVR_Demucs_Model_1.yaml` + `ebf34a2db.th`，约 167.4 MB，2 个 stem：vocals/non_vocals、44.1kHz。遵循 README 对 UVR 模型的 MIT 署名说明，不使用不明镜像或 FBA 域名。
- 本地 MPS 5 秒分离冒烟通过，耗时 10.140 秒；两首完整歌曲分离通过，耗时 34.429 秒（包括启动和读写）。进程子树峰值 RSS 2,030,551,040 bytes；不是独立显存峰值，MPS 专用峰值本次未采样。
- target：《晴天》单曲音频候选，来源 Bilibili `BV1BZbSzZEGT`，269.5 秒，上传者 VV音乐局。音频文件为 96kHz/双声道，但无法仅凭封装或标题确认原版无损；保留来源限制。
- source：《爱很简单》MV 音频，复用本仓库已审计 Bilibili `BV1wjBjYDEgF` 的 262.063729 秒文件。搜索到的其他候选含 demo、现场或串烧，未替换为这些版本。原始母带/修复过程未独立核实。
- 完整人声和伴奏保留于 `work/stage2-full/separated/`。target 静音切片候选约 221.046 秒，少于 10 分钟，人工确认干净总时长仍未知；可以开始零样本短参考测试，不能据此声称训练型数据充足。
- 源片段固定为 60–80 秒；选取 3 段 8–15 秒参考候选，依据非静音覆盖率、无削波与 RMS。这是机器筛选，不证明没有和声、混响或伴奏残留。当前输入清单 `work/stage2-clips/manifest.json`。

## 环境与模型准备

Seed-VC CLI 使用固定 README 的命令行推理依赖子集，跳过未调用的 Web UI、实时 GUI、FunASR/ModelScope 框架。PyTorch/Torchaudio 2.5.1 + Torchvision 0.20.1 替代 Mac requirements 中未锁定的 nightly，以匹配官方 PyPI ARM wheel；不是宣称原样安装完整 GUI requirements。其余原先锁定的 NumPy/Librosa/Transformers/DAC 等版本沿用上游约束。

`scripts/resolve_pypi.py` 使用目标环境内 pip 自带的解析器，只读取官方 PyPI JSON 元数据；依赖正文随后交给审计下载器。最终解析 99 个分发文件，239,781,809 bytes，含 argbind/randomname 两个需审阅并离线构建的 sdist。最终成功标准是离线安装、pip check、真实推理，不以解析成功冒充部署成功。

Seed 主模型及 RMVPE、CAMPPlus、BigVGAN、Whisper 共 9 个文件，2,486,313,240 bytes，最大约 967 MB。来源分别为项目指定的官方 HF 仓库，固定 revision，模型卡和清单保存在 `reports/evidence/stage2/` 与 `config/seed-vc-models.json`。没有下载训练优化器、其他版本生成器或明星模型。

离线运行入口 `scripts/seed_vc_local.py` 核验全部模型/上游源码哈希，启用离线标记并拒绝 Python Internet socket。Mac 适配显式记录：Whisper FP32、FP32 下不启用 autocast、光谱特征与 RMVPE 在 CPU 计算、F0 转 float32；实测 BigVGAN 在 MPS 报 grouped conv_transpose1d 通道限制，第一种修复改为 CPU 后通过；扩散、Whisper 和说话人条件模型保留 MPS。上游源码保持不变，适配后的入口副本写入本批 work/runtime；A/B 复用已加载模型、固定随机种子。

## 关键命令与证据

```bash
python3 scripts/download.py config/separation-models.json
python3 scripts/separate.py --model-repo models/demucs-uvr \
  --model UVR_Demucs_Model_1 --run-id stage2-full --device mps
python3 scripts/slice_vocals.py --input work/stage2-target-vocals --run-id stage2-slices
.envs/seed-vc/bin/python scripts/resolve_pypi.py config/seed-vc-cli.in \
  --output config/seed-vc-cli-downloads.json --lock config/seed-vc-cli.lock.txt \
  --evidence https://github.com/Plachtaa/seed-vc/blob/51383efd921027683c89e5348211d93ff12ac2a8/requirements-mac.txt
python3 scripts/download.py config/seed-vc-models.json
python3 scripts/download.py config/seed-vc-cli-downloads.json
```

分离计时：[5秒冒烟](evidence/stage2/stage2-separate-mps-smoke.json)、[完整分离](evidence/stage2/stage2-separate-full.json)。日志：`logs/stage2-*.log`、`logs/separate-stage2-full.log`。输入来源：[input-selection.json](evidence/stage2/input-selection.json)。

## 正式结果

- CLI 99 项依赖经审计下载、离线安装，`pip check` 和实际模块导入通过。旧 randomname sdist 漏报 fire 的问题修复 1 次，详见 [failures.md](failures.md)。
- 首次 5 秒 MPS 转换卡在 BigVGAN；固定 CPU 声码器后，5 秒/2 步冒烟总耗时 24.545 秒，退出 0。该冒烟接近满幅比例较高，只用于连通性测试，不是推荐试听成品。
- 正式 20 秒 A/B：F0=True、auto-F0=False、移调 0、length=1、CFG=0.7、FP32、seed=20261016，仅步数不同。A=30 步，115.778 秒，含模型加载；B=50 步，152.543 秒，复用已加载模型。两组进程总耗时 271.656 秒；不是实时转换。外层和模型内计时口径分别保留。
- 两条干人声均为 44.1kHz/单声道/19.992381 秒，有限、非静音、输入哈希未改变；对应 2 条混音为双声道 20 秒。尾部补 336 个采样（7.62ms），没有拉伸时间轴。混音按源人声 RMS 匹配增益（本次下限 0.5），最终整体峰值缩放至约 0.98。
- 纯人声 A/B 接近满幅（abs>=0.999）的比例分别为 0.0811%/0.0422%；上游声码器包含硬限幅，降低混音电平不能恢复已发生的削波，需抽听是否可闻。
- 0.1 秒采样的 MPS allocated 峰值 3,798,095,360 bytes（3.54GiB），driver 峰值 6,304,301,056 bytes（5.87GiB）；进程 RSS 峰值 4,624,023,552 bytes（4.31GiB）。三者不可相加，Apple 统一内存不是独立显存，采样可能漏过瞬时峰值。
- 本地评测/混音进程 5.834 秒，核心评测 2.839 秒；CPU RSS 峰值 1,999,798,272 bytes。评测指标和限制见 [05_eval.md](05_eval.md)。

### 试听与文件

[打开本地 A/B 试听页](../outputs/stage2-seed20/listen.html)。页面无外部资源，包含源人声、目标参考与 4 个成品播放器。

| 版本 | 干人声 | 对应伴奏混音 |
|---|---|---|
| A / 30 步 | [seed-vc_A_AI.wav](../outputs/stage2-seed20/seed-vc_A_AI.wav) | [seed-vc_A_mix_AI.wav](../outputs/stage2-seed20/seed-vc_A_mix_AI.wav) |
| B / 50 步 | [seed-vc_B_AI.wav](../outputs/stage2-seed20/seed-vc_B_AI.wav) | [seed-vc_B_mix_AI.wav](../outputs/stage2-seed20/seed-vc_B_mix_AI.wav) |

### 一键复现

```bash
python3 scripts/run_stage2_poc.py --run-id new-seed20 --device mps
```

以上入口本轮实跑通过；依次离线建/校验环境、转换 A/B、评测与混音。需当前固定源码、已审计缓存/权重和 `work/stage2-clips/`。若换素材，从 data 起步的新编排入口为 `python3 scripts/run_from_data.py --run-id new-song --start 60 --duration 20 --device mps`；各底层阶段已实跑，总编排只做参数/语法检查，未重复整条重算。

固定源码恢复方式（当前 vendor 已存在，不要重复覆盖）：

```bash
git clone --depth 1 --filter=blob:none --sparse --no-checkout https://github.com/Plachtaa/seed-vc.git vendor/seed-vc
git -C vendor/seed-vc sparse-checkout set --no-cone /inference.py /hf_utils.py /requirements-mac.txt /requirements.txt /README.md /LICENSE '/modules/**' '/configs/**'
git -C vendor/seed-vc checkout 51383efd921027683c89e5348211d93ff12ac2a8
```

未来远端 HEAD 改变时，depth=1 可能不含该 SHA，需从同一官方仓库 fetch 指定 SHA，再 checkout；仍排除示例音频和模型二进制。下载正文按 `scripts/download.py` 台账策略执行；没有自动下载权重或联网处理音频。

### 证据与遗留

- [转换进程](evidence/stage2/stage2-seed20-convert.json)、[评测进程](evidence/stage2/stage2-seed20-evaluate.json)、[完整参数与输出哈希](../outputs/stage2-seed20/run.json)、[指标 JSON](../outputs/stage2-seed20/evaluation.json)。
- [安装版本](evidence/stage2/seed-vc-installed.txt)、模型配置 `config/seed-vc-models.json`、依赖 `config/seed-vc-cli.lock.txt`；官方 README/requirements 来自固定上游 SHA。最终 34 项约束测试通过，所有脚本语法检查通过。
- 加载 checkpoint 时上游 strict=False 警告已核对：全部有效学习参数名称和形状均匹配；被跳过的是未启用的 Wavenet 分支和源码重建的位置 buffer。审计保存在 `work/stage2-seed20/runtime/checkpoint-audit.json`。
- 无实际抽听，音色相似度、咬字、高音破音的主观判断均待用户评价。目标参考未经人工洁净度审核，只有单曲、单参考，不是跨歌泛化或训练效果证据。
- 没有独立校对歌词，CER=N/A，未用 ASR 自己生成的歌词充当真值。全曲、另一项目和副歌/高音/快速咬字专项对照留待后续阶段。
