# 四位歌手《听海》独立实验

2026-10-16，四位均已完成，状态POC_PASSED。用户指定：孙燕姿《我不难过》、萧亚轩《最熟悉的陌生人》、梁静茹《崇拜》、王心凌《变成陌生人》。四个新输出目录；既有实验不覆盖。

## 固定条件

- 张惠妹《听海》MV 106–136 秒的同一段 30 秒副歌。源人声、伴奏、原唱对照均与既有实验逐文件校验 SHA256。
- Seed-VC 官方源码固定在 `51383efd921027683c89e5348211d93ff12ac2a8`；本轮查阅本地已锁定 README。独立 `.envs/seed-vc`、`.envs/demucs`，模型执行完全离线。
- A=30 步、B=50 步；F0=true，auto_f0_adjust=false，移调0，CFG=0.7，length_adjust=1，seed=20261016，FP32。A/B只改变扩散步数，不代表音色变化强度。
- Apple M4 Pro 48GiB；扩散/Whisper/CAMPPlus 使用 MPS，BigVGAN/RMVPE/mel 使用 CPU。串行运行重模型。
- 目标人声分离：UVR_Demucs_Model_1，MPS，shifts=1，overlap=0.25，segment=7，float32，j=1。权重按既有官方来源清单核验大小及哈希。
- 切片：静音阈值−40dB、最短静音0.4秒、片长2–15秒、44.1kHz单声道PCM16；8–15秒候选按非静音覆盖/削波筛选，RMS打破同分，选择前三段备选，实际推理用第一段。不能据此证明无混响、和声或伴奏残留。
- 媒体按既有授权使用公开MV；上传者和来源如实记录，标题中的“官方/4K修复”不当作官方上传者、无损音质或授权证明。许可证未明确记 unknown。

## 初始保护与下载

初始106个已有输出/素材/既有输入文件的大小、SHA256留存 `reports/evidence/stage8/before-files.json`，结束时复核。初始累计已计费下载3,519,048,505字节；前轮中断下载保留预算5,812,791字节，不自动释放。本轮不新增模型权重。

候选来源经 `scripts/media.py doctor → search/probe` 检查，随后通过同一脚本下载并登记 `reports/downloads.md`。每个原音频/分离/切片/推理输入保留独立路径及来源哈希。

