# 七人《后来》与默认参考固定

日期：2026-10-18。用户要求新建独立实验，沿用心墙/小幸运七人参考，固定为后续默认，手动指定优先。

已写入 AGENTS.md、config/default-roster.json、config/lab.json 与 README。七份参考已核验，均复用相同15秒；王心凌使用我会好好的。参考自动筛选并非人工纯净度认证。

本轮沿用前两首完整副歌试听口径，边界将由本地 Whisper 与人声能量定位。30步单版、F0开启、autoF0关闭、0半音、CFG0.7、FP32、seed20261016。本地复核 vendor/seed-vc/README.md，锁定 commit 51383efd921027683c89e5348211d93ff12ac2a8；无新模型或依赖。

旧数据、成品、历史实验配置359个文件已保存SHA256保护清单；全局文档修改前备份到 work/stage12-before/。不删除或覆盖旧音频。

媒体通过 scripts/media.py doctor→probe→download。优先[滚石官方 MV](https://www.youtube.com/watch?v=t0igPuDjYUE)，备用[Bilibili存档](https://www.bilibili.com/video/BV1gE411q7sS/)上传者郑在韩国；标题不证明许可证，unknown。来源、大小、哈希及失败计费见下载台账。

## 源素材获取

滚石官方YouTube MV首个下载尝试成功，耗时194.650秒；备用Bilibili仅探测，未下载。Opus流6,040,444 bytes，SHA256=f7843f15a28930763f4bb6d250b537efc07a9e551206e05bc51f5c1dd6dcf2b0。派生WAV65,302,022 bytes，48kHz双声道，340.114292秒，SHA256=784a2c229766139cde97fa5f41f814145ca2b5afaee6ea9da6bd588b5e061728。许可证unknown，原流/原WAV/receipt均保留。

关键命令：

```sh
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt doctor
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt probe https://www.youtube.com/watch?v=t0igPuDjYUE
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt download https://www.youtube.com/watch?v=t0igPuDjYUE --kind audio --run-id stage12-source-houlai --role source --purpose 七人固定参考阵容演唱刘若英后来，副歌源歌曲
.envs/demucs/bin/python scripts/run_houlai_experiment.py prepare-source --song houlai
```

网络阶段未使用GPU，显存=N/A。下载台账已记录来源、精确大小、许可证与哈希。

## 分离与副歌边界

本轮采用主歌后完整副歌159.1–187.1秒（2:39.1–3:07.1），共28.0秒，包含两部分及末句尾音。细化ASR首句约159.2秒；人声尾音在186.6秒衰减至RMS<0.003，截止187.1秒，避免误切尾音。ASR仅辅助定位，不用作CER真值；无人工听音声明。

参数：UVR_Demucs_Model_1，MPS，two-stems vocals，shifts1，overlap0.25，segment7，float32。共同人声44100Hz单声道，伴奏/原曲44100Hz双声道，PCM16；七人引用同一份源切片。

stage12-houlai-separate：耗时29.875秒；资源字段及完整命令见对应JSON。
stage12-houlai-asr：耗时27.842秒；资源字段及完整命令见对应JSON。
stage12-houlai-asr-refine：耗时12.748秒；资源字段及完整命令见对应JSON。

分离MPS峰值未采样，N/A；进程RSS与显存不是同一指标。Whisper后时点统一内存读数并非峰值。
七位均复用现成15秒参考，不重新挑片，无新增参考歌曲下载。来源总量均不足10分钟，本轮零样本无需训练。原切片列表与自动筛选证据仍在原manifest中。

```sh
.envs/demucs/bin/python scripts/run_houlai_experiment.py clips --song houlai --start 159.1 --end 187.1
python3 scripts/run_houlai_experiment.py generate --song houlai
```
