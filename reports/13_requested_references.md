# 指定参考重生成：雨爱 / 不痛 / 天空

2026-10-16。用户明确要求重新生成杨丞琳、张韶涵、蔡依林音色的《听海》，并覆盖原目录。沿用此前原MV106–136秒的30秒副歌，A30/B50、F0开启、原调、CFG0.7、length1、FP32、种子20261016；只按指定歌曲调整目标参考。杨丞琳仍为《雨爱》，同参考也实际重新执行两版，不把旧文件复制当作重生成。

固定Seed-VC SHA `51383efd921027683c89e5348211d93ff12ac2a8`，已于本日重读本地审计README的歌声/F0设置。推理、分离环境与官方模型沿用，不新增权重/依赖；MPS与CPU混合执行，音频全程本地处理。主观评价仍待用户试听，CER没有独立校对歌词时为N/A。

## 执行状态

| 目标音色 | 指定参考 | 状态 | 最终覆盖目录 |
|---|---|---|---|
| 杨丞琳 | 雨爱 | 已重新生成、核验并覆盖 | `outputs/stage5-rainie-tinghai/` |
| 张韶涵 | 不痛 | 已重新生成、核验并覆盖 | `outputs/stage4-angela-tinghai/` |
| 蔡依林 | 天空 | 已重新生成、核验并覆盖 | `outputs/stage6-jolin-tinghai/` |

新生成使用stage7独立工作目录；通过文件、时长、输入哈希和播放器检查后替换原目录。旧目录及旧报告保存在 `work/stage7-replaced/`，保留真实旧指标和来源。`reports/evidence/stage7/before-files.json`记录本轮操作前62个输出/原始素材文件的哈希和大小；仅以上三个成品目录属于覆盖范围。

杨丞琳参考复用已核验《雨爱》原180.590–195.590秒的15秒人声。源人声、伴奏、原唱对照复制自前轮并核验逐字节一致。初始下载预算3,436,060,042 bytes，媒体下载继续使用受审计的 `scripts/media.py`，来源与大小记录于 [downloads.md](downloads.md)。

## 素材来源与网络问题

