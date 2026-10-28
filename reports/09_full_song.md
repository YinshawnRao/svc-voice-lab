# 完整歌曲 A/B 阶段记录

日期：2026-10-16。用户反馈：20 秒两版差异听不出来，希望完整歌曲试听。该反馈仅针对短片段差异，不解读为已经认可音色/咬字质量。此阶段执行完整歌曲两版，不换模型、目标参考或移调。

## 两版到底差在哪里

A=30 个扩散步，B=50 个扩散步。都是同一固定 Seed-VC V1 歌声模型、同一个《晴天》13.288 秒人声参考、F0=True、auto-F0=False、移调0、CFG0.7、length1、FP32，随机种子20261016。步数控制生成迭代次数，不是“周杰伦音色强度”；50 步不保证更像或更好听。短版分数差异也不是听感结论。

## 本轮输入与范围

- 原 source：《爱很简单》已审计音频，完整 262.063729 秒（约4:22），来源、哈希见 [03_data.md](03_data.md)。不重新下载、不删前奏/间奏/尾奏。
- 复用已完成的全曲分离结果，写入新 `work/stage3-seed-full/inputs/`：人声单声道、伴奏双声道，均44.1kHz PCM16；只做格式统一，不截取试听窗口。
- 目标参考沿用上一轮同一音频，SHA256=e0a8510d8ee62bd132fa40cd394dbcf00d8307c0f90d84c08378363d913f697f。
- 沿用上游长音频处理：Whisper 30秒窗口、5秒上下文重叠；扩散窗口由30秒上下文减去参考长度决定，波形按16帧交叉淡化拼接。对两组使用相同规则。
- 上游SHA `51383efd921027683c89e5348211d93ff12ac2a8`，Python3.10/Torch2.5.1，扩散/Whisper/CAMPPlus在MPS，声码器/RMVPE/谱特征在CPU。来源、许可证和模型哈希延续已审计清单。本轮无新增模型或依赖下载。

## 执行

```bash
python3 scripts/run_full_song.py \
  --vocals work/stage2-full/separated/source/1548a091c1b2/UVR_Demucs_Model_1/stage2-source-aihenjiandan/vocals.wav \
  --accompaniment work/stage2-full/separated/source/1548a091c1b2/UVR_Demucs_Model_1/stage2-source-aihenjiandan/no_vocals.wav \
  --reference work/stage2-clips/target_reference_1.wav \
  --original data/source/stage2-source-aihenjiandan.wav \
  --title '《爱很简单》· 完整歌曲 A/B 对比' \
  --run-id new-full-song --device mps
```

本轮实际run-id=`stage3-seed-full`。实际启动时尚未加入可选的original/title参数；其后只将试听标题和原曲路径加入inputs/manifest.json，不改变推理音频或参数。该脚本顺序执行格式准备、离线环境校验、A/B转换、评测/混音和试听页。完整命令日志、计时见 `reports/evidence/stage3/`；每个声码器块的进度保存在输出目录 `progress.jsonl`。旧20秒成品保留。

## 已验证的准备

完整版60–80秒与上一轮源片段逐采样一致，目标参考哈希也一致；证据 `reports/evidence/stage3/input-validation.json`。混音函数重构后用旧20秒结果验证，生成文件SHA256完全一致，并验证重复调用只复用已核验回执、不同输入不覆盖成品。

试听页加入共享播放位置的A/B切换，以及原唱、源人声、AI纯人声入口；目标参考独立播放器与主播放器互斥。已做mock DOM状态检查（保留播放时间、继续/暂停、连续快速切换、错误提示），不是实际浏览器或人工试听证据。本机当前没有可用的浏览器自动化连接；不因此阻塞WAV交付。

现有34项约束测试通过，新增/修改脚本语法检查通过。A版完成后先用无模型的轻量混音入口输出完整混音，B继续生成；最终评测核对回执后复用同一文件，不二次覆盖A。

## A 版先行交付

30步整曲转换成功，1515.217秒（约25.25分钟，含模型初次加载）。纯人声262.060408秒，混音262.063741秒；仅末尾补147个采样（3.33ms）以匹配完整伴奏，没有整体变速。44.1kHz、干声单声道、混音双声道；文件哈希与有限性验证通过。

[完整A混音](../outputs/stage3-seed-full/seed-vc_A_mix_AI.wav)，[完整A纯人声](../outputs/stage3-seed-full/seed-vc_A_AI.wav)。纯人声接近满幅比例约0.0244%，混音峰值约0.98；这些是信号检查，不是听感认可。初次交付证据 `evidence/stage3/A-first-delivery.json`。

## 最终结果：完整 A/B 已交付

