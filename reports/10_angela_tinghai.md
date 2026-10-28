# 独立实验：张韶涵音色唱《听海》30 秒副歌

> 历史记录：本目录成品已按用户指定《不痛》重新生成覆盖。当前结果见 [指定参考重生成报告](13_requested_references.md)，以下旧数值/旧参考不代表当前成品。旧文件证据位于 `work/stage7-replaced/outputs/stage4-angela-tinghai/`。

日期：2026-10-16。用户明确指定本轮只需 30 秒副歌、两个版本，试听由用户进行；旧的周杰伦/陶喆整曲实验保留。

## 素材获取（已完成）

使用 `scripts/media.py` 完成 doctor → search → probe → download。Cookie 只读快照消费，不保存凭据或签名流地址。音频未上传。

| 用途 | 来源页面 | 页面发布者 | 原音频时长 | 下载音轨 bytes |
|---|---|---|---:|---:|
| source：张惠妹《听海》MV | https://www.bilibili.com/video/BV1Wk4y117ps/ | ForwardMusic | 316.480 s | 7,560,979 |
| target：张韶涵《遗失的美好》MV | https://www.bilibili.com/video/BV1yR4y1M7fa/ | 舒言星 | 284.416 s | 6,795,995 |

两条均为独唱歌曲页面；“官方/4K修复”是页面标题声明，不等于本轮核验了母带或修复质量。媒体许可证 unknown。完整回执在 `work/acquisition/stage4-*/receipt.json`，来源/大小/哈希见 [下载台账](downloads.md)。下载执行各约 3.4 秒；GPU 不涉及。