| 歌手 | 指定参考 | 公开来源 | 上传者 | 新输出目录 |
|---|---|---|---|---|
| 孙燕姿 | 我不难过 | [MV](https://www.bilibili.com/video/BV1N44y1t7Er/) | ---今晚打老虎--- | outputs/stage8-stefanie-tinghai |
| 萧亚轩 | 最熟悉的陌生人 | [MV](https://www.bilibili.com/video/BV1gE411q7aV/) | zyl2012_音乐无限 | outputs/stage8-elva-tinghai |
| 梁静茹 | 崇拜 | [MV](https://www.bilibili.com/video/BV11J411D7Kc/) | 时光音乐阁 | outputs/stage8-fish-tinghai |
| 王心凌 | 变成陌生人 | [MV](https://www.bilibili.com/video/BV1Yb411S7Rm/) | WithCyndi王心凌陪伴站 | outputs/stage8-cyndi-tinghai |

## 评测边界

混音使用 `scripts/mix_audio.py`：按源人声RMS匹配转换人声增益，限制在0.5–2倍；与原伴奏起点对齐，仅在末尾补/裁以保持原时长；全局峰值上限0.98，输出44.1kHz立体声PCM16。没有做LUFS统一，不同歌手及A/B响度差异需结合表中数值判断；每份 `.mix.json` 保存实际增益、尾部采样调整及输入输出哈希。

CAMPPlus参考相似度使用与模型条件相同的编码器，不是独立的歌手身份鉴别。F0相关在共同有声帧、零延迟计算，无DTW；需同时看覆盖率和音分误差。没有用户核对的歌词，CER=N/A。没有人工听过，不写音色相似、咬字、高音破音的主观结论。

各试听页支持在同一时间点切换A/B混音、原唱、源人声与A/B干声，并提供本轮真实参考人声。建议分别听0–10、10–20、20–30秒；这些是固定位置对照，不宣称已经人工标注“最高音/最快咬字”。

## 孙燕姿：我不难过（已完成）

[同步试听页](../outputs/stage8-stefanie-tinghai/listen.html)。参考来自指定《我不难过》原音频 **92.457–107.457秒**，长度15.000秒；activity=98.67%，clipping=0.0。共20段、244.636秒候选人声，**不足10分钟**，人工确认的干净总时长未知。零样本可使用本轮短参考；训练型仍应另备更多清晰素材，不能以此证明满足训练需求。

原始派生WAV：`data/target/stage8-target-stefanie-wobunanguo.wav`，57,704,526 bytes，327.122721秒，SHA256 `51c7610558aa7d5e6168f39c514ff9b765f899ab47fde0fd925e278b44e99da5`。网络原始流13,149,433 bytes，获取3.090秒，许可证unknown；来源与逐文件哈希见[回执](../work/acquisition/stage8-target-stefanie-wobunanguo/receipt.json)和[下载台账](downloads.md)。

目标分离18.076秒，进程RSS峰值2.33GiB，分离MPS峰值未采样；切片0.869秒。目标独立处理，source三条音轨均按哈希确认与既有副歌相同。参考SHA256 `d96f7e5eecf101b3d877175cd35fc11d05ebf7b5a41589f91d2ae53f703fe4db`。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage8-stefanie-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage8-stefanie-tinghai/seed-vc_A_AI.wav) | 178.584s | 0.8208 | 0.9979 | 78.26% | 7.48 | -15.3 |
| B50 | [试听](../outputs/stage8-stefanie-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage8-stefanie-tinghai/seed-vc_B_AI.wav) | 249.778s | 0.8265 | 0.9979 | 78.26% | 7.39 | -15.4 |

转换总耗时431.589秒，评测/混音8.173秒。MPS allocated/driver采样峰值3.58/5.92GiB，推理RSS峰值5.15GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

检查通过：两版解码采样不同、输入/输出哈希一致、44.1kHz、有限且非静音、混音精确30秒、干声与源片差在512采样以内、本地页面链接有效。播放器同位置切换通过mock DOM检查；不是人工听音或真实浏览器验收。主观音色、咬字、高音仍待用户试听。

固定随机种子抽5条供人工抽听：

- [00004_cc33b50b2f.wav](../work/stage8-stefanie-slices/target-slices/00004_cc33b50b2f.wav)，原参考歌曲92.457–107.457秒。
- [00017_cc33b50b2f.wav](../work/stage8-stefanie-slices/target-slices/00017_cc33b50b2f.wav)，原参考歌曲264.843–279.843秒。
- [00016_cc33b50b2f.wav](../work/stage8-stefanie-slices/target-slices/00016_cc33b50b2f.wav)，原参考歌曲249.843–264.843秒。
- [00013_cc33b50b2f.wav](../work/stage8-stefanie-slices/target-slices/00013_cc33b50b2f.wav)，原参考歌曲208.858–223.858秒。
- [00009_cc33b50b2f.wav](../work/stage8-stefanie-slices/target-slices/00009_cc33b50b2f.wav)，原参考歌曲148.858–163.858秒。

实际生成命令：

```bash
.envs/demucs/bin/python work/stage8-tools/prepare.py stefanie
python3 scripts/run_stage2_poc.py --run-id stage8-stefanie-tinghai --clips work/stage8-stefanie-tinghai-clips --evidence-dir reports/evidence/stage8 --device mps
.envs/demucs/bin/python work/stage8-tools/record.py stefanie
```

准备脚本校验下载回执与模型哈希，显式分离本位歌手后切片，不扫描其他歌手。精确分离命令在 `reports/evidence/stage8/stage8-stefanie-separate.json`；切片/ffmpeg命令在对应日志及prepared manifest。上面是实际记录，不可重复覆盖；复现只需保留已准备输入，使用 `scripts/run_stage2_poc.py` 并替换新的 `--run-id` 与 `--evidence-dir`。

### 本轮编排问题

孙燕姿音频及页面检查通过后，报告汇总第一次出现 `KeyError: elapsed_seconds`：下载回执在计时字段加入前已保存，最终耗时存在同ID的media-events事件JSON。一次修复改为从事件读取耗时，复用已通过的本轮文件检查和响度日志后完成。原失败日志 `logs/stage8-stefanie-validation.log`、修复成功日志 `logs/stage8-stefanie-validation-repair.log` 均保留。未重新生成或改动音频。

## 萧亚轩：最熟悉的陌生人（已完成）

[同步试听页](../outputs/stage8-elva-tinghai/listen.html)。参考来自指定《最熟悉的陌生人》原音频 **208.602–223.602秒**，长度15.000秒；activity=100.00%，clipping=0.0。共16段、219.593秒候选人声，**不足10分钟**，人工确认的干净总时长未知。零样本可使用本轮短参考；训练型仍应另备更多清晰素材，不能以此证明满足训练需求。

原始派生WAV：`data/target/stage8-target-elva-zuishuxidemoshengren.wav`，49,745,998 bytes，259.093333秒，SHA256 `fde183860f9e8a8a6311567778eb1107adbad5ae29d917789beb89e64de77525`。网络原始流7,249,323 bytes，获取2.903秒，许可证unknown；来源与逐文件哈希见[回执](../work/acquisition/stage8-target-elva-zuishuxidemoshengren/receipt.json)和[下载台账](downloads.md)。

目标分离14.539秒，进程RSS峰值2.06GiB，分离MPS峰值未采样；切片0.600秒。目标独立处理，source三条音轨均按哈希确认与既有副歌相同。参考SHA256 `5e3468909a3933c1d94749811fbcafd655fa45bc1c7be4fa379759b0672beebc`。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage8-elva-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage8-elva-tinghai/seed-vc_A_AI.wav) | 169.344s | 0.8180 | 0.9939 | 77.93% | 7.36 | -13.2 |
| B50 | [试听](../outputs/stage8-elva-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage8-elva-tinghai/seed-vc_B_AI.wav) | 215.368s | 0.8219 | 0.9939 | 77.96% | 7.34 | -13.6 |

转换总耗时387.606秒，评测/混音6.945秒。MPS allocated/driver采样峰值3.60/5.92GiB，推理RSS峰值5.52GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

检查通过：两版解码采样不同、输入/输出哈希一致、44.1kHz、有限且非静音、混音精确30秒、干声与源片差在512采样以内、本地页面链接有效。播放器同位置切换通过mock DOM检查；不是人工听音或真实浏览器验收。主观音色、咬字、高音仍待用户试听。

固定随机种子抽5条供人工抽听：

- [00004_4af549224b.wav](../work/stage8-elva-slices/target-slices/00004_4af549224b.wav)，原参考歌曲77.661–92.661秒。
- [00011_4af549224b.wav](../work/stage8-elva-slices/target-slices/00011_4af549224b.wav)，原参考歌曲173.549–178.684秒。
- [00008_4af549224b.wav](../work/stage8-elva-slices/target-slices/00008_4af549224b.wav)，原参考歌曲128.549–143.549秒。
- [00013_4af549224b.wav](../work/stage8-elva-slices/target-slices/00013_4af549224b.wav)，原参考歌曲208.602–223.602秒。
- [00010_4af549224b.wav](../work/stage8-elva-slices/target-slices/00010_4af549224b.wav)，原参考歌曲158.549–173.549秒。

实际生成命令：

```bash
.envs/demucs/bin/python work/stage8-tools/prepare.py elva
python3 scripts/run_stage2_poc.py --run-id stage8-elva-tinghai --clips work/stage8-elva-tinghai-clips --evidence-dir reports/evidence/stage8 --device mps
.envs/demucs/bin/python work/stage8-tools/record.py elva
```

准备脚本校验下载回执与模型哈希，显式分离本位歌手后切片，不扫描其他歌手。精确分离命令在 `reports/evidence/stage8/stage8-elva-separate.json`；切片/ffmpeg命令在对应日志及prepared manifest。上面是实际记录，不可重复覆盖；复现只需保留已准备输入，使用 `scripts/run_stage2_poc.py` 并替换新的 `--run-id` 与 `--evidence-dir`。

## 梁静茹：崇拜（已完成）

[同步试听页](../outputs/stage8-fish-tinghai/listen.html)。参考来自指定《崇拜》原音频 **228.574–243.574秒**，长度15.000秒；activity=100.00%，clipping=0.0。共16段、224.124秒候选人声，**不足10分钟**，人工确认的干净总时长未知。零样本可使用本轮短参考；训练型仍应另备更多清晰素材，不能以此证明满足训练需求。

原始派生WAV：`data/target/stage8-target-fish-chongbai.wav`，64,335,950 bytes，335.082667秒，SHA256 `d289530dc1934c852d0a645fc51661aad46ea9e85c9063e79b1b4997915b8193`。网络原始流8,800,686 bytes，获取2.991秒，许可证unknown；来源与逐文件哈希见[回执](../work/acquisition/stage8-target-fish-chongbai/receipt.json)和[下载台账](downloads.md)。

目标分离16.493秒，进程RSS峰值2.26GiB，分离MPS峰值未采样；切片0.658秒。目标独立处理，source三条音轨均按哈希确认与既有副歌相同。参考SHA256 `7568492206fccb0735866a933d398f0703c9e68f970ced542c3128e1222b44a7`。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage8-fish-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage8-fish-tinghai/seed-vc_A_AI.wav) | 167.193s | 0.7584 | 0.9969 | 78.49% | 7.74 | -11.1 |
| B50 | [试听](../outputs/stage8-fish-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage8-fish-tinghai/seed-vc_B_AI.wav) | 219.991s | 0.7677 | 0.9970 | 78.49% | 7.77 | -11.2 |

转换总耗时390.055秒，评测/混音7.112秒。MPS allocated/driver采样峰值3.61/5.92GiB，推理RSS峰值5.69GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

检查通过：两版解码采样不同、输入/输出哈希一致、44.1kHz、有限且非静音、混音精确30秒、干声与源片差在512采样以内、本地页面链接有效。播放器同位置切换通过mock DOM检查；不是人工听音或真实浏览器验收。主观音色、咬字、高音仍待用户试听。

固定随机种子抽5条供人工抽听：

- [00004_4fdb5de419.wav](../work/stage8-fish-slices/target-slices/00004_4fdb5de419.wav)，原参考歌曲94.551–109.551秒。
- [00011_4fdb5de419.wav](../work/stage8-fish-slices/target-slices/00011_4fdb5de419.wav)，原参考歌曲213.574–228.574秒。
- [00008_4fdb5de419.wav](../work/stage8-fish-slices/target-slices/00008_4fdb5de419.wav)，原参考歌曲168.574–183.574秒。
- [00013_4fdb5de419.wav](../work/stage8-fish-slices/target-slices/00013_4fdb5de419.wav)，原参考歌曲243.574–254.903秒。
- [00010_4fdb5de419.wav](../work/stage8-fish-slices/target-slices/00010_4fdb5de419.wav)，原参考歌曲198.574–213.574秒。

实际生成命令：

```bash
.envs/demucs/bin/python work/stage8-tools/prepare.py fish
python3 scripts/run_stage2_poc.py --run-id stage8-fish-tinghai --clips work/stage8-fish-tinghai-clips --evidence-dir reports/evidence/stage8 --device mps
.envs/demucs/bin/python work/stage8-tools/record.py fish
```

准备脚本校验下载回执与模型哈希，显式分离本位歌手后切片，不扫描其他歌手。精确分离命令在 `reports/evidence/stage8/stage8-fish-separate.json`；切片/ffmpeg命令在对应日志及prepared manifest。上面是实际记录，不可重复覆盖；复现只需保留已准备输入，使用 `scripts/run_stage2_poc.py` 并替换新的 `--run-id` 与 `--evidence-dir`。

## 王心凌：变成陌生人（已完成）

[同步试听页](../outputs/stage8-cyndi-tinghai/listen.html)。参考来自指定《变成陌生人》原音频 **182.029–197.029秒**，长度15.000秒；activity=98.00%，clipping=0.0。共19段、191.175秒候选人声，**不足10分钟**，人工确认的干净总时长未知。零样本可使用本轮短参考；训练型仍应另备更多清晰素材，不能以此证明满足训练需求。

原始派生WAV：`data/target/stage8-target-cyndi-bianchengmoshengren.wav`，50,122,830 bytes，284.142585秒，SHA256 `4b4ad683cdfbff55f6cc37703ed89bc49e43367f2c0c0bce098a7c8f5cd1700f`。网络原始流4,519,256 bytes，获取2.740秒，许可证unknown；来源与逐文件哈希见[回执](../work/acquisition/stage8-target-cyndi-bianchengmoshengren/receipt.json)和[下载台账](downloads.md)。

目标分离19.169秒，进程RSS峰值2.45GiB，分离MPS峰值未采样；切片0.705秒。目标独立处理，source三条音轨均按哈希确认与既有副歌相同。参考SHA256 `43b1a2739ca20bc2f523a8dbd6ac5bff765152478e6feb21ae69e557a8b5f353`。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage8-cyndi-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage8-cyndi-tinghai/seed-vc_A_AI.wav) | 166.818s | 0.8298 | 0.9975 | 78.09% | 7.07 | -15.2 |
| B50 | [试听](../outputs/stage8-cyndi-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage8-cyndi-tinghai/seed-vc_B_AI.wav) | 220.689s | 0.8315 | 0.9976 | 78.06% | 7.04 | -15.3 |