- 《雨爱》复用之前已核验的独立音轨/切片，不重复下载；本轮确实执行新的A/B推理。同输入、同参考、同种子可能产生相同解码波形，不刻意改变参数制造差异。
- 《不痛》优先尝试福茂唱片官方YouTube页面 `https://www.youtube.com/watch?v=zXHqzoroAj4`，音轨传输超时，138.308秒后退出，保守计入4,295,208 bytes。随后成功取得[同曲MV](https://www.bilibili.com/video/BV1Vf4y1x7dP/)，发布者zyl2012_音乐无限，AAC30280音轨9,918,324 bytes，下载/解码10.616秒；派生WAV247.850667秒、48kHz双声道。
- 《天空》官方频道 `https://www.youtube.com/watch?v=hmyEkTioX5E` 传输缓慢，158.017秒时主动中断，部分文件保留，5,812,791 bytes保守预留不自动清零。索尼音乐中国[官方MV](https://www.bilibili.com/video/BV1rJ411x7zg/)的音轨预检返回404（5.689秒，无传输）。最终成功取得[同曲MV备用来源](https://www.bilibili.com/video/BV1iLMJzpEmP/)，发布者zyl2012_音乐无限，FLAC30251音轨68,774,931 bytes，下载/解码17.402秒；派生WAV347.747417秒、48kHz双声道。

两个最终来源的媒体许可证均unknown，页面“4K修复”不证明音频母带质量。实际处理以本地解码波形为准。未下载第三方明星模型。所有完整/失败下载和保留的部分文件记录于downloads台账；中断的《天空》记录只计落盘字节下界，完整预计大小仍由reservation保守覆盖。失败证据位于 `logs/media/` 与 `reports/evidence/media-events/`；没有修改Cookie、网络或系统设置。

`reports/evidence/stage7/input-preflight.json`已验证两个新目标的成功回执、字节数和SHA256；未在失败下载后错误启动分离。三个目标各自独立处理，源片段继续按原哈希复用。

## 杨丞琳：雨爱（已完成覆盖）

[同步试听页](../outputs/stage5-rainie-tinghai/listen.html)。参考来自指定《雨爱》原音频 **180.590–195.590秒**，长度15.000秒；activity=100.00%，clipping=0.0。共15段、200.169秒候选人声，**不足10分钟**，人工确认的干净总时长未知。

本轮复用原《雨爱》分离/切片，不重复预处理；两版实际重新执行。新旧A/B干声和混音的解码采样均相同（已逐采样比较）；听感不会因这次同参数重跑而改变。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage5-rainie-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage5-rainie-tinghai/seed-vc_A_AI.wav) | 300.946s | 0.7989 | 0.9965 | 78.46% | 7.73 | -13.6 |
| B50 | [试听](../outputs/stage5-rainie-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage5-rainie-tinghai/seed-vc_B_AI.wav) | 344.001s | 0.8030 | 0.9969 | 78.43% | 7.69 | -14.0 |

转换总耗时651.189秒，评测/混音12.487秒。MPS allocated/driver采样峰值3.59/5.66GiB，推理RSS峰值4.20GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

固定随机种子抽5条供人工抽听：

- [00002_3285205575.wav](../work/stage5-rainie-slices/target-slices/00002_3285205575.wav)，原参考歌曲57.610–72.610秒。
- [00011_3285205575.wav](../work/stage5-rainie-slices/target-slices/00011_3285205575.wav)，原参考歌曲195.590–210.590秒。
- [00008_3285205575.wav](../work/stage5-rainie-slices/target-slices/00008_3285205575.wav)，原参考歌曲150.590–165.590秒。
- [00012_3285205575.wav](../work/stage5-rainie-slices/target-slices/00012_3285205575.wav)，原参考歌曲210.590–225.590秒。
- [00010_3285205575.wav](../work/stage5-rainie-slices/target-slices/00010_3285205575.wav)，原参考歌曲180.590–195.590秒。

实际生成命令：

```bash
python3 scripts/run_stage2_poc.py --run-id stage7-rainie-tinghai --clips work/stage7-rainie-tinghai-clips --evidence-dir reports/evidence/stage7 --device mps
python3 work/stage7-tools/publish.py rainie
```

以上为本次记录，不能原样重复覆盖；常规复现须换新run-id及evidence路径。覆盖是本次用户的显式授权，替换前后验证记录见 `reports/evidence/stage7/rainie-published.json`。

《天空》主参考另用离线Whisper检查15秒内容，记录 `work/stage7-jolin-reference-asr/transcript.json`：输出为连续歌词片段形式，未用MV开场片段。该检查仅用于排查对白选段，不证明歌手身份、转写准确或没有和声；不作为CER真值。执行7.797秒，进程RSS峰值约0.63GiB，MPS峰值未采样。

## 张韶涵：不痛（已完成覆盖）

[同步试听页](../outputs/stage4-angela-tinghai/listen.html)。参考来自指定《不痛》原音频 **203.283–218.283秒**，长度15.000秒；activity=100.00%，clipping=0.0。共13段、176.044秒候选人声，**不足10分钟**，人工确认的干净总时长未知。

目标分离33.056秒，进程RSS峰值2.27GiB，MPS峰值未采样；切片0.755秒。目标独立处理，新参考哈希不同于旧轮次；source三条音轨均按哈希确认完全相同。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage4-angela-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage4-angela-tinghai/seed-vc_A_AI.wav) | 240.678s | 0.8237 | 0.9980 | 78.39% | 7.36 | -11.6 |
| B50 | [试听](../outputs/stage4-angela-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage4-angela-tinghai/seed-vc_B_AI.wav) | 257.429s | 0.8292 | 0.9980 | 78.39% | 7.35 | -12.0 |

转换总耗时502.828秒，评测/混音8.696秒。MPS allocated/driver采样峰值3.59/5.92GiB，推理RSS峰值5.32GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

固定随机种子抽5条供人工抽听：

