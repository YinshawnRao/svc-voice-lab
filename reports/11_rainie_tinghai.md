# 独立实验：杨丞琳音色唱《听海》30秒副歌

> 历史记录：本目录成品已按用户指定《雨爱》重新生成覆盖。当前结果见 [指定参考重生成报告](13_requested_references.md)，以下旧数值/旧参考不代表当前成品。旧文件证据位于 `work/stage7-replaced/outputs/stage5-rainie-tinghai/`。

日期：2026-10-16。用户要求再做一轮、目标换成杨丞琳，延续上轮30秒副歌A30/B50。原唱、原曲区间106–136秒、F0、调高、种子与上一轮一致；目标参考单独准备，旧文件保留。

## 素材获取（已完成）

`scripts/media.py` doctor → search → probe → download。首选页面 [索尼音乐中国《雨爱》](https://www.bilibili.com/video/BV1YJ411x7C6/) 搜索/探测成功，但实际音轨请求返回404。改为同一首MV的[另一公开来源](https://www.bilibili.com/video/BV1ep4y1Y772/)，发布者zyl2012_音乐无限。页面“修复”声明不视为已验证音频母带质量，媒体许可证unknown。

第一次分离因在检查失败回执前就启动，没有输入音频。上游Demucs对此打印缺文件而退出0，**未生成stem、不计作分离成功**。将按下载回执核验文件存在/大小/哈希再执行，并检查实际输出文件。证据 `reports/evidence/stage5/initial-preparation-audit.json`、`logs/stage5-target-separation.log`，失败记录均保留。

源歌曲复用上一轮的张惠妹《听海》：[公开来源](https://www.bilibili.com/video/BV1Wk4y117ps/)，已定位副歌1:46–2:16。没有重复下载源歌曲，也无需重复ASR；后续将验证本轮源人声/伴奏/原唱片段与上轮哈希一致。

## 固定模型与参数

沿用Seed-VC V1 44.1kHz歌声转换，2026-10-16重读已审计源码README，SHA `51383efd921027683c89e5348211d93ff12ac2a8`。唱歌F0=True、auto-F0=False、半音偏移0、CFG0.7、length1、FP32、种子20261016；A30步、B50步。MPS扩散/Whisper/CAMPPlus + CPU BigVGAN/RMVPE；本轮不新增权重/依赖，不训练明星模型。模型与输入哈希验证、离线标记、推理Python网络阻断沿用已实测入口。


实际下载成功：[杨丞琳《雨爱》MV](https://www.bilibili.com/video/BV1ep4y1Y772/)，页面发布者 zyl2012_音乐无限。下载AAC音轨5,908,077 bytes，派生原始WAV为48kHz双声道、283.328秒、54,399,054 bytes，SHA256 `4573e10ed19819fd821fd70b98203f04d97b43875e67d0af1f3efc4a507ad78c`。成功下载耗时6.223秒，首次404尝试耗时1.594秒；无GPU使用。完整回执 `work/acquisition/stage5-target-rainie-yuai-alt/receipt.json`，逐文件来源/许可证/大小/hash见 [downloads.md](downloads.md)。失败发生于下载流预检阶段，没有已开始的媒体传输。

## 数据准备（已完成）

本轮仅分离新目标音频，source完整人声/伴奏继续使用上轮已保存文件。分离模型的2个本地文件已按下载台账重新核验，证据 `reports/evidence/stage5/separation-model-audit.json`。目标文件成功回执/大小/哈希已验证，使用新的输出目录，命令如下：

```bash
python3 scripts/run_logged.py --name stage5-target-separation-ready \
  --evidence-dir reports/evidence/stage5 --timeout 900 -- \
  .envs/demucs/bin/python -m demucs --repo models/demucs-uvr \
  -n UVR_Demucs_Model_1 --two-stems vocals -d mps --shifts 1 \
  --overlap 0.25 --segment 7 --float32 -j 1 \
  -o work/stage5-rainie-prep/separated-ready \
  data/target/stage5-target-rainie-yuai-alt.wav
```

分离实际耗时 **22.539秒**，进程RSS峰值 **2,697,084,928 bytes（约2.51GiB）**；MPS独立峰值未采样。人声/伴奏输出文件存在、非静音、有限值、44.1kHz和时长检查通过，见 `reports/evidence/stage5/separation-artifacts.json`。完整目标stem保留在 `work/stage5-rainie-prep/separated-ready/`，没有重复分离源歌曲。

目标静音切片：阈值-40dB、持续0.4s、保留2–15s、44.1kHz单声道PCM16。得到 **15段、200.169秒（3分20.17秒）候选人声**，不足10分钟；自动处理不能确认已去掉和声/混响/伴奏残留，人工确认的干净时长仍未知。足以挑短参考用于Seed-VC零样本测试，不能据此宣称已有合格的训练型数据集。切片耗时0.826秒，片段准备0.346秒，均CPU。

参考选择限定为本轮杨丞琳目录，筛8–15s并按100ms帧非静音覆盖率、削波比例、RMS排序。前三个候选均15秒、activity=100%、clipping=0；实际两版共用第一段：**原《雨爱》180.590–195.590秒**。两条备用参考分别为102.610–117.610秒、195.590–210.590秒。没有使用张韶涵/周杰伦的target切片或明星预训练模型。

本轮源人声/伴奏/原唱对照与上轮同名片段 SHA256 完全一致，源区间为106–136秒，每条都是44.1kHz、1,323,000帧、精确30秒。验证证据 `reports/evidence/stage5/source-reuse.json`；副歌定位依据复用上轮本地Whisper记录，未重新调用ASR。

固定种子抽取5条供用户抽听：

- [00002_3285205575.wav](../work/stage5-rainie-slices/target-slices/00002_3285205575.wav)，原《雨爱》57.610–72.610s。
- [00011_3285205575.wav](../work/stage5-rainie-slices/target-slices/00011_3285205575.wav)，原《雨爱》195.590–210.590s。
- [00008_3285205575.wav](../work/stage5-rainie-slices/target-slices/00008_3285205575.wav)，原《雨爱》150.590–165.590s。
- [00012_3285205575.wav](../work/stage5-rainie-slices/target-slices/00012_3285205575.wav)，原《雨爱》210.590–225.590s。
- [00010_3285205575.wav](../work/stage5-rainie-slices/target-slices/00010_3285205575.wav)，原《雨爱》180.590–195.590s。

关键准备命令（复现需更换run-id和输出路径）：

```bash
python3 scripts/slice_vocals.py --input work/stage5-rainie-prep/target-vocals --run-id stage5-rainie-slices
.envs/demucs/bin/python scripts/prepare_stage2_clips.py --slices work/stage5-rainie-slices/target-slices --source-vocals work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/vocals.wav --source-accompaniment work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/no_vocals.wav --run-id stage5-rainie-tinghai-clips --start 106 --duration 30
```

分离后只将新target的vocals复制到 `work/stage5-rainie-prep/target-vocals/rainie-yuai.wav` 再切片；原唱对照按已核验旧片段复制，复用输入/新输入哈希均在本轮manifest内。

## A/B推理（已完成）

```bash
python3 scripts/run_stage2_poc.py --run-id stage5-rainie-tinghai \
  --clips work/stage5-rainie-tinghai-clips \
  --evidence-dir reports/evidence/stage5 --device mps
```

脚本校验隔离环境、锁定模型/源码 → 30/50步转换 → 本地混音与CAMPPlus/F0诊断 → 离线同步试听页。复现时使用新的run-id，例如 `my-rainie-tinghai`。本轮未改动推理、混音或播放器实现；沿用上轮已修复相对路径的混音版本。

## 本轮交付与诊断

[打开杨丞琳音色同步试听页](../outputs/stage5-rainie-tinghai/listen.html)，同时间点切换A/B混音、原唱、源人声、AI纯人声；另可试听本轮15秒参考。

- A / 30步：[30秒混音](../outputs/stage5-rainie-tinghai/seed-vc_A_mix_AI.wav)、[纯人声](../outputs/stage5-rainie-tinghai/seed-vc_A_AI.wav)。
- B / 50步：[30秒混音](../outputs/stage5-rainie-tinghai/seed-vc_B_mix_AI.wav)、[纯人声](../outputs/stage5-rainie-tinghai/seed-vc_B_AI.wav)。

| 版本 | 转换耗时 | 目标cosine | 原唱cosine | F0 r | log2-F0 r | 共同有声覆盖 | 中位音分偏差 | 混音LUFS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A / 30步 | 188.955s | 0.7989 | 0.7749 | 0.9965 | 0.9960 | 78.46% | 7.73 | -13.6 |
| B / 50步 | 236.203s | 0.8030 | 0.7782 | 0.9969 | 0.9965 | 78.43% | 7.69 | -14.0 |

MPS allocated/driver 的0.1秒采样峰值分别为 **3.61/5.92GiB**，推理进程RSS峰值 **3.74GiB**。这些统一内存计数有重叠，不能相加或称作独立显存；采样可能漏过瞬时峰值。

A包含第一次模型加载，B复用模型。转换外层总耗时 **430.104秒（约7分10秒）**；评测/混音外层耗时 **8.477秒**，其中核心4.808秒，评测RSS峰值约2.12GiB。两版各完成3个内部块，末块约0.43秒。

两版只改变扩散步数；与张韶涵轮次比较时，源片段/伴奏/原调/种子/模型均保持一致，目标参考均15秒，但参考歌手与歌曲不同。CAMPPlus用于生成条件，指标不是独立验证；本轮目标参考和原唱的cosine都较高，不把它们解读为音色相似百分比，也不直接用不同目标参考的分数给两位歌手的结果排优劣。本轮源人声对杨丞琳参考的基线为0.6071。

F0仅统计共同有声帧，起点对齐、不做DTW或偏移寻优。两版八度错误代理比例均为0，不能证明每个音符无误。CER=N/A，缺独立校对歌词；上轮ASR只用于定位副歌，不作为歌词真值。

**主观音色、咬字、高音破音均为PENDING，由用户试听。** 建议先听A，再同时间点切换B；50步不是更强的音色替换，不依据小幅指标变化认定B更好。可听0–8、10–20、22–30秒三个窗口（原曲106–114、116–126、128–136秒），检查起句音色、咬字/长音和内部接缝；未声称这些窗口分别是全曲最高音或最快咬字。

## 验证和遗留

- 混音均44.1kHz双声道、1,323,000帧、精确30秒；纯人声均29.988571秒，混音末尾补504采样（11.43ms），没有变速。混音峰值约A0.8829/B0.8723，没有接近满幅采样；干声接近满幅比例A约0.000681%、B约0.000151%，是否有可闻问题待听辨。
- 输入/输出哈希、非静音、有限值、格式、时长、A/B文件不同、本地页面链接检查通过。提前提供的A混音在最终评测中按回执原样复用，哈希不变。
- 本轮三个source对照文件与上轮逐字节一致，target仅来自杨丞琳。此前41个文件哈希与大小均未变；新目标原始WAV哈希也未变。
- 试听页共享时间点、快速切换、暂停/播放状态、参考音频互斥等mock DOM检查通过。不是实际浏览器或人类听音验收。
- 本轮未改推理/预处理/混音/播放器脚本，未重复运行不受改动影响的单元测试；实际成品验证与页面状态检查均已运行。
- 素材首选音轨404、一次提前触发的缺输入分离已如实记录并恢复；最终两版模型执行无失败，无待修复的技术阻塞。其他模型未在本轮尝试，不算失败。

```bash
.envs/demucs/bin/python scripts/validate_full_song.py \
  --run outputs/stage5-rainie-tinghai/run.json --duration 30 \
  --evidence reports/evidence/stage5/final-validation.json
node work/stage5-ui-preview/check-player.cjs
```

验证、峰值和复现命令证据在 `reports/evidence/stage5/`；已有evidence文件重跑需换路径。只剩用户试听反馈，以及需要CER时补独立校对歌词。本轮不自动扩成长版。

## 空间与预算快照

| 目录 | 逻辑大小 bytes | MiB |
|---|---:|---:|
| work/ | 2,271,621,389 | 2166.39 |
| outputs/ | 245,812,494 | 234.43 |
| data/ | 323,575,658 | 308.59 |
| models/ | 2,657,889,680 | 2534.76 |
| .envs/ | 1,468,540,105 | 1400.51 |
| .cache/ | 500,514,155 | 477.33 |
| reports/ | 90,644,519 | 86.45 |

本轮新增计入下载 **5,908,077 bytes**，累计 **3,431,672,684/30,000,000,000 bytes**，未结束预留 0。来源/许可证/大小/hash见 [downloads.md](downloads.md)。磁盘可用 **134,471,426,048 bytes**；目录为逻辑文件量快照，后续报告写入会略变。未删除旧素材、失败记录或成品；未commit、push或发布。