[打开完整歌曲试听页](../outputs/stage3-seed-full/listen.html)。支持在同一时间点切换A/B混音、原唱、源人声和A/B纯人声；目标参考另有播放器，播放时与主播放器互斥。没有外部脚本、上传或在线分析。

| 版本 | 完整伴奏混音 | 完整纯人声 |
|---|---|---|
| A / 30步 | [seed-vc_A_mix_AI.wav](../outputs/stage3-seed-full/seed-vc_A_mix_AI.wav) | [seed-vc_A_AI.wav](../outputs/stage3-seed-full/seed-vc_A_AI.wav) |
| B / 50步 | [seed-vc_B_mix_AI.wav](../outputs/stage3-seed-full/seed-vc_B_mix_AI.wav) | [seed-vc_B_AI.wav](../outputs/stage3-seed-full/seed-vc_B_AI.wav) |

两版干声262.060408秒，混音均262.063741秒，44.1kHz；两版均只在末尾补147个采样（3.33ms），未做整体变速。每组16个音频块由上游规则交叉淡化拼接。输入哈希不变、4个完整文件的哈希/采样率/声道/有限性/长度和本地页面链接检查均通过。总长度一致不代表每个字或每个接缝都已通过人类听感确认。

| 版本 | 转换耗时 | 目标 cosine | F0 r | log2-F0 r | 共同有声覆盖率 | 中位音分偏差 | 混音 LUFS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A / 30 步 | 1515.217s（25.25min） | 0.8381 | 0.9933 | 0.9878 | 70.26% | 11.58 | -15.0 |
| B / 50 步 | 1786.578s（29.78min） | 0.8481 | 0.9928 | 0.9871 | 70.31% | 11.58 | -15.1 |

A含初次模型加载，B复用模型；耗时包含特征处理、生成和CPU声码器。整个转换进程3307.783秒（约55.13分钟），评测/混音外层进程30.908秒、核心评测27.477秒。不是实时转换，也不是严格分离模型加载成本的性能基准。

MPS allocated/driver 的0.1秒采样峰值分别为 3.86/7.24GiB，转换进程 RSS 峰值 6.37GiB。评测进程 RSS 峰值 7.57GiB。Apple统一内存指标有重叠，不可相加，也不代表独立显存；采样可能漏过瞬时峰值。

源人声对目标参考的全曲cosine基线=0.5751。目标cosine使用同一个CAMPPlus条件编码器，只有单参考，不是独立验证或相似度百分比；长曲与20秒的统计范围不同，不能直接把两张表的差异解释为质量提升。F0采用RMVPE、16kHz/10ms帧移、共同F0>50Hz帧、零延迟对齐、不使用DTW。八度误差代理（±1200±100cents）A/B约为0.196%/0.206%，约30%帧未纳入共同有声相关性；仍需听辨局部问题。

干声接近满幅（abs>=0.999）A/B约0.0244%/0.0114%；上游声码器存在硬限幅，不能通过后续调低混音电平恢复。混音最终采样峰值均0.97998；响度范围A/B=6.7/6.9LU，true peak A/B=-0.2/-0.2dBFS。响度由FFmpeg ebur128测量，没有额外修改音频做响度归一化。

用户先前反馈的是20秒两版差异听不出来，本次完整结果尚无听感反馈。助手没有实际听到输出，不宣称音色像不像、咬字或高音质量过关。CER仍为N/A，缺独立校对歌词。50步不是更强的目标音色设置；若完整听感仍无明显差异，30步可作为计算成本基线。

## 验证、复现和保留

- `run_full_song.py` 的准备→环境校验→A/B推理→评测/混音链路实跑成功。全曲验证脚本也单独实跑通过，并已加入后续一键入口末尾；无需重复计算整首验证编排。
- A版先行混音的SHA256与最终评测回执完全一致，没有被二次覆盖。旧20秒成品、5秒冒烟、所有中间文件都保留。
- 34项约束测试通过；新混音入口已验证旧结果逐字节一致、回执复用和不同输入不覆盖；页面控制的mock DOM检查通过，但没有真实浏览器/人工试听验证。
- 完整原始证据：[run](evidence/stage3/full-run.json)、[evaluation](evidence/stage3/full-evaluation.json)、[最终文件校验](evidence/stage3/stage3-seed-full-validation.json)、[响度](evidence/stage3/loudness.json)、[空间](evidence/stage3/storage.json)。转换日志 `logs/stage3-seed-full-convert.log`、评测日志 `logs/stage3-seed-full-evaluate.log`。
- 本轮没有新增模型/依赖/媒体下载，累计下载预算仍为 3,407,221,733/30,000,000,000 bytes，未结束预留0。work约1105.63MiB，outputs约194.03MiB，均为逻辑文件量；没有删除文件、修改系统设置、commit或push。