转换总耗时390.459秒，评测/混音6.804秒。MPS allocated/driver采样峰值3.61/5.92GiB，推理RSS峰值5.40GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

检查通过：两版解码采样不同、输入/输出哈希一致、44.1kHz、有限且非静音、混音精确30秒、干声与源片差在512采样以内、本地页面链接有效。播放器同位置切换通过mock DOM检查；不是人工听音或真实浏览器验收。主观音色、咬字、高音仍待用户试听。

固定随机种子抽5条供人工抽听：

- [00004_3dae262166.wav](../work/stage8-cyndi-slices/target-slices/00004_3dae262166.wav)，原参考歌曲60.221–62.724秒。
- [00017_3dae262166.wav](../work/stage8-cyndi-slices/target-slices/00017_3dae262166.wav)，原参考歌曲256.000–259.891秒。
- [00016_3dae262166.wav](../work/stage8-cyndi-slices/target-slices/00016_3dae262166.wav)，原参考歌曲242.029–254.834秒。
- [00013_3dae262166.wav](../work/stage8-cyndi-slices/target-slices/00013_3dae262166.wav)，原参考歌曲197.029–212.029秒。
- [00008_3dae262166.wav](../work/stage8-cyndi-slices/target-slices/00008_3dae262166.wav)，原参考歌曲106.364–119.331秒。