新补齐官方 Whisper-small 同一固定 revision 的 8 个分词器/生成配置文件，总计 4,185,900 bytes；复用已有模型权重。本地 ASR 只用于找副歌时间，不作为校对歌词或 CER 真值。来源：[官方模型文件](https://huggingface.co/openai/whisper-small/tree/973afd24965f72e36ca33b3055d56a652f456b4d)、[Transformers 4.46.3 文档](https://huggingface.co/docs/transformers/v4.46.3/en/model_doc/whisper)。审计清单 `config/whisper-asr-files.json`。

## 数据准备（已完成）

只分离显式指定的两首新素材。`scripts/separate.py` 新增成对的 `--target` / `--source`；不扫描旧艺术家的素材作为本轮输入。目录越界/跨角色/不完整选择均拒绝，隔离测试通过。

```bash
python3 scripts/separate.py --model-repo models/demucs-uvr \
  --model UVR_Demucs_Model_1 --run-id stage4-angela-tinghai-prep --device mps \
  --target data/target/stage4-target-angela-yishidemeihao.wav \
  --source data/source/stage4-source-tinghai.wav
```

模型、环境和 Mac 适配沿用已实测版本；Seed-VC SHA `51383efd921027683c89e5348211d93ff12ac2a8`。A=30步，B=50步；同参考、原调、F0=True、auto-F0=False、CFG=0.7、随机种子20261016。运行结果见后文。

分离使用 UVR Demucs 双 stem，shifts=1、overlap=0.25、segment=7、float32；完整源人声和伴奏保存在 `work/stage4-angela-tinghai-prep/separated/`。总耗时 **47.415 秒**，进程 RSS 峰值 **2,619,932,672 bytes**；独立 MPS 峰值未采样，不能把 RSS 当显存。

本地 Whisper 对源人声 75–185 秒区间进行中文识别，第一遍副歌起句所在分段为 **106.26–113.18 秒**。选取原始 MV **106–136 秒（1:46–2:16）**，人声、伴奏、原唱对照均为 44.1kHz、1,323,000 帧、精确 30 秒。歌词识别存在错字，只作为段落定位；这个片段不是整段完整副歌。完整识别结果保存在本机 `work/stage4-chorus-asr/transcript.json`。ASR 命令总耗时 24.151 秒，其中模型加载/识别 14.481 秒；结束时 MPS 已分配约 0.90 GiB、driver 1.59 GiB，为单点采样，非峰值。没有上传音频。

静音切片参数：-40 dB、最短静音 0.4s、保留 2–15s、44.1kHz 单声道 PCM16。19 个候选共 **186.549 秒（3分6.55秒）**，低于 10 分钟；未经人工确认的干净时长未知。该量可供 Seed-VC 零样本短参考选择，不足以直接当作高质量 RVC/so-vits 训练集。不额外声称已去掉混响、和声或伴奏残留。

筛选 8–15s 的片段，按 100ms 帧中 RMS>-40dB 的比例、削波比例、RMS 排序。前三段只来自张韶涵素材；两版实际都使用第一段 **204.887–219.887 秒的15秒参考**（activity=96.67%，clipping=0）。另存两段备选参考：234.887–249.887 秒、183.893–192.397 秒。本轮没有使用任何周杰伦素材/参考，也没有训练或使用第三方明星模型。

固定随机种子抽取的 5 个切片（待用户抽听）：

- [00004_168f3c2a9a.wav](../work/stage4-angela-slices/target-slices/00004_168f3c2a9a.wav)，原曲 60.289–68.613s。
- [00017_168f3c2a9a.wav](../work/stage4-angela-slices/target-slices/00017_168f3c2a9a.wav)，原曲 234.887–249.887s。
- [00016_168f3c2a9a.wav](../work/stage4-angela-slices/target-slices/00016_168f3c2a9a.wav)，原曲 219.887–234.887s。
- [00013_168f3c2a9a.wav](../work/stage4-angela-slices/target-slices/00013_168f3c2a9a.wav)，原曲 183.893–192.397s。
- [00008_168f3c2a9a.wav](../work/stage4-angela-slices/target-slices/00008_168f3c2a9a.wav)，原曲 114.066–118.003s。

切片耗时 0.899 秒，格式准备 0.794 秒，均为 CPU；manifest 保存所有输入哈希和 ffmpeg 命令。隔离测试通过：显式选择只处理本轮文件；跨角色路径、越界软链接、只给 target 不给 source 均拒绝。


### 本轮实际准备命令

以下命令原始参数/日志均在 `reports/evidence/stage4/`。复现时更换所有 run-id，避免覆盖本轮产物。

```bash
.envs/seed-vc/bin/python scripts/transcribe_local.py --input work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/vocals.wav --run-id stage4-chorus-asr --start 75 --duration 110 --device mps
python3 scripts/slice_vocals.py --input work/stage4-angela-tinghai-prep/target-vocals --run-id stage4-angela-slices
.envs/demucs/bin/python scripts/prepare_stage2_clips.py --slices work/stage4-angela-slices/target-slices --source-vocals work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/vocals.wav --source-accompaniment work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/no_vocals.wav --run-id stage4-angela-tinghai-clips --start 106 --duration 30
```

目标 vocals 单独复制到 `work/stage4-angela-tinghai-prep/target-vocals/angela-yishidemeihao.wav` 后切片；其哈希在切片 manifest 内。原唱对照按相同 106–136 秒裁切到 `source_original.wav`，精确命令在片段 manifest 内。

## 推理与混音（已完成）

复现已准备好的本轮片段（使用新的 run-id）：

```bash
python3 scripts/run_stage2_poc.py --run-id my-angela-tinghai \
  --clips work/stage4-angela-tinghai-clips \
  --evidence-dir reports/evidence/stage4 --device mps
```

此入口校验/准备独立 Seed-VC 环境 → 30/50 步生成 → 本地混音与 CAMPPlus/F0 诊断 → 离线试听页。输入/模型哈希核验、离线模式和 Python 网络连接阻断均启用。MPS 扩散/Whisper/CAMPPlus + CPU BigVGAN/RMVPE 的已验证 Mac 适配保持不变；固定源码/依赖详情沿用 [上一轮完整报告](09_full_song.md)。

### 已修复的问题

提前混音 A 版时，`mix_audio.py --run outputs/.../run.json` 使用相对路径，WAV 已写出后在 `dest.relative_to(ROOT)` 处报 ValueError，未生成回执。根因是输出路径未统一为绝对路径，不是模型推理失败。第 1 种修复即成功：函数入口统一 `Path.resolve()`。

未删除该次文件，将其保存在 `work/stage4-mix-recovery/seed-vc_A_mix_unreceipted_AI.wav` 后重新生成带回执的 A 混音。两份 SHA256 完全相同（`3c7974d26541749727ca56ddf15adafa95016411cf214680aeee3a5dd07e94fb`）。相对/绝对路径重复调用复用同一文件，不同输入仍拒绝覆盖。证据：`reports/evidence/stage4/mix-recovery.json`，日志 `logs/stage4-mix-recovery.log`。没有为此重跑模型。

`run_from_data.py` 同时补充了显式 target 选择：多份 target 未选择时在模型运行前拒绝，重复 `--target` 可选择同一歌手的多份素材；不再默认把不同轮的歌手拼成目标集。该入口总链路未再次整体执行，单独的拒绝歧义检查与实际使用的分离输入隔离均已通过。

## 本轮交付与诊断

[打开本轮同步试听页](../outputs/stage4-angela-tinghai/listen.html)；可切换两版混音、原唱同片段、源人声、转换纯人声，另可播放本轮张韶涵参考。

- A / 30步：[30秒混音](../outputs/stage4-angela-tinghai/seed-vc_A_mix_AI.wav)、[纯人声](../outputs/stage4-angela-tinghai/seed-vc_A_AI.wav)。
- B / 50步：[30秒混音](../outputs/stage4-angela-tinghai/seed-vc_B_mix_AI.wav)、[纯人声](../outputs/stage4-angela-tinghai/seed-vc_B_AI.wav)。

| 版本 | 转换耗时 | 目标 cosine | F0 r | log2-F0 r | 共同有声覆盖率 | 中位音分偏差 | 混音 LUFS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A / 30步 | 261.870s | 0.8549 | 0.9973 | 0.9969 | 78.39% | 7.39 | -15.0 |
| B / 50步 | 270.723s | 0.8567 | 0.9976 | 0.9973 | 78.43% | 7.11 | -15.2 |

MPS allocated/driver 的 0.1 秒采样峰值分别为 **3.59/5.86 GiB**，转换进程 RSS 峰值 **4.24 GiB**。这些 Apple 统一内存计数有重叠，不能相加或当成独立显存。

A 含初次加载，B 复用模型；因此不能把两者耗时差直接解释为步数的纯成本。转换外层总耗时 **536.818 秒（约8分57秒）**，评测/混音总耗时 **8.364 秒**，评测 RSS 峰值 **2.09 GiB**。两版各完成 3 个内部块，末块只约 0.43 秒；它们最终接成一个 30 秒混音。

CAMPPlus 与目标参考的源人声基线为 **0.5311**，A/B 结果约 0.8549/0.8567；这个编码器同时用于条件生成，不能当作独立音色验证，也不是“85%像”。F0 为 RMVPE、起点对齐、共同有声帧，不作 DTW 或偏移寻优；两版八度误差代理值均为 0，不证明所有音符/咬字无误。**CER=N/A**：本次虽用 ASR 找了副歌，但没有独立校对歌词，不能把 ASR 自身当答案。

主观音色相似度、咬字、高音破音：**PENDING，由用户试听**。建议先听 A，按同时间点比较 B；两版只改变扩散步数，B 不是更强的“张韶涵程度”，指标上的小差距不支持先验判定更好听。暂不自动扩成长版或增加其他模型。

可对照本片段 0–8 秒、10–20 秒、22–30 秒（原 MV 106–114、116–126、128–136 秒），分别检查起句音色、咬字/长音、后段和内部拼接。它们是定位于副歌的试听窗口，没有据此声称某窗必为全曲最高音或最快咬字。

### 最终检查

- 两版混音均 44.1kHz 双声道、1,323,000 帧、精确30秒；干声均29.988571秒，混音只在末尾补504个采样（11.43ms），没有变速。混音峰值 A≈0.8611、B≈0.8632，无接近满幅采样；干声接近满幅比例约0.00287%/0.00219%，是否可闻失真待听辨。
- 本轮输入/输出哈希核验、非静音/有限值、A/B并非同一文件、本地页面文件存在均通过；先前19个文件及本轮原始素材哈希未变。
- 35项约束测试通过。混音相对路径、回执复用与防覆盖实测通过；试听页播放位置切换/快速切换/暂停恢复/参考互斥通过 mock DOM 检查，未声称真实浏览器或主观听音验收。
- 已完成本次独立测试，模型无失败；仅发生并修复一次混音路径错误。新模型推理过程中网络连接被阻断。其他开源路线未在这一轮执行，不算失败。

验证命令：

```bash
.envs/demucs/bin/python scripts/validate_full_song.py \
  --run outputs/stage4-angela-tinghai/run.json --duration 30 \
  --evidence reports/evidence/stage4/final-validation.json
node work/stage4-ui-preview/check-player.cjs
python3 -m unittest discover -s tests -v
```

验证报告/日志保存在 `reports/evidence/stage4/`、`logs/stage4-*`。文件输出不覆盖；上述 evidence 已存在时需换新路径。

## 空间与预算快照

| 目录 | 逻辑大小 bytes | MiB |
|---|---:|---:|
| work/ | 1,865,943,333 | 1779.50 |
| outputs/ | 224,634,701 | 214.23 |
| data/ | 269,176,604 | 256.71 |
| models/ | 2,657,889,680 | 2534.76 |
| .envs/ | 1,468,540,105 | 1400.51 |
| .cache/ | 500,514,155 | 477.33 |
| reports/ | 90,599,353 | 86.40 |

累计预算计入 **3,425,764,607/30,000,000,000 bytes**，本轮新增 **18,542,874 bytes**，未结束预留0；逐文件台账见 [downloads.md](downloads.md)。可用磁盘 **101,916,311,552 bytes**。为逻辑文件量快照，后续报告写入会略变。未删除任何原始/中间/成品文件；未commit、push或发布。
