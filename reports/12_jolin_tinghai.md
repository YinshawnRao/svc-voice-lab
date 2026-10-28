# 独立实验：蔡依林音色唱《听海》30秒副歌

> 历史记录：本目录成品已按用户指定《天空》重新生成覆盖。当前结果见 [指定参考重生成报告](13_requested_references.md)，以下旧数值/旧参考不代表当前成品。旧文件证据位于 `work/stage7-replaced/outputs/stage6-jolin-tinghai/`。

2026-10-16。用户要求继续实验、目标改为蔡依林。本轮继承最近两轮的30秒副歌和A30/B50，原唱区间106–136秒（1:46–2:16）；源人声/伴奏/原唱对照已按哈希确认与之前相同，目标参考独立准备。

## 素材获取（完成）

通过 `scripts/media.py` doctor → search → probe → download 获取[《倒带》蔡依林](https://www.bilibili.com/video/BV1YJ411x7JC/)，页面发布者“索尼音乐中国”。下载音轨4,387,358 bytes，成功耗时3.738秒；解码WAV48kHz双声道、264.234667秒、50,733,134 bytes，SHA256 `023a7f0fab533149d6acf27bbd90b74a7e33a3d879d6afaf57255cd92f1470fa`。许可证unknown，页面“官方MV”不等于取得再发行许可；本轮限本地实验，无音频上传。

下载回执：`work/acquisition/stage6-target-jolin-daodai/receipt.json`；逐文件大小、来源、许可、SHA256见 [downloads.md](downloads.md)。Cookie只读快照消费，无凭据或签名CDN地址落盘。此次首选来源一次成功，无需备用来源。下载未用GPU。

《听海》来源和副歌定位沿用[张韶涵轮次](10_angela_tinghai.md)；不重复下载、分离或ASR源歌曲。原始素材、前轮成品与中间产物保留。

## 固定技术条件

2026-10-16重读已审计的Seed-VC README，固定SHA `51383efd921027683c89e5348211d93ff12ac2a8`。V1 44.1kHz歌声模式，F0=True、auto-F0=False、半音偏移0、CFG0.7、length1、FP32、种子20261016；A30步、B50步。MPS扩散/Whisper/CAMPPlus，CPU BigVGAN/RMVPE。权重、环境、推理/混音/播放器实现均沿用已验证版本，本轮不新增模型或依赖、不训练明星模型。

## 数据准备（完成）

`reports/evidence/stage6/input-preflight.json`已确认下载成功、文件存在、大小/哈希正确。`separation-model-audit.json`核验Demucs本地权重和YAML。只分离本轮新目标音频，日志和关键命令由 `scripts/run_logged.py` 写入 `reports/evidence/stage6/stage6-target-separation.json` 和 `logs/stage6-target-separation.log`。以实际stem格式/有限值/时长核验作为完成依据。

分离耗时 **18.542秒**，进程RSS峰值2,319,040,512 bytes（约2.16GiB）；MPS峰值未单独采样。两条stem的存在、时长、44.1kHz、非静音和有限值检查通过，详见 `separation-artifacts.json`。切片0.774秒，片段准备0.395秒，均CPU。

目标静音切片参数：-40dB、持续0.4秒、保留2–15秒、44.1kHz单声道PCM16。得到 **17段、225.337秒（3分45.34秒）候选人声**，不足10分钟；干净时长未经人工确认。此量用于零样本参考选择，不直接认定为训练型模型的合格数据集；没有声称去混响/和声或伴奏残留审查已完成。

8–15秒候选按100ms帧非静音率、削波率、RMS排序。本轮两版共用第一段：**《倒带》61.100–76.100秒的15秒人声**，activity100%、clipping0。备用段为224.982–239.982秒（100%、0）和179.162–194.162秒（99.33%、0）。所有参考均来自本轮蔡依林目录。

本轮《听海》源人声、伴奏、原唱对照与杨丞琳轮次逐字节一致，并延续张韶涵轮次；每条44.1kHz、1,323,000帧、精确30秒。证据 `reports/evidence/stage6/source-reuse.json`。没有混入前轮target，也没有重复生成源stem造成差异。

固定种子抽取5条供用户抽听：

- [00004_f00593e0b5.wav](../work/stage6-jolin-slices/target-slices/00004_f00593e0b5.wav)，原《倒带》61.100–76.100s。
- [00013_f00593e0b5.wav](../work/stage6-jolin-slices/target-slices/00013_f00593e0b5.wav)，原《倒带》209.982–224.982s。
- [00008_f00593e0b5.wav](../work/stage6-jolin-slices/target-slices/00008_f00593e0b5.wav)，原《倒带》134.162–149.162s。
- [00016_f00593e0b5.wav](../work/stage6-jolin-slices/target-slices/00016_f00593e0b5.wav)，原《倒带》252.691–260.388s。
- [00007_f00593e0b5.wav](../work/stage6-jolin-slices/target-slices/00007_f00593e0b5.wav)，原《倒带》119.162–134.162s。

实际准备命令（复现须换run-id/输出目录）：

```bash
.envs/demucs/bin/python -m demucs --repo models/demucs-uvr -n UVR_Demucs_Model_1 --two-stems vocals -d mps --shifts 1 --overlap 0.25 --segment 7 --float32 -j 1 -o work/stage6-jolin-prep/separated data/target/stage6-target-jolin-daodai.wav
python3 scripts/slice_vocals.py --input work/stage6-jolin-prep/target-vocals --run-id stage6-jolin-slices
.envs/demucs/bin/python scripts/prepare_stage2_clips.py --slices work/stage6-jolin-slices/target-slices --source-vocals work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/vocals.wav --source-accompaniment work/stage4-angela-tinghai-prep/separated/source/689eb325b048/UVR_Demucs_Model_1/stage4-source-tinghai/no_vocals.wav --run-id stage6-jolin-tinghai-clips --start 106 --duration 30
```

分离完成后，只将本轮vocals复制到 `work/stage6-jolin-prep/target-vocals/jolin-daodai.wav` 再切片；原唱对照从已核验旧片段复制。原件、复制件、参考和输出的哈希均记录于各阶段manifest。

## A/B推理（已完成）

```bash
python3 scripts/run_stage2_poc.py --run-id stage6-jolin-tinghai \
  --clips work/stage6-jolin-tinghai-clips \
  --evidence-dir reports/evidence/stage6 --device mps
```

复现可用新run-id `my-jolin-tinghai`。入口校验独立环境 → 固定本地模型/源码哈希 → A30/B50 → 本地混音/诊断 → 离线试听页。推理启用离线标记并阻断Python互联网连接；沿用已实测的Mac适配，无新权重/依赖下载。

## 本轮交付与诊断

[打开蔡依林音色同步试听页](../outputs/stage6-jolin-tinghai/listen.html)，同时间点切换A/B混音、原唱、源人声和AI纯人声；另可试听本轮《倒带》15秒参考。

- A / 30步：[30秒混音](../outputs/stage6-jolin-tinghai/seed-vc_A_mix_AI.wav)、[纯人声](../outputs/stage6-jolin-tinghai/seed-vc_A_AI.wav)。
- B / 50步：[30秒混音](../outputs/stage6-jolin-tinghai/seed-vc_B_mix_AI.wav)、[纯人声](../outputs/stage6-jolin-tinghai/seed-vc_B_AI.wav)。

| 版本 | 转换耗时 | 目标cosine | 原唱cosine | F0 r | log2-F0 r | 共同有声覆盖 | 中位音分偏差 | 混音LUFS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A / 30步 | 243.160s | 0.7611 | 0.7569 | 0.9939 | 0.9900 | 78.39% | 8.12 | -13.3 |
| B / 50步 | 353.812s | 0.7683 | 0.7671 | 0.9934 | 0.9893 | 78.39% | 8.25 | -13.7 |

MPS allocated/driver 的0.1秒采样峰值分别为 **3.59/5.86GiB**，推理进程RSS峰值 **4.38GiB**。这些统一内存计数有重叠，不能相加或称作独立显存；采样可能漏过瞬时峰值。

A包含第一次模型加载，B复用模型。转换外层总耗时 **602.888秒（约10.05分钟）**；评测/混音外层耗时 **15.371秒**，其中核心9.956秒，评测RSS峰值约2.13GiB。

本轮源人声对蔡依林参考的cosine基线为0.5440。CAMPPlus同时用于生成条件，指标非独立验证，不能解释为像歌手的百分比；不同歌手的参考分数不能直接用于排名。F0按同一起点的共同有声帧计算，不做DTW或偏移寻优，未共同发声的帧不纳入相关系数。CER缺独立校对歌词，仍为N/A；之前ASR仅用于定位副歌。

**主观音色相似度、咬字、高音破音均为PENDING，由用户试听。** 先听A，再同时间点切换B；两版只改变30/50扩散步数，50步不代表音色替换更强或听感更好。可比较0–8、10–20、22–30秒三个窗口（原曲106–114、116–126、128–136秒），检查起句、咬字/长音和接缝；未认定这些窗口分别是全曲最高音或最快咬字。

## 验证和遗留

- 两版混音44.1kHz双声道、1,323,000帧、精确30秒；纯人声29.988571秒，混音末尾补504采样（11.43ms），没有变速。格式、时长、非静音、有限值、输入/输出哈希和两版文件不同均已验证。
- 先提供的A混音由最终评测按回执原样复用，哈希不变。三个source对照文件与前轮逐字节一致，target仅来自本轮蔡依林素材。此前59个受保护文件的大小和哈希均未变，新目标原始WAV也未变。
- 试听页标题/参考/6个本地音轨链接核验通过；同时间点切换、快速切换、播放/暂停状态、参考互斥和错误回退的mock DOM检查通过。这不是实际浏览器或人工听音验收。
- 本轮未修改推理、预处理、混音或播放器实现，未重复运行无关单元测试；实际产物验证和页面状态检查已运行。
- 媒体获取、分离、A/B推理及评测均成功，无新增失败或待修复技术阻塞。其他模型本轮未尝试，不记作失败。没有新权重/依赖下载，没有训练。

混音峰值/响度和干声近满幅比例见 `reports/evidence/stage6/final-validation.json`、`loudness.json` 与 `outputs/stage6-jolin-tinghai/run.json`；不能据非静音和峰值检查宣称没有可闻失真。

```bash
.envs/demucs/bin/python scripts/validate_full_song.py --run outputs/stage6-jolin-tinghai/run.json --duration 30 --evidence reports/evidence/stage6/final-validation.json
node work/stage6-ui-preview/check-player.cjs
python3 work/stage6-ui-preview/check-artifacts.py
```

已有验证证据重新运行需换输出路径。只剩用户试听反馈，以及需要CER时补独立校对歌词。本轮不自动扩成长版。

## 空间与预算快照

| 目录 | 逻辑大小 bytes | MiB |
|---|---:|---:|
| work/ | 2,654,138,715 | 2531.18 |
| outputs/ | 266,990,271 | 254.62 |
| data/ | 374,308,792 | 356.97 |
| models/ | 2,657,889,680 | 2534.76 |
| .envs/ | 1,468,540,105 | 1400.51 |
| .cache/ | 500,514,155 | 477.33 |
| reports/ | 90,689,583 | 86.49 |

本轮新增计入下载 **4,387,358 bytes**，累计 **3,436,060,042/30,000,000,000 bytes**，未结束预留 **0**。来源/许可证/大小/hash见 [downloads.md](downloads.md)。磁盘可用 **122,479,878,144 bytes**；目录为逻辑文件量快照，后续报告写入会略变。未删除任何素材、中间产物或成品；未commit、push或发布。