实际生成命令：

```bash
.envs/demucs/bin/python work/stage8-tools/prepare.py cyndi
python3 scripts/run_stage2_poc.py --run-id stage8-cyndi-tinghai --clips work/stage8-cyndi-tinghai-clips --evidence-dir reports/evidence/stage8 --device mps
.envs/demucs/bin/python work/stage8-tools/record.py cyndi
```

准备脚本校验下载回执与模型哈希，显式分离本位歌手后切片，不扫描其他歌手。精确分离命令在 `reports/evidence/stage8/stage8-cyndi-separate.json`；切片/ffmpeg命令在对应日志及prepared manifest。上面是实际记录，不可重复覆盖；复现只需保留已准备输入，使用 `scripts/run_stage2_poc.py` 并替换新的 `--run-id` 与 `--evidence-dir`。

## 收尾检查

8个版本、16个音频文件均通过时长、采样率、声道、有限值、非静音、输入输出哈希、独立参考来源和本地链接检查。混音精确30秒，干声29.988571秒，混音尾部补504采样（11.43ms），无变速。A/B解码采样不同；播放器mock DOM同位置切换检查通过，不替代真实浏览器和人工听音。全部106个既有保护文件的大小和SHA256未变，之前三位歌手及完整《爱很简单》保留。本轮无生成失败；未删除文件，未commit、push或发布。

