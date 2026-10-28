# 03 数据预处理记录

最新新增：孙燕姿《我不难过》、萧亚轩《最熟悉的陌生人》、梁静茹《崇拜》、王心凌《变成陌生人》，四个独立目录的《听海》30秒A/B均完成，详见 [14_four_singers.md](14_four_singers.md)。前轮三位指定参考结果保留，见 [13_requested_references.md](13_requested_references.md)。以下保留历史阶段记录。

更新日期：2026-10-16。状态：完整人声/伴奏已分离，参考候选已切片，尚未经人工抽听。初始空目录状态已由本轮自主获取素材解除。

## 输入与来源

| 用途 | 文件 | 时长 | 来源 |
|---|---|---:|---|
| target | `data/target/stage2-target-qingtian.wav` | 269.500s | [Bilibili BV1BZbSzZEGT](https://www.bilibili.com/video/BV1BZbSzZEGT/) |
| source | `data/source/stage2-source-aihenjiandan.wav` | 262.063729s | [Bilibili BV1wjBjYDEgF](https://www.bilibili.com/video/BV1wjBjYDEgF/) |

均为公开候选音频，许可 unknown；没有依据标题把“HiRes/无损/修复”认定为事实。目标文件采样率 96kHz，源文件 48kHz，均双声道。来源回执、哈希及选择理由见 [input-selection](evidence/stage2/input-selection.json)。用户原素材与下载流未改动。

## 工具和参数

- 已审计的 UVR 官方 `UVR_Demucs_Model_1`（`ebf34a2db.th`）通过 Demucs 4.0.1 执行；两路 vocals/non_vocals；MPS；shifts=1、overlap=0.25、segment=7 秒、jobs=1；输出 float32 WAV / 44.1kHz / 双声道。
- 完整分离输出与逐曲命令见 `work/stage2-full/separated/manifest.json`；source 的完整 vocals 和 no_vocals 均保留，时间轴未截断。
- target vocals 另存至 `work/stage2-target-vocals/` 再切片；FFmpeg 静音阈值 -40dB、最短静音 0.4 秒；切片 2–15 秒，单声道 44.1kHz PCM16。
- 未额外运行去混响/去和声模型，无法据自动分离保证无残留；每片 cleanliness=unreviewed。

共 17 个候选片段，合计 **221.046 秒（约 3.68 分钟）**；本轮静音规则未发现需丢弃的过短尾片。人工认可的干净总时长为 **未知**，而不是零或 221 秒。

候选时长不足 10 分钟：足以尝试 Seed-VC 的短参考零样本路线；不能据此宣称 RVC/Applio/so-vits 训练数据质量或时长已经充足，训练对照前仍需增加/审阅数据。

## 供抽听的 5 个随机切片

固定随机种子 20261016，路径与原曲时间：

- [00004_1ad9446b74.wav](../work/stage2-slices/target-slices/00004_1ad9446b74.wav)：75.681–83.186s。
- [00013_1ad9446b74.wav](../work/stage2-slices/target-slices/00013_1ad9446b74.wav)：211.837–226.837s。
- [00008_1ad9446b74.wav](../work/stage2-slices/target-slices/00008_1ad9446b74.wav)：129.248–142.563s。
- [00016_1ad9446b74.wav](../work/stage2-slices/target-slices/00016_1ad9446b74.wav)：256.837–266.121s。
- [00007_1ad9446b74.wav](../work/stage2-slices/target-slices/00007_1ad9446b74.wav)：114.248–129.248s。

## 20 秒实验输入

源片段固定为《爱很简单》60–80 秒，干净人声与伴奏裁切同一时间区间，不做变速。

参考候选以 8–15 秒长度、100ms 帧非静音比例、削波率筛选，RMS 用于排序。以下为机器选择，尚未听感确认：

- `work/stage2-clips/target_reference_1.wav`：原曲 182.730–196.017s，13.288s，活动帧比例 1.000，削波比例 0.000000。
- `work/stage2-clips/target_reference_2.wav`：原曲 167.518–182.123s，14.605s，活动帧比例 1.000，削波比例 0.000000。
- `work/stage2-clips/target_reference_3.wav`：原曲 196.837–211.837s，15.000s，活动帧比例 0.993，削波比例 0.000000。

全部命令、文件哈希、声道与采样率见 `work/stage2-clips/manifest.json`。

## 耗时和资源

5 秒 MPS 分离冒烟 10.140s；完整两曲分离 34.429s；切片 0.757s。完整分离子树峰值 RSS 2,030,551,040 bytes；这是主机进程驻留内存，不是独立显存。MPS 显存峰值 N/A（本次未采样）。所有处理在本地完成。

遗留：人工抽听、伴奏残留/混响/和声审查、更多目标素材、独立校对歌词。缺歌词时 CER 不计算；不阻塞当前短片段链路验证。