- [00002_c0b49bea6d.wav](../work/stage7-angela-slices/target-slices/00002_c0b49bea6d.wav)，原参考歌曲65.042–80.042秒。
- [00011_c0b49bea6d.wav](../work/stage7-angela-slices/target-slices/00011_c0b49bea6d.wav)，原参考歌曲203.283–218.283秒。
- [00008_c0b49bea6d.wav](../work/stage7-angela-slices/target-slices/00008_c0b49bea6d.wav)，原参考歌曲158.283–173.283秒。
- [00010_c0b49bea6d.wav](../work/stage7-angela-slices/target-slices/00010_c0b49bea6d.wav)，原参考歌曲188.283–203.283秒。
- [00006_c0b49bea6d.wav](../work/stage7-angela-slices/target-slices/00006_c0b49bea6d.wav)，原参考歌曲128.283–143.283秒。

实际生成命令：

```bash
python3 scripts/run_stage2_poc.py --run-id stage7-angela-tinghai --clips work/stage7-angela-tinghai-clips --evidence-dir reports/evidence/stage7 --device mps
python3 work/stage7-tools/publish.py angela
```

以上为本次记录，不能原样重复覆盖；常规复现须换新run-id及evidence路径。覆盖是本次用户的显式授权，替换前后验证记录见 `reports/evidence/stage7/angela-published.json`。

## 蔡依林：天空（已完成覆盖）

[同步试听页](../outputs/stage6-jolin-tinghai/listen.html)。参考来自指定《天空》原音频 **200.127–215.127秒**，长度15.000秒；activity=100.00%，clipping=0.0。共16段、225.298秒候选人声，**不足10分钟**，人工确认的干净总时长未知。

目标分离44.494秒，进程RSS峰值2.64GiB，MPS峰值未采样；切片1.770秒。目标独立处理，新参考哈希不同于旧轮次；source三条音轨均按哈希确认完全相同。

| 版本 | 混音 | 纯人声 | 推理耗时 | 目标cosine | F0 r | 有声覆盖 | 中位音分误差 | LUFS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A30 | [试听](../outputs/stage6-jolin-tinghai/seed-vc_A_mix_AI.wav) | [试听](../outputs/stage6-jolin-tinghai/seed-vc_A_AI.wav) | 182.193s | 0.8029 | 0.9950 | 78.13% | 8.03 | -13.0 |
| B50 | [试听](../outputs/stage6-jolin-tinghai/seed-vc_B_mix_AI.wav) | [试听](../outputs/stage6-jolin-tinghai/seed-vc_B_AI.wav) | 237.073s | 0.8052 | 0.9950 | 78.13% | 7.89 | -13.4 |

转换总耗时422.677秒，评测/混音8.155秒。MPS allocated/driver采样峰值3.59/5.92GiB，推理RSS峰值5.48GiB；统一内存各计数有重叠，不能相加，0.1秒采样可能漏峰值。

固定随机种子抽5条供人工抽听：

- [00004_c64972c2c0.wav](../work/stage7-jolin-slices/target-slices/00004_c64972c2c0.wav)，原参考歌曲108.859–123.859秒。
- [00011_c64972c2c0.wav](../work/stage7-jolin-slices/target-slices/00011_c64972c2c0.wav)，原参考歌曲215.127–230.127秒。
- [00008_c64972c2c0.wav](../work/stage7-jolin-slices/target-slices/00008_c64972c2c0.wav)，原参考歌曲170.127–185.127秒。
- [00013_c64972c2c0.wav](../work/stage7-jolin-slices/target-slices/00013_c64972c2c0.wav)，原参考歌曲275.866–290.866秒。
- [00010_c64972c2c0.wav](../work/stage7-jolin-slices/target-slices/00010_c64972c2c0.wav)，原参考歌曲200.127–215.127秒。

实际生成命令：

```bash
python3 scripts/run_stage2_poc.py --run-id stage7-jolin-tinghai --clips work/stage7-jolin-tinghai-clips --evidence-dir reports/evidence/stage7 --device mps
python3 work/stage7-tools/publish.py jolin
```

以上为本次记录，不能原样重复覆盖；常规复现须换新run-id及evidence路径。覆盖是本次用户的显式授权，替换前后验证记录见 `reports/evidence/stage7/jolin-published.json`。

## 最终交付与共同限制