| 音色 / 参考 | 版本 | 推理耗时 | 目标cosine | F0 r | 共同有声覆盖 | 混音LUFS |
|---|---|---:|---:|---:|---:|---:|
| 孙燕姿 / 我不难过 | A30 | 178.584s | 0.8208 | 0.9979 | 78.26% | -15.3 |
| 孙燕姿 / 我不难过 | B50 | 249.778s | 0.8265 | 0.9979 | 78.26% | -15.4 |
| 萧亚轩 / 最熟悉的陌生人 | A30 | 169.344s | 0.8180 | 0.9939 | 77.93% | -13.2 |
| 萧亚轩 / 最熟悉的陌生人 | B50 | 215.368s | 0.8219 | 0.9939 | 77.96% | -13.6 |
| 梁静茹 / 崇拜 | A30 | 167.193s | 0.7584 | 0.9969 | 78.49% | -11.1 |
| 梁静茹 / 崇拜 | B50 | 219.991s | 0.7677 | 0.9970 | 78.49% | -11.2 |
| 王心凌 / 变成陌生人 | A30 | 166.818s | 0.8298 | 0.9975 | 78.09% | -15.2 |
| 王心凌 / 变成陌生人 | B50 | 220.689s | 0.8315 | 0.9976 | 78.06% | -15.3 |

