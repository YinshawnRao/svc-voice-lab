# 七人副歌实验：素材准备

查阅与执行：2026-10-16。所有音频均在本地处理；未上传。

## 源片段

张惠妹《如果你也听说》，使用本地离线Whisper定位副歌，再查看100ms人声RMS寻找乐句边界；选取67.3–100.6秒，共33.3秒。略长于30秒是为保留副歌第一段的结尾乐句。定位为机器辅助，非人工听感审核。
转写证据：`work/stage9-chorus-asr/transcript.json`、`work/stage9-chorus-refine/transcript.json`。
源页面：https://www.bilibili.com/video/BV1Ky4y1J7nq/ ，上传者郑在韩国；未把标题中的official当作官方上传认证。

## 工具与参数

UVR_Demucs_Model_1，`--two-stems vocals -d mps --shifts 1 --overlap 0.25 --segment 7 --float32 -j 1`。参数与模型沿用已审计的环境。
按静音切片：参数见`config/lab.json`和各切片manifest；候选片段2–15秒。参考选择8–15秒内非静音覆盖高、削波少的片段，以RMS打破平局；最终每人使用15秒。
统一44.1kHz；源人声/参考单声道、伴奏/原唱双声道。原音频不修改。未额外去混响/去和声，不声称自动筛选保证干净。

| 歌手 | 参考歌 | 原曲参考区间/s | 候选时长/s |
|---|---|---|---:|
| 孙燕姿 | 我怀念的 | [202.307007, 217.307007] | 234.67 |
| 蔡依林 | 天空 | [200.127415, 215.127415] | 225.30 |
| 萧亚轩 | 错的人 | [189.094785, 204.094785] | 248.31 |
| 梁静茹 | 崇拜 | [228.574104, 243.574104] | 224.12 |
| 张韶涵 | 亲爱的那不是爱情 | [41.227755, 56.227755] | 197.06 |
| 杨丞琳 | 雨爱 | [180.589705, 195.589705] | 200.17 |
| 王心凌 | 变成陌生人 | [182.029252, 197.029252] | 191.17 |

所有候选素材均不足10分钟；人工确认干净时长尚未测。本轮为零样本15秒参考，不适合作为充分的训练型素材准备证明。

## 各歌手随机抽听片段

### 孙燕姿《我怀念的》

- `work/stage9-stefanie-slices/target-slices/00004_40cc4ffc87.wav`
- `work/stage9-stefanie-slices/target-slices/00023_40cc4ffc87.wav`
- `work/stage9-stefanie-slices/target-slices/00017_40cc4ffc87.wav`
- `work/stage9-stefanie-slices/target-slices/00016_40cc4ffc87.wav`
- `work/stage9-stefanie-slices/target-slices/00021_40cc4ffc87.wav`

### 蔡依林《天空》

- `work/stage7-jolin-slices/target-slices/00004_c64972c2c0.wav`
- `work/stage7-jolin-slices/target-slices/00011_c64972c2c0.wav`
- `work/stage7-jolin-slices/target-slices/00008_c64972c2c0.wav`
- `work/stage7-jolin-slices/target-slices/00013_c64972c2c0.wav`
- `work/stage7-jolin-slices/target-slices/00010_c64972c2c0.wav`

### 萧亚轩《错的人》

- `work/stage9-elva-slices/target-slices/00004_66c9e11b15.wav`
- `work/stage9-elva-slices/target-slices/00023_66c9e11b15.wav`
- `work/stage9-elva-slices/target-slices/00017_66c9e11b15.wav`
- `work/stage9-elva-slices/target-slices/00016_66c9e11b15.wav`
- `work/stage9-elva-slices/target-slices/00021_66c9e11b15.wav`

### 梁静茹《崇拜》

- `work/stage8-fish-slices/target-slices/00004_4fdb5de419.wav`
- `work/stage8-fish-slices/target-slices/00011_4fdb5de419.wav`
- `work/stage8-fish-slices/target-slices/00008_4fdb5de419.wav`
- `work/stage8-fish-slices/target-slices/00013_4fdb5de419.wav`
- `work/stage8-fish-slices/target-slices/00010_4fdb5de419.wav`

### 张韶涵《亲爱的那不是爱情》

- `work/stage9-angela-slices/target-slices/00002_5fd0001d62.wav`
- `work/stage9-angela-slices/target-slices/00011_5fd0001d62.wav`
- `work/stage9-angela-slices/target-slices/00008_5fd0001d62.wav`
- `work/stage9-angela-slices/target-slices/00012_5fd0001d62.wav`
- `work/stage9-angela-slices/target-slices/00010_5fd0001d62.wav`

### 杨丞琳《雨爱》

- `work/stage5-rainie-slices/target-slices/00002_3285205575.wav`
- `work/stage5-rainie-slices/target-slices/00011_3285205575.wav`
- `work/stage5-rainie-slices/target-slices/00008_3285205575.wav`
- `work/stage5-rainie-slices/target-slices/00012_3285205575.wav`
- `work/stage5-rainie-slices/target-slices/00010_3285205575.wav`

### 王心凌《变成陌生人》

- `work/stage8-cyndi-slices/target-slices/00004_3dae262166.wav`
- `work/stage8-cyndi-slices/target-slices/00017_3dae262166.wav`
- `work/stage8-cyndi-slices/target-slices/00016_3dae262166.wav`
- `work/stage8-cyndi-slices/target-slices/00013_3dae262166.wav`
- `work/stage8-cyndi-slices/target-slices/00008_3dae262166.wav`

## 命令与耗时

- source 分离：23.391秒，子进程RSS峰值2.48GiB；MPS峰值未采样，N/A。命令见同名evidence JSON。
- stefanie 分离：21.244秒，子进程RSS峰值2.53GiB；MPS峰值未采样，N/A。命令见同名evidence JSON。
- elva 分离：13.94秒，子进程RSS峰值2.25GiB；MPS峰值未采样，N/A。命令见同名evidence JSON。
- angela 分离：12.821秒，子进程RSS峰值2.37GiB；MPS峰值未采样，N/A。命令见同名evidence JSON。

新增4个音频下载共82,197,108字节；每文件远低于5GB，详见下载台账（台账为准确预算来源）。
孙燕姿首个候选码率偏低，仅探测未下载；改选另一份MV的FLAC音频流。编码格式不等于原始母带或无损来源认证。
遗留/修复：旧《雨爱》参考manifest缺少original_interval_seconds；首次准备抛出KeyError。已按原切片manifest和SHA256补齐新实验元数据，核验后续跑；不修改旧音频。失败日志`logs/stage9-clips-launch.log`，修复重跑`logs/stage9-clips-retry1.log`，一次修复成功。
输入校验：`reports/evidence/stage9/inputs-validation.json`，七人source完全一致、七份reference互不相同，且源音频不是旧《听海》。