| 音色 | 指定参考 | 同步试听 | A30混音 | B50混音 |
|---|---|---|---|---|
| 杨丞琳 | 雨爱 | [打开](../outputs/stage5-rainie-tinghai/listen.html) | [A](../outputs/stage5-rainie-tinghai/seed-vc_A_mix_AI.wav) | [B](../outputs/stage5-rainie-tinghai/seed-vc_B_mix_AI.wav) |
| 张韶涵 | 不痛 | [打开](../outputs/stage4-angela-tinghai/listen.html) | [A](../outputs/stage4-angela-tinghai/seed-vc_A_mix_AI.wav) | [B](../outputs/stage4-angela-tinghai/seed-vc_B_mix_AI.wav) |
| 蔡依林 | 天空 | [打开](../outputs/stage6-jolin-tinghai/listen.html) | [A](../outputs/stage6-jolin-tinghai/seed-vc_A_mix_AI.wav) | [B](../outputs/stage6-jolin-tinghai/seed-vc_B_mix_AI.wav) |

三轮均为同一段《听海》原MV106–136秒（1:46–2:16）。每人两版共用15秒目标参考，只改变30/50扩散步数，保持F0、原调、CFG和随机种子。杨丞琳仍使用原《雨爱》参考，实际重跑后的A/B干声和混音解码采样均与旧版一致；张韶涵、蔡依林已分别换成《不痛》《天空》。

CAMPPlus同时用于条件编码，cosine不是独立评价，不能解释为相似百分比，也不对不同参考歌手的分数排名。F0仅覆盖共同有声帧，起点对齐，无DTW或偏移寻优。CER缺独立校对歌词，N/A；主观音色、咬字和高音待用户试听。

六个新版本、十二个音频文件已通过时长、采样率、声道、有限值、哈希和本地链接检查；混音均精确30秒，干声29.988571秒，混音只在尾部补504采样，无变速。播放器mock DOM切换检查通过，不是实际浏览器或人工听音验收。原先30个被替换文件完整保存在work/stage7-replaced/；其余32个范围外文件大小/哈希未变。没有新增模型执行失败，媒体获取失败及中断均已留证。

预处理使用UVR_Demucs_Model_1、MPS、shifts1、overlap0.25、segment7；切片阈值-40dB/0.4秒，保留2–15秒、44.1kHz单声道PCM16。参考按8–15秒长度、非静音覆盖、低削波、RMS排序；自动排序不证明没有伴奏、混响或和声。新目标没有额外去混响/和声模型，三个目标的候选总时长均不足10分钟，不认定为合格训练集。本轮仅零样本转换，不执行训练。

完整预处理入口为 `.envs/demucs/bin/python work/stage7-tools/prepare.py angela` 和 `jolin`；命令及时间记录于本轮evidence。这些固定批次入口用于本次执行记录，复现必须使用新的目录。推理/评测模型入口未修改，没有运行无关的全套单元测试；已运行实际生成、替换前后验证和页面状态检查。

人工对照窗口可使用输出0–8、10–20、22–30秒，分别比较起句、长音/咬字、接缝；没有认定为全曲最高音或最快咬字。

## 空间与下载预算快照

| 目录 | 逻辑大小 bytes | MiB |
|---|---:|---:|
| work/ | 3,661,646,274 | 3492.02 |
| outputs/ | 266,990,264 | 254.62 |
| data/ | 488,663,780 | 466.03 |
| models/ | 2,657,889,680 | 2534.76 |
| .envs/ | 1,468,540,105 | 1400.51 |
| .cache/ | 500,547,115 | 477.36 |
| reports/ | 90,800,696 | 86.59 |

本轮新增计费82,988,463 bytes，另保留已中断YouTube下载的5,812,791 bytes保守预留；没有该下载进程仍在运行，也没有自动清零预留。累计计费3,519,048,505 bytes，加预留合计3,524,861,296/30,000,000,000 bytes。磁盘可用116,112,859,136 bytes。逐文件来源、大小、许可和哈希见 [downloads.md](downloads.md)。目录为逻辑大小快照，后续报告写入会略变；旧文件移入本地证据目录，未删除其他内容，未commit、push或发布。