CAMPPlus也用于生成条件，cosine非独立评价，不能解释为相似百分比或跨歌手排名。F0仅覆盖共同有声帧，零延迟，无DTW。CER缺独立校对歌词，N/A；音色相似度、咬字和高音仍待用户试听。

推荐先听各自A30，再在同一位置切换B50；步数更多不代表音色更像。每位实际参考均可从试听页展开播放，候选未经人工洁净度确认。

## 空间与预算

| 目录 | 逻辑大小 bytes | MiB |
|---|---:|---:|
| work/ | 5,381,761,459 | 5132.45 |
| outputs/ | 351,701,595 | 335.41 |
| data/ | 710,573,084 | 677.66 |
| models/ | 2,657,889,680 | 2534.76 |
| .envs/ | 1,468,540,105 | 1400.51 |
| .cache/ | 500,547,115 | 477.36 |
| reports/ | 90,964,305 | 86.75 |

本轮4次素材下载均成功，新计费33,718,698 bytes；累计3,552,767,203 bytes，前轮中断下载保留预留5,812,791 bytes，合计3,558,579,994/30,000,000,000 bytes。旧预留不代表仍有下载进程。本轮无模型/依赖新增下载。磁盘可用113,368,100,864 bytes。逐文件来源、大小、许可证与哈希见 [downloads.md](downloads.md)。空间为逻辑大小快照，后续写报告会略变。
