# 六人《我知道你很难过》准备

日期：2026-10-18。新建独立实验 stage18-nanguo，成品目录 outputs/stage18-six-nanguo/。按“四大三小其中6个人”排除原唱蔡依林，制作孙燕姿、萧亚轩、梁静茹、张韶涵、杨丞琳、王心凌。

完整默认阵容冻结于 reports/evidence/stage18/default-roster.json，SHA256 `c228d2daea315fa2b0509c6a9bd23e49c8796a38b2ab9fe9528ac3eb2f8f8f8a`。六份既有15秒参考已逐一核验歌手、歌曲、原区间与SHA256，不换曲、不重新挑片。每人零样本参考，不训练；各参考候选不足10分钟，未经人工确认的干净总时长 N/A。

复核本地官方 Seed-VC README 与锁定 commit `51383efd921027683c89e5348211d93ff12ac2a8`，README SHA256 `293507df928d542341a69b9c93e3b7344f7cc7abe73ac4b2c6395d86527a1ce4`。歌声模型为 V1 `seed-uvit-whisper-base`。README 写明歌唱转换使用 f0-condition、不使用 auto-f0-adjust、0 半音、CFG 0.7，扩散步数建议 30–50。本轮按用户默认取 30 步。README 的 fp16 默认在本机改为已审计的 FP32；MPS 跑扩散、Whisper、CAMPPlus，CPU 跑 BigVGAN、RMVPE 和频谱。没有新安装或新权重。显存峰值未测项目写 N/A；MPS 分配与驱动读数分开记录，不是独立显存。

stage17《突然想起你》批次当时仍在运行。本轮在分离和冒烟前等待其结束，排队 390.849 秒，没有中断该进程。677 个已完成成品、参考片段和历史配置已记录大小与 SHA256；当时仍在变化的 stage17 文件不纳入保护清单。

## 素材

统一媒体入口 doctor 通过，yt-dlp 2026.06.09。Cookie 只经只读快照使用。

先下载华纳音乐 Warner Music Taiwan 的 [Jolin 我知道你很難過](https://www.youtube.com/watch?v=3b6fqTMNaU4)。opus 精确 4,313,533 字节，SHA256 `ecc410c27387bfb8fd68a03c27a4d9bc2bdbfb63fa72807654d93426c16b6957`；派生 WAV 47,277,394 字节，48 kHz 立体声，246.236 秒。分离后人声的离线 ASR 开头是“大家会不会唱”，并出现万人合唱，因此不作为转换源。原始流、WAV、分离结果和回执保留。

[Golden Era 歌词版](https://www.youtube.com/watch?v=ppEp4uShYuQ) 已探测，265 秒，opus 精确 4,442,056 字节。第一次 GET 超时且 0 字节；同一地址重试返回 HTTP 403。两次失败目录保留，未覆盖。

改用 [Peculiar音樂 265 秒上传](https://www.youtube.com/watch?v=wcl8NMTSPWY)。标题为高音质，上传者不是厂牌，许可证 unknown。opus 精确 4,372,614 字节，SHA256 `5935dee7020e5c3240f8af5c4f95b0f3384e9e15a9e52a8e7cac4c558eaac7e5`；派生 WAV 50,881,874 字节，48 kHz 立体声，265.009 秒，SHA256 `09a931bc605714ebdfe00838b1fa86693be20afdffdc2f43c54be06b96b17c4f`。开头短窗识别为歌名接第一段主歌，没有现场口播。

## 副歌定位与预处理

选定第一段完整副歌 81.10–117.40 秒，共 36.3 秒。开头 0–20 秒只有歌名和衬词，不是完整副歌。74 秒短窗把前句结束在 81.04 秒；人声 RMS 在 80.5 秒后落到接近底噪，副歌起音在 81.3 秒，因此从 81.10 秒切入。末句短窗把“伤得比较久”识别到 116.28 秒；116.6 秒后 RMS 低于 0.001，直到约 125 秒才重新有能量。122 秒短窗识别的是下一段主歌。收在 117.40 秒，保留尾音，不带入下一句。长窗口时间戳有漂移，边界以短窗和波形为准。非人工听音，CER=N/A。

分离使用 UVR_Demucs_Model_1，MPS，two-stems vocals、shifts 1、overlap 0.25、segment 7、float32。正式源分离 17.530 秒，全曲人声 ASR 22.943 秒。被放弃的现场源分离 13.645 秒。分离 MPS 峰值未采样，记 N/A；日志里的 RSS 不是显存。

4 秒 30 步 MPS 技术冒烟通过，外层耗时 38.175 秒。证据 smoke-validation.json。短片段不替代正式副歌。

六人共用这一段。片段 44100 Hz PCM16，人声单声道，伴奏和原曲双声道。六份 target 是既有 15 秒参考的逐字节复制。
